#!/usr/bin/env python3
import random
from datetime import datetime
from typing import List

import time
from kubernetes import *
from kubernetes.client import models, V1ObjectMeta, V1ObjectReference, V1Event, V1EventSource

scheduler_name = "efficient"


def init():
    config.load_kube_config()


def list_unscheduled_pods() -> List[models.V1Pod]:
    api = client.CoreV1Api()
    pods = api.list_pod_for_all_namespaces(
        field_selector=("spec.nodeName=,spec.schedulerName=%s" % scheduler_name)).items
    print("Found %d unscheduled pods" % len(pods))
    return pods


def get_nodes() -> List[models.V1Node]:
    return client.CoreV1Api().list_node().items


def notify_binding(pod, node):
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


def assign_pod_to_node(pod: models.V1Pod, node: models.V1Node):
    print("Scheduling %s on %s" % (pod.metadata.name, node.metadata.name))
    binding = models.V1Binding(
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


def schedule(pods: List[models.V1Pod]):
    nodes = get_nodes()
    for pod in pods:
        random_node = random.choice(nodes)
        assign_pod_to_node(pod, random_node)


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
