#include <stdio.h>
#include <sgx_capable.h>
#include <sgx_errlist.h>

#ifdef ENABLE_SGX
#include <unistd.h>
#include <stdlib.h>
#include <libgen.h>
#include <enclave_dummy_u.h>
#include <sgx_initenclave.h>
extern "C" {
void ocall_print(const char *str) {
    printf("%s",str);
}
}

sgx_enclave_id_t global_eid = 0;
#endif

void print_sgx_status( sgx_device_status_t s ) {
    switch( s ) {
    case SGX_ENABLED:
        printf("SGX is enabled\n"); break;
    case SGX_DISABLED_REBOOT_REQUIRED:
        printf("A reboot is required to finish enabling SGX\n"); break;
    case SGX_DISABLED_LEGACY_OS:
        printf("SGX is disabled and a Software Control Interface is not available to enable it\n"); break;
    case SGX_DISABLED:
        printf("SGX is not enabled on this platform. More details are unavailable.\n"); break;
    case SGX_DISABLED_SCI_AVAILABLE:
        printf("SGX is disabled, but a Software Control Interface is available to enable it\n"); break;
    case SGX_DISABLED_MANUAL_ENABLE:
        printf("SGX is disabled, but can be enabled manually in the BIOS setup\n"); break;
    case SGX_DISABLED_HYPERV_ENABLED:
        printf("Detected an unsupported version of Windows* 10 with Hyper-V enabled\n"); break;
    case SGX_DISABLED_UNSUPPORTED_CPU:
        printf("SGX is not supported by this CPU\n"); break;
    default:
        printf("Unknown status\n");
    }
}

int main( int argc, char **argv ) {
    sgx_device_status_t sgx_status;
    printf("sgx_cap_get_status: ");
    print_error_message( sgx_cap_get_status( &sgx_status ) );
    print_sgx_status( sgx_status );

    if( sgx_status == SGX_DISABLED_SCI_AVAILABLE ) {
        sgx_cap_enable_device( &sgx_status );
        printf("sgx_cap_enable_device: ");
        print_sgx_status( sgx_status );
    }

    if( sgx_status != SGX_ENABLED ) return -1;

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

    if( ecall_dummy( global_eid ) == SGX_SUCCESS ) 
        printf("enclave function succesfully called\n");
    else
        printf("problem when calling enclave function\n");
#endif
}

