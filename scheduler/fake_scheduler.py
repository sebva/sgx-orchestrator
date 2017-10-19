#!/usr/bin/env python3
import argparse as argparse
import math
import policy_binpack

import itertools

jobs = []
jobs_by_start_time = []
jobs_by_end_time = []
initial_time_trace = None

epc_pages = 23936

column_start_time = 0
column_end_time = 1
column_requested_memory = 3
column_maximum_memory = 4


def parse_trace(jobs_csv, skip: int):
    global jobs_by_start_time, jobs_by_end_time, initial_time_trace

    job_id = 0  # Always incremented

    for line in (x.rstrip() for x in jobs_csv):
        # Skip one in N jobs
        if skip > 1 and job_id % skip != 0:
            job_id += 1
            continue

        split = line.split(",")

        job = (
            float(split[column_start_time]) / 1000000,
            float(split[column_end_time]) / 1000000,
            float(split[column_requested_memory]) * epc_pages,
            float(split[column_maximum_memory]) * epc_pages
        )

        if math.isclose(job[2], 0) or math.isclose(job[3], 0):
            print("Skipping job '%d' requiring 0 memory" % job_id)
            job_id += 1
            continue

        if initial_time_trace is None:
            initial_time_trace = job[0]

        jobs.append((job_id,) + job)

        job_id += 1

    jobs_by_start_time = sorted(jobs, key=lambda x: x[1])
    jobs_by_end_time = sorted(jobs, key=lambda x: x[2])


def replay_trace():
    current_time = initial_time_trace
    index_start = 0
    index_end = 0

    while index_start < len(jobs_by_start_time) or index_end < len(jobs_by_end_time):
        created = []
        ended = []
        try:
            while jobs_by_start_time[index_start][1] <= current_time:
                created.append(jobs_by_start_time[index_start])
                index_start += 1
        except IndexError:
            pass

        try:
            while jobs_by_end_time[index_end][2] <= current_time:
                ended.append(jobs_by_end_time[index_end])
                index_end += 1
        except IndexError:
            pass

        yield created, ended
        current_time += 1


def main(trace: str, skip: int):
    with open(trace) as fp:
        parse_trace(fp, skip)

    policy = policy_binpack.PolicyBinpack()
    for time, (created, ended) in zip(itertools.count(), replay_trace()):
        print(time, created, ended)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("skip", type=int)
    parser.add_argument("trace")
    args = parser.parse_args()

    main(args.trace, args.skip)

