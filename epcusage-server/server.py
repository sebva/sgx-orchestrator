import os
import re
from fcntl import fcntl, F_SETFL
from http.server import BaseHTTPRequestHandler, HTTPServer

import docker
import psutil


class Collector(BaseHTTPRequestHandler):
    def __init__(self, request, client_address, server):
        self.isgx = IsgxDriver()
        super().__init__(request, client_address, server)

    def fetch_format_isgx(self):
        state = self.isgx.sgx_usage()
        return "\n".join(": ".join(x) for x in state.items())

    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-Type", "text/plain")
        self.end_headers()
        self.wfile.write(self.fetch_format_isgx().encode())


def run_server_forever():
    print("Server is about to start")
    httpd = HTTPServer(('0.0.0.0', 100), Collector)
    try:
        print("Server will serve on port %d" % httpd.server_port)
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass


class DockerMetrics(object):
    def __init__(self):
        self.dker = docker.from_env()

    def epc_usage_for_container(self, container_id) -> float:
        return 0

    def container_id_for_ip(self, ip_address):
        for net in self.dker.networks.list():
            for container_id, container_data in net.attrs["Containers"].items():
                if container_data["IPv4Address"].split("/")[0] == ip_address or \
                                container_data["IPv6Address"].split("/")[0] == ip_address:
                    return container_id
        return None

    def pids_of_container(self, container_id):
        parent_pid = self.dker.containers.get(container_id).attrs["State"]["Pid"]
        proc = psutil.Process(parent_pid)
        proc.children(recursive=True)


class IsgxDriver(object):
    # Name can be anything, type is a Python format argument
    _sgx_enclave_usage = (
        {
            "name": "dummy",
            "type": "Q",
            "default_value": 0,
        },
    )

    def __init__(self):
        self._epc_ranges = []
        self._read_epc_physical_space()

    def _read_epc_physical_space(self):
        epc_ranges = []
        number_of_epcs = 0

        f = open("/dev/kmsg")
        fd = os.dup(f.fileno())
        f.close()
        fcntl(fd, F_SETFL, os.O_NONBLOCK)

        with open(fd) as kmsg:
            ksmg_header_re = re.compile(r"intel_sgx: Intel SGX Driver v.+")
            kmsg_number_of_epc_re = re.compile(r"intel_sgx: Number of EPCs ([0-9]+)")
            kmsg_epc_range_re = re.compile(r"intel_sgx: EPC memory range 0x([0-9a-f]+)-0x([0-9a-f]+)")
            for line in kmsg:
                if ksmg_header_re.search(line) is not None:
                    # Reset the ranges already detected, the driver may have been unloaded/loaded multiple times
                    epc_ranges = []
                    continue
                search = kmsg_number_of_epc_re.search(line)
                if search is not None:
                    number_of_epcs = int(search.group(1))
                    continue
                search = kmsg_epc_range_re.search(line)
                if search is not None:
                    start = int(search.group(1), 16)
                    end = int(search.group(2), 16)
                    epc_ranges.append((start, end))

        assert len(epc_ranges) > 0, "No EPC found"
        assert len(epc_ranges) == number_of_epcs, "Mismatch between number of EPCs declared and found"
        self._epc_ranges = epc_ranges

    def sgx_usage(self):
        return {val["name"]: "0" for idx, val in enumerate(self._sgx_enclave_usage)}


if __name__ == "__main__":
    # driver = IsgxDriver()
    # print(driver._epc_ranges)
    run_server_forever()
