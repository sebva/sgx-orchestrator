#!/usr/bin/env python3
import argparse
import datetime
import json
import re
import sys
import time

import kubernetes
from kubernetes.client import V1Pod, CoreV1Api

kubernetes.config.load_kube_config()
kube_client = CoreV1Api()


def load_multiple_json(fp):
    buffer = ""
    for line in fp:
        buffer += line
        try:
            yield json.loads(buffer)
            buffer = ""
        except ValueError:
            pass


def get_pod_k8s(pod_id: str) -> V1Pod:
    return kube_client.read_namespaced_pod(pod_id, "default")


def datetime_to_timestamp(dt: datetime.datetime) -> float:
    return time.mktime(dt.timetuple())


def parse_runner_output(fp):
    regex = re.compile("([0-9]+\.[0-9]*) Starting job \('(\w+)', ([0-9]+), ([0-9]+), ([0-9]+), (True|False)\)\n")
    for line in fp:
        match = regex.fullmatch(line)
        if match is not None:
            (runner_start_time, job_id, duration, requested_pages, actual_pages, is_sgx) = match.groups()
            try:
                runner_start_time = datetime.datetime.utcfromtimestamp(float(runner_start_time))
                pod_info = get_pod_k8s("experiment-" + job_id)
                k8s_created_time = pod_info.metadata.creation_timestamp
                k8s_actual_start_time = pod_info.status.container_statuses[0].state.terminated.started_at
                k8s_actual_end_time = pod_info.status.container_statuses[0].state.terminated.finished_at

                yield (job_id, duration, requested_pages, actual_pages, is_sgx, runner_start_time,
                       k8s_created_time, k8s_actual_start_time, k8s_actual_end_time)
            except:
                print("Error with %s" % job_id, file=sys.stderr)


def main(filename_in: str, filename_out=None):
    # May or may not be needed, as the info can be retrieved from Kubernetes after the run is complete:
    # with open("results/kube-events-2017-10-16-0057.json") as fp:
    #     for extracted in load_multiple_json(fp):
    #         print(extracted)

    print("job_id,duration,requested_pages,actual_pages,is_sgx,runner_start_time,k8s_created_time"
          ",k8s_actual_start_time,k8s_actual_end_time")
    output = None

    try:
        output = open(filename_out, "w") if filename_out is not None else sys.stdout
        with open(filename_in) as fp_in:
            for item in parse_runner_output(fp_in):
                print(",".join(str(x) for x in item), file=output)
    finally:
        if filename_out is not None and output is not None:
            output.close()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("filename")
    args = parser.parse_args()

    main(args.filename)
