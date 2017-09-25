import docker
import kubernetes
from influxdb import InfluxDBClient

influx_client = InfluxDBClient("monitoring-influxdb.kube-system.svc.cluster.local", database="k8s")
docker_client = docker.from_env(version="1.24")
kubernetes.config.load_incluster_config()
kubernetes_client = kubernetes.client.CoreV1Api()


def fetch_metrics():
    # TODO Fill the lambdas
    tags = [
        ("type", lambda: 0),
        ("pod_id", lambda: 0),
        ("pod_name", lambda: 0),
        ("pod_namespace", lambda: 0),
        ("namespace_name", lambda: 0),
        ("namespace_id", lambda: 0),
        ("container_name", lambda: 0),
        ("labels", lambda: 0),
        ("nodename", lambda: 0),
        ("hostname", lambda: 0),
        ("resource_id", lambda: 0),
        ("host_id", lambda: 0),
        ("container_base_image", lambda: 0),
    ]


def push_to_influx(metric_name: str, value, labels: dict) -> bool:
    points = [
        {
            "measurement": metric_name,
            "fields": {
                "value": value
            },
            "tags": labels,
        }
    ]
    return influx_client.write_points(points)


def main():
    # TODO Loop: fetch, push
    pass


if __name__ == '__main__':
    main()


# InfluxDB labels from Heapster source code:
# LabelMetricSetType = LabelDescriptor{
# 		Key:         "type",
# 		Description: "Type of the metrics set (container, pod, namespace, node, cluster)",
# 	}
# 	MetricSetTypeSystemContainer = "sys_container"
# 	MetricSetTypePodContainer    = "pod_container"
# 	MetricSetTypePod             = "pod"
# 	MetricSetTypeNamespace       = "ns"
# 	MetricSetTypeNode            = "node"
# 	MetricSetTypeCluster         = "cluster"
#
# 	LabelPodId = LabelDescriptor{
# 		Key:         "pod_id",
# 		Description: "The unique ID of the pod",
# 	}
# 	LabelPodName = LabelDescriptor{
# 		Key:         "pod_name",
# 		Description: "The name of the pod",
# 	}
# 	// Deprecated label
# 	LabelPodNamespace = LabelDescriptor{
# 		Key:         "pod_namespace",
# 		Description: "The namespace of the pod",
# 	}
# 	LabelNamespaceName = LabelDescriptor{
# 		Key:         "namespace_name",
# 		Description: "The name of the namespace",
# 	}
# 	LabelPodNamespaceUID = LabelDescriptor{
# 		Key:         "namespace_id",
# 		Description: "The UID of namespace of the pod",
# 	}
# 	LabelContainerName = LabelDescriptor{
# 		Key:         "container_name",
# 		Description: "User-provided name of the container or full container name for system containers",
# 	}
# 	LabelLabels = LabelDescriptor{
# 		Key:         "labels",
# 		Description: "Comma-separated list of user-provided labels",
# 	}
# 	LabelNodename = LabelDescriptor{
# 		Key:         "nodename",
# 		Description: "nodename where the container ran",
# 	}
# 	LabelHostname = LabelDescriptor{
# 		Key:         "hostname",
# 		Description: "Hostname where the container ran",
# 	}
# 	LabelResourceID = LabelDescriptor{
# 		Key:         "resource_id",
# 		Description: "Identifier(s) specific to a metric",
# 	}
# 	LabelHostID = LabelDescriptor{
# 		Key:         "host_id",
# 		Description: "Identifier specific to a host. Set by cloud provider or user",
# 	}
# 	LabelContainerBaseImage = LabelDescriptor{
# 		Key:         "container_base_image",
# 		Description: "User-defined image name that is run inside the container",
# 	}
