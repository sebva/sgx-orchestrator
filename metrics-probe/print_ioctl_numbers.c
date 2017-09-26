#include <linux/types.h>
#include <linux/ioctl.h>
#include <stdio.h>

#define SGX_MAGIC 0xA4

#define SGX_IOC_ENCLAVE_CREATE \
	_IOW(SGX_MAGIC, 0x00, struct sgx_enclave_create)
#define SGX_IOC_ENCLAVE_ADD_PAGE \
	_IOW(SGX_MAGIC, 0x01, struct sgx_enclave_add_page)
#define SGX_IOC_ENCLAVE_INIT \
	_IOW(SGX_MAGIC, 0x02, struct sgx_enclave_init)
#define SGX_IOC_EPC_USAGE \
	_IOR(SGX_MAGIC, 0x03, struct sgx_enclave_usage)

/**
 * struct sgx_enclave_create - parameter structure for the
 *                             %SGX_IOC_ENCLAVE_CREATE ioctl
 * @src:	address for the SECS page data
 */
struct sgx_enclave_create  {
	__u64	src;
} __attribute((packed));

/**
 * struct sgx_enclave_add_page - parameter structure for the
 *                               %SGX_IOC_ENCLAVE_ADD_PAGE ioctl
 * @addr:	address in the ELRANGE
 * @src:	address for the page data
 * @secinfo:	address for the SECINFO data
 * @mrmask:	bitmask for the 256 byte chunks that are to be measured
 */
struct sgx_enclave_add_page {
	__u64	addr;
	__u64	src;
	__u64	secinfo;
	__u16	mrmask;
} __attribute((packed));

/**
 * struct sgx_enclave_init - parameter structure for the
 *                           %SGX_IOC_ENCLAVE_INIT ioctl
 * @addr:	address in the ELRANGE
 * @sigstruct:	address for the page data
 * @einittoken:	address for the SECINFO data
 */
struct sgx_enclave_init {
	__u64	addr;
	__u64	sigstruct;
	__u64	einittoken;
} __attribute((packed));

struct sgx_enclave_destroy {
	__u64	addr;
} __attribute((packed));

/**
 * struct sgx_enclave_usage - parameter structure for the
 *                            %SGX_IOC_EPC_USAGE ioctl
 */
struct sgx_enclave_usage {
    __u64 sgx_pid; // in
    __u64 enclave_cnt; // out
    __u64 epc_pages_cnt; // out
    __u64 va_pages_cnt; // out
} __attribute((packed));

int main(int argc, char** argv) {
    printf("SGX_IOC_ENCLAVE_CREATE = %lld\n", SGX_IOC_ENCLAVE_CREATE);
    printf("SGX_IOC_ENCLAVE_ADD_PAGE = %lld\n", SGX_IOC_ENCLAVE_ADD_PAGE);
    printf("SGX_IOC_ENCLAVE_INIT = %lld\n", SGX_IOC_ENCLAVE_INIT);
    printf("SGX_IOC_EPC_USAGE = %lld\n", SGX_IOC_EPC_USAGE);
    return 0;
}
