# SGX Scheduler for Kubernetes

## How to deploy

On your local machine, build the Docker container. You can use the [build-and-push.sh](build-and-push.sh) script.

On your Kubernetes master, deploy the scheduler in the cluster:
```bash
kubectl apply -f scheduler.yaml
```

You can check that the scheduler is running by checking its logs:
```bash
kubectl logs -f deployment/scheduler
```

## Usage

Once the scheduler is running, we advise you to ask Kubernetes to schedule all pods using this scheduler to prevent SGX nodes from being overloaded by non-SGX jobs.
An example on how to achieve this is to use the following Job specification for each Job deployed in the cluster:
```yaml
apiVersion: batch/v1
kind: Job
metadata:
  name: helloscone
spec:
  template:
    metadata:
      name: helloscone
    spec:
      schedulerName: efficient
      containers:
      - name: helloscone
        image: 172.16.0.25:5000/helloscone:1.0
      restartPolicy: OnFailure
```
The important part is the `schedulerName` key in the PodSpec.
