#!/opt/homebrew/bin/python3
import argparse
import os
import signal
import subprocess
import sys
import signal
from time import sleep, time

CWD = f"{os.path.dirname(os.path.abspath(__file__))}/"
klima_work_dir = ".klima/k8scfg"
first_cp_name = "cp1"
k8s_node_prefix = "lima-"
USER_HOME_DIR = os.path.expanduser("~")

class Knode:
    k8s_prefix = "lima-"
    template = "k8s-cluster.yaml"
    
    def __init__(self, name, cpu, mem, disk_size, additional_disk_size, role):
        self.name = name
        self.cpu = cpu
        self.mem = mem
        self.disk_size = disk_size
        self.additional_disk_size = additional_disk_size
        self.role = role

    def create(self):
        if debug: print(f"Creating {self.name}")
        with_disk = ""
        if self.additional_disk_size:
            run_cmd(f"limactl disk create {self.get_diskname()} --size={self.additional_disk_size} --format=raw")
            with_disk = f"| .additionalDisks[0].name = \"{self.get_diskname()}\" | .additionalDisks[0].format = false"

        # automating the command limactl create --name=cp1 k8s-cluster.yaml --set '.disk = "30GiB" | .cpus = 2 | .memory = "4GiB"' --tty=false 
        return run_cmd(f"limactl create --name={self.name} {self.template} --set '.disk = \"{self.disk_size}\" | .cpus = {self.cpu} | .memory = \"{self.mem}\" {with_disk}' --tty=false")

    def start(self):
        if debug: print(f"Starting {self}")
        #run_command(f"limactl start {self.name} --tty=false")
        run_cmd(f"limactl start --name={self.name} --tty=false")

    def stop(self):
        run_cmd(f"limactl stop {self.name}")

        
    def kill_vm(self):
        if debug: print(f"Stopping and removing {self.name}")
        if self.is_vm():
            subprocess.run(['limactl', 'stop', self.name])
            subprocess.run(['limactl', 'delete', self.name])
        else:
            if debug: print(f"{self.name} is not a VM")

    def pull_node(self):
        if debug: print(f"Draining and removing node {self.name}")
        subprocess.run(['kubectl', 'drain', f"lima-{self.name}", '--delete-local-data', '--force', '--ignore-daemonsets'])
        subprocess.run(['kubectl', 'delete', 'node', f"lima-{self.name}"])

    def is_vm(self):
        if debug: print(f"Checking if {self.name} is a VM")
        return self.name in self.get_vm_names()
    
    def get_vm_names(self):
        result = subprocess.run(['limactl', 'list', '--format', '{{.Name}}'], capture_output=True, text=True)
        return result.stdout.splitlines()

    def is_ready(self):
        if not self.is_vm():
            return False
        node = f"{self.k8s_prefix}{self.name}"
        if debug: print(f"Checking if {node} is ready")
        #result = subprocess.run(['kubectl', 'get', 'node', node, '-o=jsonpath={.metadata.name}'], capture_output=True, text=True)
        cmd = ['kubectl', 'get', 'node', node, '-o=jsonpath={.metadata.name}']
        result = run_cmd(cmd)
        if result.returncode == 0:
            print(f"{node} is ready")
            return True
        return False

    def is_leader(self):
        return self.role == "leader"
    
    def get_diskname(self):
        return f"{self.name}-data"

    def remove_disk(self):
        subprocess.run(['limactl', 'disk', 'delete', self.get_diskname()])

    def get_disks(self):
        result = subprocess.run(['limactl', 'disk', 'list'], capture_output=True, text=True)
        lines = result.stdout.splitlines()
        disk_names = []
        for line in lines:
            parts = line.split()
            print(parts)
            if len(parts) > 0 and parts[0] != 'NAME':
                disk_names.append(parts[0])
        return disk_names

class Kluster:
    # Node Role:
    # leader is the initial control plane node
    # follower is a control plane node that joins the cluster after the leader
    # worker is a node that joins the cluster after the control plane nodes
    # Disk Size:
    # disk_size is the size of the default disk
    # raw_disk_size is the size of the additional raw disk attached to the node 0 or null if no disk is attached 
    SINGLE_NODE_TOPOLOGY = {
        #"cp1": {"cpu": 2, "mem": 4, "disk_size": "30GiB", "raw_disk_size": "50GiB", "role": "leader"}
        Knode("cp1", 2, "8GiB", "30GiB", "100GiB", "leader")
    }

    FOUR_NODE_TOPOLOGY = {
        #"n3":  {"cpu": 2, "mem": 4, "disk_size": "30GiB", "raw_disk_size": "50GiB", "role": "worker"}
        Knode("cp1", 4, "4GiB", "30GiB", "30GiB", "leader"),
        Knode("n1",  4, "4GiB", "30GiB", "50GiB", "worker"),
        Knode("n2",  4, "4GiB", "30GiB", "50GiB", "worker"),
        Knode("n3",  4, "4GiB", "30GiB", "50GiB", "worker")
    }
    work_dir = f"{CWD}.klima/k8scfg"
    config_dir = f"{USER_HOME_DIR}/.kube"
    template = "k8s-base.yaml"

    def __init__(self, topology=None, name="FOUR_NODE_TOPOLOGY"):
        if topology is None:
            self.topology = self.FOUR_NODE_TOPOLOGY
            self.name = name
        else:
            self.topology = topology
            self.name = name
        os.makedirs(self.work_dir, exist_ok=True)

    def is_up(self):
        return self.get_leader().is_ready()

    def get_nodes(self):
        return [node for node in self.topology]
    
    def get_vm_names(self):
        result = subprocess.run(['limactl', 'list', '--format', '{{.Name}}'], capture_output=True, text=True)
        return result.stdout.splitlines()
    
    def get_disk_names(self):
        result = subprocess.run(['limactl', 'disk', 'list'], capture_output=True, text=True)
        lines = result.stdout.splitlines()

    def get_leader(self):
        for node in self.topology:
            if node.role == "leader":
                return node
    
    def get_followers(self):
        followers = []
        for node in self.topology:
            if self.topology[node].role == "follower":
                followers.append(node)
        return followers
    
    def get_workers(self):
        workers = []
        for node in self.topology:
            if node.role == "worker":
                workers.append(node)
        
        if debug: print(f"# workers is {len(workers)}")
        return workers
    
    def get_kubeconfig(self):
        # Copy the kubeconfig file to the host
        if debug: print("Updating ~/.kube/config...")
        subprocess.run(['cp', f"{self.work_dir}/admin.conf", f"{self.config_dir}/config"])

#    def create(self):
#        print(f"Creating cluster {self.name}")
#        os.makedirs(self.work_dir, exist_ok=True)

    def destroy(self):
        if debug: print(f"Destroying cluster {self.name}")
        run_cmd(f"rm -rf {self.work_dir}")

def run_cmd(command):
    try: 
        if isinstance(command, list):
            result = subprocess.run(command)
        else:
            result = subprocess.run(command, shell=True)
        if result.stderr:
            print(result.stderr.decode('utf-8'))
        return result
    except subprocess.CalledProcessError as e:
        print(f"An error occurred: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
    finally:
        pass

#def run_command(command):
#    if isinstance(command, list):
#        result = subprocess.run(command, capture_output=True, text=True)
#    else:
#        result = subprocess.run(command, shell=True)
#    if result.stdout:
#        print(result.stdout.decode('utf-8'))
#    if result.stderr:
#        print(result.stderr.decode('utf-8'))
#    return

## Bring up an individual node
def node_up(node):
    #print(f"Bringing up node {node.name}")
    try:
        if not node.is_vm():
            node.create()

        # we need to do something a little different for the leader node
        if node.is_leader():
            node.start()
        elif not node.is_ready():
            node.start()
        else:
            print(f"{node.name} is ready. Nothing to do.")

    except subprocess.CalledProcessError as e:
        print(f"An error occurred: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
    finally:
        pass

## Tear down an individual node
def node_down(node):
    # print(f"Bringing down node {node.name}")
    node.kill_vm()
    node.remove_disk()

## Bring up a cluster topology
def cluster_up(cluster):
    if not cluster.is_up():
        #cluster.create()
        # 1st Task: Start the initial control plane
        leader = cluster.get_leader()
        node_up(leader)
        cluster.get_kubeconfig()
    
    for node in cluster.get_workers():
        if debug: print(f"Bring up worker {node.name}")
        node_up(node)

## Tear down a cluster topology
def cluster_down(cluster, force=False):
    if not force:
        input("!!! WARNING !!! \n\n \
This is a permanent action. All lima VMs and disks will be lost forever. \n \
Press Enter to continue...\n")
    
    for node in cluster.get_nodes():
        node_down(node)
    
    print(f"VMs remaining: {cluster.get_vm_names()}")
    print(f"Disks remaining: {cluster.get_disk_names()}")
    

def main(args):
    cluster = Kluster()
    if args.up:
        cluster_up(cluster)
    elif args.klober:
        cluster_down(cluster, args.force)
        cluster.destroy()
 
if __name__ == "__main__":
    start_time = time()
    def print_total_time():
        total_time = time() - start_time
        print(f"Execution time: {total_time / 60:.2f} minutes")

    def signal_handler(sig, frame):
        print_total_time()
        sys.exit(0)

    parser = argparse.ArgumentParser(description="Manage lima VMs and disks")
    task_group = parser.add_mutually_exclusive_group(required=True)
    task_group.add_argument('--klober', action='store_true', help='remove all VMs and disks')
    task_group.add_argument('--up', action='store_true', help='stand up all VMs and disks')
    task_group.add_argument('--time', action='store_true', help='manage node time')
    parser.add_argument('--single', '-s', required=False, action='store_true', help='stand up cp1 only node in a k8s cluster')
    parser.add_argument('--cp1disk', required=False, action='store_true', help='add data disk to cp1')
    parser.add_argument('--node', '-n', required=False, type=str, help='remove a single node from a k8s cluster')
    parser.add_argument('--force', '-f', required=False, action='store_true', help='force remove all VMs and disks')
    parser.add_argument('--debug', '-d', required=False, action='store_true', help='debug mode')
    args = parser.parse_args()
    signal.signal(signal.SIGINT, signal_handler)
    
    global debug
    debug = args.debug

    main(args)

    print_total_time()