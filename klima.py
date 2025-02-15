#!/opt/homebrew/bin/python3
import argparse
import os
import signal
import subprocess
import sys
import signal
from time import sleep, time


template = "k8s-base.yaml"
CWD = f"{os.path.dirname(os.path.abspath(__file__))}/"
klima_work_dir = ".klima/k8scfg"
first_cp_name = "cp1"
k8s_node_prefix = "lima-"


def get_vm_names():
    result = subprocess.run(['limactl', 'list', '--format', '{{.Name}}'], capture_output=True, text=True)
    return result.stdout.splitlines()

def get_disk_names():
    result = subprocess.run(['limactl', 'disk', 'list'], capture_output=True, text=True)
    lines = result.stdout.splitlines()
    disk_names = []
    for line in lines:
        parts = line.split()
        if len(parts) > 0 and parts[0] != 'NAME':
            disk_names.append(parts[0])
    return disk_names

def stop_and_remove_vm(vm_name):
    print(f"Stopping and removing {vm_name}")
    subprocess.run(['limactl', 'stop', vm_name])
    subprocess.run(['limactl', 'delete', vm_name])

def remove_disk(d_name):
    subprocess.run(['limactl', 'disk', 'delete', d_name])

def drain_and_remove_node(vm_name):
    print(f"Draining and removing node {vm_name}")
    subprocess.run(['kubectl', 'drain', f"lima-{vm_name}", '--delete-local-data', '--force', '--ignore-daemonsets'])
    subprocess.run(['kubectl', 'delete', 'node', f"lima-{vm_name}"])


def klober_main(args):
    if args.node:
        vm_names = get_vm_names()
        if args.node in vm_names:
            drain_and_remove_node(args.node)
            stop_and_remove_vm(args.node)
            print(f"VM {args.node} stopped and removed")
        return
    
    if not args.force:
        input("!!! WARNING !!! \n\n \
This is a permanent action. All lima VMs and disks will be lost forever. \n \
Press Enter to continue...\n")
    
    vm_names = get_vm_names()
    for vm_name in vm_names:
        stop_and_remove_vm(vm_name)
    print("VMs stopped and removed")

    d_names = get_disk_names()
    for d_name in d_names:
        remove_disk(d_name)
    print("Disks removed")
    
    subprocess.run(['rm', '-rf', './.klima'])
    print("klima working directory removed")

    subprocess.run(['limactl', 'list'])
    subprocess.run(['limactl', 'disk', 'list'])


def get_vm_names():
    result = subprocess.run(['limactl', 'list', '--format', '{{.Name}}'], capture_output=True, text=True)
    return result.stdout.splitlines()

def verify_node(node):
    result = subprocess.run(['kubectl', 'get', 'node', node, '-o=jsonpath={.metadata.name}'], capture_output=True, text=True)
    if result.stdout.splitlines()[0] == node:
        print(f"{node} is ready")
        return True
    else:
        print(f"{node} is not ready")
        return False

def run_command(command):
    result = subprocess.run(command, shell=True, check=True)
    if result.stdout != None:
        print(result.stdout.decode('utf-8'))
    if result.stderr != None:
        print(result.stderr.decode('utf-8'))
    return #result.stdout.decode('utf-8')

def up_main():
    os.makedirs(CWD+klima_work_dir, exist_ok=True)
    try:
        if first_cp_name not in get_vm_names():
            # TODO: make disks configurable
            ## remove disk from CP to avoid conjestion from ceph
            ##run_command("limactl disk create {}-data --size=50GiB --format=raw".format(CP))
            ##run_command(f"limactl create --name=cp1 {template} --set '.additionalDisks[0].name = \"{}-data\" | .additionalDisks[0].format = false' --tty=false".format(CP))
            run_command(f"limactl create --name=cp1 {template} --tty=false")
            run_command("limactl start cp1 --tty=false")
            print("Control Plane has been started")

            # Copy the kubeconfig file to the host
            run_command(f"cp {CWD}{klima_work_dir}/admin.conf ~/.kube/config")
            run_command("kubectl get nodes")
            
            if verify_node(f"{k8s_node_prefix}{first_cp_name}"):
                print("Control Plane is ready. Waiting 30s to begin adding worker nodes")
                sleep(30)
            else:
                sys.exit(1)

#        input("Ctrl+C to stop. Press Enter to add worker nodes...")
#        #TODO: Add a parser to get -q or --quiet flag to skip the input prompt
#        #TODO: Add a check to wait for the CP to be ready before proceeding

        for node in ["n1", "n2", "n3"]:
            print(f"Creating {node}")
            run_command(f"limactl disk create {node}-data --size=50GiB --format=raw")
            run_command(f"limactl create --name={node} {template} --set '.additionalDisks[0].name = \"{node}-data\" | .additionalDisks[0].format = false' --tty=false")
            run_command(f"limactl start {node} --tty=false")
            verify_node(f"{k8s_node_prefix}{node}")

    except subprocess.CalledProcessError as e:
        print(f"An error occurred: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
    finally:
        pass
        # print("Exiting gracefully")

def main(args):
    if args.up:
        up_main()
    elif args.klober:
        klober_main(args)

def signal_handler(sig, frame): 
    sys.exit(0)
        
if __name__ == "__main__":
    start_time = time()
    def print_total_time():
        total_time = time() - start_time
        print(f"Execution time: {total_time / 60:.2f} minutes")

    parser = argparse.ArgumentParser(description="Manage lima VMs and disks")
    task_group = parser.add_mutually_exclusive_group(required=True)
    task_group.add_argument('--klober', action='store_true', help='remove all VMs and disks')
    task_group.add_argument('--up', action='store_true', help='stand up all VMs and disks')
    parser.add_argument('--node', '-n', required=False, type=str, help='remove a single node from a k8s cluster')
    parser.add_argument('--force', '-f', required=False, action='store_true', help='force remove all VMs and disks')
    args = parser.parse_args()
    signal.signal(signal.SIGINT, signal_handler)
    
    main(args)

    print_total_time()