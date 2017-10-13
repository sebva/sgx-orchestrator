#ifdef ENABLE_SGX
#include <enclave_dummy_t.h>
#include <sgx_trts.h>
#else
#include <stdio.h>
#include <stdlib.h>
#endif

void ecall_dummy(size_t pages) {
    size_t sz = pages*(1<<12);
    void *mem = malloc(sz);
#ifdef ENABLE_SGX
    sgx_read_rand( (unsigned char*) mem, sz );
#else
    FILE *f = fopen("/dev/urandom","r");
    fread(mem, 1, sz, f);
    fclose(f);
#endif
    free(mem);
}

