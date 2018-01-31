#!/usr/bin/env python3
import argparse
import re
from itertools import tee, filterfalse
from typing import Tuple

from cluster import Cluster

cluster = None
args = None

units = {
    "k": 1e3,
    "M": 1e6,
    "G": 1e9,
}


def deploy_pod():
    match = re.fullmatch(r"(\d+(\.\d+)?)( ?([kMG]))?", args.memory)
    if match is None:
        print("Invalid memory usage")
        return
    memory = float(match.group(1))
    unit = match.group(4)
    try:
        memory *= units[unit]
    except KeyError:
        pass

    match = re.fullmatch(r"(\d+(\.\d+)?)( ?([kMG]))?", args.limit)
    if match is None:
        print("Invalid memory limit")
        return
    limit = float(match.group(1))
    unit = match.group(4)
    try:
        limit *= units[unit]
    except KeyError:
        pass

    if args.node is None:
        scheduler = args.scheduler
    else:
        scheduler = "demo"

    cluster.launch_pod(args.name, scheduler, args.duration, limit, memory, args.sgx, args.node)


def node_status():
    all_pods = cluster.list_pods()

    nodes = args.node
    if nodes is None:
        nodes = sorted(list({x.spec.node_name for x in all_pods if x.spec.node_name is not None}))

    for node in nodes:
        pods = [x for x in all_pods if x.spec.node_name == node and (not args.running or x.status.phase == "Running")]
        if len(pods) < 1:
            continue

        for metric in args.metrics:
            string_format = node_metrics[metric][0]
            func = node_metrics[metric][1]

            formatted_output = string_format % tuple(sum(x) for x in zip(*map(func, pods)))
            print("%s %s: %s" % (node, metric, formatted_output))


def count_sgx_standard(pods) -> Tuple[int, int]:
    i1, i2 = tee(pods)
    standard_pods, sgx_pods = filterfalse(cluster.pod_requests_sgx, i1), filter(cluster.pod_requests_sgx, i2)

    return len(list(standard_pods)), len(list(sgx_pods))


def global_status():
    pods = cluster.list_pods()

    for metric in args.metrics:
        filtered = filter(global_metrics[metric], pods)
        print("%s: standard=%d sgx=%d" % ((metric,) + count_sgx_standard(filtered)))


functions = {
    "deploy": deploy_pod,
    "node-status": node_status,
    "global-status": global_status,
}

node_metrics = {
    "pods": ("standard=%d sgx=%d", lambda pod: count_sgx_standard([pod])),
    "epc": ("epc_pages=%d", lambda pod: [Cluster.pod_sum_resources_requests(pod, "intel.com/sgx")]),
    "memory": ("memory=%d", lambda pod: [Cluster.pod_sum_resources_requests(pod, "memory")]),
}

global_metrics = {
    "pending": lambda pod: pod.spec.node_name is None,
    "running": lambda pod: pod.status.phase == "Running",
    "finished": lambda pod: pod.status.phase == "Succeeded",
    "total": lambda x: x,
}

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Convenience scripts for scheduler demo")
    subparsers = parser.add_subparsers(dest="command")
    subparsers.required = True

    deploy_subparser = subparsers.add_parser("deploy")
    deploy_subparser.add_argument("name", help="Pod identifier")
    deploy_subparser.add_argument("--node", "-n", help="Node on which to deploy the pod (bypass the scheduler)")
    deploy_subparser.add_argument("--sgx", action="store_true", help="Job will be SGX")
    deploy_subparser.add_argument("--memory", "-m", "--epc", "-e", required=True)
    deploy_subparser.add_argument("--limit", "-l", required=True)
    deploy_subparser.add_argument("--scheduler", "-s", default="", help="Scheduler to use",
                                  choices=["spread", "binpack", "", "dummy"])
    deploy_subparser.add_argument("--duration", "-d", help="Jobs runs for this much seconds", type=int, default=300)

    node_status_subparser = subparsers.add_parser("node-status")
    node_status_subparser.add_argument("--node", "-n", action="append",
                                       help="Node(s) for which to print the status (no argument = all nodes)")
    node_status_subparser.add_argument("--running", "-r", action="store_true", help="Only consider running pods")
    node_status_subparser.add_argument("metrics", nargs="+", help="Metrics to fetch", choices=node_metrics.keys())

    global_status_subparser = subparsers.add_parser("global-status")
    global_status_subparser.add_argument("metrics", nargs="+", help="Metrics to fetch", choices=global_metrics.keys())

    args = parser.parse_args()

    cluster = Cluster()
    functions[args.command]()
