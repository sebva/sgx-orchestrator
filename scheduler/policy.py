from abc import ABC, abstractmethod
from typing import List, Optional

from kubernetes.client import V1Pod, V1Node

from utils import separate_nodes, pod_requests_sgx


class Policy(ABC):
    def filter(self, nodes: List[V1Node], pod: V1Pod) -> List[V1Node]:
        sgx_nodes, standard_nodes = separate_nodes(nodes)
        if pod_requests_sgx(pod):
            return sgx_nodes
        else:
            return nodes

    @abstractmethod
    def select(self, filtered_nodes: List[V1Node], pod: V1Pod) -> Optional[V1Node]:
        pass
