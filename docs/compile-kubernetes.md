# How to compile and deploy a custom Kubernetes build

## Prerequisites

* [Bazel](https://docs.bazel.build/versions/master/install-ubuntu.html)
* A Docker registry accessible to both the machine that compiles and the machines where Kubernetes will be deployed

## Compilation

1. Checkout the sources as described in [setup-kubernetes-ide.md](docs/setup-kubernetes-ide.md)
    1. In order to get the _deviceplugins_ feature built-in, you can use the repository at https://github.com/sebyx31/kubernetes, on the `sgx-deviceplugin` branch.
2. Compile the `.deb` packages
    1. If bazel complains about faulty checksums, the file to modify is [`build/root/WORKSPACE`](https://github.com/sebyx31/kubernetes/blob/sgx-deviceplugin/build/root/WORKSPACE)
```bash
bazel build //build/debs --incompatible_disallow_set_constructor=false
```
3. Setup a couple environment variables
```bash
export KUBE_DOCKER_REGISTRY=127.0.0.1:5000  # The address of the Docker registry
export KUBE_DOCKER_IMAGE_TAG=v1.8.0-beta.1  # The version tag that will be referenced by kubeadm
```
4. Build the Docker containers
```bash
make quick-release
```
5. Push the Docker containers
```bash
docker push 127.0.0.1:5000/kube-apiserver-amd64:v1.8.0
docker push 127.0.0.1:5000/kube-controller-manager-amd64:v1.8.0
docker push 127.0.0.1:5000/cloud-controller-manager-amd64:v1.8.0
docker push 127.0.0.1:5000/kube-aggregator-amd64:v1.8.0
docker push 127.0.0.1:5000/kube-scheduler-amd64:v1.8.0
docker push 127.0.0.1:5000/kube-proxy-amd64:v1.8.0
docker pull gcr.io/google_containers/etcd-amd64:3.0.17
docker tag gcr.io/google_containers/etcd-amd64:3.0.17 127.0.0.1:5000/etcd-amd64:3.0.17
docker push 127.0.0.1:5000/etcd-amd64:3.0.17
docker pull gcr.io/google_containers/k8s-dns-kube-dns-amd64:1.14.4
docker tag gcr.io/google_containers/k8s-dns-kube-dns-amd64:1.14.4 127.0.0.1:5000/k8s-dns-kube-dns-amd64:1.14.4
docker push 127.0.0.1:5000/k8s-dns-kube-dns-amd64:1.14.4
docker pull gcr.io/google_containers/k8s-dns-dnsmasq-nanny-amd64:1.14.4
docker tag gcr.io/google_containers/k8s-dns-dnsmasq-nanny-amd64:1.14.4 127.0.0.1:5000/k8s-dns-dnsmasq-nanny-amd64:1.14.4
docker push 127.0.0.1:5000/k8s-dns-dnsmasq-nanny-amd64:1.14.4
docker pull gcr.io/google_containers/k8s-dns-sidecar-amd64:1.14.4
docker tag gcr.io/google_containers/k8s-dns-sidecar-amd64:1.14.4 127.0.0.1:5000/k8s-dns-sidecar-amd64:1.14.4
docker push 127.0.0.1:5000/k8s-dns-sidecar-amd64:1.14.4
docker pull gcr.io/google_containers/k8s-dns-sidecar-amd64:1.14.4
docker tag gcr.io/google_containers/k8s-dns-sidecar-amd64:1.14.4 127.0.0.1:5000/k8s-dns-sidecar-amd64:1.14.4
docker push 127.0.0.1:5000/k8s-dns-sidecar-amd64:1.14.4
docker pull weaveworks/weave-npc:2.0.4
docker tag weaveworks/weave-npc:2.0.4 127.0.0.1:5000/weaveworks/weave-npc:2.0.4
docker push 127.0.0.1:5000/weaveworks/weave-npc:2.0.4
docker pull weaveworks/weave-kube:2.0.4
docker tag weaveworks/weave-kube:2.0.4 127.0.0.1:5000/weaveworks/weave-kube:2.0.4
docker push 127.0.0.1:5000/weaveworks/weave-kube:2.0.4
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
kubernetesVersion: v1.8.0
apiServerExtraArgs:
  feature-gates: "DevicePlugins=true"
```
4. If you did not compile Kubernetes with the _deviceplugins_ feature built-in, then add the following line in 
`/etc/systemd/system/kubelet.service.d/kubeadm-10.conf`
```ini
Environment="KUBELET_EXTRA_ARGS=--feature-gates=DevicePlugins=true"
```
5. Reload `kubelet`
```bash
sudo systemctl daemon-reload
sudo systemctl restart kubelet
```
6. Initialize the cluster by following the instructions in [setup-kubernetes-cluster.md](setup-kubernetes-cluster.md)
