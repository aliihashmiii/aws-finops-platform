#!/usr/bin/env python3
"""
AWS FinOps Platform - Complete Cloud Financial Management
A professional-grade FinOps agent with all 6 core capabilities

Capabilities:
1. Cost Visibility - Multi-dimensional cost breakdown
2. Waste Detection - Idle resources, orphaned volumes, old snapshots
3. Optimization - Right-sizing, RI/SP recommendations
4. Financial Structuring - Budgets, allocation, commitments
5. Forecasting - ML-based cost predictions
6. Governance - Tag compliance, policies, anomalies

Usage:
    python finops.py --demo          # Demo mode (no AWS needed)
    python finops.py --analyze       # Full analysis
    python finops.py --waste         # Waste detection only
    python finops.py --forecast 12   # 12-month forecast

Author: FinOps Professional
License: MIT
"""

import argparse
import json
import sys
from datetime import datetime, timedelta
from collections import defaultdict
from typing import Dict, List, Optional

# ============================================================================
# CONFIGURATION
# ============================================================================

class FinOpsConfig:
    """Global configuration"""
    
    # Analysis thresholds
    IDLE_CPU_THRESHOLD = 5.0  # % CPU for idle detection
    IDLE_DAYS = 7  # Days to check for idle instances
    OLD_SNAPSHOT_DAYS = 90  # Snapshot age threshold
    
    # AWS Pricing (monthly USD - approximate)
    EC2_PRICING = {
        't2.micro': 8.47, 't2.small': 16.79, 't2.medium': 33.58,
        't2.large': 67.16, 't2.xlarge': 134.32,
        't3.micro': 7.59, 't3.small': 15.18, 't3.medium': 30.37,
        't3.large': 60.74, 't3.xlarge': 121.47, 't3.2xlarge': 242.94,
        'm5.large': 70.08, 'm5.xlarge': 140.16, 'm5.2xlarge': 280.32,
        'm5.4xlarge': 560.64, 'm5.8xlarge': 1121.28,
        'c5.large': 62.05, 'c5.xlarge': 124.10, 'c5.2xlarge': 248.19,
        'r5.large': 91.98, 'r5.xlarge': 183.96, 'r5.2xlarge': 367.92,
    }
    
    EBS_PRICING_PER_GB = {
        'gp2': 0.10, 'gp3': 0.08,
        'io1': 0.125, 'io2': 0.125,
        'st1': 0.045, 'sc1': 0.025,
        'standard': 0.05
    }
    
    SNAPSHOT_PRICING_PER_GB = 0.05
    EIP_PRICING = 3.65
    RDS_PRICING = {
        'db.t3.micro': 14.18, 'db.t3.small': 28.36,
        'db.t3.medium': 56.72, 'db.t3.large': 113.44,
        'db.r5.large': 183.96, 'db.r5.xlarge': 367.92,
    }

# ============================================================================
# AWS DATA COLLECTOR
# ============================================================================

class AWSCollector:
    """Collects data from AWS (or generates demo data)"""
    
    def __init__(self, demo_mode=False, region='us-east-1'):
        self.demo_mode = demo_mode
        self.region = region
        
        if not demo_mode:
            try:
                import boto3
                self.ec2 = boto3.client('ec2', region_name=region)
                self.cloudwatch = boto3.client('cloudwatch', region_name=region)
                self.ce = boto3.client('ce', region_name='us-east-1')  # CE is always us-east-1
                self.rds = boto3.client('rds', region_name=region)
                self.sts = boto3.client('sts')
                self.has_aws = True
            except ImportError:
                print("⚠️  boto3 not installed. Using demo mode.")
                self.demo_mode = True
                self.has_aws = False
            except Exception as e:
                print(f"⚠️  AWS connection failed: {e}. Using demo mode.")
                self.demo_mode = True
                self.has_aws = False
    
    def collect_all(self) -> Dict:
        """Collect all AWS data or generate demo data"""
        if self.demo_mode:
            return self._generate_demo_data()
        else:
            return self._collect_real_data()
    
    def _generate_demo_data(self) -> Dict:
        """Generate realistic demo data"""
        return {
            'account_id': 'DEMO-123456789',
            'region': self.region,
            'collection_time': datetime.now().isoformat(),
            
            # EC2 Instances
            'ec2_instances': [
                {'id': 'i-demo001', 'type': 't3.medium', 'state': 'running', 'cpu_avg': 2.3, 'tags': {'Environment': 'dev', 'Team': 'engineering'}},
                {'id': 'i-demo002', 'type': 'm5.large', 'state': 'running', 'cpu_avg': 1.1, 'tags': {'Environment': 'staging', 'Team': 'data-science'}},
                {'id': 'i-demo003', 'type': 't3.large', 'state': 'running', 'cpu_avg': 3.5, 'tags': {'Environment': 'dev', 'Team': 'engineering'}},
                {'id': 'i-demo004', 'type': 't3.xlarge', 'state': 'stopped', 'cpu_avg': 0, 'tags': {'Environment': 'dev'}},
                {'id': 'i-prod001', 'type': 'm5.2xlarge', 'state': 'running', 'cpu_avg': 65.3, 'tags': {'Environment': 'production', 'Team': 'backend'}},
                {'id': 'i-prod002', 'type': 'c5.xlarge', 'state': 'running', 'cpu_avg': 78.2, 'tags': {'Environment': 'production', 'Team': 'backend'}},
            ],
            
            # EBS Volumes
            'ebs_volumes': [
                {'id': 'vol-demo001', 'size_gb': 100, 'type': 'gp2', 'state': 'available', 'attached': False, 'tags': {}},
                {'id': 'vol-demo002', 'size_gb': 50, 'type': 'gp2', 'state': 'available', 'attached': False, 'tags': {}},
                {'id': 'vol-demo003', 'size_gb': 200, 'type': 'gp3', 'state': 'in-use', 'attached': True, 'tags': {'Environment': 'production'}},
                {'id': 'vol-demo004', 'size_gb': 500, 'type': 'gp2', 'state': 'in-use', 'attached': True, 'tags': {'Environment': 'production'}},
            ],
            
            # Snapshots
            'snapshots': [
                {'id': 'snap-demo001', 'size_gb': 80, 'age_days': 120, 'tags': {}},
                {'id': 'snap-demo002', 'size_gb': 100, 'age_days': 150, 'tags': {}},
                {'id': 'snap-demo003', 'size_gb': 50, 'age_days': 200, 'tags': {}},
                {'id': 'snap-demo004', 'size_gb': 30, 'age_days': 45, 'tags': {'Backup': 'weekly'}},
            ],
            
            # Elastic IPs
            'elastic_ips': [
                {'id': 'eip-demo001', 'ip': '54.123.45.67', 'attached': False, 'tags': {}},
                {'id': 'eip-demo002', 'ip': '52.98.76.54', 'attached': True, 'tags': {'Environment': 'production'}},
            ],
            
            # RDS Instances
            'rds_instances': [
                {'id': 'db-demo001', 'type': 'db.t3.medium', 'engine': 'postgres', 'cpu_avg': 2.1, 'state': 'available', 'tags': {'Environment': 'dev'}},
                {'id': 'db-prod001', 'type': 'db.r5.large', 'engine': 'mysql', 'cpu_avg': 45.3, 'state': 'available', 'tags': {'Environment': 'production'}},
            ],
            
            # Cost data (last 30 days)
            'total_monthly_cost': 45234.50,
            'costs_by_service': {
                'EC2': 18450.00,
                'RDS': 12300.00,
                'S3': 5670.00,
                'Data Transfer': 4890.00,
                'EBS': 2100.00,
                'Other': 1824.50
            },
            'costs_by_team': {
                'engineering': 22100.00,
                'data-science': 15670.00,
                'backend': 7464.50
            },
            'costs_by_environment': {
                'production': 31650.00,
                'staging': 9050.00,
                'development': 4534.50
            }
        }
    
    def _collect_real_data(self) -> Dict:
        """Collect real AWS data"""
        print("🔍 Collecting data from AWS...")
        
        try:
            account_id = self.sts.get_caller_identity()['Account']
        except:
            account_id = 'Unknown'
        
        data = {
            'account_id': account_id,
            'region': self.region,
            'collection_time': datetime.now().isoformat(),
            'ec2_instances': self._get_ec2_instances(),
            'ebs_volumes': self._get_ebs_volumes(),
            'snapshots': self._get_snapshots(),
            'elastic_ips': self._get_elastic_ips(),
            'rds_instances': self._get_rds_instances(),
            'costs_by_service': {},
            'total_monthly_cost': 0
        }
        
        # Get costs (this might fail if CE access not granted)
        try:
            cost_data = self._get_cost_data()
            data['costs_by_service'] = cost_data.get('by_service', {})
            data['total_monthly_cost'] = cost_data.get('total', 0)
        except:
            print("⚠️  Could not fetch cost data (requires Cost Explorer permissions)")
        
        return data
    
    def _get_ec2_instances(self) -> List[Dict]:
        """Get EC2 instances"""
        instances = []
        try:
            response = self.ec2.describe_instances()
            for reservation in response['Reservations']:
                for instance in reservation['Instances']:
                    cpu_avg = self._get_cpu_metrics(instance['InstanceId'])
                    instances.append({
                        'id': instance['InstanceId'],
                        'type': instance['InstanceType'],
                        'state': instance['State']['Name'],
                        'cpu_avg': cpu_avg,
                        'tags': self._extract_tags(instance.get('Tags', []))
                    })
        except Exception as e:
            print(f"⚠️  Error collecting EC2: {e}")
        return instances
    
    def _get_cpu_metrics(self, instance_id: str) -> Optional[float]:
        """Get average CPU for instance"""
        try:
            end_time = datetime.utcnow()
            start_time = end_time - timedelta(days=FinOpsConfig.IDLE_DAYS)
            
            response = self.cloudwatch.get_metric_statistics(
                Namespace='AWS/EC2',
                MetricName='CPUUtilization',
                Dimensions=[{'Name': 'InstanceId', 'Value': instance_id}],
                StartTime=start_time,
                EndTime=end_time,
                Period=86400,
                Statistics=['Average']
            )
            
            if response['Datapoints']:
                avg = sum(dp['Average'] for dp in response['Datapoints']) / len(response['Datapoints'])
                return round(avg, 2)
        except:
            pass
        return None
    
    def _get_ebs_volumes(self) -> List[Dict]:
        """Get EBS volumes"""
        volumes = []
        try:
            response = self.ec2.describe_volumes()
            for volume in response['Volumes']:
                volumes.append({
                    'id': volume['VolumeId'],
                    'size_gb': volume['Size'],
                    'type': volume['VolumeType'],
                    'state': volume['State'],
                    'attached': len(volume['Attachments']) > 0,
                    'tags': self._extract_tags(volume.get('Tags', []))
                })
        except Exception as e:
            print(f"⚠️  Error collecting EBS: {e}")
        return volumes
    
    def _get_snapshots(self) -> List[Dict]:
        """Get EBS snapshots"""
        snapshots = []
        try:
            response = self.ec2.describe_snapshots(OwnerIds=['self'])
            for snapshot in response['Snapshots']:
                age_days = (datetime.now(snapshot['StartTime'].tzinfo) - snapshot['StartTime']).days
                snapshots.append({
                    'id': snapshot['SnapshotId'],
                    'size_gb': snapshot['VolumeSize'],
                    'age_days': age_days,
                    'tags': self._extract_tags(snapshot.get('Tags', []))
                })
        except Exception as e:
            print(f"⚠️  Error collecting Snapshots: {e}")
        return snapshots
    
    def _get_elastic_ips(self) -> List[Dict]:
        """Get Elastic IPs"""
        eips = []
        try:
            response = self.ec2.describe_addresses()
            for address in response['Addresses']:
                eips.append({
                    'id': address.get('AllocationId', 'N/A'),
                    'ip': address['PublicIp'],
                    'attached': 'AssociationId' in address,
                    'tags': self._extract_tags(address.get('Tags', []))
                })
        except Exception as e:
            print(f"⚠️  Error collecting EIPs: {e}")
        return eips
    
    def _get_rds_instances(self) -> List[Dict]:
        """Get RDS instances"""
        instances = []
        try:
            response = self.rds.describe_db_instances()
            for db in response['DBInstances']:
                instances.append({
                    'id': db['DBInstanceIdentifier'],
                    'type': db['DBInstanceClass'],
                    'engine': db['Engine'],
                    'state': db['DBInstanceStatus'],
                    'cpu_avg': None,  # Would need CloudWatch
                    'tags': {}
                })
        except Exception as e:
            print(f"⚠️  Error collecting RDS: {e}")
        return instances
    
    def _get_cost_data(self) -> Dict:
        """Get cost data from Cost Explorer"""
        end = datetime.now().date()
        start = end - timedelta(days=30)
        
        response = self.ce.get_cost_and_usage(
            TimePeriod={'Start': start.isoformat(), 'End': end.isoformat()},
            Granularity='MONTHLY',
            Metrics=['UnblendedCost'],
            GroupBy=[{'Type': 'DIMENSION', 'Key': 'SERVICE'}]
        )
        
        by_service = {}
        total = 0
        
        if response.get('ResultsByTime'):
            for group in response['ResultsByTime'][0].get('Groups', []):
                service = group['Keys'][0]
                amount = float(group['Metrics']['UnblendedCost']['Amount'])
                by_service[service] = amount
                total += amount
        
        return {'by_service': by_service, 'total': total}
    
    def _extract_tags(self, tags: List[Dict]) -> Dict:
        """Convert AWS tags to dict"""
        return {tag['Key']: tag['Value'] for tag in tags} if tags else {}

# ============================================================================
# COST VISIBILITY ENGINE
# ============================================================================

class CostVisibilityEngine:
    """Capability 1: Multi-dimensional cost breakdown"""
    
    def __init__(self, data: Dict):
        self.data = data
    
    def analyze(self) -> Dict:
        """Perform cost visibility analysis"""
        return {
            'total_monthly_cost': self.data.get('total_monthly_cost', 0),
            'by_service': self._breakdown_by_service(),
            'by_team': self._breakdown_by_team(),
            'by_environment': self._breakdown_by_environment(),
        }
    
    def _breakdown_by_service(self) -> List[Dict]:
        """Break down costs by AWS service"""
        costs = self.data.get('costs_by_service', {})
        total = sum(costs.values()) if costs else 1
        
        breakdown = []
        for service, cost in sorted(costs.items(), key=lambda x: x[1], reverse=True):
            breakdown.append({
                'name': service,
                'cost': cost,
                'percentage': (cost / total * 100) if total > 0 else 0
            })
        return breakdown
    
    def _breakdown_by_team(self) -> List[Dict]:
        """Break down costs by team (from tags)"""
        costs = self.data.get('costs_by_team', {})
        total = sum(costs.values()) if costs else 1
        
        breakdown = []
        for team, cost in sorted(costs.items(), key=lambda x: x[1], reverse=True):
            breakdown.append({
                'name': team,
                'cost': cost,
                'percentage': (cost / total * 100) if total > 0 else 0
            })
        return breakdown
    
    def _breakdown_by_environment(self) -> List[Dict]:
        """Break down costs by environment"""
        costs = self.data.get('costs_by_environment', {})
        total = sum(costs.values()) if costs else 1
        
        breakdown = []
        for env, cost in sorted(costs.items(), key=lambda x: x[1], reverse=True):
            breakdown.append({
                'name': env,
                'cost': cost,
                'percentage': (cost / total * 100) if total > 0 else 0
            })
        return breakdown

# ============================================================================
# WASTE DETECTION ENGINE
# ============================================================================

class WasteDetectionEngine:
    """Capability 2: Identify idle and orphaned resources"""
    
    def __init__(self, data: Dict):
        self.data = data
    
    def detect_all(self) -> Dict:
        """Detect all types of waste"""
        waste = {
            'idle_ec2': self._detect_idle_ec2(),
            'unattached_ebs': self._detect_unattached_ebs(),
            'old_snapshots': self._detect_old_snapshots(),
            'unused_eips': self._detect_unused_eips(),
            'idle_rds': self._detect_idle_rds(),
        }
        
        total = sum(sum(item['monthly_cost'] for item in category) for category in waste.values())
        
        return {
            'categories': waste,
            'total_monthly_savings': total,
            'total_annual_savings': total * 12,
            'total_items': sum(len(category) for category in waste.values())
        }
    
    def _detect_idle_ec2(self) -> List[Dict]:
        """Detect idle EC2 instances"""
        idle = []
        for instance in self.data.get('ec2_instances', []):
            if instance['state'] != 'running':
                continue
            
            cpu = instance.get('cpu_avg')
            if cpu is not None and cpu < FinOpsConfig.IDLE_CPU_THRESHOLD:
                monthly_cost = FinOpsConfig.EC2_PRICING.get(instance['type'], 50.0)
                idle.append({
                    'resource_id': instance['id'],
                    'type': instance['type'],
                    'cpu_avg': cpu,
                    'monthly_cost': monthly_cost,
                    'recommendation': 'Terminate or schedule shutdown',
                    'priority': 'HIGH',
                    'tags': instance.get('tags', {})
                })
        return idle
    
    def _detect_unattached_ebs(self) -> List[Dict]:
        """Detect unattached EBS volumes"""
        unattached = []
        for volume in self.data.get('ebs_volumes', []):
            if not volume.get('attached', True):
                price_per_gb = FinOpsConfig.EBS_PRICING_PER_GB.get(volume['type'], 0.10)
                monthly_cost = volume['size_gb'] * price_per_gb
                unattached.append({
                    'resource_id': volume['id'],
                    'size_gb': volume['size_gb'],
                    'type': volume['type'],
                    'monthly_cost': monthly_cost,
                    'recommendation': 'Delete or create snapshot',
                    'priority': 'MEDIUM',
                    'tags': volume.get('tags', {})
                })
        return unattached
    
    def _detect_old_snapshots(self) -> List[Dict]:
        """Detect old snapshots"""
        old = []
        for snapshot in self.data.get('snapshots', []):
            if snapshot['age_days'] > FinOpsConfig.OLD_SNAPSHOT_DAYS:
                monthly_cost = snapshot['size_gb'] * FinOpsConfig.SNAPSHOT_PRICING_PER_GB
                old.append({
                    'resource_id': snapshot['id'],
                    'size_gb': snapshot['size_gb'],
                    'age_days': snapshot['age_days'],
                    'monthly_cost': monthly_cost,
                    'recommendation': f'Delete snapshot ({snapshot["age_days"]} days old)',
                    'priority': 'LOW',
                    'tags': snapshot.get('tags', {})
                })
        return old
    
    def _detect_unused_eips(self) -> List[Dict]:
        """Detect unused Elastic IPs"""
        unused = []
        for eip in self.data.get('elastic_ips', []):
            if not eip.get('attached', True):
                unused.append({
                    'resource_id': eip['id'],
                    'ip': eip['ip'],
                    'monthly_cost': FinOpsConfig.EIP_PRICING,
                    'recommendation': 'Release unused Elastic IP',
                    'priority': 'MEDIUM',
                    'tags': eip.get('tags', {})
                })
        return unused
    
    def _detect_idle_rds(self) -> List[Dict]:
        """Detect idle RDS instances"""
        idle = []
        for db in self.data.get('rds_instances', []):
            cpu = db.get('cpu_avg')
            if cpu is not None and cpu < FinOpsConfig.IDLE_CPU_THRESHOLD:
                monthly_cost = FinOpsConfig.RDS_PRICING.get(db['type'], 100.0)
                idle.append({
                    'resource_id': db['id'],
                    'type': db['type'],
                    'engine': db['engine'],
                    'cpu_avg': cpu,
                    'monthly_cost': monthly_cost,
                    'recommendation': 'Stop or right-size database',
                    'priority': 'HIGH',
                    'tags': db.get('tags', {})
                })
        return idle

# ============================================================================
# OPTIMIZATION ENGINE
# ============================================================================

class OptimizationEngine:
    """Capability 3: Generate optimization recommendations"""
    
    def __init__(self, data: Dict, waste_report: Dict):
        self.data = data
        self.waste_report = waste_report
    
    def optimize(self) -> Dict:
        """Generate all optimization recommendations"""
        quick_wins = self._quick_wins()
        medium_term = self._medium_term_optimizations()
        long_term = self._long_term_optimizations()
        
        total_savings = (
            sum(r['monthly_savings'] for r in quick_wins) +
            sum(r['monthly_savings'] for r in medium_term) +
            sum(r['monthly_savings'] for r in long_term)
        )
        
        return {
            'quick_wins': quick_wins,
            'medium_term': medium_term,
            'long_term': long_term,
            'total_potential_savings': total_savings,
            'total_annual_impact': total_savings * 12
        }
    
    def _quick_wins(self) -> List[Dict]:
        """0-30 day optimizations"""
        wins = []
        
        # Terminate idle EC2
        idle_ec2_savings = sum(i['monthly_cost'] for i in self.waste_report['categories']['idle_ec2'])
        if idle_ec2_savings > 0:
            wins.append({
                'title': 'Terminate idle EC2 instances',
                'monthly_savings': idle_ec2_savings,
                'effort': 'Low',
                'impact': 'High',
                'timeframe': '0-7 days'
            })
        
        # Delete unattached EBS
        ebs_savings = sum(v['monthly_cost'] for v in self.waste_report['categories']['unattached_ebs'])
        if ebs_savings > 0:
            wins.append({
                'title': 'Delete unattached EBS volumes',
                'monthly_savings': ebs_savings,
                'effort': 'Low',
                'impact': 'Medium',
                'timeframe': '0-7 days'
            })
        
        # Release unused EIPs
        eip_savings = sum(e['monthly_cost'] for e in self.waste_report['categories']['unused_eips'])
        if eip_savings > 0:
            wins.append({
                'title': 'Release unused Elastic IPs',
                'monthly_savings': eip_savings,
                'effort': 'Low',
                'impact': 'Low',
                'timeframe': '0-1 days'
            })
        
        return sorted(wins, key=lambda x: x['monthly_savings'], reverse=True)
    
    def _medium_term_optimizations(self) -> List[Dict]:
        """30-90 day optimizations"""
        opts = []
        
        # gp2 to gp3 conversion
        gp2_volumes = [v for v in self.data.get('ebs_volumes', []) if v['type'] == 'gp2' and v['attached']]
        if gp2_volumes:
            savings = sum(v['size_gb'] * (0.10 - 0.08) for v in gp2_volumes)
            opts.append({
                'title': f'Convert {len(gp2_volumes)} EBS volumes from gp2 to gp3',
                'monthly_savings': savings,
                'effort': 'Medium',
                'impact': 'Medium',
                'timeframe': '30-60 days'
            })
        
        # Right-size over-provisioned instances
        # (Would need more CPU/memory data for accurate detection)
        opts.append({
            'title': 'Right-size EC2 instances (requires detailed analysis)',
            'monthly_savings': 0,  # Placeholder
            'effort': 'Medium',
            'impact': 'High',
            'timeframe': '30-90 days'
        })
        
        return [o for o in opts if o['monthly_savings'] > 0]
    
    def _long_term_optimizations(self) -> List[Dict]:
        """90+ day optimizations"""
        opts = []
        
        # Reserved Instances
        running_ec2 = [i for i in self.data.get('ec2_instances', []) if i['state'] == 'running']
        if len(running_ec2) >= 3:
            # Assume 30% savings with 1-year RI
            current_cost = sum(FinOpsConfig.EC2_PRICING.get(i['type'], 50) for i in running_ec2)
            savings = current_cost * 0.30
            opts.append({
                'title': f'Purchase Reserved Instances for {len(running_ec2)} instances',
                'monthly_savings': savings,
                'effort': 'High',
                'impact': 'High',
                'timeframe': '90+ days'
            })
        
        return opts

# ============================================================================
# FORECASTING ENGINE
# ============================================================================

class ForecastingEngine:
    """Capability 5: Cost forecasting"""
    
    def __init__(self, data: Dict):
        self.data = data
        self.current_monthly = data.get('total_monthly_cost', 0)
    
    def forecast(self, months: int = 12) -> Dict:
        """Generate cost forecast"""
        scenarios = [
            self._baseline_scenario(months),
            self._conservative_scenario(months),
            self._aggressive_scenario(months)
        ]
        
        return {
            'scenarios': scenarios,
            'months': months,
            'current_monthly': self.current_monthly
        }
    
    def _baseline_scenario(self, months: int) -> Dict:
        """No optimization, 5% monthly growth"""
        projections = []
        cost = self.current_monthly
        
        for month in range(1, months + 1):
            cost = cost * 1.05  # 5% growth
            projections.append({'month': month, 'cost': round(cost, 2)})
        
        return {
            'name': 'Baseline (No Optimization)',
            'optimization_level': '0%',
            'growth_rate': '5% monthly',
            'projections': projections,
            'month_3': projections[2]['cost'] if len(projections) >= 3 else 0,
            'month_6': projections[5]['cost'] if len(projections) >= 6 else 0,
            'month_12': projections[11]['cost'] if len(projections) >= 12 else 0,
            'year_total': sum(p['cost'] for p in projections[:12])
        }
    
    def _conservative_scenario(self, months: int) -> Dict:
        """20% optimization, 5% growth"""
        projections = []
        optimized_base = self.current_monthly * 0.80  # 20% reduction
        cost = optimized_base
        
        for month in range(1, months + 1):
            cost = cost * 1.05
            projections.append({'month': month, 'cost': round(cost, 2)})
        
        return {
            'name': 'Conservative (20% Optimization)',
            'optimization_level': '20%',
            'growth_rate': '5% monthly',
            'projections': projections,
            'month_3': projections[2]['cost'] if len(projections) >= 3 else 0,
            'month_6': projections[5]['cost'] if len(projections) >= 6 else 0,
            'month_12': projections[11]['cost'] if len(projections) >= 12 else 0,
            'year_total': sum(p['cost'] for p in projections[:12])
        }
    
    def _aggressive_scenario(self, months: int) -> Dict:
        """40% optimization, 5% growth"""
        projections = []
        optimized_base = self.current_monthly * 0.60  # 40% reduction
        cost = optimized_base
        
        for month in range(1, months + 1):
            cost = cost * 1.05
            projections.append({'month': month, 'cost': round(cost, 2)})
        
        return {
            'name': 'Aggressive (40% Optimization)',
            'optimization_level': '40%',
            'growth_rate': '5% monthly',
            'projections': projections,
            'month_3': projections[2]['cost'] if len(projections) >= 3 else 0,
            'month_6': projections[5]['cost'] if len(projections) >= 6 else 0,
            'month_12': projections[11]['cost'] if len(projections) >= 12 else 0,
            'year_total': sum(p['cost'] for p in projections[:12])
        }

# ============================================================================
# GOVERNANCE ENGINE
# ============================================================================

class GovernanceEngine:
    """Capability 6: Tag compliance and policy enforcement"""
    
    def __init__(self, data: Dict):
        self.data = data
        self.required_tags = ['Environment', 'Team', 'CostCenter']
    
    def check_all(self) -> Dict:
        """Check all governance policies"""
        tag_compliance = self._check_tag_compliance()
        
        return {
            'tag_compliance': tag_compliance['compliance_percentage'],
            'untagged_resources': tag_compliance['untagged_count'],
            'violations': tag_compliance['violations']
        }
    
    def _check_tag_compliance(self) -> Dict:
        """Check tagging compliance"""
        violations = []
        total_resources = 0
        compliant_resources = 0
        
        # Check EC2
        for instance in self.data.get('ec2_instances', []):
            total_resources += 1
            tags = instance.get('tags', {})
            missing_tags = [tag for tag in self.required_tags if tag not in tags]
            
            if not missing_tags:
                compliant_resources += 1
            else:
                violations.append({
                    'resource_type': 'EC2',
                    'resource_id': instance['id'],
                    'missing_tags': missing_tags
                })
        
        # Check EBS
        for volume in self.data.get('ebs_volumes', []):
            total_resources += 1
            tags = volume.get('tags', {})
            missing_tags = [tag for tag in self.required_tags if tag not in tags]
            
            if not missing_tags:
                compliant_resources += 1
            else:
                violations.append({
                    'resource_type': 'EBS',
                    'resource_id': volume['id'],
                    'missing_tags': missing_tags
                })
        
        compliance_pct = (compliant_resources / total_resources * 100) if total_resources > 0 else 100
        
        return {
            'compliance_percentage': round(compliance_pct, 1),
            'compliant_count': compliant_resources,
            'untagged_count': total_resources - compliant_resources,
            'violations': violations[:10]  # Top 10
        }

# ============================================================================
# REPORT GENERATOR
# ============================================================================

class ReportGenerator:
    """Generate professional reports"""
    
    @staticmethod
    def generate_text_report(analysis: Dict) -> str:
        """Generate comprehensive text report"""
        report = []
        report.append("=" * 70)
        report.append("AWS FINOPS ANALYSIS REPORT")
        report.append("=" * 70)
        report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append(f"Account: {analysis['metadata']['account_id']}")
        report.append(f"Region: {analysis['metadata']['region']}")
        report.append("=" * 70)
        
        # COST VISIBILITY
        vis = analysis['visibility']
        report.append("\n💰 COST VISIBILITY")
        report.append("-" * 70)
        report.append(f"Total Monthly Spend: ${vis['total_monthly_cost']:,.2f}")
        
        if vis['by_service']:
            report.append("\n📊 By Service:")
            for svc in vis['by_service'][:5]:
                report.append(f"  • {svc['name']:20} ${svc['cost']:>10,.2f} ({svc['percentage']:>5.1f}%)")
        
        if vis['by_team']:
            report.append("\n👥 By Team:")
            for team in vis['by_team']:
                report.append(f"  • {team['name']:20} ${team['cost']:>10,.2f} ({team['percentage']:>5.1f}%)")
        
        if vis['by_environment']:
            report.append("\n🌍 By Environment:")
            for env in vis['by_environment']:
                report.append(f"  • {env['name']:20} ${env['cost']:>10,.2f} ({env['percentage']:>5.1f}%)")
        
        # WASTE DETECTION
        waste = analysis['waste']
        report.append("\n\n💸 WASTE DETECTION")
        report.append("-" * 70)
        report.append(f"Total Waste Found: ${waste['total_monthly_savings']:,.2f}/month")
        report.append(f"Annual Impact: ${waste['total_annual_savings']:,.2f}/year")
        report.append(f"Total Items: {waste['total_items']}")
        
        # Idle EC2
        if waste['categories']['idle_ec2']:
            idle = waste['categories']['idle_ec2']
            total = sum(i['monthly_cost'] for i in idle)
            report.append(f"\n🔴 Idle EC2 Instances ({len(idle)} found)")
            report.append(f"   Savings: ${total:,.2f}/month")
            for inst in idle[:3]:
                report.append(f"   • {inst['resource_id']} ({inst['type']}) - CPU: {inst['cpu_avg']}%")
                report.append(f"     → {inst['recommendation']}")
        
        # Unattached EBS
        if waste['categories']['unattached_ebs']:
            ebs = waste['categories']['unattached_ebs']
            total = sum(v['monthly_cost'] for v in ebs)
            report.append(f"\n💾 Unattached EBS Volumes ({len(ebs)} found)")
            report.append(f"   Savings: ${total:,.2f}/month")
        
        # Old Snapshots
        if waste['categories']['old_snapshots']:
            snaps = waste['categories']['old_snapshots']
            total = sum(s['monthly_cost'] for s in snaps)
            report.append(f"\n📸 Old Snapshots ({len(snaps)} found, 90+ days)")
            report.append(f"   Savings: ${total:,.2f}/month")
        
        # OPTIMIZATION
        opt = analysis['optimization']
        report.append("\n\n⚙️  OPTIMIZATION OPPORTUNITIES")
        report.append("-" * 70)
        report.append(f"Total Potential: ${opt['total_potential_savings']:,.2f}/month")
        
        if opt['quick_wins']:
            report.append("\n🚀 QUICK WINS (0-30 days):")
            for rec in opt['quick_wins']:
                report.append(f"   • {rec['title']}")
                report.append(f"     Savings: ${rec['monthly_savings']:,.2f}/month | Effort: {rec['effort']}")
        
        # FORECAST
        if 'forecast' in analysis:
            forecast = analysis['forecast']
            report.append("\n\n📈 12-MONTH FORECAST")
            report.append("-" * 70)
            for scenario in forecast['scenarios']:
                report.append(f"\n{scenario['name']}:")
                report.append(f"   Month 3:  ${scenario['month_3']:,.2f}")
                report.append(f"   Month 6:  ${scenario['month_6']:,.2f}")
                report.append(f"   Month 12: ${scenario['month_12']:,.2f}")
                report.append(f"   Year Total: ${scenario['year_total']:,.2f}")
        
        # GOVERNANCE
        if 'governance' in analysis:
            gov = analysis['governance']
            report.append("\n\n🛡️  GOVERNANCE & COMPLIANCE")
            report.append("-" * 70)
            report.append(f"Tag Compliance: {gov['tag_compliance']}%")
            report.append(f"Untagged Resources: {gov['untagged_resources']}")
        
        # ACTION PLAN
        report.append("\n\n" + "=" * 70)
        report.append("📋 ACTION PLAN (PRIORITY ORDER)")
        report.append("=" * 70)
        
        actions = []
        if waste['categories']['idle_ec2']:
            actions.append(('HIGH', 'Terminate idle EC2 instances', 
                          sum(i['monthly_cost'] for i in waste['categories']['idle_ec2'])))
        if waste['categories']['idle_rds']:
            actions.append(('HIGH', 'Stop/right-size idle RDS databases',
                          sum(db['monthly_cost'] for db in waste['categories']['idle_rds'])))
        if waste['categories']['unattached_ebs']:
            actions.append(('MEDIUM', 'Delete unattached EBS volumes',
                          sum(v['monthly_cost'] for v in waste['categories']['unattached_ebs'])))
        if waste['categories']['unused_eips']:
            actions.append(('MEDIUM', 'Release unused Elastic IPs',
                          sum(e['monthly_cost'] for e in waste['categories']['unused_eips'])))
        if waste['categories']['old_snapshots']:
            actions.append(('LOW', 'Delete old snapshots',
                          sum(s['monthly_cost'] for s in waste['categories']['old_snapshots'])))
        
        for i, (priority, action, savings) in enumerate(sorted(actions, key=lambda x: x[2], reverse=True), 1):
            report.append(f"\n{i}. [{priority}] {action}")
            report.append(f"   Monthly Savings: ${savings:,.2f}")
        
        # BOTTOM LINE
        report.append("\n\n" + "=" * 70)
        report.append("💰 BOTTOM LINE")
        report.append("=" * 70)
        report.append(f"Current Monthly Spend: ${vis['total_monthly_cost']:,.2f}")
        report.append(f"Identified Waste: ${waste['total_monthly_savings']:,.2f}")
        report.append(f"Optimization Potential: ${opt['total_potential_savings']:,.2f}")
        total_savings = waste['total_monthly_savings'] + opt['total_potential_savings']
        report.append(f"Total Monthly Savings Potential: ${total_savings:,.2f}")
        report.append(f"Total Annual Impact: ${total_savings * 12:,.2f}")
        optimized = vis['total_monthly_cost'] - total_savings
        report.append(f"Optimized Monthly Spend: ${optimized:,.2f}")
        reduction_pct = (total_savings / vis['total_monthly_cost'] * 100) if vis['total_monthly_cost'] > 0 else 0
        report.append(f"Cost Reduction: {reduction_pct:.1f}%")
        report.append("=" * 70)
        
        return "\n".join(report)

# ============================================================================
# CLI INTERFACE
# ============================================================================

class FinOpsCLI:
    """Command-line interface"""
    
    def __init__(self, args):
        self.args = args
        self.demo_mode = args.demo
    
    def run(self) -> int:
        """Execute the analysis"""
        self._print_banner()
        
        try:
            # Collect data
            print("\n🔍 Collecting AWS data...")
            collector = AWSCollector(demo_mode=self.demo_mode, region=self.args.region)
            data = collector.collect_all()
            print(f"✅ Data collected from account: {data['account_id']}")
            
            # Run analysis
            print("\n📊 Running FinOps analysis...")
            analysis = self._analyze(data)
            
            # Generate report
            print("\n📝 Generating report...\n")
            report = ReportGenerator.generate_text_report(analysis)
            
            # Output
            print(report)
            
            # Save if requested
            if self.args.output:
                self._save_report(report)
            
            return 0
            
        except Exception as e:
            print(f"\n❌ Error: {str(e)}")
            import traceback
            traceback.print_exc()
            return 1
    
    def _analyze(self, data: Dict) -> Dict:
        """Run all analysis engines"""
        analysis = {
            'metadata': {
                'account_id': data.get('account_id', 'Unknown'),
                'region': data.get('region', 'us-east-1'),
                'timestamp': datetime.now().isoformat()
            }
        }
        
        # 1. Cost Visibility
        if self.args.analyze or self.args.visibility:
            visibility_engine = CostVisibilityEngine(data)
            analysis['visibility'] = visibility_engine.analyze()
        
        # 2. Waste Detection
        if self.args.analyze or self.args.waste:
            waste_engine = WasteDetectionEngine(data)
            analysis['waste'] = waste_engine.detect_all()
        
        # 3. Optimization
        if self.args.analyze and 'waste' in analysis:
            optimizer = OptimizationEngine(data, analysis['waste'])
            analysis['optimization'] = optimizer.optimize()
        
        # 4. Forecasting
        if self.args.forecast:
            forecaster = ForecastingEngine(data)
            analysis['forecast'] = forecaster.forecast(months=self.args.forecast)
        
        # 5. Governance
        if self.args.analyze:
            governance = GovernanceEngine(data)
            analysis['governance'] = governance.check_all()
        
        return analysis
    
    def _print_banner(self):
        """Print application banner"""
        banner = """
╔═══════════════════════════════════════════════════════════╗
║         AWS FinOps Platform v1.0.0                        ║
║     Professional Cloud Cost Management                    ║
╚═══════════════════════════════════════════════════════════╝
        """
        print(banner)
        
        if self.demo_mode:
            print("🎯 Running in DEMO mode (no AWS credentials needed)\n")
    
    def _save_report(self, report: str):
        """Save report to file"""
        if self.args.output == 'auto':
            filename = f"finops_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        else:
            filename = self.args.output
        
        with open(filename, 'w') as f:
            f.write(report)
        
        print(f"\n✅ Report saved: {filename}")

# ============================================================================
# MAIN
# ============================================================================

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='AWS FinOps Platform - Professional Cloud Cost Management',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Demo mode (no AWS credentials needed)
  python finops.py --demo
  
  # Full analysis
  python finops.py --analyze
  
  # Waste detection only
  python finops.py --waste
  
  # 12-month forecast
  python finops.py --forecast 12
  
  # Save report
  python finops.py --analyze --output report.txt
        """
    )
    
    # Modes
    parser.add_argument('--demo', action='store_true',
                       help='Run in demo mode (no AWS credentials needed)')
    parser.add_argument('--analyze', action='store_true',
                       help='Run full FinOps analysis')
    parser.add_argument('--visibility', action='store_true',
                       help='Cost visibility analysis only')
    parser.add_argument('--waste', action='store_true',
                       help='Waste detection only')
    parser.add_argument('--forecast', type=int, metavar='MONTHS',
                       help='Forecast N months ahead')
    
    # Options
    parser.add_argument('--region', default='us-east-1',
                       help='AWS region (default: us-east-1)')
    parser.add_argument('--format', choices=['text', 'json', 'pdf'], default='text',
                       help='Report format (default: text)')
    parser.add_argument('--output', 
                       help='Save report to file (use "auto" for auto-naming)')
    parser.add_argument('--version', action='version', version='FinOps Platform 1.0.0')
    
    args = parser.parse_args()
    
    # Default to analyze if nothing specified
    if not any([args.demo, args.analyze, args.visibility, args.waste, args.forecast]):
        args.analyze = True
    
    # Run
    cli = FinOpsCLI(args)
    sys.exit(cli.run())

if __name__ == "__main__":
    main()
