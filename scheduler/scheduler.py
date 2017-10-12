#!/usr/bin/env python3
import argparse
import sys
import time
from datetime import datetime
from typing import List

from kubernetes import client, config
from kubernetes.client import V1ObjectMeta, V1ObjectReference, V1Event, V1EventSource, V1Pod, V1Node, V1Binding

from policy_binpack import PolicyBinpack
from policy_dumb import PolicyDumb
from policy_spread import PolicySpread

policy = None
policies = {
    "dumb": PolicyDumb,
    "binpack": PolicyBinpack,
    "spread": PolicySpread,
}


def init(policy_str: str):
    global policy
    config.load_kube_config()

    try:
        policy = policies[policy_str]()
        print("Using '%s' policy" % policy_str)
    except KeyError:
        print("The policy you specified does not exist", file=sys.stderr)
        sys.exit(1)


def list_unscheduled_pods() -> List[V1Pod]:
    api = client.CoreV1Api()
    pods = api.list_pod_for_all_namespaces(
        field_selector=("spec.nodeName=,spec.schedulerName=%s" % scheduler_name)).items
    print("Found %d unscheduled pods" % len(pods))
    return pods


def get_nodes() -> List[V1Node]:
    return client.CoreV1Api().list_node().items


def notify_binding(pod: V1Pod, node: V1Node):
    timestamp = datetime.utcnow().isoformat("T") + "Z"

    event = V1Event(
        count=1,
        message=("Scheduled %s on %s" % (pod.metadata.name, node.metadata.name)),
        metadata=V1ObjectMeta(generate_name=pod.metadata.name + "-"),
        reason="Scheduled",
        last_timestamp=timestamp,
        first_timestamp=timestamp,
        type="Normal",
        source=V1EventSource(component="efficient-scheduler"),
        involved_object=V1ObjectReference(
            kind="Pod",
            name=pod.metadata.name,
            namespace="default",
            uid=pod.metadata.uid
        )
    )
    client.CoreV1Api().create_namespaced_event("default", event)
    print("Event sent")


def assign_pod_to_node(pod: V1Pod, node: V1Node):
    print("Scheduling %s on %s" % (pod.metadata.name, node.metadata.name))
    binding = V1Binding(
        api_version="v1",
        kind="Binding",
        metadata=V1ObjectMeta(
            name=pod.metadata.name
        ),
        target=V1ObjectReference(
            api_version="v1",
            kind="Node",
            name=node.metadata.name
        )
    )
    client.CoreV1Api().create_namespaced_pod_binding(pod.metadata.name, "default", binding)
    print("Scheduled %s on %s" % (pod.metadata.name, node.metadata.name))

    notify_binding(pod, node)


def schedule(pods: List[V1Pod]):
    nodes = get_nodes()
    for pod in pods:
        filtered_nodes = policy.filter(nodes, pod)
        if filtered_nodes is None or len(filtered_nodes) <= 0:
            print("Pod %s cannot be scheduled at this time (filter)" % pod.metadata.name)
            continue

        selected_node = policy.select(filtered_nodes, pod)
        if selected_node is None:
            print("Pod %s cannot be scheduled at this time (select)" % pod.metadata.name)
            continue

        assign_pod_to_node(pod, selected_node)


def main_loop():
    try:
        while True:
            pods = list_unscheduled_pods()
            schedule(pods)
            time.sleep(5)
    except KeyboardInterrupt:
        pass


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="SGX-Aware scheduler")
    parser.add_argument("-n", "--name", help="Name of the scheduler", default="efficient", type=str)
    parser.add_argument('-p', '--policy', help="Set which policy to use for the scheduler", default="binpack",
                        choices=policies.keys())
    args = parser.parse_args()

    scheduler_name = args.name
    print("Scheduler starts as '%s'" % scheduler_name)
    init(args.policy)
    print("Scheduler started")
    main_loop()
