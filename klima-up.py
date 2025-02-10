#!/opt/homebrew/bin/python3
import os
import signal
import subprocess
import sys

template = "k8s-base.yaml"
CWD = f"{os.path.dirname(os.path.abspath(__file__))}/"
klima_work_dir = ".klima/k8scfg"
first_cp_name = "cp1"


def get_vm_names():
    result = subprocess.run(['limactl', 'list', '--format', '{{.Name}}'], capture_output=True, text=True)
    return result.stdout.splitlines()

def run_command(command):
    result = subprocess.run(command, shell=True, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    print(result.stdout.decode('utf-8'))
    print(result.stderr.decode('utf-8'))
    return #result.stdout.decode('utf-8')

def main():
    os.makedirs(klima_work_dir, exist_ok=True)
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
            
        input("Ctrl+C to stop. Press Enter to add worker nodes...")
        #TODO: Add a parser to get -q or --quiet flag to skip the input prompt
        #TODO: Add a check to wait for the CP to be ready before proceeding

        for node in ["n1", "n2", "n3"]:
            print(f"Creating {node}")
            run_command(f"limactl disk create {node}-data --size=50GiB --format=raw")
            run_command(f"limactl create --name={node} {template} --set '.additionalDisks[0].name = \"{node}-data\" | .additionalDisks[0].format = false' --tty=false")
            run_command(f"limactl start {node} --tty=false")
            print(f"{node} is ready")
    except subprocess.CalledProcessError as e:
        print(f"An error occurred: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
    finally:
        pass
        # print("Exiting gracefully")

def signal_handler(sig, frame): 
    sys.exit(0)

if __name__ == "__main__":
    signal.signal(signal.SIGINT, signal_handler)

    main()
