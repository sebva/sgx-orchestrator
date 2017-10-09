from typing import List, Optional

from kubernetes.client import V1Node, V1Pod

from policy import Policy
from utils import node_supports_sgx, pod_requests_sgx


class PolicyBinpack(Policy):
    def select(self, filtered_nodes: List[V1Node], pod: V1Pod) -> Optional[V1Node]:
        # When select is called, only nodes which can potentially host the pod are left

        if len(filtered_nodes) <= 0:
            return None

        if pod_requests_sgx(pod):
            sort_key = lambda node: node.metadata.name
        else:
            # In Python, False is before True, and sorted() can sort based on a tuple.
            # This way, non-sgx nodes are sorted before the standard ones.
            sort_key = lambda node: (node_supports_sgx(node), node.metadata.name)

        return sorted(filtered_nodes, key=sort_key)[0]
