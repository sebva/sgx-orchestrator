import random
from typing import List

from kubernetes.client import V1Node, V1Pod

from policy import Policy, separate_nodes, pod_requests_sgx


class PolicyDumb(Policy):
    def filter(self, nodes: List[V1Node], pod: V1Pod) -> List[V1Node]:
        sgx_nodes, standard_nodes = separate_nodes(nodes)
        if pod_requests_sgx(pod):
            # TODO Filter nodes with EPC already full
            return sgx_nodes
        else:
            return nodes

    def select(self, filtered_nodes: List[V1Node], pod: V1Pod) -> V1Node:
        return random.choice(filtered_nodes)
