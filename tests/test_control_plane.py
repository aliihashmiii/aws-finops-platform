from backend.services.config_service import ConfigService
from backend.services.finops_service import FinOpsService
from finops.models.findings import dedupe_findings, make_finding, total_savings


def service():
    return FinOpsService(config=ConfigService())


def test_demo_dashboard_reconciles_platform_spend():
    summary = service().dashboard()["summary"]
    assert summary["total_monthly_spend"] == summary["aws_spend"] + summary["kubernetes_spend"] + summary["ai_spend"]
    assert summary["aws_spend"] == 45234.5
    assert summary["ai_spend"] == 5510.0


def test_kubernetes_efficiency_and_safe_recommendation():
    workloads = service().k8s_workloads_response()["workloads"]
    checkout = next(item for item in workloads if item["name"] == "checkout-api")
    assert checkout["cpu_efficiency"] == 0.2
    assert checkout["memory_efficiency"] == 0.2625
    assert checkout["recommended_cpu_request"] > checkout["cpu_usage"]
    assert checkout["recommended_memory_request"] > checkout["memory_usage"]


def test_ai_token_and_unit_economics_math():
    finops = service()
    overview = finops.ai_overview()
    assert overview["input_tokens"] == 103000000
    assert overview["output_tokens"] == 19000000
    assert overview["total_tokens"] == 122000000
    assert round(overview["monthly_spend"], 2) == 5510.0
    assert overview["cost_per_1k_tokens"] > 0
    assert finops.ai_unit_economics()["metrics"][0]["denominator_count"] == sum(item["request_count"] for item in finops.ai_usage())


def test_aws_thresholds_are_configuration_driven():
    finops = service()
    baseline = {item["id"] for item in finops.waste()["findings"]}
    assert "aws:i-demo001:idle-instance" in baseline
    finops.config.update({"analysis": {"idle_cpu_threshold": 1.0}})
    after = {item["id"] for item in finops.waste()["findings"]}
    assert "aws:i-demo001:idle-instance" not in after


def test_forecast_is_explicit_scenario_modeling():
    forecast = service().forecast()
    assert forecast["method"] == "scenario modeling"
    assert forecast["projections"][0]["conservative"] < forecast["projections"][0]["baseline"]
    assert forecast["projections"][0]["aggressive"] < forecast["projections"][0]["conservative"]


def test_governance_reports_missing_tags_and_policy_gaps():
    governance = service().governance()
    assert "Environment" in governance["required_tags"]
    assert governance["aws"]["overall"] < 100
    assert "report-cron" in governance["kubernetes"]["workloads_without_requests"]
    assert governance["ai"]["budget_utilization"] > 0


def test_savings_are_deduplicated_by_unique_identity():
    first = make_finding(platform="AWS", resource_id="i-123", resource_type="EC2", service="EC2", category="idle-instance", issue="idle", recommendation="stop", savings=100, confidence="Medium", priority="HIGH", risk="Medium", source="test", explanation="test")
    duplicate = dict(first, estimated_monthly_savings=80)
    unrelated = dict(first, id="aws:i-456:idle-instance", resource_id="i-456", estimated_monthly_savings=25)
    assert len(dedupe_findings([first, duplicate, unrelated])) == 2
    assert total_savings([first, duplicate, unrelated]) == 125
