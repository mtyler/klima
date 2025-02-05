#!/opt/homebrew/bin/python3

import os
import signal
import subprocess
import sys

def get_vm_names():
    result = subprocess.run(['limactl', 'list', '--format', '{{.Name}}'], capture_output=True, text=True)
    return result.stdout.splitlines()

def run_command(command):
    result = subprocess.run(command, shell=True, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    #    result = subprocess.run(command, shell=True, check=True)
    return result.stdout.decode('utf-8')

def main():
    CP = "cp1"
    try:
        if CP not in get_vm_names():
            run_command("limactl disk create {}-data --size=50GiB --format=raw".format(CP))
            run_command("limactl create --name=cp1 ./k8s-base.yaml --set '.additionalDisks[0].name = \"{}-data\" | .additionalDisks[0].format = false' --tty=false".format(CP))
            run_command("limactl start cp1 --tty=false")

            # Copy the kubeconfig file to the host
            run_command("cp ../data/lima/k8scfg/admin.conf ~/.kube/config")
            run_command("kubectl get nodes")
            print("Control Plane is ready")

        input("Press Enter to add worker nodes...")

        for node in ["n1", "n2", "n3"]:
            print("Creating {}".format(node))
            run_command("limactl disk create {}-data --size=50GiB --format=raw".format(node))
            run_command("limactl create --name={} ./k8s-base.yaml --set '.additionalDisks[0].name = \"{}-data\" | .additionalDisks[0].format = false' --tty=false".format(node, node))
            run_command("limactl start {} --tty=false".format(node))
            print("{} is ready".format(node))
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
