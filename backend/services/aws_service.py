"""AWS domain service facade.

The unified engine owns cross-platform aggregation; this facade keeps AWS integration discoverable
and is the extension point for Cost Explorer, CloudWatch, EC2, EBS, Elastic IP, and RDS collectors.
"""

from finops.aws.collector import AWSCollector

__all__ = ["AWSCollector"]
