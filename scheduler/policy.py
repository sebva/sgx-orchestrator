from abc import ABC, abstractmethod
from typing import List, Tuple

from kubernetes.client import V1Pod, V1Node


class Policy(ABC):
    @abstractmethod
    def filter(self, nodes: List[V1Node], pod: V1Pod) -> List[V1Node]:
        pass

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
