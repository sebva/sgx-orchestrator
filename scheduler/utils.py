import functools
from typing import List, Tuple, Dict

from influxdb import InfluxDBClient
from kubernetes.client import V1Node, V1Pod

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
    results = influx_client.query(
        'SELECT SUM(epc) AS epc FROM (SELECT MAX(value) AS epc FROM "sgx/epc" WHERE value <> 0 AND time >= now() - 25s'
        ' GROUP BY pod_name, nodename) GROUP BY nodename'
    )
    return {k[1]["nodename"]: next(v)["epc"] for k, v in results.items()}


def nodes_memory_usage() -> Dict[str, float]:
    results = influx_client.query(
        'SELECT MEAN(value) AS memory FROM "memory/usage" WHERE time >= now() - 3m AND type=\'node\' GROUP BY nodename'
    )
    return {k[1]["nodename"]: next(v)["memory"] for k, v in results.items()}


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
        pod.spec.containers, 0
    )
