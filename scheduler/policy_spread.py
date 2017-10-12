import random
import statistics
from typing import List, Optional, Dict, Union

from kubernetes.client import V1Node, V1Pod

import utils
from policy import Policy
from utils import pod_requests_sgx, pod_sum_resources_requests, separate_nodes


class PolicySpread(Policy):
    def select(self, filtered_nodes: List[V1Node], pod: V1Pod) -> Optional[V1Node]:
        # When select is called, only nodes which can potentially host the pod are left

        if len(filtered_nodes) <= 0:
            return None

        if pod_requests_sgx(pod):
            raw_usages = utils.nodes_epc_usage()
        else:
            (sgx_nodes, standard_nodes) = separate_nodes(filtered_nodes)
            if len(standard_nodes) >= 1:  # Only allow placement on SGX nodes when there is no other choice
                filtered_nodes = standard_nodes
            raw_usages = utils.nodes_memory_usage()

        random.shuffle(filtered_nodes)  # Better fairness when nodes have the same usage

        base_usages = [[node.metadata.name, projected_memory_usage(node, None, raw_usages)] for node in filtered_nodes]
        best_node = filtered_nodes[0]
        best_stdev = 10**100  # Big number
        for node in filtered_nodes:
            usages_copy = list(base_usages)
            for usage in usages_copy:
                if usage[0] == node.metadata.name:
                    usage[1] = projected_memory_usage(node, pod, raw_usages)
                    break
            stdev = statistics.pstdev(x[1] for x in usages_copy)
            if stdev < best_stdev:
                best_stdev = stdev
                best_node = node

        return best_node


def projected_memory_usage(node: V1Node, pod: Optional[V1Pod], usage: Dict[str, Union[int, float]]) -> Union[int, float]:
    try:
        usage = usage[node.metadata.name]
    except KeyError:
        usage = 0

    if pod is not None:
        usage += pod_sum_resources_requests(pod, "intel.com/sgx" if pod_requests_sgx(pod) else "memory")
    return usage
