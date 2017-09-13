FROM ubuntu:xenial

WORKDIR /usr/src/sdk

RUN apt-get update && apt-get install -yq --no-install-recommends ca-certificates build-essential ocaml automake autoconf libtool wget python libssl-dev libcurl4-openssl-dev protobuf-compiler libprotobuf-dev alien

ADD http://registrationcenter-download.intel.com/akdlm/irc_nas/11414/iclsClient-1.45.449.12-1.x86_64.rpm ./iclsclient.rpm

RUN alien --scripts -i iclsclient.rpm

ADD https://github.com/01org/linux-sgx/archive/sgx_1.9.tar.gz ./sgx.tar.gz
RUN tar -xf ./sgx.tar.gz && rm -f ./sgx.tar.gz
COPY install-psw.patch ./

RUN cd linux-sgx-sgx_1.9 && \
    patch -p1 -i ../install-psw.patch && \
    ./download_prebuilt.sh && \
    make -j$(nproc) sdk_install_pkg psw_install_pkg && \
    ./linux/installer/bin/sgx_linux_x64_sdk_1.9.100.39124.bin --prefix=/opt/intel && \
    ./linux/installer/bin/sgx_linux_x64_psw_1.9.100.39124.bin


