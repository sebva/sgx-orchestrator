#!/bin/bash

ssh -L 127.2.0.1:5000:172.16.0.25:5000 -N svaucher@clusterinfo.unineuchatel.ch &
pid=$!

sleep 1

docker build -t k8smaster:5000/efficient-scheduler:1.0 .
docker push k8smaster:5000/efficient-scheduler:1.0

kill ${pid}
