import traceback

import kubernetes
from kubernetes.client import *
from kubernetes.client.rest import ApiException


class Cluster(object):
    def __init__(self):
        kubernetes.config.load_kube_config()
        self.api = CoreV1Api()

    def launch_pod(self, pod_name: str, duration: int, requested_pages: int, actual_pages: int, image: str):
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
                    image=image,
                    args=["-d", str(duration), str(actual_pages)],
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
