# Setting up a Kubernetes cluster

This document describes the steps to follow to deploy a Kubernetes cluster with the required components for a scheduler to work.
We assume that the deployment is done on IIUN's _clusterinfo_.

## Virtual machines

We tested the deployment on the Ubuntu 16.04 image (v5.4.0) that is available in OpenNebula Marketplace. At the time of writing, the image is downloaded as ID 913.
We recommend a separate partition for Docker data which can be large (mounted at `/var/lib/docker`).

## Pre-installation on all machines

Connect as _root_ on all machines (use `clusterssh` for easier operation).

1. Install system updates
2. Make sure that each machine has a distinct hostname, and that its IP address is referenced in `/etc/hosts`
3. Install Docker using the `docker.io` package available in the regular Ubuntu repositories
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

## Instantiate the cluster

Execute these commands on the master machine using the normal user created previously.

7. Create the Kubernetes cluster. It may take several minutes for the "Control plane" to be ready.
```
sudo kubeadm init
```
8. **Read the output of `kubeadm init` carefully**
    1. There are some commands to execute on the master first
    2. **Do not join the nodes yet!**
9. Check that Kubernetes is working by executing `kubectl version` on the master
10. Deploy WeaveNet to the cluster
```
kubectl apply -f "https://cloud.weave.works/k8s/net?k8s-version=$(kubectl version | base64 | tr -d '\n')"
```
11. Join the nodes using the command that was written in the output of `kubeadm init`
12. Wait for the nodes to be ready by monitoring the output of `kubectl get nodes`
13. Verify that everything that is needed is here
```
kubectl get pods --all-namespaces
```

