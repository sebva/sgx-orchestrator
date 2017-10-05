To compile for SGX:
```
$ make SGX=1
```

To generate several binaries with different heap size allocations:
```
./generate_binaries.sh bin-sgx/dummy.so src/enclave_dummy.config.xml src/enclave-key.pem 35 5 50
```
Starts with `35` pages (140Kb), increment of `5` (20Kb) up to `50` (200Kb).

