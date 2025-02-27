# Klima

Klima is a wrapper script to start and stop Lima VMs. The template used here deploys Kubernetes with kubeadm on Ubuntu. The purpose is 

1. to create a minimally viable, just-enough-k8s cluster to operate Kubernetes in a local (re: laptop) environment.
2. to create a cluster template, compatible with vanilla Lima VM 

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

##### Issue: Time is Not Staying Up to Date: Chrony has been installed but something is causeing the clock to jump forward. When this happens, the only resolution I'vefound is to restart the node.

- DNS settings in coredns configmap. forward . 8.8.8.8 instead of resolve.conf

unable to set time after sync issue

timedatectl set-time '2025-02-25 10:00:00' < should work but doesn't

chronyc -a 'burst 4/4'
200 OK
200 OK
# chronyc -a makestep
200 OK

l shell cp1 sudo chronyc -N 'sources -a -v'


##### Issue: Error: failed to reserve container name "kube-scheduler_kube-scheduler-lima-cp1_kube-system_84cee8be17e4518a644c3a40e1d0b7d2_3":
- kubelet unable to start pods.
possibly caused by containerd restart 

List and remove pods
sudo crictl pods
sudo crictl stopp 38eb2f5bfb1ec
sudo crictl rmp 38eb2f5bfb1ec

timedatectl list-timezones | egrep -o "America/N.*"

systemctl list-units | grep failed
sudo journalctl -u cloud-final.service