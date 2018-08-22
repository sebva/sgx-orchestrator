SGX-aware container orchestrator
================================

This repository hosts the technical documentation and source code of our SGX-aware container orchestrator project.
Its architecture and implementation are described in our paper _"SGX-Aware Container Orchestration for Heterogeneous Clusters"_, to appear in the proceedings of the [38th IEEE International Conference on Distributed Computing Systems (ICDCS 2018)](http://icdcs2018.ocg.at/).
The paper also contains a broad evaluation of the scheduler itself, as well as micro-benchmarks relative to running SGX-enabled containers in a multi-tenant cloud.

Our SGX-aware orchestrator is based on [Kubernetes](https://kubernetes.io/).
It allows to efficiently schedule SGX-enabled containers in a heterogeneous cluster of SGX- and non-SGX-enabled machines.

This effort is part of the [SecureCloud project](https://www.securecloudproject.eu/).
SecureCloud has received funding from the European Union's Horizon 2020 research and innovation programme and was supported by the Swiss State Secretariat for Education, Research and Innovation (SERI) under grant agreement No 690111.

This program is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.
This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
See the GNU General Public License for more details.
You should have received a copy of the GNU General Public License along with this program.
If not, see <http://www.gnu.org/licenses/>.

Citing this work in your own research article
---------------------------------------------

If you use this work in your reasearch, please cite our paper [_"SGX-Aware Container Orchestration for Heterogeneous Clusters"_](https://arxiv.org/pdf/1805.05847.pdf).

```
@inproceedings{vaucher2018sgxaware,
    author={S. Vaucher and R. Pires and P. Felber and M. Pasin and V. Schiavoni and C. Fetzer},
    booktitle={2018 IEEE 38th International Conference on Distributed Computing Systems (ICDCS)},
    title={{SGX}-Aware Container Orchestration for Heterogeneous Clusters},
    month={July},
    year={2018},
    pages={730-741},
    doi={10.1109/ICDCS.2018.00076},
    issn={2575-8411},
}
```

Also, if you use _Stress-SGX_ as a workload, please also cite the corresponding paper [_"Stress-SGX: Load and Stress your Enclaves for Fun and Profit"_](https://seb.vaucher.org/papers/stress-sgx.pdf).

_BibTeX entry details will be included here after the proceedings of NETYS 2018 are published._

Sources organization, compilation and deployment
------------------------------------------------

This repository is organized as such:

```
sgx-scheduler
|_ demo                     Demonstration utility script (for public presentation)
|_ deviceplugin             Kubernetes-compatible device plugin
|_ docker-sgx               Root image for SGX-enabled Docker containers
|_ docs                     Miscellaneous documentation files
|_ heapster                 Heapster monitoring framework (known-working commit)
|_ kubernetes               Modified version of Kubernetes
|  |_ pkg
|     |_ kubelet
|        |_ kuberuntime     Communication of EPC limits
|_ metrics-probe            Metrics probe running on each node
|_ results-parser           Fetches and parses results right after an experiment ends
|_ runner                   Automated running of benchmarks/demonstrator
|_ scheduler                Actual scheduler
|_ sgx-app-mem              Sample SGX-enabled workload _(legacy)_
|_ sgx-driver               Modified SGX driver that enforces EPC usage limits
|_ standard-app-mem         Sample non-SGX workload based on stress-ng
|_ stress-sgx               SGX-enabled stressing application, to be used as workload
|_ README.md                The document that you are currently reading
```

In the following sections, we detail how to compile and deploy each component in order to end up with an SGX-compatible Kubernetes cluster.

### Requirements

We assume that the following components are ready to use:

1.  A Docker registry. In the following explanations, we will
    refer to its address as `$docker_registry`.
2.  A cluster of SGX- and non-SGX-enabled machines that meet the following criteria:
    1.  Connected together to the same network
    2.  With access to the Docker registry at `$docker_registry`
    3.  One machine is dedicated as Kubernetes master
    4.  SGX-compatible machines are used as SGX-enabled nodes
        * The Intel SGX Platform Software (PSW) must be disabled
    5.  The remaining machines are used as standard nodes

### Custom SGX driver

In order to leverage our SGX-aware monitoring framework, we need to
modify the SGX driver given by Intel. Additionally, our modifications
are used to enforce EPC consumption limits in a per-pod basis. The
modified driver has to be compiled and then installed on each
SGX-enabled node of the cluster.

The following commands will compile, install and insert our custom
module:

```bash
cd sgx-driver
make
sudo make install
sudo depmod
sudo modprobe isgx
```

### Custom version of Kubernetes

We ship a custom version of Kubernetes to enable the *deviceplugin* alpha feature by default, and implement EPC utilisation limits.
We refer to the official documentation given by Kubernetes' developers for [building instructions](https://github.com/kubernetes/kubernetes/blob/v1.8.5/build/README.md).
We use [*kubeadm*](https://v1-8.docs.kubernetes.io/docs/setup/independent/create-cluster-kubeadm/) to deploy our test cluster.
We similarly refer to its official documentation for deployment guidance.

Some documentation of ours is also available in the `docs/` directory.
In the following sections, we assume that the `kubectl` command is available and configured to operate on the newly-deployed Kubernetes cluster.

### Device plugin

The goal of the device plugin is to enable the execution of SGX
applications on Kubernetes nodes. It fetches the number of trusted EPC
pages available on each node, and communicates it to Kubelet.

As this component is written in Python, no compilation is needed. It has
to be deployed on each SGX-enabled node in the Kubernetes cluster. It
suffices to run `sgx_deviceplugin.py` as a daemon (as root) to fully take
advantage of it.
No external dependencies are needed.

_Note:_ We plan to package this component as a Kubernetes _DaemonSet_ in a future revision.

### Heapster

[Heapster](https://github.com/kubernetes/heapster) is the standard monitoring layer of Kubernetes. We
use it to collect regular metrics about the state of the cluster, which
are then sent into InfluxDB.

The steps to deploy Heapster to the cluster are as follows:

2.  Modify the manifest of *Grafana* to use `NodePort`. In
    `grafana.yaml` inside directory
    `heapster/deploy/kube-config/influxdb`, the following line has to be
    uncommented:
    ```yaml
    spec:
      # ...
      type: NodePort  # <>-- This line
      ports:
      - port: 80
      # ...
    ```
3.  Start Heapster and deploy its RBAC rules
    ```bash
    ./heapster/deploy/kube.sh start
    kubectl create -f heapster/deploy/kube-config/rbac/heapster-rbac.yaml
    ```

### Metrics probe

The metrics probe component is built as a Docker image. The following
commands will build the image and push it to the Docker registry
specified as `$docker_registry`.

```bash
cd metrics-probe
docker build -t ${docker_registry}/metrics-probe:1.5 .
docker push ${docker_registry}/metrics-probe:1.5
```

Our metric probe has to be deployed on all SGX nodes in the cluster.
We leverage Kubernetes to automatically deploy this component.

```bash
cd metrics-probe
kubectl apply -f metrics-probe.yaml
```

### SGX-aware scheduler

Similarly to the metrics probe, the scheduler is deployed as a
Kubernetes pod. To build it as a Docker image, the following commands
need to be executed:

```bash
cd scheduler
docker build -t ${docker_registry}/efficient-scheduler:2.9 .
docker push ${docker_registry}/efficient-scheduler:2.9
```

Both strategies of the scheduler can be deployed at the same time using
the following commands:

```bash
cd scheduler
kubectl apply -f spread-scheduler.yaml
kubectl apply -f binpack-scheduler.yaml
```

Executing SGX-enabled jobs on the cluster
-----------------------------------------

After all the steps mentioned above are completed, it becomes possible to
deploy jobs towards the Kubernetes cluster.
Standard Kubernetes APIs are used to interact with it.

To activate the scheduler for a specific pod as a user, the
`schedulerName` key needs to be set in its pod specification. Therefore,
the following YAML description is sufficient to deploy an SGX-enabled
job in the cluster, scheduled using our SGX-aware scheduler.

```yaml
spec:
  template:
    metadata:
      name: my-workload
    spec:
      schedulerName: spread  # or binpack
      containers:
      - name: my-container
        image: my-image
        resources:
          requests:
            intel.com/sgx: 5000
          limits:
            intel.com/sgx: 5000
```

It can be deployed using Kubernetes' standard tool *kubectl*:

```bash
kubectl apply -f workload.yml
```

### Sample workloads

As part of this demonstrator, we provide sample jobs that can be
executed in the cluster. Their behaviour consists in allocating a
particular amount of memory---standard or EPC, depending on the nature of the job---and
repeatedly iterating on it to keep it marked as active. As they are
based on Docker images, they can be built and deployed in the standard
Docker-specific way:

```bash
docker build -t ${docker_registry}/sgx-app-mem:1.2 ./sgx-app-mem
docker build -t ${docker_registry}/standard-app-mem:1.2 ./standard-app-mem
docker push ${docker_registry}/sgx-app-mem:1.2
docker push ${docker_registry}/standard-app-mem:1.2
```

### Stress-SGX

We consider the sample workloads described above as "legacy".
Instead, we recommend the use of [Stress-SGX](https://github.com/sebva/stress-sgx) as a stress workload.
Further instructions are given in its [own repository](https://github.com/sebva/stress-sgx/blob/master/README.md).

Stress-SGX is described in more detail in the associated paper _"Stress-SGX: Load and Stress your Enclaves for Fun and Profit"_, to appear in the proceedings of the [6th Edition of The International Conference on NETworked sYStems (NETYS 2018)](http://netys.net/).

### Running multiple workloads in batch

For evaluation and demonstration purposes, we developed a collection of
scripts that are able to deploy multiple jobs, with respect to a trace.
Our demonstrator uses the [Google Borg Trace](https://research.googleblog.com/2011/11/more-google-cluster-data.html).
The trace was recorded in 2011 on a Google cluster of about machines.
The nature of the jobs in the trace is undisclosed. We are not aware of any publicly
available trace that would contain SGX-enabled jobs. Therefore, we
arbitrarily designate a subset of trace jobs as SGX-enabled. Our scripts
are able to insert various percentages of SGX jobs in the system.

The trace reports several metrics measured for the Google jobs. We
extract the following metrics out of it: *submission time*, *duration*,
*assigned memory* and *maximal memory usage*. The submission time is
crucial to model the same arrival pattern of the jobs in our cluster.
The run time of each job matches exactly the one reported in the trace.
We use the assigned memory as the value advertised to Kubernetes when
submitting the job to the system. However, the job will allocate the
amount given in the maximal memory usage field. We believe this creates
real-world-like behaviour *w.r.t.* the memory consumption advertised on
creation compared to the memory that is actually used.

The trace specifies the memory usage of each job as a percentage of the
total memory available on Google's servers (without actually reporting
the absolute values). In our experiments, we set the memory usage of
SGX-enabled jobs by multiplying the memory usage factor obtained from
the trace to the total usable size of the EPC (93.5 MiB in our case). As
for standard jobs, we compute their memory usage by multiplying them to
32 GiB. We think that it yields amounts that match real-world values.
These numbers are defined in [`runner/runner.py`](runner/runner.py) as `epc_size_pages` and `memory_size_bytes`.

Given the size of Google's cluster, we have to scale down the trace
before being able to replay it on our own cluster setup. Our scripts can
skip every nth job in the trace to bring it down to a
reasonable number of jobs.

In the `runner` directory, there are 2 scripts that can be used to
launch a batch of processes: [`runner.py`](runner/runner.py) and [`superrunner.py`](runner/superrunner.py).
`runner.py` is the base script; it launches multiple jobs fetched from
the trace. `superrunner.py` uses `runner.py` to launch multiple
experiments back-to-back, and makes use of our [`results-parser`](results-parser/logs_parser.py) to
produce ready-to-use data for production of plots.

We provide the subset of the Google Borg trace (from 6480s to 10080s) that we used to perform the experiments presented in our paper.
You can find the data in the `runner/trace/task_1h.csv.xz` compressed file.
The file must be uncompressed before it can be given to the experiments runner.

The scripts can be run on any machine that is configured with the
cluster's API endpoint in its *kubectl* configuration. Therefore, there is no building
needed. The dependencies needed for the scripts can be installed using a
Python [virtual environment](https://docs.python.org/3/tutorial/venv.html) as follows:

```bash
cd runner
virtualenv -p /usr/bin/python3.6 --distribute .venv
. ./.venv/bin/activate
pip install -r requirements.txt
```

`runner.py` accepts the following options:

```
usage: runner.py [-h] [-s [SCHEDULER]] [-k [SKIP]] [-x [SGX]] [-o [OUTPUT]] trace

Experiments runner

positional arguments:
trace                 Trace file to use

optional arguments:
-h, --help            show this help message and exit
-s [SCHEDULER], --scheduler [SCHEDULER]
                      Name of the custom scheduler to use
-k [SKIP], --skip [SKIP]
                      Skip every nth job
-x [SGX], --sgx [SGX]
                      Proportion of SGX jobs between 0 (no SGX) and 1 (all SGX)
-o [OUTPUT], --output [OUTPUT]
                      Also output prints to file
```

`superrunner.py` accepts the following options:

```
usage: superrunner.py [-h] -s SCHEDULER [SCHEDULER ...] -x SGX [SGX ...]
                      -a ATTACKER [ATTACKER ...] [-k [SKIP]] trace

Super Runner

positional arguments:
trace                 Trace file

optional arguments:
-h, --help            show this help message and exit
-s SCHEDULER [SCHEDULER ...], --scheduler SCHEDULER [SCHEDULER ...]
                      Scheduler(s) to use
-x SGX [SGX ...], --sgx SGX [SGX ...]
                      Fraction(s) of SGX jobs
-a ATTACKER [ATTACKER ...], --attacker ATTACKER [ATTACKER ...]
                      Fraction(s) of memory allocated by attacker
-k [SKIP], --skip [SKIP]
                      Skip every nth job
```

After an execution of `superrunner.py`, results are echoed in the console.
They can be saved by redirecting its output into a file.
Here is an excerpt from an output file.
Each line represents the metrics gathered from a given job that run in the cluster.

```csv
job_id,duration,requested_pages,actual_pages,is_sgx,runner_start_time,k8s_created_time,k8s_actual_start_time,k8s_actual_end_time
0,120,1849,1589,True,2017-12-11 15:38:06.553203,2017-12-11 15:38:06+00:00,2017-12-11 15:38:08+00:00,2017-12-11 15:40:08+00:00
2000,300,692,521,True,2017-12-11 15:40:06.653301,2017-12-11 15:40:06+00:00,2017-12-11 15:40:18+00:00,2017-12-11 15:45:19+00:00
4000,300,414,306,True,2017-12-11 15:40:06.668214,2017-12-11 15:40:06+00:00,2017-12-11 15:40:15+00:00,2017-12-11 15:45:16+00:00
10000,300,139,9,True,2017-12-11 15:40:06.694733,2017-12-11 15:40:06+00:00,2017-12-11 15:40:09+00:00,2017-12-11 15:45:09+00:00
12000,300,777,782,True,2017-12-11 15:40:06.705448,2017-12-11 15:40:06+00:00,2017-12-11 15:40:11+00:00,2017-12-11 15:45:12+00:00
14000,300,791,645,True,2017-12-11 15:40:06.715891,2017-12-11 15:40:06+00:00,2017-12-11 15:40:14+00:00,2017-12-11 15:45:14+00:00
```

