#include <string.h>
#include <stdio.h>
#include <stdlib.h>

#ifdef ENABLE_SGX
#include <unistd.h>
#include <libgen.h>
#include <enclave_dummy_u.h>
#include <sgx_initenclave.h>
extern "C" {
void ocall_print(const char *str) {
    printf("%s",str);
}
}

sgx_enclave_id_t global_eid = 0;
#else
extern void ecall_dummy(size_t);
#endif

int main( int argc, char **argv ) {
    if( argc != 2 ) {
        printf("Usage: %s [enclave_filename.signed.so]\n", argv[0]);
        return -1;
    }

#ifdef ENABLE_SGX
    /* Changing dir to where the executable is.*/
    char *ptr = realpath( dirname(argv[0]),NULL );

    if( ptr == NULL ){ perror("Error:"); abort(); }
    if( chdir(ptr) != 0) abort();

    /* Initialize the enclave */
    if(initialize_enclave( global_eid,
                           argv[1],"enclave.dummy-mem.token") < 0) {
        return -2;
    }
    free(ptr);
#endif

    size_t pages;
    char *fname = basename( argv[1] );
    char *p1 = strtok(fname,"-"),
         *p2 = strtok(NULL,".");
    if( p2 )
        pages = atoi( p2 ); 
    else {
        printf("Filename must be in the form [whatever]-NUMBEROFPAGES.[whatever]\n");
        return -2;
    }

    while(true) {
#ifdef ENABLE_SGX
        ecall_dummy( global_eid, pages );
#else
        ecall_dummy( pages );
#endif
    }
}

