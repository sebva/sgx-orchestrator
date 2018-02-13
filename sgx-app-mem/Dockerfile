FROM sebvaucher/sgx-base:sgx_1.9

RUN apt-get update && apt-get -yq install --no-install-recommends bc && apt-get clean

COPY sgx_common ./sgx_common/
COPY src ./src/
COPY Makefile generate_binaries.sh dummy-entrypoint.py ./

RUN make SGX=1

RUN ./generate_binaries.sh bin-sgx/dummy.so src/enclave_dummy.config.xml src/enclave-key.pem 1 1 9 > /dev/null && \
    ./generate_binaries.sh bin-sgx/dummy.so src/enclave_dummy.config.xml src/enclave-key.pem 10 10 90 > /dev/null && \
    ./generate_binaries.sh bin-sgx/dummy.so src/enclave_dummy.config.xml src/enclave-key.pem 100 100 900 > /dev/null && \
    ./generate_binaries.sh bin-sgx/dummy.so src/enclave_dummy.config.xml src/enclave-key.pem 1000 1000 24000 > /dev/null


ENTRYPOINT ["python2", "-u", "./dummy-entrypoint.py"]
