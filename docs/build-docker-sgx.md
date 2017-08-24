# How to build a sgx-enabled Docker build in Ubuntu/Debian

```
sudo apt-get build-dep docker.io
cd `mktemp -d`
apt-get source docker.io
```

* Apply patch

```
dpkg-source --commit
dch -i
DEB_BUILD_OPTIONS=nocheck fakeroot dpkg-buildpackage -uc -us
```

