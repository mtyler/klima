#

## Usage

start.py - starts a 4 node cluster

clean-all.py deletes all lima disks and vms


below are setup notes that require cleaning...


## development environment

currently we need to create a virtual python environment
python3 -m venv venv
source venv/bin/activate
python3 -m pip install xyz


## prereqs

- ~~socket_vmnet installed from binary with launchd service: https://github.com/lima-vm/socket_vmnet?tab=readme-ov-file#from-binary~~

- ~~configure socket_vmnet networking https://lima-vm.io/docs/config/network/#socket_vmnet~~

- ~~get info: sudo launchctl print system/io.github.lima-vm.socket_vmnet | grep state~~

## Setup 

~~1. verify paths.socketVMNet matches installed socket_vmnet~~

1. limactl create --set='.networks[].macAddress="52:55:55:12:34:01"' --name cp-1 machines/ubuntu-lts-machine.yaml --tty=false
1. limactl create --set='.networks[].macAddress="52:55:55:12:34:04"' --name worker-1 machines/ubuntu-lts-machine.yaml --tty=false

1. limactl sudoers > etc_sudoers.d_lima && sudo install -o root etc_sudoers.d_lima /private/etc/sudoers.d/lima && rm etc_sudoers.d_lima
limactl sudoers >etc_sudoers.d_lima && sudo install -o root etc_sudoers.d_lima "/private/etc/sudoers.d/lima"

1. limactl start cp-1
1. limactl start worker-1

1. limactl sudoers | sudo tee /etc/sudoers.d/lima
1. limactl create --network=lima:shared template://default

1. replace default ~/.lima/_config/networks.yaml



### verify socket_vmnet & QEMU

brew install qemu

/opt/socket_vmnet/bin/socket_vmnet_client /var/run/socket_vmnet qemu-system-aarch64 \
-device virtio-net-pci,netdev=net0 -netdev socket,id=net0,fd=3 -m 4096 -accel hvf -cdrom /Users/mtyler/Downloads/ubuntu-24.04.1-live-server-arm64.iso


mkdir -p /var/run sudo /opt/socket_vmnet/bin/socket_vmnet --vmnet-gateway=192.168.105.1 /var/run/socket_vmnet



## starting from the provided lima k8s.yaml template


limactl disk create cp1-data --size=50GB --format=raw
limactl create --name cp1 ./k8s.yaml --tty=false
limactl start cp1
cp /Users/mtyler/.lima/cp1/copied-from-guest/kubeconfig.yaml ~/.kube/config
kubectl get nodes


limactl disk create 

sudo lsblk -o NAME,FSTYPE,SIZE,MOUNTPOINT,LABEL


## storage
lima provides ext4 formatted partition

ceph / rook - required unpartitioned drive
nfs is possible but does not provide the type of service falco requires
topolvm - requires a Volume Group. VG requires a non-partitioned disk

### minio
minio requires the drive to be configured/initialized with DirectPV


## Additional nodes

generate the controlplane join command on cp1
kubeadm token create --print-join-command --certificate-key $(kubeadm certs certificate-key)

generate the worker join command on cp1
kubeadm token create --print-join-command 
- or - 
use command aboave and strip off "control plane and certificate
