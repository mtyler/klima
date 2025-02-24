# Klima

Klima is a slightly opinionated wrapper script around Lima VM. The purpose is to create a minimally viable, just-enough-k8s cluster to operate Kubernetes in a local (re: laptop) environment. Kubernetes is deployed with kubeadm on Ubuntu Lima VMs.

Klima provisions a Virtual Machine-based Kubernetes cluster and facilitates the attachment of raw disks. It is meant to stand up and tear down quickly and easily.

## Dependencies and Pre-requisites

- **Lima VM** (brew install)
- **socket_vmnet** (binary install)
- **qemu** (brew install)
- **Python3** (brew install)

## Usage

- `klima.py --up` starts a 4-node cluster
- `klima.py --klober` deletes the cluster

### Install and Verify socket_vmnet & QEMU

```sh
brew install qemu

/opt/socket_vmnet/bin/socket_vmnet_client /var/run/socket_vmnet qemu-system-aarch64 \
-device virtio-net-pci,netdev=net0 -netdev socket,id=net0,fd=3 -m 4096 -accel hvf -cdrom /Users/mtyler/Downloads/ubuntu-24.04.1-live-server-arm64.iso

mkdir -p /var/run
sudo /opt/socket_vmnet/bin/socket_vmnet --vmnet-gateway=192.168.105.1 /var/run/socket_vmnet
```

## Storage

- **lima** provides ext4 formatted partition
- **ceph / rook** - requires unpartitioned drive
- **nfs** is possible but does not provide the type of service falco requires
- **topolvm** - requires a Volume Group. VG requires a non-partitioned disk

### Issues

- Time is Not Staying Up to Date: Chrony has been installed but something is causeing the clock to jump forward. When this happens, the only resolution I'vefound is to restart the node.


