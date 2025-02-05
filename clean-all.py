#!/opt/homebrew/bin/python3

import subprocess

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

def main():
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
    
if __name__ == "__main__":
    main()