#!/usr/bin/env python3
import argparse
import traceback

import atexit
from kubernetes import config
from kubernetes.client import *
from kubernetes.client.rest import ApiException

config.load_kube_config()
api = CoreV1Api()

scheduler_name = "binpack"
pods = []

sgx_image = "172.28.3.1:5000/sgx-app-mem:1.0"
standard_image = "172.28.3.1:5000/standard-app-mem:1.0"


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
    with open(filename) as jobs_csv:
        for line in jobs_csv:
            # TODO Write parser here
            yield (
                "398274392",  # pod_name
                120,  # duration
                5000,  # requested_pages
                5500,  # actual_pages
                True,  # is_sgx
            )


@atexit.register
def cleanup_pods():
    for p in pods:
        pod_name = p.metadata.name
        print("Deleting %s" % pod_name)
        try:
            api.delete_namespaced_pod(pod_name, "default", V1DeleteOptions())
        except ApiException:
            print("Delete failed")


def main():
    # TODO Enable when parser is ready
    # for job in jobs_to_execute("trace/filename.txt"):
    #     launch_pod(*job)

    launch_pod("test", 30, 5000, 6000, is_sgx=False)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Experiments runner")
    parser.add_argument("-s", "--scheduler", type=str, default=scheduler_name, nargs="?",
                        help="Name of the custom scheduler to use")
    args = parser.parse_args()
    scheduler_name = args.scheduler

    main()
