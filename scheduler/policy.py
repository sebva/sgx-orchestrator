import random
from typing import List

from kubernetes.client import V1Pod, V1Node


def policy_filter(nodes: List[V1Node], pod: V1Pod) -> List[V1Node]:
    # TODO real policy
    return nodes


def policy_select(filtered_nodes: List[V1Node], pod: V1Pod) -> V1Node:
    # TODO real policy
    return random.choice(filtered_nodes)
