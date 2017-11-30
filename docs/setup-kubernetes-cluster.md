# Setting up a Kubernetes cluster

This document describes the steps to follow to deploy a Kubernetes cluster with the required components for a scheduler to work.
We assume that the deployment is done on IIUN's _clusterinfo_.

## Virtual machines

We tested the deployment on the Ubuntu 16.04 image (v5.4.0) that is available in OpenNebula Marketplace. At the time of writing, the image is downloaded as ID 913.
We recommend a separate partition for Docker data which can be large (mounted at `/var/lib/docker`).

## Physical machine

If you are installing Kubernetes on a physical machine, you have to **completely disable its swap**!

## Combine virtual and physical machines

In order to use the desktop SGX machines that are in the cluster, it is a good idea to make them communicate with the VMs directly, without routing over that poor `clusterinfo` machine. To do so, you can join the SGX machine to the VLAN with ID 2100.

* **Double check that the IP ranges and VLAN ID specified here are still correct by cross-checking in OpenNebula**
* Choose a free IP in the range and hold it in OpenNebula (I chose `172.16.63.63`)
* Find out the name of the network device that is connected to the switch in the cluster (`enp0s31f6` in this case)

When you have gathered all the information, perform the changes:
```
sudo ip link add link enp0s31f6 name enp0s31f6.2100 type vlan id 2100  # Declare a virtual device
sudo ip addr add 172.16.63.63/16 dev enp0s31f6.2100                    # Add an IP address to it
sudo ip link set enp0s31f6.2100 up                                     # Bring up the device
```

Verify that the connection is direct between the nodes:
```
traceroute 172.16.0.25                               
```
The answer should be:
```
traceroute to 172.16.0.25 (172.16.0.25), 30 hops max, 60 byte packets
 1  172.16.0.25 (172.16.0.25)  0.566 ms  0.533 ms  0.536 ms
```

## Pre-installation on all machines

Connect as _root_ on all machines (use `clusterssh` for easier operation).

1. Install system updates
2. Make sure that each machine has a distinct hostname, and that its IP address is referenced in `/etc/hosts`
3. Install Docker using the `docker.io` package available in the regular Ubuntu repositories
    1. Also install the tools related to the storage backend that Docker will be using. Eg. `aufs-tools` in the case of `aufs` (default in Ubuntu).
4. Install `kubeadm` from the repository from Google
```
apt install apt-transport-https
curl -s https://packages.cloud.google.com/apt/doc/apt-key.gpg | apt-key add -
cat <<EOF >/etc/apt/sources.list.d/kubernetes.list
deb http://apt.kubernetes.io/ kubernetes-xenial main
EOF
apt update
apt install kubeadm
```
5. Add a normal user for regular operation (we chose the name _ubuntu_)
```
adduser ubuntu
usermod -a -G docker ubuntu
usermod -a -G sudo ubuntu
```
6. **Allow traffic between hosts**
```
sudo iptables -P FORWARD ACCEPT
```

## Instantiate the cluster

Execute these commands on the master machine using the normal user created previously.

6. Create the config file for `kubeadm`. `imageRepository` and `kubernetesVersion` are only needed if you require a specific version of Kubernetes.
```yaml
apiVersion: kubeadm.k8s.io/v1alpha1
imageRepository: "172.16.0.25:5000"
kubernetesVersion: v1.8.0-beta.1
networking:
  podSubnet: 10.244.0.0/16
```
7. Create the Kubernetes cluster. It may take several minutes for the "Control plane" to be ready.
```
sudo kubeadm init --config kubeadm-config.yml
```
8. **Read the output of `kubeadm init` carefully**
    1. There are some commands to execute on the master first
    2. **Do not join the nodes yet!**
9. Check that Kubernetes is working by executing `kubectl version` on the master
10. Wait for all pods to settle to a _Running_ state (observe using `kubectl get pods --all-namespaces`)
11. Deploy Flannel to the cluster
```
kubectl apply -f https://raw.githubusercontent.com/coreos/flannel/fc5fbd7aa3be924b06e770bfb0e7f4d69d649735/Documentation/kube-flannel.yml
kubectl apply -f https://raw.githubusercontent.com/coreos/flannel/fc5fbd7aa3be924b06e770bfb0e7f4d69d649735/Documentation/kube-flannel-rbac.yml
```
12. Join the nodes using the command that was written in the output of `kubeadm init`
13. Wait for the nodes to be ready by monitoring the output of `kubectl get nodes`
14. Verify that everything that is needed is here
```
kubectl get pods --all-namespaces
```
15. Check the logs on all your machines and check that nothing suspicious happens
```
sudo journalctl -xeu docker -u kubelet
```

### Heapster

You can now [deploy Heapster](deploy-heapster.md) to your cluster to monitor the nodes and pods.
