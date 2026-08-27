"""Deterministic demo data used by the same engine as live collectors."""

from __future__ import annotations

from datetime import date
from typing import Any, Dict, List


def _months() -> List[Dict[str, float]]:
    # A stable 12-month history makes screenshots and tests reproducible.
    values = [53520, 54810, 56240, 57180, 58460, 59210, 60140, 61420, 62580, 63110, 62890, 63584]
    months = ["2025-09", "2025-10", "2025-11", "2025-12", "2026-01", "2026-02", "2026-03", "2026-04", "2026-05", "2026-06", "2026-07", "2026-08"]
    return [{"period": period, "cost": float(cost)} for period, cost in zip(months, values)]


def load_demo_data() -> Dict[str, Any]:
    aws_resources = {
        "ec2_instances": [
            {"id": "i-demo001", "type": "t3.medium", "state": "running", "region": "us-east-1", "cpu_avg": 2.3, "monthly_cost": 30.37, "tags": {"Environment": "development", "Team": "Engineering", "CostCenter": "ENG-100"}},
            {"id": "i-demo002", "type": "m5.large", "state": "running", "region": "us-east-1", "cpu_avg": 1.1, "monthly_cost": 70.08, "tags": {"Environment": "staging", "Team": "Data", "CostCenter": "DATA-200"}},
            {"id": "i-demo003", "type": "t3.large", "state": "running", "region": "us-west-2", "cpu_avg": 3.5, "monthly_cost": 60.74, "tags": {"Environment": "development", "Team": "Engineering", "CostCenter": "ENG-100"}},
            {"id": "i-demo004", "type": "t3.xlarge", "state": "stopped", "region": "us-east-1", "cpu_avg": 0.0, "monthly_cost": 121.47, "tags": {"Environment": "development", "Team": "Engineering"}},
            {"id": "i-prod001", "type": "m5.2xlarge", "state": "running", "region": "us-east-1", "cpu_avg": 65.3, "monthly_cost": 280.32, "tags": {"Environment": "production", "Team": "Backend", "CostCenter": "BE-300"}},
            {"id": "i-prod002", "type": "c5.xlarge", "state": "running", "region": "us-west-2", "cpu_avg": 78.2, "monthly_cost": 124.10, "tags": {"Environment": "production", "Team": "Backend", "CostCenter": "BE-300"}},
        ],
        "ebs_volumes": [
            {"id": "vol-demo001", "size_gb": 100, "type": "gp2", "state": "available", "attached": False, "region": "us-east-1", "monthly_cost": 10.0, "tags": {}},
            {"id": "vol-demo002", "size_gb": 50, "type": "gp2", "state": "available", "attached": False, "region": "us-east-1", "monthly_cost": 5.0, "tags": {}},
            {"id": "vol-demo003", "size_gb": 200, "type": "gp3", "state": "in-use", "attached": True, "region": "us-west-2", "monthly_cost": 16.0, "tags": {"Environment": "production", "Team": "Backend", "CostCenter": "BE-300"}},
            {"id": "vol-demo004", "size_gb": 500, "type": "gp2", "state": "in-use", "attached": True, "region": "us-east-1", "monthly_cost": 50.0, "tags": {"Environment": "production", "Team": "Backend", "CostCenter": "BE-300"}},
        ],
        "snapshots": [
            {"id": "snap-demo001", "size_gb": 80, "age_days": 120, "region": "us-east-1", "monthly_cost": 4.0, "tags": {}},
            {"id": "snap-demo002", "size_gb": 100, "age_days": 150, "region": "us-east-1", "monthly_cost": 5.0, "tags": {}},
            {"id": "snap-demo003", "size_gb": 50, "age_days": 200, "region": "us-west-2", "monthly_cost": 2.5, "tags": {}},
            {"id": "snap-demo004", "size_gb": 30, "age_days": 45, "region": "us-west-2", "monthly_cost": 1.5, "tags": {"Backup": "weekly"}},
        ],
        "elastic_ips": [
            {"id": "eip-demo001", "ip": "54.123.45.67", "attached": False, "region": "us-east-1", "monthly_cost": 3.65, "tags": {}},
            {"id": "eip-demo002", "ip": "52.98.76.54", "attached": True, "region": "us-west-2", "monthly_cost": 0.0, "tags": {"Environment": "production", "Team": "Backend", "CostCenter": "BE-300"}},
        ],
        "rds_instances": [
            {"id": "db-demo001", "type": "db.t3.medium", "engine": "postgres", "cpu_avg": 2.1, "state": "available", "region": "us-east-1", "monthly_cost": 56.72, "tags": {"Environment": "development", "Team": "Engineering", "CostCenter": "ENG-100"}},
            {"id": "db-prod001", "type": "db.r5.large", "engine": "mysql", "cpu_avg": 45.3, "state": "available", "region": "us-east-1", "monthly_cost": 183.96, "tags": {"Environment": "production", "Team": "Backend", "CostCenter": "BE-300"}},
        ],
        "costs_by_service": {"EC2": 18450.0, "RDS": 12300.0, "S3": 5670.0, "Data Transfer": 4890.0, "EBS": 2100.0, "Other": 1824.5},
        "costs_by_region": {"us-east-1": 38420.0, "us-west-2": 14814.5, "eu-west-1": 0.0},
        "costs_by_team": {"Engineering": 22100.0, "Data": 15670.0, "Backend": 7464.5},
        "costs_by_environment": {"production": 31650.0, "staging": 9050.0, "development": 4534.5},
        "total_monthly_cost": 45234.5,
        "history": [{"period": item["period"], "cost": round(item["cost"] * 0.71, 2), "platform": "AWS"} for item in _months()],
    }

    k8s_nodes = [
        {"node_id": "node-001", "name": "ip-10-0-3-42", "instance_type": "m5.2xlarge", "cpu_capacity": 8.0, "memory_capacity": 32.0, "cpu_requested": 4.0, "memory_requested": 20.0, "cpu_usage": 0.96, "memory_usage": 6.08, "monthly_cost": 410.0},
        {"node_id": "node-002", "name": "ip-10-0-4-17", "instance_type": "m5.2xlarge", "cpu_capacity": 8.0, "memory_capacity": 32.0, "cpu_requested": 6.0, "memory_requested": 24.0, "cpu_usage": 5.44, "memory_usage": 20.48, "monthly_cost": 410.0},
        {"node_id": "node-003", "name": "ip-10-0-5-09", "instance_type": "r6i.2xlarge", "cpu_capacity": 8.0, "memory_capacity": 64.0, "cpu_requested": 5.0, "memory_requested": 48.0, "cpu_usage": 3.84, "memory_usage": 38.4, "monthly_cost": 520.0},
        {"node_id": "node-004", "name": "ip-10-0-6-11", "instance_type": "m5.xlarge", "cpu_capacity": 4.0, "memory_capacity": 16.0, "cpu_requested": 1.0, "memory_requested": 4.0, "cpu_usage": 0.48, "memory_usage": 3.04, "monthly_cost": 260.0},
    ]
    for node in k8s_nodes:
        node["utilization"] = round(((node["cpu_usage"] / node["cpu_capacity"]) + (node["memory_usage"] / node["memory_capacity"])) / 2, 4)

    k8s_workloads = [
        {"workload_id": "wl-checkout", "name": "checkout-api", "namespace": "production", "type": "Deployment", "replicas": 4, "cpu_request": 4.0, "cpu_usage": 0.8, "memory_request": 8.0, "memory_usage": 2.1, "monthly_cost": 2310.0, "has_requests": True, "has_limits": True},
        {"workload_id": "wl-payments", "name": "payments", "namespace": "production", "type": "Deployment", "replicas": 3, "cpu_request": 2.0, "cpu_usage": 1.4, "memory_request": 4.0, "memory_usage": 3.1, "monthly_cost": 1840.0, "has_requests": True, "has_limits": True},
        {"workload_id": "wl-search", "name": "search-indexer", "namespace": "staging", "type": "StatefulSet", "replicas": 2, "cpu_request": 3.0, "cpu_usage": 0.7, "memory_request": 8.0, "memory_usage": 2.4, "monthly_cost": 1290.0, "has_requests": True, "has_limits": False},
        {"workload_id": "wl-worker", "name": "async-worker", "namespace": "staging", "type": "Deployment", "replicas": 5, "cpu_request": 2.5, "cpu_usage": 1.4, "memory_request": 5.0, "memory_usage": 2.5, "monthly_cost": 850.0, "has_requests": True, "has_limits": True},
        {"workload_id": "wl-portal", "name": "internal-portal", "namespace": "development", "type": "Deployment", "replicas": 3, "cpu_request": 1.5, "cpu_usage": 0.3, "memory_request": 3.0, "memory_usage": 1.0, "monthly_cost": 620.0, "has_requests": True, "has_limits": True},
        {"workload_id": "wl-cron", "name": "report-cron", "namespace": "development", "type": "CronJob", "replicas": 1, "cpu_request": 0.8, "cpu_usage": 0.12, "memory_request": 1.5, "memory_usage": 0.4, "monthly_cost": 410.0, "has_requests": False, "has_limits": False},
    ]

    ai_usage = [
        {"provider": "OpenAI", "model": "gpt-4o", "timestamp": "2026-08-01", "application": "Customer Support", "team": "Support", "environment": "production", "input_tokens": 42000000, "output_tokens": 8000000, "request_count": 125000, "latency_ms": 740.0, "cost": 1840.0, "cache_hit_rate": 0.12},
        {"provider": "Anthropic", "model": "claude-3-5-sonnet", "timestamp": "2026-08-01", "application": "Search", "team": "Engineering", "environment": "production", "input_tokens": 31000000, "output_tokens": 6000000, "request_count": 80000, "latency_ms": 610.0, "cost": 920.0, "cache_hit_rate": 0.08},
        {"provider": "OpenAI", "model": "gpt-4o-mini", "timestamp": "2026-08-01", "application": "Internal Tools", "team": "Engineering", "environment": "development", "input_tokens": 12000000, "output_tokens": 2500000, "request_count": 170000, "latency_ms": 290.0, "cost": 410.0, "cache_hit_rate": 0.22},
        {"provider": "Google", "model": "gemini-1.5-pro", "timestamp": "2026-08-01", "application": "Document Processing", "team": "Operations", "environment": "production", "input_tokens": 10000000, "output_tokens": 1500000, "request_count": 54000, "latency_ms": 820.0, "cost": 1510.0, "cache_hit_rate": 0.05},
        {"provider": "AWS Bedrock", "model": "amazon.nova-lite", "timestamp": "2026-08-01", "application": "Marketing", "team": "Marketing", "environment": "staging", "input_tokens": 8000000, "output_tokens": 1000000, "request_count": 40000, "latency_ms": 350.0, "cost": 830.0, "cache_hit_rate": 0.18},
    ]

    return {
        "mode": "demo",
        "account_id": "DEMO-123456789",
        "region": "us-east-1",
        "collected_at": f"{date.today().isoformat()}T12:00:00",
        "aws": aws_resources,
        "kubernetes": {"cluster": {"cluster_id": "cluster-demo", "name": "finops-demo", "provider": "EKS-compatible", "region": "us-east-1"}, "nodes": k8s_nodes, "workloads": k8s_workloads, "history": [{"period": item["period"], "cost": round(item["cost"] * 0.20, 2), "platform": "Kubernetes"} for item in _months()]},
        "ai": {"usage": ai_usage, "history": [{"period": item["period"], "cost": round(item["cost"] * 0.09, 2), "platform": "AI"} for item in _months()]},
    }
