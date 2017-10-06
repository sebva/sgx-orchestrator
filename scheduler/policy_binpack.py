import functools
import random
from typing import List

from kubernetes.client import V1Node, V1Pod

from policy import Policy, pod_requests_sgx, nodes_epc_usage

overcommit_tolerance = 1.1


class PolicyBinpack(Policy):
    def filter(self, nodes: List[V1Node], pod: V1Pod) -> List[V1Node]:
        nodes = super().filter(nodes, pod)

        if pod_requests_sgx(pod):
            return filter_sgx(nodes, pod)
        else:
            return filter_standard(nodes, pod)

    def select(self, filtered_nodes: List[V1Node], pod: V1Pod) -> V1Node:
        return random.choice(filtered_nodes)


def filter_sgx(nodes: List[V1Node], pod: V1Pod) -> List[V1Node]:
    epc_usage = nodes_epc_usage()
    ret = []
    for node in nodes:
        node_name = node.metadata.name
        node_total_epc = int(node.status.allocatable["intel.com/sgx"])
        pod_epc = functools.reduce(lambda acc, container: acc + int(container.resources.requests["intel.com/sgx"]),
                                   pod.spec.containers, 0)
        if epc_usage[node_name] + pod_epc < node_total_epc * overcommit_tolerance:
            ret.append(node)
    return ret


def filter_standard(nodes: List[V1Node], pod: V1Pod) -> List[V1Node]:
    # TODO
    return nodes
