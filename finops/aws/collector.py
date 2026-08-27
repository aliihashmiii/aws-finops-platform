"""Read-only AWS collector with structured partial-error reporting."""

from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List


class AWSCollector:
    def __init__(self, region: str = "us-east-1") -> None:
        try:
            import boto3
        except ImportError as exc:
            raise RuntimeError("boto3 is required for live AWS mode") from exc
        self.region = region
        self.ec2 = boto3.client("ec2", region_name=region)
        self.rds = boto3.client("rds", region_name=region)
        self.cloudwatch = boto3.client("cloudwatch", region_name=region)
        self.ce = boto3.client("ce", region_name="us-east-1")
        self.sts = boto3.client("sts")

    @staticmethod
    def _tags(raw: List[Dict[str, str]]) -> Dict[str, str]:
        return {item["Key"]: item["Value"] for item in raw if "Key" in item and "Value" in item}

    def _cpu(self, instance_id: str, days: int = 7) -> float | None:
        end = datetime.now(timezone.utc)
        response = self.cloudwatch.get_metric_statistics(Namespace="AWS/EC2", MetricName="CPUUtilization", Dimensions=[{"Name": "InstanceId", "Value": instance_id}], StartTime=end - timedelta(days=days), EndTime=end, Period=86400, Statistics=["Average"])
        points = response.get("Datapoints", [])
        return round(sum(point["Average"] for point in points) / len(points), 2) if points else None

    def collect(self) -> Dict[str, Any]:
        data: Dict[str, Any] = {"account_id": "Unknown", "region": self.region, "collected_at": datetime.now(timezone.utc).isoformat(), "ec2_instances": [], "ebs_volumes": [], "snapshots": [], "elastic_ips": [], "rds_instances": [], "costs_by_service": {}, "costs_by_region": {self.region: 0.0}, "costs_by_team": {}, "costs_by_environment": {}, "total_monthly_cost": 0.0, "history": []}
        errors: List[str] = []
        try:
            data["account_id"] = self.sts.get_caller_identity()["Account"]
        except Exception as exc:  # AWS SDK exceptions vary by provider/botocore version.
            errors.append(f"STS: {type(exc).__name__}: {exc}")
        try:
            response = self.ec2.describe_instances()
            for reservation in response.get("Reservations", []):
                for instance in reservation.get("Instances", []):
                    iid = instance["InstanceId"]
                    try:
                        cpu = self._cpu(iid)
                    except Exception as exc:
                        errors.append(f"CloudWatch {iid}: {type(exc).__name__}: {exc}")
                        cpu = None
                    data["ec2_instances"].append({"id": iid, "type": instance.get("InstanceType", "unknown"), "state": instance.get("State", {}).get("Name", "unknown"), "region": self.region, "cpu_avg": cpu, "monthly_cost": 0.0, "tags": self._tags(instance.get("Tags", []))})
        except Exception as exc:
            errors.append(f"EC2: {type(exc).__name__}: {exc}")
        try:
            for volume in self.ec2.describe_volumes().get("Volumes", []):
                data["ebs_volumes"].append({"id": volume["VolumeId"], "size_gb": volume.get("Size", 0), "type": volume.get("VolumeType", "unknown"), "state": volume.get("State", "unknown"), "attached": bool(volume.get("Attachments")), "region": self.region, "monthly_cost": 0.0, "tags": self._tags(volume.get("Tags", []))})
        except Exception as exc:
            errors.append(f"EBS: {type(exc).__name__}: {exc}")
        try:
            for snapshot in self.ec2.describe_snapshots(OwnerIds=["self"]).get("Snapshots", []):
                started = snapshot.get("StartTime")
                age = (datetime.now(started.tzinfo) - started).days if started else 0
                data["snapshots"].append({"id": snapshot["SnapshotId"], "size_gb": snapshot.get("VolumeSize", 0), "age_days": age, "region": self.region, "monthly_cost": 0.0, "tags": self._tags(snapshot.get("Tags", []))})
        except Exception as exc:
            errors.append(f"Snapshots: {type(exc).__name__}: {exc}")
        try:
            for address in self.ec2.describe_addresses().get("Addresses", []):
                data["elastic_ips"].append({"id": address.get("AllocationId", address.get("PublicIp", "unknown")), "ip": address.get("PublicIp", "unknown"), "attached": bool(address.get("AssociationId")), "region": self.region, "monthly_cost": 0.0, "tags": self._tags(address.get("Tags", []))})
        except Exception as exc:
            errors.append(f"Elastic IP: {type(exc).__name__}: {exc}")
        try:
            for db in self.rds.describe_db_instances().get("DBInstances", []):
                data["rds_instances"].append({"id": db["DBInstanceIdentifier"], "type": db.get("DBInstanceClass", "unknown"), "engine": db.get("Engine", "unknown"), "cpu_avg": None, "state": db.get("DBInstanceStatus", "unknown"), "region": self.region, "monthly_cost": 0.0, "tags": {}})
        except Exception as exc:
            errors.append(f"RDS: {type(exc).__name__}: {exc}")
        try:
            end = datetime.now(timezone.utc).date()
            start = end - timedelta(days=31)
            response = self.ce.get_cost_and_usage(TimePeriod={"Start": start.isoformat(), "End": end.isoformat()}, Granularity="MONTHLY", Metrics=["UnblendedCost"], GroupBy=[{"Type": "DIMENSION", "Key": "SERVICE"}])
            groups = response.get("ResultsByTime", [{}])[0].get("Groups", [])
            for group in groups:
                data["costs_by_service"][group["Keys"][0]] = float(group["Metrics"]["UnblendedCost"]["Amount"])
            data["total_monthly_cost"] = round(sum(data["costs_by_service"].values()), 2)
        except Exception as exc:
            errors.append(f"Cost Explorer: {type(exc).__name__}: {exc}")
        if errors:
            return {"status": "partial", "error": "AWSCollectionPartial", "message": "; ".join(errors), "data": data}
        return {"status": "ok", "data": data}
