"""Typed response models used by the API and shared analysis engine."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field


Platform = Literal["AWS", "Kubernetes", "AI"]


class Finding(BaseModel):
    """A deduplicated optimization opportunity across every platform."""

    id: str
    platform: Platform
    resource_id: str
    resource_type: str
    service: str
    category: str
    issue: str
    recommendation: str
    estimated_monthly_savings: float = Field(ge=0)
    confidence: Literal["High", "Medium", "Low"]
    priority: Literal["HIGH", "MEDIUM", "LOW"]
    risk: Literal["Low", "Medium", "High"]
    source: str
    explanation: str


class PartialError(BaseModel):
    status: Literal["partial", "error"] = "partial"
    service: str
    error: str
    message: str


class APIEnvelope(BaseModel):
    status: Literal["ok", "partial"]
    mode: Literal["demo", "live"]
    last_updated: datetime
    warnings: List[PartialError] = Field(default_factory=list)


class Cluster(BaseModel):
    cluster_id: str
    name: str
    provider: str
    region: str
    monthly_cost: float
    allocated_cost: float
    unallocated_cost: float
    efficiency: float


class Node(BaseModel):
    node_id: str
    name: str
    instance_type: str
    cpu_capacity: float
    memory_capacity: float
    cpu_requested: float
    memory_requested: float
    cpu_usage: float
    memory_usage: float
    monthly_cost: float
    utilization: float


class Namespace(BaseModel):
    namespace: str
    monthly_cost: float
    cpu_cost: float
    memory_cost: float
    pod_count: int
    workload_count: int
    cluster_cost_pct: float


class Workload(BaseModel):
    workload_id: str
    name: str
    namespace: str
    type: str
    replicas: int
    cpu_request: float
    cpu_usage: float
    memory_request: float
    memory_usage: float
    monthly_cost: float
    cpu_efficiency: float
    memory_efficiency: float
    efficiency: float
    recommended_cpu_request: float
    recommended_memory_request: float
    estimated_savings: float
    confidence: str
    risk: str
    has_limits: bool = True
    has_requests: bool = True


class AIUsage(BaseModel):
    provider: str
    model: str
    timestamp: str
    application: str
    team: str
    environment: str
    input_tokens: int
    output_tokens: int
    total_tokens: int
    request_count: int
    latency_ms: float
    cost: float
    cache_hit_rate: float = 0.0


class UnitEconomics(BaseModel):
    metric: str
    value: float
    unit: str
    numerator_cost: float
    denominator_count: int


class DashboardSummary(BaseModel):
    total_monthly_spend: float
    potential_monthly_savings: float
    waste_pct: float
    overall_efficiency: float
    aws_spend: float
    kubernetes_spend: float
    ai_spend: float
    finding_count: int


class SettingsPatch(BaseModel):
    """Safe, allow-listed settings that can be changed from the UI."""

    idle_cpu_threshold: Optional[float] = Field(default=None, ge=0, le=100)
    idle_days: Optional[int] = Field(default=None, ge=1, le=365)
    old_snapshot_days: Optional[int] = Field(default=None, ge=1, le=3650)
    cpu_efficiency_threshold: Optional[float] = Field(default=None, ge=0, le=1)
    memory_efficiency_threshold: Optional[float] = Field(default=None, ge=0, le=1)
    node_utilization_threshold: Optional[float] = Field(default=None, ge=0, le=1)
    safety_margin: Optional[float] = Field(default=None, ge=0, le=1)
    monthly_budget: Optional[float] = Field(default=None, ge=0)
    alert_threshold: Optional[float] = Field(default=None, ge=0, le=100)
    high_cost_request: Optional[float] = Field(default=None, ge=0)
    forecast_horizon_months: Optional[int] = Field(default=None, ge=1, le=24)
    growth_rate: Optional[float] = Field(default=None, ge=-1, le=10)


class SettingsResponse(BaseModel):
    settings: Dict[str, Any]
    mode: Literal["demo", "live"]
    updated_at: datetime
