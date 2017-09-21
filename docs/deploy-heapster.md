# Heapster deployment

## Prerequisites

* [A working Kubernetes cluster](setup-kubernetes-cluster.md)

## Deployment

1. Clone _heapster_ sources:
```
git clone https://github.com/kubernetes/heapster.git
git checkout 5f8a3ac2c0e3c23afa99ed0c1d7803b6b39c9ae2  # Specific commit that was at the tip of master at the time of writing
```
2. Modify the manifest of _Grafana_ to use `NodePort`
    1. In `heapster/deploy/kube-config/influxdb/grafana.yaml`, uncomment this line:
```yaml
spec:
  # ...
  type: NodePort  # <-- This line
  ports:
  - port: 80
# ...
```
3. Start _heapster_, including RBAC rules
```
./heapster/deploy/kube.sh start
kubectl create -f heapster/deploy/kube-config/rbac/heapster-rbac.yaml
```

## Accessing the system

### Access to Grafana using a browser outside the cluster

1. Find the name of the _Grafana_ pod
```
kubectl get pods -n kube-system | grep grafana
```
2. Setup a port forward to it
```
kubectl port-forward monitoring-grafana-<some-numbers> 3001:3000 -n kube-system
```
3. Access _Grafana_ at http://localhost:3001/

### Access to InfluxDB within the cluster

Use the domain name `monitoring-influxdb.kube-system.svc.cluster.local` and port 8086

## Destroying

```
kubectl delete -f heapster/deploy/kube-config/rbac/heapster-rbac.yaml
./heapster/deploy/kube.sh stop
```
