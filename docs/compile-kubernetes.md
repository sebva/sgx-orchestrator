# How to compile and deploy a custom Kubernetes build

## Prerequisites

* [Bazel 0.16.1](https://github.com/bazelbuild/bazel/releases/tag/0.16.1)
* A Docker registry accessible to both the machine that compiles and the machines where Kubernetes will be deployed

## Compilation

1. Checkout the sources as described in [setup-kubernetes-ide.md](docs/setup-kubernetes-ide.md)
    1. In order to get the EPC usage limit feature built-in, you have to use the repository at https://github.com/sebva/kubernetes, on the `sgx-deviceplugin` branch.
2. Compile the `.deb` packages
    1. If bazel complains about faulty checksums, the file to modify is [`build/root/WORKSPACE`](https://github.com/sebva/kubernetes/blob/sgx-deviceplugin/build/root/WORKSPACE)
```bash
bazel build //build/debs
```
3. Setup a couple environment variables
```bash
export KUBE_DOCKER_REGISTRY=127.0.0.1:5000  # The address of the Docker registry
export KUBE_DOCKER_IMAGE_TAG=v1.11.2  # The version tag that will be referenced by kubeadm
```
4. Build the Docker containers
```bash
make quick-release
```
5. Push the Docker containers
```bash
docker push 127.0.0.1:5000/kube-apiserver-amd64:v1.11.2
docker push 127.0.0.1:5000/kube-controller-manager-amd64:v1.11.2
docker push 127.0.0.1:5000/cloud-controller-manager-amd64:v1.11.2
docker push 127.0.0.1:5000/kube-aggregator-amd64:v1.11.2
docker push 127.0.0.1:5000/kube-scheduler-amd64:v1.11.2
docker push 127.0.0.1:5000/kube-proxy-amd64:v1.11.2
docker pull gcr.io/google_containers/pause:3.1
docker tag gcr.io/google_containers/pause:3.1 127.0.0.1:5000/pause:3.1
docker push 127.0.0.1:5000/pause:3.1
docker pull gcr.io/google_containers/coredns:1.1.3
docker tag gcr.io/google_containers/coredns:1.1.3 127.0.0.1:5000/coredns:1.1.3
docker push 127.0.0.1:5000/coredns:1.1.3
docker pull gcr.io/google_containers/etcd-amd64:3.2.18
docker tag gcr.io/google_containers/etcd-amd64:3.2.18 127.0.0.1:5000/etcd-amd64:3.2.18
docker push 127.0.0.1:5000/etcd-amd64:3.2.18
docker pull gcr.io/google_containers/k8s-dns-kube-dns-amd64:1.14.5
docker tag gcr.io/google_containers/k8s-dns-kube-dns-amd64:1.14.5 127.0.0.1:5000/k8s-dns-kube-dns-amd64:1.14.5
docker push 127.0.0.1:5000/k8s-dns-kube-dns-amd64:1.14.5
docker pull gcr.io/google_containers/k8s-dns-dnsmasq-nanny-amd64:1.14.5
docker tag gcr.io/google_containers/k8s-dns-dnsmasq-nanny-amd64:1.14.5 127.0.0.1:5000/k8s-dns-dnsmasq-nanny-amd64:1.14.5
docker push 127.0.0.1:5000/k8s-dns-dnsmasq-nanny-amd64:1.14.5
docker pull gcr.io/google_containers/k8s-dns-sidecar-amd64:1.14.5
docker tag gcr.io/google_containers/k8s-dns-sidecar-amd64:1.14.5 127.0.0.1:5000/k8s-dns-sidecar-amd64:1.14.5
docker push 127.0.0.1:5000/k8s-dns-sidecar-amd64:1.14.5
docker pull gcr.io/google_containers/k8s-dns-sidecar-amd64:1.14.5
docker tag gcr.io/google_containers/k8s-dns-sidecar-amd64:1.14.5 127.0.0.1:5000/k8s-dns-sidecar-amd64:1.14.5
docker push 127.0.0.1:5000/k8s-dns-sidecar-amd64:1.14.5
```
6. Transfer the install packages to the target machine
```bash
cd bazel-bin/build/debs
echo ubuntu@172.16.0.2{5,6,7,8}:~ | xargs -n1 rsync -L --progress {kubeadm,kubectl,kubernetes-cni,kubelet}.deb
```

## On the target machine

1. Install all `.deb` packages
```bash
sudo dpkg -i *.deb
```
2. Declare the registry running on the target machine as insecure on all machines. See [this page](https://docs.docker.com/registry/insecure/) for instructions.
3. Create the config file for `kubeadm` (save as `kubeadm-config.yml`)
```yaml
apiVersion: kubeadm.k8s.io/v1alpha1
imageRepository: "172.16.0.25:5000"
kubernetesVersion: v1.11.2
```
4. Reload `kubelet`
```bash
sudo systemctl daemon-reload
sudo systemctl restart kubelet
```
5. Initialize the cluster by following the instructions in [setup-kubernetes-cluster.md](setup-kubernetes-cluster.md)

