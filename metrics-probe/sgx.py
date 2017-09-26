import struct
import sys
from fcntl import ioctl

# This structure is used to parse the result from the ioctl
# name can be anything, and is used to retrieve  type is a Python format argument
_sgx_enclave_usage = (
    {
        # Input
        "name": "sgx_pid",
        "type": "Q",
        "default_value": 0,
    },
    {
        # Output
        "name": "enclave_cnt",
        "type": "Q",
        "default_value": 0,
    },
    {
        # Output
        "name": "epc_pages_cnt",
        "type": "Q",
        "default_value": 0,
    },
    {
        # Output
        "name": "va_pages_cnt",
        "type": "Q",
        "default_value": 0,
    },
)

# Use the _real_ value, after transformation
_SGX_IOC_EPC_USAGE = 2149622787


def sgx_stats_pid(pid: int) -> dict:
    fmt = "".join(x["type"] for x in _sgx_enclave_usage)
    buffer = struct.pack(fmt, *(pid if x["name"] == "sgx_pid" else x["default_value"] for x in _sgx_enclave_usage))
    try:
        with open("/dev/isgx", "r+b", buffering=0) as isgx:
            result = struct.unpack(fmt, ioctl(isgx, _SGX_IOC_EPC_USAGE, buffer))
            return {val["name"]: str(result[idx]) for idx, val in enumerate(_sgx_enclave_usage)}
    except EnvironmentError:
        print("Unable to open /dev/isgx. Check driver and permissions.", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    print(str(sgx_stats_pid(int(sys.argv[1]))))
