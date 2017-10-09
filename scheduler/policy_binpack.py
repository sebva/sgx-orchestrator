import functools
from typing import List, Optional

from kubernetes.client import V1Node, V1Pod

from policy import Policy
from utils import node_supports_sgx, pod_requests_sgx, nodes_epc_usage, nodes_memory_usage, convert_k8s_suffix

overcommit_tolerance = 1.1


class PolicyBinpack(Policy):
    def filter(self, nodes: List[V1Node], pod: V1Pod) -> List[V1Node]:
        nodes = super().filter(nodes, pod)

        if pod_requests_sgx(pod):
            return filter_sgx(nodes, pod)
        else:
            return filter_standard(nodes, pod)

    def select(self, filtered_nodes: List[V1Node], pod: V1Pod) -> Optional[V1Node]:
        if len(filtered_nodes) <= 0:
            return None

        if pod_requests_sgx(pod):
            sort_key = lambda node: node.metadata.name
        else:
            # In Python, False is before True, and sorted() can sort based on a tuple.
            # This way, non-sgx nodes are sorted before the standard ones.
            sort_key = lambda node: (node_supports_sgx(node), node.metadata.name)

        return sorted(filtered_nodes, key=sort_key)[0]


def filter_sgx(nodes: List[V1Node], pod: V1Pod) -> List[V1Node]:
    """
    Filter nodes that can accommodate the pod, tolerating overcommit_tolerance.
    """
    epc_usage = nodes_epc_usage()
    ret = []
    for node in nodes:
        node_name = node.metadata.name
        node_total_epc = convert_k8s_suffix(node.status.allocatable["intel.com/sgx"])
        pod_epc = functools.reduce(
            lambda acc, container: acc + convert_k8s_suffix(container.resources.requests["intel.com/sgx"]),
            pod.spec.containers, 0
        )
        if epc_usage[node_name] + pod_epc < node_total_epc * overcommit_tolerance:
            ret.append(node)
    return ret


def filter_standard(nodes: List[V1Node], pod: V1Pod) -> List[V1Node]:
    # FIXME Factorize with filter_sgx
    memory_usage = nodes_memory_usage()
    ret = []
    for node in nodes:
        node_name = node.metadata.name
        node_total_memory = convert_k8s_suffix(node.status.allocatable["memory"])
        pod_memory = functools.reduce(
            lambda acc, container: acc + convert_k8s_suffix(container.resources.requests["memory"]),
            pod.spec.containers, 0
        )
        if memory_usage[node_name] + pod_memory < node_total_memory:  # No overcommit for standard memory
            ret.append(node)
    return ret
