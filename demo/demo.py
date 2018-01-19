#!/usr/bin/env python3
import argparse


def deploy_pod():
    print("deploy")


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

    deploy_subparser = subparsers.add_parser("deploy")
    deploy_subparser.add_argument("name", help="Pod identifier")
    deploy_subparser.add_argument("--node", "-n", help="Node on which to deploy the pod (bypass the scheduler)")

    node_status_subparser = subparsers.add_parser("node-status")
    node_status_subparser.add_argument("node")
    node_status_subparser.add_argument("metrics", nargs="+", help="Metrics to fetch", choices=node_metrics.keys())

    global_status_subparser = subparsers.add_parser("global-status")
    global_status_subparser.add_argument("metrics", nargs="+", help="Metrics to fetch", choices=node_metrics.keys())

    args = parser.parse_args()

    functions[args.command]()
