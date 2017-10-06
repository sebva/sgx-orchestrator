import random
from typing import List

from kubernetes.client import V1Node, V1Pod

from policy import Policy


class PolicyDumb(Policy):
    def select(self, filtered_nodes: List[V1Node], pod: V1Pod) -> V1Node:
        return random.choice(filtered_nodes)
