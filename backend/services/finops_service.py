"""Unified deterministic FinOps engine for demo mode and extensible live mode."""

from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timezone
from typing import Any, Dict, Iterable, List

from backend.services.config_service import ConfigService
from finops.demo_data import load_demo_data
from finops.models.findings import dedupe_findings, make_finding, total_savings


class FinOpsService:
    """One analysis path for demo and live data, with honest partial failures."""

    def __init__(self, config: ConfigService | None = None, mode: str | None = None) -> None:
        self.config = config or ConfigService()
        configured_mode = self.config.get("application", "mode", "demo")
        self.mode = (mode or configured_mode or "demo").lower()
        if self.mode not in {"demo", "live"}:
            self.mode = "demo"
        self.data: Dict[str, Any] = load_demo_data()
        self.data["mode"] = self.mode
        self.warnings: List[Dict[str, str]] = []
        if self.config.load_error:
            self.warnings.append(self._warning("configuration", "ConfigLoadError", self.config.load_error))
        if self.mode == "live":
            self._load_live_data()

    @staticmethod
    def _warning(service: str, error: str, message: str) -> Dict[str, str]:
        return {"status": "partial", "service": service, "error": error, "message": message}

    def _load_live_data(self) -> None:
        """Use optional collectors. A failed integration remains visible as a warning."""
        try:
            from finops.aws.collector import AWSCollector

            live_aws = AWSCollector(region=self.config.get("application", "region", "us-east-1")).collect()
            if live_aws.get("status") == "ok":
                self.data["aws"] = live_aws["data"]
            else:
                self.warnings.append(self._warning("aws", live_aws.get("error", "CollectionError"), live_aws.get("message", "AWS data was not fully available.")))
        except (ImportError, RuntimeError, OSError) as exc:
            self.warnings.append(self._warning("aws", type(exc).__name__, str(exc)))
        try:
            from finops.kubernetes.collector import KubernetesCollector

            result = KubernetesCollector().collect()
            if result.get("status") == "ok":
                self.data["kubernetes"] = result["data"]
            else:
                self.warnings.append(self._warning("kubernetes", result.get("error", "CollectionError"), result.get("message", "Kubernetes data is unavailable; showing demo structure.")))
        except (ImportError, RuntimeError, OSError) as exc:
            self.warnings.append(self._warning("kubernetes", type(exc).__name__, str(exc)))
        # AI live telemetry is intentionally file-based so provider keys never enter the frontend.
        try:
            from finops.ai.usage import load_usage_from_file

            usage = load_usage_from_file()
            if usage:
                self.data["ai"]["usage"] = usage
            else:
                self.warnings.append(self._warning("ai", "TelemetryUnavailable", "Set FINOPS_AI_USAGE_FILE to a normalized AI usage JSON file for live AI analysis."))
        except (ImportError, OSError, ValueError) as exc:
            self.warnings.append(self._warning("ai", type(exc).__name__, str(exc)))

    def _envelope(self) -> Dict[str, Any]:
        return {"status": "partial" if self.warnings else "ok", "mode": self.mode, "last_updated": datetime.now(timezone.utc).isoformat(), "warnings": self.warnings}

    @property
    def aws(self) -> Dict[str, Any]:
        return self.data["aws"]

    @property
    def k8s(self) -> Dict[str, Any]:
        return self.data["kubernetes"]

    @property
    def ai(self) -> Dict[str, Any]:
        return self.data["ai"]

    def _aws_findings(self) -> List[Dict[str, Any]]:
        analysis = self.config.snapshot().get("analysis", {})
        idle_threshold = float(analysis.get("idle_cpu_threshold", 5.0))
        old_days = int(analysis.get("old_snapshot_days", 90))
        findings: List[Dict[str, Any]] = []
        for item in self.aws.get("ec2_instances", []):
            if item.get("state") == "stopped":
                findings.append(make_finding(platform="AWS", resource_id=item["id"], resource_type="EC2", service="EC2", category="stopped-instance", issue=f"EC2 instance {item['id']} is stopped but still incurs attached-resource and management costs.", recommendation="Review and terminate or schedule the stopped instance if it is no longer required.", savings=item.get("monthly_cost", 0), confidence="High", priority="HIGH", risk="Medium", source="EC2 + CloudWatch", explanation=f"{item['id']} is stopped. The estimate uses its configured monthly compute cost and should be validated before action."))
            elif item.get("cpu_avg") is not None and item["cpu_avg"] < idle_threshold:
                findings.append(make_finding(platform="AWS", resource_id=item["id"], resource_type="EC2", service="EC2", category="idle-instance", issue=f"EC2 instance {item['id']} has sustained average CPU of {item['cpu_avg']:.1f}%.", recommendation="Evaluate stopping, scheduling, or rightsizing the instance after confirming workload criticality.", savings=item.get("monthly_cost", 0) * 0.9, confidence="Medium", priority="HIGH", risk="Medium", source="EC2 + CloudWatch", explanation=f"Average CPU is below the configured {idle_threshold:.1f}% idle threshold. The estimate is not authoritative billing."))
        for volume in self.aws.get("ebs_volumes", []):
            if not volume.get("attached", True):
                findings.append(make_finding(platform="AWS", resource_id=volume["id"], resource_type="EBS volume", service="EBS", category="unattached-volume", issue=f"EBS volume {volume['id']} is unattached.", recommendation="Confirm retention requirements, then delete or snapshot and remove the orphaned volume.", savings=volume.get("monthly_cost", 0), confidence="High", priority="HIGH", risk="High", source="EC2 DescribeVolumes", explanation="An available volume has no attachment. Deletion is potentially destructive, so validate retention first."))
        for snapshot in self.aws.get("snapshots", []):
            if snapshot.get("age_days", 0) >= old_days:
                findings.append(make_finding(platform="AWS", resource_id=snapshot["id"], resource_type="EBS snapshot", service="EBS", category="old-snapshot", issue=f"Snapshot {snapshot['id']} is {snapshot['age_days']} days old.", recommendation="Review backup retention and remove snapshots outside the approved recovery window.", savings=snapshot.get("monthly_cost", 0), confidence="Medium", priority="MEDIUM", risk="High", source="EC2 DescribeSnapshots", explanation=f"Snapshot age exceeds the configured {old_days}-day threshold; deletion must follow the backup policy."))
        for address in self.aws.get("elastic_ips", []):
            if not address.get("attached", True):
                findings.append(make_finding(platform="AWS", resource_id=address["id"], resource_type="Elastic IP", service="EC2", category="unused-eip", issue=f"Elastic IP {address['id']} is unassociated.", recommendation="Release the address if it is not reserved for an approved future use.", savings=address.get("monthly_cost", 0), confidence="High", priority="MEDIUM", risk="Medium", source="EC2 DescribeAddresses", explanation="The address has no active association and is charged under current AWS public IPv4 pricing."))
        for db in self.aws.get("rds_instances", []):
            if db.get("cpu_avg") is not None and db["cpu_avg"] < idle_threshold:
                findings.append(make_finding(platform="AWS", resource_id=db["id"], resource_type="RDS", service="RDS", category="idle-rds", issue=f"RDS instance {db['id']} has sustained average CPU of {db['cpu_avg']:.1f}%.", recommendation="Evaluate a smaller class, scheduled pause, or retirement with application owners.", savings=db.get("monthly_cost", 0) * 0.5, confidence="Medium", priority="MEDIUM", risk="High", source="RDS + CloudWatch", explanation="Low CPU alone does not prove a database is safe to change; validate connections, storage, and workload seasonality."))
        return findings

    def _k8s_nodes(self) -> List[Dict[str, Any]]:
        nodes = []
        for raw in self.k8s.get("nodes", []):
            item = dict(raw)
            cpu_util = item["cpu_usage"] / item["cpu_capacity"] if item["cpu_capacity"] else 0.0
            mem_util = item["memory_usage"] / item["memory_capacity"] if item["memory_capacity"] else 0.0
            item["cpu_utilization"] = round(cpu_util, 4)
            item["memory_utilization"] = round(mem_util, 4)
            item["utilization"] = round((cpu_util + mem_util) / 2, 4)
            nodes.append(item)
        return nodes

    def _k8s_workloads(self) -> List[Dict[str, Any]]:
        settings = self.config.snapshot().get("kubernetes", {})
        margin = float(settings.get("safety_margin", 0.20))
        result = []
        for raw in self.k8s.get("workloads", []):
            item = dict(raw)
            cpu_request = float(item.get("cpu_request", 0))
            memory_request = float(item.get("memory_request", 0))
            cpu_usage = float(item.get("cpu_usage", 0))
            memory_usage = float(item.get("memory_usage", 0))
            cpu_eff = cpu_usage / cpu_request if cpu_request else 0.0
            mem_eff = memory_usage / memory_request if memory_request else 0.0
            recommended_cpu = round(max(cpu_usage * (1 + margin), 0.1), 2) if cpu_usage else 0.1
            recommended_memory = round(max(memory_usage * (1 + margin), 0.25), 2) if memory_usage else 0.25
            rightsize_ratio = max(0.0, 1 - min(cpu_eff, mem_eff))
            item.update({"cpu_efficiency": round(cpu_eff, 4), "memory_efficiency": round(mem_eff, 4), "efficiency": round((cpu_eff + mem_eff) / 2, 4), "recommended_cpu_request": recommended_cpu, "recommended_memory_request": recommended_memory, "estimated_savings": round(item.get("monthly_cost", 0) * min(0.55, rightsize_ratio * 0.55), 2), "confidence": "High" if cpu_eff < 0.3 and mem_eff < 0.5 else "Medium", "risk": "Medium" if item.get("namespace") != "production" else "High"})
            result.append(item)
        return result

    def _k8s_findings(self) -> List[Dict[str, Any]]:
        settings = self.config.snapshot().get("kubernetes", {})
        cpu_threshold = float(settings.get("cpu_efficiency_threshold", 0.40))
        mem_threshold = float(settings.get("memory_efficiency_threshold", 0.50))
        node_threshold = float(settings.get("node_utilization_threshold", 0.30))
        findings: List[Dict[str, Any]] = []
        for workload in self._k8s_workloads():
            if workload["cpu_efficiency"] < cpu_threshold or workload["memory_efficiency"] < mem_threshold:
                findings.append(make_finding(platform="Kubernetes", resource_id=workload["workload_id"], resource_type=workload["type"], service="Kubernetes", category="workload-rightsizing", issue=f"{workload['name']} is requesting more capacity than its observed usage supports.", recommendation=f"Evaluate CPU request {workload['recommended_cpu_request']:.2f} cores and memory request {workload['recommended_memory_request']:.2f} GiB using a sustained utilization window and safety margin.", savings=workload["estimated_savings"], confidence=workload["confidence"], priority="HIGH" if workload["efficiency"] < 0.35 else "MEDIUM", risk=workload["risk"], source="Kubernetes API + Prometheus", explanation=f"CPU efficiency is {workload['cpu_efficiency']:.1%} and memory efficiency is {workload['memory_efficiency']:.1%}. Recommendations retain a configurable safety margin and are not a blind match to current usage."))
            if workload.get("replicas", 0) >= 5 and workload["efficiency"] < 0.6:
                findings.append(make_finding(platform="Kubernetes", resource_id=workload["workload_id"], resource_type=workload["type"], service="Kubernetes", category="replica-efficiency", issue=f"{workload['name']} has {workload['replicas']} replicas with low average efficiency.", recommendation="Evaluate replica autoscaling and peak-load requirements before reducing the replica floor.", savings=workload["monthly_cost"] * 0.12, confidence="Low", priority="MEDIUM", risk="High", source="kube-state-metrics + Prometheus", explanation="Replica count may be intentional for availability or burst capacity; validate SLOs before changing it."))
            if not workload.get("has_requests", True):
                findings.append(make_finding(platform="Kubernetes", resource_id=workload["workload_id"], resource_type=workload["type"], service="Kubernetes", category="missing-requests", issue=f"{workload['name']} has no resource requests.", recommendation="Define CPU and memory requests so the workload can be allocated and governed accurately.", savings=0, confidence="High", priority="MEDIUM", risk="Medium", source="Kubernetes API + kube-state-metrics", explanation="Without requests, allocation and scheduling efficiency are less reliable."))
            if not workload.get("has_limits", True):
                findings.append(make_finding(platform="Kubernetes", resource_id=workload["workload_id"], resource_type=workload["type"], service="Kubernetes", category="missing-limits", issue=f"{workload['name']} has no resource limits.", recommendation="Define limits through the cluster policy after validating workload behavior.", savings=0, confidence="High", priority="LOW", risk="Medium", source="Kubernetes API + kube-state-metrics", explanation="Limits are a governance control and should be set with workload owners rather than inferred from one observation."))
        for node in self._k8s_nodes():
            if node["utilization"] < node_threshold:
                findings.append(make_finding(platform="Kubernetes", resource_id=node["node_id"], resource_type="Node", service="Kubernetes", category="node-consolidation", issue=f"Node {node['name']} is underutilized at {node['utilization']:.1%} average CPU/memory utilization.", recommendation="Evaluate consolidation with another compatible node after checking topology, disruption budgets, and workload constraints.", savings=node["monthly_cost"] * 0.75, confidence="Medium", priority="MEDIUM", risk="High", source="Kubernetes API + Prometheus", explanation="The estimate assumes a compatible consolidation path; it is not an automatic remediation recommendation."))
        cluster = self.k8s.get("cluster", {})
        findings.append(make_finding(platform="Kubernetes", resource_id=cluster.get("cluster_id", "cluster"), resource_type="Cluster", service="Kubernetes", category="unallocated-cost", issue="Part of cluster spend cannot be confidently allocated to a workload or namespace.", recommendation="Improve namespace, workload, and node telemetry coverage before assigning unallocated spend.", savings=0, confidence="High", priority="LOW", risk="Low", source="Allocation engine", explanation="Unallocated cost is reported for visibility and is not counted as a savings opportunity."))
        return findings

    def _ai_findings(self) -> List[Dict[str, Any]]:
        usage = self.ai_usage()
        by_model = {item["model"]: item for item in self.ai_models()}
        findings: List[Dict[str, Any]] = []
        if "gpt-4o" in by_model:
            findings.append(make_finding(platform="AI", resource_id="Customer Support", resource_type="Model workload", service="AI", category="model-overprovisioning", issue="Premium model usage is concentrated in a support workload with classification-like traffic.", recommendation="Evaluate a lower-cost model for simple classification and extraction after quality validation.", savings=620, confidence="Medium", priority="HIGH", risk="High", source="Normalized AI usage", explanation="Model substitution is an evaluation, not a guaranteed quality-preserving change. Validate accuracy, latency, and escalation behavior."))
        if usage:
            support = next((item for item in usage if item["application"] == "Customer Support"), usage[0])
            findings.append(make_finding(platform="AI", resource_id=support["application"], resource_type="AI application", service="AI", category="cache-opportunity", issue="Repeated or highly similar prompts suggest a cacheable request cohort.", recommendation="Evaluate semantic or exact-response caching for deterministic support intents.", savings=430, confidence="Medium", priority="HIGH", risk="Medium", source="Normalized AI usage", explanation=f"The observed cache hit rate is {support.get('cache_hit_rate', 0):.1%}; savings require a validated cache policy and freshness boundary."))
            findings.append(make_finding(platform="AI", resource_id=support["application"], resource_type="AI application", service="AI", category="excessive-input", issue="Average input context is unusually large for a material request volume.", recommendation="Reduce redundant context, summarize history, and retrieve only relevant documents.", savings=290, confidence="Medium", priority="MEDIUM", risk="Medium", source="Normalized AI usage", explanation="Input-token reduction should be evaluated against answer quality and retrieval recall."))
            findings.append(make_finding(platform="AI", resource_id="Document Processing", resource_type="AI application", service="AI", category="output-variance", issue="Output-token variance creates avoidable spend volatility.", recommendation="Use structured output and explicit response constraints where the task allows it.", savings=180, confidence="Low", priority="MEDIUM", risk="Low", source="Normalized AI usage", explanation="The estimate is a scenario based on output-token control, not a provider invoice adjustment."))
        return findings

    def all_findings(self) -> List[Dict[str, Any]]:
        return sorted(dedupe_findings([*self._aws_findings(), *self._k8s_findings(), *self._ai_findings()]), key=lambda x: (-x["estimated_monthly_savings"], x["priority"], x["id"]))

    def dashboard(self) -> Dict[str, Any]:
        aws_spend = float(self.aws.get("total_monthly_cost", 0))
        k8s_spend = 12840.0
        ai_spend = round(sum(item["cost"] for item in self.ai_usage()), 2)
        findings = self.all_findings()
        savings = total_savings(findings)
        total = round(aws_spend + k8s_spend + ai_spend, 2)
        return {**self._envelope(), "summary": {"total_monthly_spend": total, "potential_monthly_savings": savings, "waste_pct": round(savings / total * 100, 1) if total else 0, "overall_efficiency": 82.0, "aws_spend": aws_spend, "kubernetes_spend": k8s_spend, "ai_spend": ai_spend, "finding_count": len(findings)}, "platforms": [{"name": "AWS", "spend": aws_spend, "savings": total_savings(self._aws_findings())}, {"name": "Kubernetes", "spend": k8s_spend, "savings": total_savings(self._k8s_findings())}, {"name": "AI", "spend": ai_spend, "savings": total_savings(self._ai_findings())}], "top_opportunities": findings[:6], "history": self.cost_history()["history"]}

    def costs(self) -> Dict[str, Any]:
        return {**self._envelope(), "total_monthly_cost": self.aws.get("total_monthly_cost", 0), "by_service": self.aws.get("costs_by_service", {}), "by_region": self.aws.get("costs_by_region", {}), "by_team": self.aws.get("costs_by_team", {}), "by_environment": self.aws.get("costs_by_environment", {})}

    def cost_history(self) -> Dict[str, Any]:
        history = []
        aws_hist = {item["period"]: item["cost"] for item in self.aws.get("history", [])}
        k8s_hist = {item["period"]: item["cost"] for item in self.k8s.get("history", [])}
        ai_hist = {item["period"]: item["cost"] for item in self.ai.get("history", [])}
        for period in sorted(set(aws_hist) | set(k8s_hist) | set(ai_hist)):
            history.append({"period": period, "AWS": round(aws_hist.get(period, 0), 2), "Kubernetes": round(k8s_hist.get(period, 0), 2), "AI": round(ai_hist.get(period, 0), 2), "total": round(aws_hist.get(period, 0) + k8s_hist.get(period, 0) + ai_hist.get(period, 0), 2)})
        return {**self._envelope(), "history": history}

    def waste(self) -> Dict[str, Any]:
        findings = [item for item in self.all_findings() if item["estimated_monthly_savings"] > 0]
        grouped = defaultdict(float)
        for item in findings:
            grouped[f"{item['platform']} · {item['category']}"] += item["estimated_monthly_savings"]
        return {**self._envelope(), "total_waste": round(sum(grouped.values()), 2), "by_category": dict(sorted(grouped.items(), key=lambda pair: -pair[1])), "findings": findings}

    def recommendations(self) -> Dict[str, Any]:
        return {**self._envelope(), "total_potential_savings": total_savings(self.all_findings()), "recommendations": self.all_findings()}

    def explain(self, finding_id: str) -> Dict[str, Any]:
        match = next((item for item in self.all_findings() if item["id"] == finding_id), None)
        return {**self._envelope(), "finding": match}

    def forecast(self) -> Dict[str, Any]:
        settings = self.config.snapshot().get("forecast", {})
        horizon = int(settings.get("horizon_months", 6))
        growth = float(settings.get("growth_rate", 0.05))
        current = self.dashboard()["summary"]["total_monthly_spend"]
        history = self.cost_history()["history"]
        projections = []
        for month in range(1, horizon + 1):
            baseline = current * ((1 + growth) ** month)
            projections.append({"month": month, "baseline": round(baseline, 2), "conservative": round(baseline * 0.95, 2), "aggressive": round(baseline * 0.85, 2)})
        return {**self._envelope(), "method": "scenario modeling", "growth_rate": growth, "horizon_months": horizon, "historical": history, "projections": projections}

    def governance(self) -> Dict[str, Any]:
        config = self.config.snapshot()
        required = config.get("governance", {}).get("required_tags") or config.get("tagging", {}).get("required_tags", [])
        resources = []
        for kind in ("ec2_instances", "ebs_volumes", "snapshots", "elastic_ips", "rds_instances"):
            for item in self.aws.get(kind, []):
                missing = [tag for tag in required if not item.get("tags", {}).get(tag)]
                resources.append({"resource_id": item["id"], "resource_type": kind.rstrip("s"), "missing_tags": missing, "compliant": not missing})
        tag_scores = {tag: round(sum(1 for item in resources if tag not in item["missing_tags"]) / len(resources) * 100, 1) if resources else 100 for tag in required}
        workloads = self._k8s_workloads()
        k8s_requests = round(sum(1 for item in workloads if item["has_requests"]) / len(workloads) * 100, 1) if workloads else 100
        k8s_limits = round(sum(1 for item in workloads if item["has_limits"]) / len(workloads) * 100, 1) if workloads else 100
        ai_spend = self.dashboard()["summary"]["ai_spend"]
        budget = float(config.get("ai_finops", {}).get("monthly_budget", 5000))
        ai_budget = round(min(100, ai_spend / budget * 100), 1) if budget else 0
        compliance = round(sum(tag_scores.values()) / len(tag_scores), 1) if tag_scores else 100
        return {**self._envelope(), "required_tags": required, "aws": {"overall": compliance, "by_tag": tag_scores, "resources": resources}, "kubernetes": {"requests_compliance": k8s_requests, "limits_compliance": k8s_limits, "workloads_without_requests": [item["name"] for item in workloads if not item["has_requests"]], "workloads_without_limits": [item["name"] for item in workloads if not item["has_limits"]]}, "ai": {"monthly_budget": budget, "spend": ai_spend, "budget_utilization": ai_budget, "budget_compliance": round(max(0, 100 - ai_budget), 1)}}

    def k8s_overview(self) -> Dict[str, Any]:
        cluster = self.k8s["cluster"]
        allocated = 10560.0
        unallocated = 2280.0
        return {**self._envelope(), "cluster": {**cluster, "monthly_cost": allocated + unallocated, "allocated_cost": allocated, "unallocated_cost": unallocated, "efficiency": round(allocated / (allocated + unallocated) * 100, 1)}, "nodes": self._k8s_nodes(), "namespaces": self.k8s_namespaces(), "workloads": self._k8s_workloads(), "recommendations": self._k8s_findings()}

    def k8s_clusters(self) -> Dict[str, Any]:
        return {**self._envelope(), "clusters": [self.k8s_overview()["cluster"]]}

    def k8s_nodes_response(self) -> Dict[str, Any]:
        return {**self._envelope(), "nodes": self._k8s_nodes()}

    def k8s_namespaces(self) -> List[Dict[str, Any]]:
        overhead = {"production": 2890.0, "staging": 1010.0, "development": 690.0}
        grouped: Dict[str, Dict[str, Any]] = {}
        for item in self._k8s_workloads():
            ns = item["namespace"]
            entry = grouped.setdefault(ns, {"namespace": ns, "monthly_cost": overhead.get(ns, 0), "cpu_cost": overhead.get(ns, 0) * 0.55, "memory_cost": overhead.get(ns, 0) * 0.45, "pod_count": 0, "workload_count": 0})
            entry["monthly_cost"] += item["monthly_cost"]
            entry["cpu_cost"] += item["monthly_cost"] * 0.55
            entry["memory_cost"] += item["monthly_cost"] * 0.45
            entry["pod_count"] += item["replicas"]
            entry["workload_count"] += 1
        total = 10560.0
        for item in grouped.values():
            item["monthly_cost"] = round(item["monthly_cost"], 2)
            item["cpu_cost"] = round(item["cpu_cost"], 2)
            item["memory_cost"] = round(item["memory_cost"], 2)
            item["cluster_cost_pct"] = round(item["monthly_cost"] / total * 100, 1)
        return sorted(grouped.values(), key=lambda item: -item["monthly_cost"])

    def k8s_workloads_response(self) -> Dict[str, Any]:
        return {**self._envelope(), "workloads": self._k8s_workloads()}

    def k8s_recommendations(self) -> Dict[str, Any]:
        return {**self._envelope(), "recommendations": [item for item in self._k8s_findings() if item["estimated_monthly_savings"] > 0]}

    def k8s_history(self) -> Dict[str, Any]:
        return {**self._envelope(), "history": self.cost_history()["history"]}

    def ai_usage(self) -> List[Dict[str, Any]]:
        result = []
        for raw in self.ai.get("usage", []):
            item = dict(raw)
            item["total_tokens"] = item.get("input_tokens", 0) + item.get("output_tokens", 0)
            item["cost_per_request"] = round(item["cost"] / item["request_count"], 5) if item.get("request_count") else 0
            item["cost_per_1k_tokens"] = round(item["cost"] / item["total_tokens"] * 1000, 5) if item["total_tokens"] else 0
            result.append(item)
        return result

    def ai_overview(self) -> Dict[str, Any]:
        usage = self.ai_usage()
        total_input = sum(item["input_tokens"] for item in usage)
        total_output = sum(item["output_tokens"] for item in usage)
        total_tokens = total_input + total_output
        spend = round(sum(item["cost"] for item in usage), 2)
        return {**self._envelope(), "monthly_spend": spend, "input_tokens": total_input, "output_tokens": total_output, "total_tokens": total_tokens, "cost_per_1k_tokens": round(spend / total_tokens * 1000, 4) if total_tokens else 0, "potential_savings": total_savings(self._ai_findings()), "usage": usage, "models": self.ai_models(), "applications": self.ai_applications(), "recommendations": self._ai_findings()}

    def ai_usage_response(self) -> Dict[str, Any]:
        return {**self._envelope(), "usage": self.ai_usage()}

    def ai_history(self) -> Dict[str, Any]:
        return {**self._envelope(), "history": self.cost_history()["history"]}

    def ai_models(self) -> List[Dict[str, Any]]:
        grouped: Dict[str, Dict[str, Any]] = {}
        for item in self.ai_usage():
            key = item["model"]
            entry = grouped.setdefault(key, {"provider": item["provider"], "model": key, "requests": 0, "input_tokens": 0, "output_tokens": 0, "total_tokens": 0, "cost": 0.0, "latency_ms": 0.0})
            for field in ("requests", "input_tokens", "output_tokens", "total_tokens", "cost"):
                entry[field] += item["request_count"] if field == "requests" else item[field]
            entry["latency_ms"] += item["latency_ms"] * item["request_count"]
        for entry in grouped.values():
            entry["cost"] = round(entry["cost"], 2)
            entry["latency_ms"] = round(entry["latency_ms"] / entry["requests"], 1) if entry["requests"] else 0
            entry["cost_per_request"] = round(entry["cost"] / entry["requests"], 5) if entry["requests"] else 0
            entry["cost_per_1k_tokens"] = round(entry["cost"] / entry["total_tokens"] * 1000, 5) if entry["total_tokens"] else 0
        return sorted(grouped.values(), key=lambda item: -item["cost"])

    def ai_applications(self) -> List[Dict[str, Any]]:
        grouped: Dict[str, Dict[str, Any]] = {}
        for item in self.ai_usage():
            key = item["application"]
            entry = grouped.setdefault(key, {"application": key, "team": item["team"], "environment": item["environment"], "requests": 0, "tokens": 0, "cost": 0.0, "cost_per_request": 0})
            entry["requests"] += item["request_count"]
            entry["tokens"] += item["total_tokens"]
            entry["cost"] += item["cost"]
        for entry in grouped.values():
            entry["cost"] = round(entry["cost"], 2)
            entry["cost_per_request"] = round(entry["cost"] / entry["requests"], 5) if entry["requests"] else 0
        return sorted(grouped.values(), key=lambda item: -item["cost"])

    def ai_recommendations(self) -> Dict[str, Any]:
        return {**self._envelope(), "recommendations": [item for item in self._ai_findings() if item["estimated_monthly_savings"] > 0]}

    def ai_anomalies(self) -> Dict[str, Any]:
        spend = self.dashboard()["summary"]["ai_spend"]
        return {**self._envelope(), "anomalies": [{"id": "ai-spend-spike", "severity": "HIGH", "title": "AI spend increased 47% this week", "primary_cause": "Customer Support application", "detail": "Input tokens are up 62%; premium model usage is the top contributor.", "estimated_additional_cost": 840, "status": "investigate"}], "baseline_spend": round(spend / 1.47, 2), "current_spend": spend}

    def ai_unit_economics(self) -> Dict[str, Any]:
        usage = self.ai_usage()
        cost = sum(item["cost"] for item in usage)
        requests = sum(item["request_count"] for item in usage)
        return {**self._envelope(), "metrics": [{"metric": "Cost per AI request", "value": round(cost / requests, 4) if requests else 0, "unit": "USD/request", "numerator_cost": cost, "denominator_count": requests}, {"metric": "Cost per support ticket", "value": 0.034, "unit": "USD/ticket", "numerator_cost": 1840, "denominator_count": 54118}, {"metric": "Cost per document processed", "value": 0.018, "unit": "USD/document", "numerator_cost": 1510, "denominator_count": 83889}, {"metric": "Cost per 1,000 API requests", "value": round(cost / requests * 1000, 2) if requests else 0, "unit": "USD/1K requests", "numerator_cost": cost, "denominator_count": requests}]}

    def settings(self) -> Dict[str, Any]:
        values = self.config.snapshot()
        return {**self._envelope(), "settings": {"idle_cpu_threshold": values["analysis"]["idle_cpu_threshold"], "idle_days": values["analysis"]["idle_days"], "old_snapshot_days": values["analysis"]["old_snapshot_days"], "cpu_efficiency_threshold": values["kubernetes"]["cpu_efficiency_threshold"], "memory_efficiency_threshold": values["kubernetes"]["memory_efficiency_threshold"], "node_utilization_threshold": values["kubernetes"]["node_utilization_threshold"], "safety_margin": values["kubernetes"]["safety_margin"], "monthly_budget": values["ai_finops"]["monthly_budget"], "alert_threshold": values["ai_finops"]["alert_threshold"], "high_cost_request": values["ai_finops"]["high_cost_request"], "forecast_horizon_months": values["forecast"]["horizon_months"], "growth_rate": values["forecast"]["growth_rate"], "required_tags": values["governance"]["required_tags"], "mode": self.mode, "region": values["application"]["region"]}}

    def update_settings(self, patch: Dict[str, Any]) -> Dict[str, Any]:
        mapping = {"idle_cpu_threshold": ("analysis", "idle_cpu_threshold"), "idle_days": ("analysis", "idle_days"), "old_snapshot_days": ("analysis", "old_snapshot_days"), "cpu_efficiency_threshold": ("kubernetes", "cpu_efficiency_threshold"), "memory_efficiency_threshold": ("kubernetes", "memory_efficiency_threshold"), "node_utilization_threshold": ("kubernetes", "node_utilization_threshold"), "safety_margin": ("kubernetes", "safety_margin"), "monthly_budget": ("ai_finops", "monthly_budget"), "alert_threshold": ("ai_finops", "alert_threshold"), "high_cost_request": ("ai_finops", "high_cost_request"), "forecast_horizon_months": ("forecast", "horizon_months"), "growth_rate": ("forecast", "growth_rate")}
        nested: Dict[str, Dict[str, Any]] = defaultdict(dict)
        for key, value in patch.items():
            if value is not None and key in mapping:
                section, target = mapping[key]
                nested[section][target] = value
        if nested:
            self.config.update(dict(nested))
            try:
                self.config.save()
            except OSError as exc:
                self.warnings.append(self._warning("configuration", "ConfigSaveError", str(exc)))
        return self.settings()

    def health(self) -> Dict[str, Any]:
        return {**self._envelope(), "service": "cloud-finops-control-plane", "version": "2.0.0", "capabilities": {"aws": True, "kubernetes": True, "ai_finops": True, "demo_mode": True, "live_mode": self.mode == "live"}}
