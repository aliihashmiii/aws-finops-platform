"""Optional read-only Kubernetes discovery adapter."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict


class KubernetesCollector:
    def collect(self) -> Dict[str, Any]:
        try:
            from kubernetes import client, config
        except ImportError:
            return {"status": "partial", "error": "KubernetesClientUnavailable", "message": "Install kubernetes and configure kubeconfig or in-cluster credentials for live Kubernetes analysis."}
        try:
            try:
                config.load_incluster_config()
            except config.ConfigException:
                config.load_kube_config()
            core = client.CoreV1Api()
            nodes = core.list_node().items
            namespaces = core.list_namespace().items
            data = {"cluster": {"cluster_id": "live-cluster", "name": "Kubernetes cluster", "provider": "Kubernetes", "region": "unknown"}, "nodes": [], "workloads": [], "history": []}
            for node in nodes:
                capacity = node.status.capacity or {}
                data["nodes"].append({"node_id": node.metadata.uid or node.metadata.name, "name": node.metadata.name, "instance_type": node.metadata.labels.get("node.kubernetes.io/instance-type", "unknown"), "cpu_capacity": float(str(capacity.get("cpu", "0")).rstrip("m")) / (1000 if str(capacity.get("cpu", "0")).endswith("m") else 1), "memory_capacity": 0.0, "cpu_requested": 0.0, "memory_requested": 0.0, "cpu_usage": 0.0, "memory_usage": 0.0, "monthly_cost": 0.0})
            for namespace in namespaces:
                data["workloads"].append({"workload_id": namespace.metadata.uid or namespace.metadata.name, "name": namespace.metadata.name, "namespace": namespace.metadata.name, "type": "Namespace", "replicas": 0, "cpu_request": 0.0, "cpu_usage": 0.0, "memory_request": 0.0, "memory_usage": 0.0, "monthly_cost": 0.0, "has_requests": False, "has_limits": False})
            return {"status": "partial", "error": "UsageTelemetryUnavailable", "message": "Kubernetes API discovery succeeded, but Prometheus and kube-state-metrics are required for cost allocation and utilization analysis.", "data": data}
        except Exception as exc:
            return {"status": "partial", "error": type(exc).__name__, "message": str(exc)}
