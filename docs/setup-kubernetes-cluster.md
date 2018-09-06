# Setting up a Kubernetes cluster

This document describes the steps to follow to deploy a Kubernetes cluster with the required components for a scheduler to work.

## Pre-requisites

We assume that your cluster of machines runs Ubuntu 16.04.
Your cluster will be split in 3 types of machines:

1. 1 machine will be your Kubernetes master
2. Some SGX-enabled machines will be used as SGX-enabled Kubernetes nodes
3. The rest of the machines will be used as regular Kuberetes nodes

Before starting, **please carefully read this**: If you are installing Kubernetes on a physical machine, you have to **completely disable its swap**!

## Pre-installation on all machines

Connect as _root_ on all machines (you may want to use `clusterssh` for easier operation).

1. Install system updates (recommended)
2. Make sure that each machine has a distinct hostname, and that its IP address is referenced in `/etc/hosts`
3. Install Docker using the `docker.io` package available in the regular Ubuntu repositories
    1. Also install the tools related to the storage backend that Docker will be using. Eg. `aufs-tools` in the case of `aufs` (default in Ubuntu).
4. Install `kubeadm` from the repository from Google (if you compiled Kubernetes yourself, install your own version)
```
apt install apt-transport-https
curl -s https://packages.cloud.google.com/apt/doc/apt-key.gpg | apt-key add -
cat <<EOF >/etc/apt/sources.list.d/kubernetes.list
deb http://apt.kubernetes.io/ kubernetes-xenial main
EOF
apt update
apt install kubeadm
```
5. Add a normal user for regular operation (we choose the name _ubuntu_)
```
adduser ubuntu
usermod -a -G docker ubuntu
usermod -a -G sudo ubuntu
```
6. **Very important: Allow traffic between hosts**
```
iptables -P FORWARD ACCEPT
```

## Instantiate the cluster

Execute these commands **on the master machine only**, using the normal user created previously.

6. Create the config file for `kubeadm`. `imageRepository` and `kubernetesVersion` are only needed if you require a specific version of Kubernetes (_e.g._, if you compiled Kubernetes yourself).
```yaml
apiVersion: kubeadm.k8s.io/v1alpha1
imageRepository: "172.16.0.25:5000"
kubernetesVersion: v1.11.2
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

