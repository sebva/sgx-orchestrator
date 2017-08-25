# How to setup the Gogland IDE to develop on Kubernetes

_Gogland_ is the Go IDE from JetBrains. It is in early-access, and so can be [downloaded](https://www.jetbrains.com/go/download/#section=linux) for free for the time being.

The [steps to download the dependencies](https://github.com/kubernetes/community/blob/master/contributors/devel/godep.md) are taken from the Kubernetes Community repository.

1. Create a folder where to put the sources.
2. Export that folder as `$KPATH`
```
export KPATH=~/develop/kubernetes
```
3. Clone the code from Kubernetes
```
mkdir -p $KPATH/src/k8s.io
cd $KPATH/src/k8s.io
git clone https://github.com/$YOUR_GITHUB_USERNAME/kubernetes.git
```
4. Download the dependencies
```
export GOPATH=$KPATH
go get -u github.com/tools/godep
export PATH=$PATH:$KPATH/bin
cd $KPATH/src/k8s.io/kubernetes
./hack/godep-restore.sh
```
5. Open Gogland and open the `$KPATH/src/k8s.io/kubernetes` folder
6. Go to `File`->`Settings`, then in `Go`->`GOPATH`, add `$KPATH` as the "Project GOPATH"

