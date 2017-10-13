import functools
from collections import defaultdict
from typing import List, Tuple, Dict

from influxdb import InfluxDBClient
from kubernetes.client import V1Node, V1Pod, CoreV1Api

influx_client = InfluxDBClient("monitoring-influxdb.kube-system.svc.cluster.local", database="k8s")


def node_supports_sgx(node: V1Node) -> bool:
    return "intel.com/sgx" in node.status.capacity.keys()


def separate_nodes(nodes: List[V1Node]) -> Tuple[List[V1Node], List[V1Node]]:
    sgx_nodes = []
    standard_nodes = []
    for node in nodes:
        sgx_nodes.append(node) if node_supports_sgx(node) else standard_nodes.append(node)
    return sgx_nodes, standard_nodes


def pod_requests_sgx(pod: V1Pod) -> bool:
    for container in pod.spec.containers:
        for demands in (container.resources.limits, container.resources.requests):
            if isinstance(demands, dict) and "intel.com/sgx" in demands.keys():
                return True
    return False


def nodes_epc_usage() -> Dict[str, int]:
    """
    Fetches the EPC usage for all nodes in the cluster.
    Takes the bigger value between measured usage and sum of requests.
    """
    k8s_api = CoreV1Api()
    pods = k8s_api.list_pod_for_all_namespaces(
        field_selector="spec.nodeName!="
    ).items
    nodes_pods_usage = (
        (x.spec.node_name, pod_sum_resources_requests(x, "intel.com/sgx")) for x in pods if pod_requests_sgx(x)
    )
    usage_per_node = defaultdict(lambda: 0)
    for (node_name, usage) in nodes_pods_usage:
        usage_per_node[node_name] += usage

    influx_results = influx_client.query(
        'SELECT SUM(epc) AS epc FROM (SELECT MAX(value) AS epc FROM "sgx/epc" WHERE value <> 0 AND time >= now() - 25s'
        ' GROUP BY pod_name, nodename) GROUP BY nodename'
    )
    return {k[1]["nodename"]: max(next(v)["epc"], usage_per_node[k[1]["nodename"]]) for k, v in influx_results.items()}


def nodes_memory_usage() -> Dict[str, float]:
    """
    Fetches the memory usage for all nodes in the cluster.
    Takes the bigger value between measured usage and sum of requests.
    """
    k8s_api = CoreV1Api()
    pods = k8s_api.list_pod_for_all_namespaces(
        field_selector="spec.nodeName!="
    ).items
    nodes_pods_usage = (
        (x.spec.node_name, pod_sum_resources_requests(x, "memory")) for x in pods
    )
    usage_per_node = defaultdict(lambda: 0)
    for (node_name, usage) in nodes_pods_usage:
        usage_per_node[node_name] += usage

    influx_results = influx_client.query(
        'SELECT MEAN(value) AS memory FROM "memory/usage" WHERE time >= now() - 3m AND type=\'node\' GROUP BY nodename'
    )
    return {k[1]["nodename"]: max(next(v)["memory"], usage_per_node[k[1]["nodename"]]) for k, v in
            influx_results.items()}


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
            print("orig: %s, no suff: %s" % (k8s_value, k8s_value_without_suffix))
            return float(k8s_value_without_suffix) * (suffix[1] ** suffix[2])
    return float(k8s_value)


def pod_sum_resources_requests(pod: V1Pod, metric: str):
    return functools.reduce(
        lambda acc, container: acc + convert_k8s_suffix(container.resources.requests[metric]),
        filter(lambda x: metric in x.resources.requests, pod.spec.containers), 0
    )
