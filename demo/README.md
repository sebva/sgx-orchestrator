# Demonstration utility script

The goal of `demo.py` is to be able to demonstrate our SGX-aware scheduler in front of a live audience.
It allows to deploy arbitrary jobs, and fetch certain metrics without needing to use `kubectl`.

## Pre-requisites

- Python >= 3.6
    - pip
    - virtualenv
- Kubernetes access token in `~/.kube/config`

## Usage using local Python 3 install

### Installing dependencies

Arch Linux-based systems

```bash
sudo pacman -Sy python-pip python-virtualenv
```

Debian-based systems

```bash
sudo apt update
sudo apt install python3-pip python3-virtualenv virtualenv 
```

Create virtualenv, enter it, install Python dependencies

```bash
virtualenv -p /ust/bin/python3 --distribute .venv
. ./.venv/bin/activate
pip install -r requirements.txt
```

### Use script

```bash
./demo.py --help
./demo.py deploy --help
./demo.py node-status --help
./demo.py global-status --help
```

## Usage using Docker

```bash
docker build -t demo .
docker run --volume ~/.kube/config:/root/.kube/config:ro --rm -ti demo
```

## Output format

When querying metrics, the following format is used:

```
node1 metric: metric1=value1 metric2=value2
node2 metric: metric1=value1 metric2=value2
```

When the metric applies to the whole cluster, no node is printed.
