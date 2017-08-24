# SGX-aware container scheduler

This repo hosts the technical documentation and code of the SGX-aware container scheduler project.

We first wanted to use [Docker Swarm](https://github.com/docker/swarmkit) for this project, but ultimately switched to [Kubernetes](https://github.com/kubernetes/kubernetes).
The old Docker Swarm-related content is in the `docker-swarm` folder.

A modified version of Docker that always mounts the SGX device is available in a [separate repository](https://github.com/sebyx31/docker.io-sgx). [.deb binaries](https://github.com/sebyx31/docker.io-sgx/releases) are available as well.
