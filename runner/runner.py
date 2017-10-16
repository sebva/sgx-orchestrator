#!/usr/bin/env python3
import argparse
import traceback

import atexit

import time
from kubernetes import config
from kubernetes.client import *
from kubernetes.client.rest import ApiException

config.load_kube_config()
api = CoreV1Api()

scheduler_name = "binpack"
pods = []

sgx_image = "172.28.3.1:5000/sgx-app-mem:1.0"
standard_image = "172.28.3.1:5000/standard-app-mem:1.0"

column_start_time = 0
column_end_time = 1
column_requested_memory = 3
column_maximum_memory = 4


def launch_pod(pod_name: str, duration: int, requested_pages: int, actual_pages: int, is_sgx: bool):
    global pods
    print("Launching a %s Pod that lasts %d seconds, requests %d pages and allocates %d pages" % (
        "SGX" if is_sgx else "standard", duration, requested_pages, actual_pages
    ))

    resource_requirements = V1ResourceRequirements(
        limits={"intel.com/sgx": requested_pages},
        requests={"intel.com/sgx": requested_pages}
    ) if is_sgx else None

    pod = V1Pod(
        api_version="v1",
        kind="Pod",
        metadata=V1ObjectMeta(
            name="experiment-%s" % pod_name
        ),
        spec=V1PodSpec(
            termination_grace_period_seconds=0,
            scheduler_name=scheduler_name,
            containers=[V1Container(
                name="app",
                image=sgx_image if is_sgx else standard_image,
                args=["-d", str(duration), str(actual_pages)],
                resources=resource_requirements
            )],
            restart_policy="OnFailure"
        )
    )

    try:
        api.create_namespaced_pod("default", pod)
        pods.append(pod)
    except ApiException:
        print("Creating Pod failed!")
        traceback.print_exc()


def jobs_to_execute(filename: str):
    """
    Reads the file with the parsed trace, and yield a job description when needed
    :param filename: File to parse
    """
    with open(filename) as jobs_csv:
        initial_time_trace = None
        initial_time_real = None
        job_id = 0

        for line in jobs_csv:
            # Skip one in N jobs
            if job_id % 100 != 0:
                job_id += 1
                continue

            split = line.split(",")

            (start_time, end_time, requested_memory, actual_memory) = (
                float(split[column_start_time]) / 1000000,
                float(split[column_end_time]) / 1000000,
                float(split[column_requested_memory]),  # Fraction of memory, TODO relate to absolute number of pages
                float(split[column_maximum_memory])  # Same as above
            )

            if requested_memory < 1 or actual_memory < 1:
                print("Skipping job '%d' requiring 0 memory" % job_id)
                continue

            if initial_time_trace is None:
                initial_time_trace = start_time
                initial_time_real = time.time()

            expected_relative_time = start_time - initial_time_trace
            actual_relative_time = time.time() - initial_time_real

            while expected_relative_time > actual_relative_time:
                time.sleep(expected_relative_time - actual_relative_time)  # Wait until it's time
                actual_relative_time = time.time() - initial_time_real

            yield (
                str(job_id),  # pod_name
                int(end_time - start_time),  # duration
                int(requested_memory),  # requested_pages
                int(actual_memory),  # actual_pages
                True,  # is_sgx TODO decide when to use SGX or not
            )

            job_id += 1


@atexit.register
def cleanup_pods():
    for p in pods:
        pod_name = p.metadata.name
        print("Deleting %s" % pod_name)
        try:
            api.delete_namespaced_pod(pod_name, "default", V1DeleteOptions())
        except ApiException:
            print("Delete failed")


def main(trace_file: str):
    last_job = None
    for job in jobs_to_execute(trace_file):
        print("Starting job %s" % job.__repr__())
        launch_pod(*job)
        last_job = job

    print("Last job started, waiting for completion")
    time.sleep(last_job[1] * 1.5)  # Wait until the end of the experiment
    # launch_pod("test", 30, 5000, 6000, is_sgx=False)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Experiments runner")
    parser.add_argument("-s", "--scheduler", type=str, default=scheduler_name, nargs="?",
                        help="Name of the custom scheduler to use")
    parser.add_argument("trace", help="Trace file to use")
    args = parser.parse_args()
    scheduler_name = args.scheduler

    main(args.trace)
