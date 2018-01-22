import traceback
from typing import List

import functools
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

    @staticmethod
    def convert_k8s_suffix(k8s_value: str) -> float:
        try:
            return float(k8s_value)
        except ValueError:
            pass

        suffixes = [
            ("Ki", 2, 10),
            ("Mi", 2, 20),
            ("Gi", 2, 30),
            ("Ti", 2, 40),
            ("Pi", 2, 50),
            ("Ei", 2, 60),
            ("n", 10, -9),
            ("u", 10, -6),
            ("m", 10, -3),
            ("k", 10, 3),
            ("M", 10, 6),
            ("G", 10, 9),
            ("T", 10, 12),
            ("P", 10, 15),
            ("E", 10, 18),
        ]
        for suffix in suffixes:
            if k8s_value.endswith(suffix[0]):
                k8s_value_without_suffix = k8s_value[:-len(suffix[0])]
                return float(k8s_value_without_suffix) * (suffix[1] ** suffix[2])
        return float(k8s_value)

    @staticmethod
    def pod_sum_resources_requests(pod: V1Pod, metric: str):
        return functools.reduce(
            lambda acc, container: acc + Cluster.convert_k8s_suffix(container.resources.requests[metric]),
            filter(lambda x: x.resources.requests is not None and metric in x.resources.requests, pod.spec.containers),
            0
        )

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
