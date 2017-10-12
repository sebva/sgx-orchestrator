from time import sleep
from typing import List, Tuple

import docker.models.containers
import kubernetes
import psutil
from docker.models.containers import Container
from influxdb import InfluxDBClient
from kubernetes.client import V1Pod, V1ContainerStatus

import sgx

psutil.PROCFS_PATH = "/hostproc"
influx_client = InfluxDBClient("monitoring-influxdb.kube-system.svc.cluster.local", database="k8s")
docker_client = docker.from_env(version="1.24")
try:
    kubernetes.config.load_incluster_config()
except kubernetes.config.config_exception.ConfigException:
    kubernetes.config.load_kube_config()
kubernetes_client = kubernetes.client.CoreV1Api()


def get_all_pods_on_node(node_name: str = docker_client.info()["Name"]) -> List[V1Pod]:
    return kubernetes_client.list_pod_for_all_namespaces(field_selector="spec.nodeName={}".format(node_name)).items


def get_sgx_docker_containers() -> List[Container]:
    docker_containers = docker_client.containers.list()
    return [x for x in docker_containers if
            isinstance(x.attrs['HostConfig']['Devices'], list) and
            '/dev/isgx' in map(lambda y: y['PathOnHost'], x.attrs['HostConfig']['Devices'])]


def get_sgx_k8s_containers_in_pod(pod: V1Pod, sgx_docker_containers: List[Container] = get_sgx_docker_containers()) -> \
        List[Tuple[V1ContainerStatus, Container]]:
    container_statuses = pod.status.container_statuses
    if container_statuses is None:
        return []

    result = []
    for k8s_container in container_statuses:
        for docker_container in sgx_docker_containers:
            if k8s_container.container_id is not None and k8s_container.container_id[9:] == docker_container.id:
                result.append((k8s_container, docker_container))

    return result


def flatten_labels(labels: dict) -> str:
    return ','.join("{}:{}".format(key, value) for key, value in labels.items())


def container_to_influxdb_tags(pod: V1Pod, pod_container: V1ContainerStatus) -> dict:
    cluster_name = pod.metadata.cluster_name
    if cluster_name is None:
        cluster_name = "default"
    return {
        "type": "pod_container",
        "pod_id": pod.metadata.uid,
        "pod_name": pod.metadata.name,
        "pod_namespace": pod.metadata.namespace,
        "namespace_name": pod.metadata.namespace,
        # "namespace_id": None,
        "container_name": pod_container.name,
        "labels": flatten_labels(pod.metadata.labels),
        "nodename": pod.spec.node_name,
        "hostname": pod.spec.hostname,
        # "resource_id": None,
        # "host_id": None,
        "container_base_image": pod_container.image_id[18:],
        "cluster_name": cluster_name
    }


def batch_push_to_influx(metrics: List[Tuple[str, int, dict]]) -> bool:
    points = [
        {
            "measurement": metric_name,
            "fields": {
                "value": value
            },
            "tags": labels,
        } for metric_name, value, labels in metrics
    ]
    return influx_client.write_points(points)


def push_to_influx(metric_name: str, value: int, labels: dict) -> bool:
    return batch_push_to_influx([(metric_name, value, labels)])


def get_sgx_memory_usage(pid: int) -> int:
    return int(sgx.sgx_stats_pid(pid)['epc_pages_cnt'])


def main():
    print("Metrics probe started")
    while True:
        print("Listing all pods")
        all_pods = get_all_pods_on_node()
        print("Listing Docker containers")
        docker_containers = get_sgx_docker_containers()
        metrics = []
        for pod in all_pods:
            sgx_containers = get_sgx_k8s_containers_in_pod(pod, docker_containers)
            for (k8s_container, docker_container) in sgx_containers:
                influxdb_tags = container_to_influxdb_tags(pod, k8s_container)
                parent_pid = docker_container.attrs['State']['Pid']

                epc_usage = get_sgx_memory_usage(parent_pid)

                for child_process in psutil.Process(parent_pid).children(recursive=True):
                    epc_usage += get_sgx_memory_usage(child_process.pid)

                metrics.append(("sgx/epc", epc_usage, influxdb_tags,))
        print("Pushing metrics: " + str(metrics))
        batch_push_to_influx(metrics)
        print("Sleeping 7 seconds")
        sleep(7)


if __name__ == '__main__':
    main()


# InfluxDB labels from Heapster source code:
# LabelMetricSetType = LabelDescriptor{
# 		Key:         "type",
# 		Description: "Type of the metrics set (container, pod, namespace, node, cluster)",
# 	}
# 	MetricSetTypeSystemContainer = "sys_container"
# 	MetricSetTypePodContainer    = "pod_container"
# 	MetricSetTypePod             = "pod"
# 	MetricSetTypeNamespace       = "ns"
# 	MetricSetTypeNode            = "node"
# 	MetricSetTypeCluster         = "cluster"
#
# 	LabelPodId = LabelDescriptor{
# 		Key:         "pod_id",
# 		Description: "The unique ID of the pod",
# 	}
# 	LabelPodName = LabelDescriptor{
# 		Key:         "pod_name",
# 		Description: "The name of the pod",
# 	}
# 	// Deprecated label
# 	LabelPodNamespace = LabelDescriptor{
# 		Key:         "pod_namespace",
# 		Description: "The namespace of the pod",
# 	}
# 	LabelNamespaceName = LabelDescriptor{
# 		Key:         "namespace_name",
# 		Description: "The name of the namespace",
# 	}
# 	LabelPodNamespaceUID = LabelDescriptor{
# 		Key:         "namespace_id",
# 		Description: "The UID of namespace of the pod",
# 	}
# 	LabelContainerName = LabelDescriptor{
# 		Key:         "container_name",
# 		Description: "User-provided name of the container or full container name for system containers",
# 	}
# 	LabelLabels = LabelDescriptor{
# 		Key:         "labels",
# 		Description: "Comma-separated list of user-provided labels",
# 	}
# 	LabelNodename = LabelDescriptor{
# 		Key:         "nodename",
# 		Description: "nodename where the container ran",
# 	}
# 	LabelHostname = LabelDescriptor{
# 		Key:         "hostname",
# 		Description: "Hostname where the container ran",
# 	}
# 	LabelResourceID = LabelDescriptor{
# 		Key:         "resource_id",
# 		Description: "Identifier(s) specific to a metric",
# 	}
# 	LabelHostID = LabelDescriptor{
# 		Key:         "host_id",
# 		Description: "Identifier specific to a host. Set by cloud provider or user",
# 	}
# 	LabelContainerBaseImage = LabelDescriptor{
# 		Key:         "container_base_image",
# 		Description: "User-defined image name that is run inside the container",
# 	}
