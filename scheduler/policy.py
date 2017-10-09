from abc import ABC, abstractmethod
from typing import List, Optional

from kubernetes.client import V1Pod, V1Node

from utils import separate_nodes, pod_requests_sgx, nodes_epc_usage, convert_k8s_suffix, nodes_memory_usage, \
    pod_sum_resources_requests

overcommit_tolerance = 1.1


class Policy(ABC):
    def filter(self, nodes: List[V1Node], pod: V1Pod) -> List[V1Node]:
        sgx_nodes, standard_nodes = separate_nodes(nodes)
        if pod_requests_sgx(pod):
            return filter_sgx(sgx_nodes, pod)
        else:
            return filter_standard(nodes, pod)

    @abstractmethod
    def select(self, filtered_nodes: List[V1Node], pod: V1Pod) -> Optional[V1Node]:
        pass


def filter_sgx(nodes: List[V1Node], pod: V1Pod) -> List[V1Node]:
    """
    Filter nodes that can accommodate the pod, tolerating overcommit_tolerance.
    """
    epc_usage = nodes_epc_usage()
    ret = []
    for node in nodes:
        node_name = node.metadata.name
        node_total_epc = convert_k8s_suffix(node.status.allocatable["intel.com/sgx"])
        pod_epc = pod_sum_resources_requests(pod, "intel.com/sgx")
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
        pod_memory = pod_sum_resources_requests(pod, "memory")
        if memory_usage[node_name] + pod_memory < node_total_memory:  # No overcommit for standard memory
            ret.append(node)
    return ret
