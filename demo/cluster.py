import traceback

import kubernetes
from kubernetes.client import *
from kubernetes.client.rest import ApiException


class Cluster(object):
    sgx_image = "10.75.0.2:5000/sgx-app-mem:1.2"
    standard_image = "10.75.0.2:5000/standard-app-mem:1.2"

    def __init__(self):
        kubernetes.config.load_kube_config()
        self.api = CoreV1Api()

    def launch_pod(self, pod_name: str, scheduler: str, duration: int, limit: float, actual: float, is_sgx: bool):
        resource_requirements = V1ResourceRequirements(
            limits={"intel.com/sgx": int(limit / 4096)},
            requests={"intel.com/sgx": int(limit / 4096)},
        ) if is_sgx else V1ResourceRequirements(
            limits={"memory": limit},
            requests={"memory": limit},
        )

        pod = V1Pod(
            api_version="v1",
            kind="Pod",
            metadata=V1ObjectMeta(
                name=pod_name
            ),
            spec=V1PodSpec(
                termination_grace_period_seconds=0,
                scheduler_name=scheduler,
                containers=[V1Container(
                    name="app",
                    image=self.sgx_image if is_sgx else self.standard_image,
                    args=["-d", str(duration), str(int(actual / 4096))],
                    resources=resource_requirements
                )],
                restart_policy="OnFailure"
            )
        )

        try:
            self.api.create_namespaced_pod("default", pod)
        except ApiException:
            print("Creating Pod failed!")
            traceback.print_exc()
