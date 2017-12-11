#!/usr/bin/env python3
import argparse as argparse
import math
import sys
from collections import defaultdict
from functools import reduce
from typing import Tuple, Dict

jobs = []
jobs_by_start_time = []
initial_time_trace = None

epc_pages = None
overcommit_tolerance = 0.8

trace_column_start_time = 0
trace_column_end_time = 1
trace_column_requested_memory = 3
trace_column_maximum_memory = 4

job_column_job_id = 0
job_column_start_time = 1
job_column_end_time = 2
job_column_requested_memory = 3
job_column_actual_memory = 4
job_column_assigned_node = 5


def parse_trace(jobs_csv, skip: int):
    global jobs_by_start_time, initial_time_trace

    job_id = 0  # Always incremented

    for line in (x.rstrip() for x in jobs_csv):
        # Skip one in N jobs
        if skip > 1 and job_id % skip != 0:
            job_id += 1
            continue

        split = line.split(",")

        job = (
            round(int(split[trace_column_start_time]) / 1000000),
            round(int(split[trace_column_end_time]) / 1000000),
            math.ceil(float(split[trace_column_requested_memory]) * 23936),
            math.ceil(float(split[trace_column_maximum_memory]) * 23936),
        )

        if max(job[2], job[3]) > real_epc_pages:
            print("Job cannot fit in EPC, skipped", file=sys.stderr)
            job_id += 1
            continue

        if math.isclose(job[2], 0) or math.isclose(job[3], 0):
            job_id += 1
            continue

        if initial_time_trace is None:
            initial_time_trace = job[0]

        jobs.append(list((job_id, ) + job + ("",)))

        job_id += 1

    jobs_by_start_time = sorted(jobs, key=lambda x: x[job_column_start_time])


def replay_trace():
    current_time = initial_time_trace
    index_start = 0

    while index_start < len(jobs_by_start_time):
        created = []
        try:
            while jobs_by_start_time[index_start][1] <= current_time:
                created.append(jobs_by_start_time[index_start])
                index_start += 1
        except IndexError:
            pass

        yield created
        current_time += 1


def select_node(nodes: Dict[str, int], pod: Tuple[int, int, int, int, int]) -> str:
    for node_name, node_epc_usage in sorted(nodes.items(), key=lambda x: x[0]):
        pod_epc = pod[job_column_requested_memory]

        if node_epc_usage + pod_epc < real_epc_pages * overcommit_tolerance:
            return node_name


def main(trace: str, skip: int):
    with open(trace) as fp:
        parse_trace(fp, skip)

    nodes = {
        "sgx-1": 0,
        "sgx-2": 0,
    }

    jobs_finish_times = defaultdict(list)
    jobs_backlog = []
    created_jobs_gen = replay_trace()
    time = 0

    while True:
        try:
            jobs_backlog += next(created_jobs_gen)
        except StopIteration:
            if max(jobs_finish_times.keys()) < time and len(jobs_backlog) == 0:
                break

        for job in jobs_finish_times[time]:
            nodes[job[job_column_assigned_node]] -= job[job_column_actual_memory]

        i = 0
        n = len(jobs_backlog)
        while i < n:
            job = jobs_backlog[i]
            node = select_node(nodes, job)
            if node is not None:
                del jobs_backlog[i]
                n -= 1

                nodes[node] += job[job_column_actual_memory]
                job[job_column_assigned_node] = node
                finish_time = time + (job[job_column_end_time] - job[job_column_start_time])
                jobs_finish_times[finish_time].append(job)
            else:
                i += 1

        print(time / 60.0, reduce(lambda acc, elem: acc + elem[job_column_requested_memory], jobs_backlog, 0) * 4096, sep=",")
        time += 1


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("-e", "--epc", type=int, help="Size of the EPC in MiB", default=128)
    parser.add_argument("skip", type=int)
    parser.add_argument("trace")
    args = parser.parse_args()

    # Formula to compute the amount of usable pages
    real_epc_pages = ((args.epc * 1024 * 1024 * 3 / 4) - 2621440) / 4096
    print("%d MiB -> %d pages" % (args.epc, real_epc_pages), file=sys.stderr)

    main(args.trace, args.skip)
