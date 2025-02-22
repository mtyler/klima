# Klima

Is a slightly opinionated wrapper script around Lima VM. The purpose is to create a minimally viable, just-enough-k8s cluster to operate kubernetes in a local (re: laptop) environment. Kubernetes is deployed with kubeadm on ubuntu Lima VMs. 

Klima provisions a Virtual Machine based kubernetes cluster and facilitates the attachment of raw disks. 

Meant to standup and teardown quickly and easily.

## Dependancies and Pre-reqs

Lima VM (brew install)
socket_vmnet (binary install)
qemu (brew install)
Python3 (brew install)

## Usage

Beware... this is still a bit WIPy

klima.py --up starts a 4 node cluster

klima.py --klober deletes the cluster


### verify socket_vmnet & QEMU

brew install qemu

/opt/socket_vmnet/bin/socket_vmnet_client /var/run/socket_vmnet qemu-system-aarch64 \
-device virtio-net-pci,netdev=net0 -netdev socket,id=net0,fd=3 -m 4096 -accel hvf -cdrom /Users/mtyler/Downloads/ubuntu-24.04.1-live-server-arm64.iso


mkdir -p /var/run sudo /opt/socket_vmnet/bin/socket_vmnet --vmnet-gateway=192.168.105.1 /var/run/socket_vmnet


## storage
lima provides ext4 formatted partition

ceph / rook - required unpartitioned drive
nfs is possible but does not provide the type of service falco requires
topolvm - requires a Volume Group. VG requires a non-partitioned disk



### Issues

#### time is not staying up to date
installed and configured chrony
issue is slightly better but still persists

[ 1128.763113] rcu: INFO: rcu_preempt self-detected stall on CPU
[ 1128.763203] rcu: 	0-...!: (6 ticks this GP) idle=4a6c/1/0x4000000000000002 softirq=71946/71948 fqs=0
[ 1128.763208] rcu: 	(t=3002413905695 jiffies g=82521 q=3405 ncpus=2)
[ 1128.763213] rcu: rcu_preempt kthread timer wakeup didn't happen for 3002413905692 jiffies! g82521 f0x0 RCU_GP_WAIT_FQS(5) ->state=0x402
[ 1128.763216] rcu: 	Possible timer handling issue on cpu=1 timer-softirq=18806
[ 1128.763218] rcu: rcu_preempt kthread starved for 3002413905695 jiffies! g82521 f0x0 RCU_GP_WAIT_FQS(5) ->state=0x402 ->cpu=1
[ 1128.763221] rcu: 	Unless rcu_preempt kthread gets sufficient CPU time, OOM is now expected behavior.
[ 1128.763223] rcu: RCU grace-period kthread stack dump:
[ 1128.763225] task:rcu_preempt     state:I stack:0     pid:17    tgid:17    ppid:2      flags:0x00000008

increased cpu to 4, mem left at 8GB
