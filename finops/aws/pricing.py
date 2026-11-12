"""AWS list-price estimates used when resource-level billing data is unavailable.

These are public on-demand list prices (Linux, shared tenancy, us-east-1 base) and are
used only to *estimate* resource cost. Cost Explorer remains the source of truth for
actual spend. Every estimate produced here is labelled with ``PRICE_SOURCE`` so the
UI can show where a number came from.
"""

from __future__ import annotations

from typing import Optional

HOURS_PER_MONTH = 730
PRICE_SOURCE = "AWS public on-demand list price estimate (us-east-1 base, Linux)"

# USD per instance-hour, on-demand, Linux, us-east-1.
EC2_ON_DEMAND_HOURLY = {
    "t3.small": 0.0208, "t3.medium": 0.0416, "t3.large": 0.0832, "t3.xlarge": 0.1664, "t3.2xlarge": 0.3328,
    "m5.large": 0.096, "m5.xlarge": 0.192, "m5.2xlarge": 0.384, "m5.4xlarge": 0.768,
    "m6i.large": 0.096, "m6i.xlarge": 0.192, "m6i.2xlarge": 0.384,
    "c5.large": 0.085, "c5.xlarge": 0.17, "c5.2xlarge": 0.34, "c5.4xlarge": 0.68,
    "r5.large": 0.126, "r5.xlarge": 0.252, "r5.2xlarge": 0.504,
    "r6i.large": 0.126, "r6i.xlarge": 0.252, "r6i.2xlarge": 0.504,
}

# USD per DB-instance-hour, single-AZ. Multi-AZ doubles the instance charge.
RDS_HOURLY = {
    "db.t3.micro": 0.017, "db.t3.small": 0.034, "db.t3.medium": 0.068, "db.t3.large": 0.136,
    "db.m5.large": 0.171, "db.m5.xlarge": 0.342,
    "db.r5.large": 0.25, "db.r5.xlarge": 0.50, "db.r5.2xlarge": 1.00,
}

# USD per GB-month.
EBS_GB_MONTH = {"gp2": 0.10, "gp3": 0.08, "io1": 0.125, "io2": 0.125, "st1": 0.045, "sc1": 0.015, "standard": 0.05}
RDS_STORAGE_GB_MONTH = {"gp2": 0.115, "gp3": 0.115, "io1": 0.125}
SNAPSHOT_GB_MONTH = 0.05
PUBLIC_IPV4_HOURLY = 0.005  # Charged for every public IPv4 address since February 2024.
EKS_CONTROL_PLANE_HOURLY = 0.10

# Coarse regional uplift relative to us-east-1.
REGION_MULTIPLIER = {"us-east-1": 1.0, "us-east-2": 1.0, "us-west-2": 1.0, "us-west-1": 1.12, "eu-west-1": 1.11, "eu-central-1": 1.15, "ap-southeast-1": 1.2}


def _region(region: Optional[str]) -> float:
    return REGION_MULTIPLIER.get(region or "us-east-1", 1.1)


def ec2_monthly(instance_type: str, region: str = "us-east-1") -> Optional[float]:
    hourly = EC2_ON_DEMAND_HOURLY.get(instance_type)
    return None if hourly is None else round(hourly * HOURS_PER_MONTH * _region(region), 2)


def rds_monthly(instance_class: str, region: str = "us-east-1", multi_az: bool = False, storage_gb: float = 0, storage_type: str = "gp2") -> Optional[float]:
    hourly = RDS_HOURLY.get(instance_class)
    if hourly is None:
        return None
    instance = hourly * HOURS_PER_MONTH * (2 if multi_az else 1)
    storage = storage_gb * RDS_STORAGE_GB_MONTH.get(storage_type, 0.115) * (2 if multi_az else 1)
    return round((instance + storage) * _region(region), 2)


def ebs_monthly(volume_type: str, size_gb: float, region: str = "us-east-1") -> Optional[float]:
    rate = EBS_GB_MONTH.get(volume_type)
    return None if rate is None else round(rate * size_gb * _region(region), 2)


def gp3_migration_savings(volume_type: str, size_gb: float, region: str = "us-east-1") -> float:
    """gp2 -> gp3 storage delta. Baseline gp3 performance (3,000 IOPS / 125 MB/s) is included."""
    if volume_type != "gp2":
        return 0.0
    return round((EBS_GB_MONTH["gp2"] - EBS_GB_MONTH["gp3"]) * size_gb * _region(region), 2)


def snapshot_monthly(billed_gb: float, region: str = "us-east-1") -> float:
    """Snapshots are incremental; ``billed_gb`` is the unique stored data, not the volume size."""
    return round(SNAPSHOT_GB_MONTH * billed_gb * _region(region), 2)


def public_ipv4_monthly() -> float:
    return round(PUBLIC_IPV4_HOURLY * HOURS_PER_MONTH, 2)


def eks_control_plane_monthly() -> float:
    return round(EKS_CONTROL_PLANE_HOURLY * HOURS_PER_MONTH, 2)
