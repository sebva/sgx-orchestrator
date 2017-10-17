#!/usr/bin/python3 -u
import argparse
import os
import sys
import time
import traceback
from typing import List

sys.path.insert(1, os.path.join(sys.path[0], '../results-parser'))
import logs_parser
from kubernetes.client import V1Pod
from kubernetes.client.models.v1_delete_options import V1DeleteOptions

import runner


def running_experiment_pods() -> List[V1Pod]:
    return [x for x in runner.api.list_namespaced_pod("default").items if x.metadata.name.startswith("experiment-")]


def clean_experiment_pods():
    pod_names = (x.metadata.name for x in running_experiment_pods())
    for pod_name in pod_names:
        print("Deleting " + pod_name)
        runner.api.delete_namespaced_pod(pod_name, "default", V1DeleteOptions())


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Super Runner")
    parser.add_argument("-s", "--scheduler", help="Scheduler(s) to use", nargs="+", required=True)
    parser.add_argument("-x", "--sgx", help="Fraction(s) of SGX jobs", type=float, nargs="+", required=True)
    parser.add_argument("-k", "--skip", default=-1, type=int, nargs="?", help="Skip every nth job")
    parser.add_argument("trace", help="Trace file")
    args = parser.parse_args()

    filename_time = time.strftime("%Y-%m-%d-%H%M")

    print("--- SUPER RUNNER ---")
    for scheduler in args.scheduler:
        for sgx_fraction in args.sgx:
            try:
                runner.scheduler_name = scheduler
                runner.proportion_sgx = sgx_fraction
                print("Checking that no experiment pods are present")
                if len(running_experiment_pods()) > 0:
                    print("Cleaning up before new job")
                    clean_experiment_pods()

                print("SR job starts. scheduler: '%s', sgx: %f, trace: '%s', skip: %d" % (
                    scheduler, sgx_fraction, args.trace, args.skip
                ))
                intermediate_file = "rawrunner_%s_%s_%f.txt" % (filename_time, scheduler, sgx_fraction)

                runner.main(args.trace, args.skip, intermediate_file)
                print("Runner finished, waiting for all pods to finish...")

                while True:
                    nb_pods = len([x for x in running_experiment_pods() if x.status.phase in ("Pending", "Running")])
                    print("Still %d pods to wait" % nb_pods)
                    if nb_pods > 0:
                        time.sleep(10)
                    else:
                        break

                print("Finished, now parsing logs")
                output_file = "runner_%s_%s_%f.txt" % (filename_time, scheduler, sgx_fraction)
                print("Output is: " + output_file)
                logs_parser.main(intermediate_file, output_file)
                print("Parsing finished, cleaning up...")
                clean_experiment_pods()
                print("SR job ends")
            except:  # Gotta Catch 'Em All!
                traceback.print_exc()
                print("SR JOB HAS CRASHED! Continuing...")

    print("--- SUPER RUNNER END ---")
