#!/usr/bin/python2
import argparse
import os
import re
import subprocess

import time

numbers_regex = re.compile("[0-9]+")

available_sizes = sorted(
    int(numbers_regex.search(x).group(0)) for x in os.listdir('bin-sgx') if numbers_regex.search(x) is not None
)

parser = argparse.ArgumentParser()
parser.add_argument("--duration", "-d", type=float, help="Time that the SGX program has to run. Infinite when not specified")
parser.add_argument("pages", type=int, help="Number of EPC pages to allocate (circa +2)", default=1000, nargs="?")
args = parser.parse_args()

requested_size = args.pages
closest_size = min(available_sizes, key=lambda x: abs(x - requested_size))

print("Using %d as size closest to %d" % (closest_size, requested_size))

sgx_process = subprocess.Popen(("/entrypoint.sh", "./bin-sgx/dummy", "dummy.so-%d.signed" % closest_size))
if args.duration is not None:
    time_left = args.duration
    power = 1
    try:
        while time_left > 0 and sgx_process.poll() is None:
            time.sleep(power)
            time_left -= power
            power *= 2
            if power > time_left:
                power = time_left
    except KeyboardInterrupt:
        pass

if sgx_process.poll() is None:
    print("Killing SGX process")
    sgx_process.kill()
