#!/usr/bin/env python3
import argparse

import re

from cluster import Cluster

cluster = None
args = None

units = {
    "k": 1e3,
    "M": 1e6,
    "G": 1e9,
}


def deploy_pod():
    print("deploy")

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

    cluster.launch_pod(args.name, args.scheduler, args.duration, limit, memory, args.sgx)


def node_status():
    print("node")


def global_status():
    print("global")


functions = {
    "deploy": deploy_pod,
    "node-status": node_status,
    "global-status": global_status,
}

node_metrics = {
    "pods": None,
}

global_metrics = {
    "pending": None,
    "total": None,
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
                                  choices=["spread", "binpack", ""])
    deploy_subparser.add_argument("--duration", "-d", help="Jobs runs for this much seconds", default=300)

    node_status_subparser = subparsers.add_parser("node-status")
    node_status_subparser.add_argument("node")
    node_status_subparser.add_argument("metrics", nargs="+", help="Metrics to fetch", choices=node_metrics.keys())

    global_status_subparser = subparsers.add_parser("global-status")
    global_status_subparser.add_argument("metrics", nargs="+", help="Metrics to fetch", choices=node_metrics.keys())

    args = parser.parse_args()

    cluster = Cluster()
    functions[args.command]()
