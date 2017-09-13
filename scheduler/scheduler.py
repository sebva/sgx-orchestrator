#!/usr/bin/env python3
import time
from datetime import datetime
from typing import List

from kubernetes import client, config
from kubernetes.client import V1ObjectMeta, V1ObjectReference, V1Event, V1EventSource, V1Pod, V1Node, V1Binding

from policy import policy_filter, policy_select

scheduler_name = "efficient"


def init():
    config.load_kube_config()


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
        filtered_nodes = policy_filter(nodes, pod)
        selected_node = policy_select(filtered_nodes, pod)
        assign_pod_to_node(pod, selected_node)


if __name__ == '__main__':
    print("Scheduler starts")
    init()
    print("Scheduler started")
    try:
        while True:
            pods = list_unscheduled_pods()
            schedule(pods)
            time.sleep(5)
    except KeyboardInterrupt:
        pass
