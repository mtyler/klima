#!/opt/homebrew/bin/python3
import argparse
import signal
import subprocess
import sys

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

def main(args):
    if args.node:
        vm_names = get_vm_names()
        if args.node in vm_names:
            drain_and_remove_node(args.node)
            stop_and_remove_vm(args.node)
            print(f"VM {args.node} stopped and removed")
        return
    
    input("This will destroy all lima VMs and disks. Press Enter to continue...")
    
    vm_names = get_vm_names()
    for vm_name in vm_names:
        stop_and_remove_vm(vm_name)
    print("VMs stopped and removed")

    d_names = get_disk_names()
    for d_name in d_names:
        remove_disk(d_name)
    print("Disks removed")
    
    subprocess.run(['limactl', 'list'])
    subprocess.run(['limactl', 'disk', 'list'])

def signal_handler(sig, frame): 
    sys.exit(0)
        
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Destroy lima VMs and disks")
    parser.add_argument('--node', '-n', required=False, type=str, help='remove a single node from a k8s cluster')
    args = parser.parse_args()
    signal.signal(signal.SIGINT, signal_handler)
    main(args)