import sys
from array import array
from fcntl import ioctl
from http.server import BaseHTTPRequestHandler, HTTPServer


class Collector(BaseHTTPRequestHandler):
    def __init__(self, request, client_address, server):
        self.isgx = IsgxDriver()
        super().__init__(request, client_address, server)

    def fetch_format_isgx(self):
        state = self.isgx.sgx_ioctl()
        return "\n".join(": ".join(x) for x in state.items())

    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-Type", "text/plain")
        self.end_headers()
        self.wfile.write(self.fetch_format_isgx().encode())


def run_server_forever():
    print("Server is about to start")
    httpd = HTTPServer(('0.0.0.0', 4567), Collector)
    try:
        print("Server will serve on port %d" % httpd.server_port)
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass


class IsgxDriver(object):
    # Name can be anything, type is a Python format argument
    _sgx_enclave_usage = (
        {
            "name": "dummy",
            "type": "Q",
            "default_value": 0,
        },
    )
    # Use the _real_ value, after transformation
    _calls = {
        "SGX_IOC_EPC_USAGE": 2148049923,
    }

    def sgx_ioctl(self):
        buffer = array("".join(x["type"] for x in self._sgx_enclave_usage),
                       [x["default_value"] for x in self._sgx_enclave_usage])
        try:
            with open("/dev/isgx", "r+b", buffering=0) as isgx:
                ioctl(isgx, self._calls["SGX_IOC_EPC_USAGE"], buffer, True)
        except EnvironmentError:
            print("Unable to open /dev/isgx. Check driver and permissions.", file=sys.stderr)
            sys.exit(1)

        return {val["name"]: str(buffer[idx]) for idx, val in enumerate(self._sgx_enclave_usage)}


if __name__ == "__main__":
    # print(IsgxDriver().sgx_ioctl())
    run_server_forever()
