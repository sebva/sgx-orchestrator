#!/bin/bash
SGX_SDK="/opt/intel/sgxsdk"
SGX_ENCLAVE_SIGNER="${SGX_SDK}/bin/x64/sgx_sign"

if [ $# -ne 6 ]; then
    echo "Missing arguments"
    echo "Usage: $ $0 enclave_object config_xml key pages_min pages_inc pages_max"
    exit -1
fi

for i in $(seq $4 $5 $6); do
    CONFIGFNAME=/tmp/config-$i.xml
    heap_size=$(printf "0x%x" $(echo "$i*4*1024" | bc))
    sed "s/<HeapMaxSize>\s*0x[0-9]*/<HeapMaxSize>$heap_size/" $2 >${CONFIGFNAME}
    ${SGX_ENCLAVE_SIGNER} sign -enclave $1 -config ${CONFIGFNAME} -out $1-$i.signed -key $3
done

