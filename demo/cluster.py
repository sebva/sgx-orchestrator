import traceback
from typing import List

import kubernetes
from kubernetes.client import *
from kubernetes.client.rest import ApiException

DEFAULT_NAMESPACE = "default"


class Cluster(object):
    sgx_image = "10.75.0.2:5000/sgx-app-mem:1.2"
    standard_image = "10.75.0.2:5000/standard-app-mem:1.2"

    def __init__(self):
        kubernetes.config.load_kube_config()
        self.api = CoreV1Api()

    @staticmethod
    def pod_requests_sgx(pod: V1Pod) -> bool:
        for container in pod.spec.containers:
            for demands in (container.resources.limits, container.resources.requests):
                if isinstance(demands, dict) and "intel.com/sgx" in demands.keys():
                    return True
        return False

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
            self.api.create_namespaced_pod(DEFAULT_NAMESPACE, pod)
        except ApiException:
            print("Creating Pod failed!")
            traceback.print_exc()

    def list_pods(self) -> List[V1Pod]:
        return self.api.list_namespaced_pod(DEFAULT_NAMESPACE).items
