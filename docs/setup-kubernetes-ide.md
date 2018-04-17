# How to setup the GoLand IDE to develop on Kubernetes

[_GoLand_](https://www.jetbrains.com/go/download/#section=linux) is the Go IDE from JetBrains.
We find it to be a really valuable help to read through Kubernetes code and modify it.
It is a commercial product, but JetBrains provides free liceses for academic use and open-source projects.

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
./hack/godep-restore.sh -v
```
5. Open GoLand and open the `$KPATH/src/k8s.io/kubernetes` folder
6. Go to `File`->`Settings`, then in `Go`->`GOPATH`, add `$KPATH` as the "Project GOPATH"

