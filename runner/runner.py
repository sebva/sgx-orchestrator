#!/usr/bin/python3 -u
import argparse
import math
import random
import time
import traceback

from kubernetes import config
from kubernetes.client import *
from kubernetes.client.rest import ApiException

config.load_kube_config()
api = CoreV1Api()
random.seed(792283085)

scheduler_name = "binpack"
proportion_sgx = 0

sgx_image = "172.28.3.1:5000/sgx-app-mem:1.1"
standard_image = "172.28.3.1:5000/standard-app-mem:1.1"

epc_size_pages = 23936
memory_size_bytes = 64.0 * (2 ** 30)

column_start_time = 0
column_end_time = 1
column_requested_memory = 3
column_maximum_memory = 4


def is_job_sgx(nth: int) -> bool:
    return random.random() < proportion_sgx


def launch_pod(pod_name: str, duration: int, requested_pages: int, actual_pages: int, is_sgx: bool):
    resource_requirements = V1ResourceRequirements(
        limits={"intel.com/sgx": requested_pages},
        requests={"intel.com/sgx": requested_pages}
    ) if is_sgx else V1ResourceRequirements(
        requests={"memory": requested_pages * 4096}
        # Do not set limits, otherwise Kubernetes will kill the pod if it gets exceeded
    )

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
    except ApiException:
        print("Creating Pod failed!")
        traceback.print_exc()


def jobs_to_execute(filename: str, skip: int = -1):
    """
    Reads the file with the parsed trace, and yield a job description when needed
    :param filename: File to parse
    :param skip: Only parser every nth job in the trace (negative value to disable)
    """
    with open(filename) as jobs_csv:
        initial_time_trace = None
        initial_time_real = None
        job_id = 0  # Always incremented
        nth_job = 0  # Only incremented after a job is actually started

        for line in jobs_csv:
            # Skip one in N jobs
            if skip > 1 and job_id % skip != 0:
                job_id += 1
                continue

            split = line.split(",")

            (start_time, end_time, requested_memory, actual_memory) = (
                float(split[column_start_time]) / 1000000,
                float(split[column_end_time]) / 1000000,
                float(split[column_requested_memory]),
                float(split[column_maximum_memory])
            )

            if math.isclose(requested_memory, 0) or math.isclose(actual_memory, 0):
                print("Skipping job '%d' requiring 0 memory" % job_id)
                job_id += 1
                continue

            is_sgx = is_job_sgx(nth_job)
            if is_sgx:
                requested_memory *= epc_size_pages
                actual_memory *= epc_size_pages
            else:
                requested_memory *= memory_size_bytes / 4096
                actual_memory *= memory_size_bytes / 4096

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
                is_sgx,  # is_sgx
            )

            nth_job += 1
            job_id += 1


def main(trace_file: str, skip: int = -1):
    for job in jobs_to_execute(trace_file, skip):
        print("%f Starting job %s" % (time.time(), job.__repr__()))
        launch_pod(*job)
    print("End of experiment. Gather the results, and only after may you clean finished pods.")
    print("kubectl get pod --show-all | grep experiment | cut -d' ' -f 1 | xargs kubectl delete pod")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Experiments runner")
    parser.add_argument("-s", "--scheduler", type=str, default=scheduler_name, nargs="?",
                        help="Name of the custom scheduler to use")
    parser.add_argument("-k", "--skip", default=-1, type=int, nargs="?", help="Skip every nth job")
    parser.add_argument("-x", "--sgx", default=0, type=float, nargs="?",
                        help="Proportion of SGX jobs between 0 (no SGX) and 1 (all SGX)")
    parser.add_argument("trace", help="Trace file to use")
    args = parser.parse_args()
    scheduler_name = args.scheduler
    proportion_sgx = args.sgx

    main(args.trace, args.skip)
