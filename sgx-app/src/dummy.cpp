
#ifdef ENABLE_SGX
#include <unistd.h>
#include <stdlib.h>
#include <libgen.h>
#include <stdio.h>
#include <enclave_dummy_u.h>
#include <sgx_initenclave.h>
extern "C" {
void ocall_print(const char *str) {
    printf("%s",str);
}
}

sgx_enclave_id_t global_eid = 0;
#endif

int main( int argc, char **argv ) {
#ifdef ENABLE_SGX
    if( argc != 2 ) {
        printf("Usage: %s [enclave_filename.signed.so]\n", argv[0]);
    }

    /* Changing dir to where the executable is.*/
    char *ptr = realpath( dirname(argv[0]),NULL );

    if( ptr == NULL ){ perror("Error:"); abort(); }
    if( chdir(ptr) != 0) abort();

    /* Initialize the enclave */
    if(initialize_enclave( global_eid,
                           argv[1],"enclave.dummy.token") < 0) {
        return -2;
    }
    free(ptr);
#endif
}

