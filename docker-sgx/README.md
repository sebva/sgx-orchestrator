# Dockerization of SGX container built using Intel SDK

Instructions:
* Create a new container with this one as a base, or mount your source code at `/usr/src/app`
* The driver must be loaded in the host, but `aesmd` and `jhid` must be stopped
