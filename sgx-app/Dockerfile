FROM sebvaucher/sgx-base:sgx-1.9

COPY sgx_common ./sgx_common/
COPY src ./src/
COPY Makefile generate_binaries.sh ./

RUN make SGX=1

CMD ./bin-sgx/dummy dummy.signed.so

