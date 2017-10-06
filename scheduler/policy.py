from abc import ABC, abstractmethod
from typing import List, Tuple, Dict

from influxdb import InfluxDBClient
from kubernetes.client import V1Pod, V1Node

influx_client = InfluxDBClient("monitoring-influxdb.kube-system.svc.cluster.local", database="k8s")


class Policy(ABC):
    def filter(self, nodes: List[V1Node], pod: V1Pod) -> List[V1Node]:
        sgx_nodes, standard_nodes = separate_nodes(nodes)
        if pod_requests_sgx(pod):
            return sgx_nodes
        else:
            return nodes

    @abstractmethod
    def select(self, filtered_nodes: List[V1Node], pod: V1Pod) -> V1Node:
        pass


def separate_nodes(nodes: List[V1Node]) -> Tuple[List[V1Node], List[V1Node]]:
    sgx_nodes = []
    standard_nodes = []
    for node in nodes:
        sgx_nodes.append(node) if "intel.com/sgx" in node.status.capacity.keys() else standard_nodes.append(node)
    return sgx_nodes, standard_nodes


def pod_requests_sgx(pod: V1Pod) -> bool:
    for container in pod.spec.containers:
        for demands in (container.resources.limits, container.resources.requests):
            if isinstance(demands, dict) and "intel.com/sgx" in demands.keys():
                return True
    return False


def nodes_epc_usage() -> Dict[str, int]:
    results = influx_client.query(
        'SELECT SUM(epc) AS epc FROM (SELECT MODE(value) AS epc FROM "sgx/epc" WHERE value <> 0 AND time >= now() - 3m '
        'GROUP BY pod_name, nodename) GROUP BY nodename'
    )
    return {k[1]["nodename"]: next(v)["epc"] for k, v in results.items()}
