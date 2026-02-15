# AWS FinOps Platform - Created and Maintained by Ali Hashmi 

[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

**Professional-grade AWS FinOps platform for cloud cost optimization and financial management.**

Detects waste, optimizes spend, forecasts costs, and enforces governance across your AWS infrastructure.

---

## Features

### Cost Visibility
- Multi-dimensional cost breakdown (Service, Team, Environment, Application)
- Historical trend analysis
- Budget vs actual tracking
- Unit economics (cost per customer, per transaction)

### Waste Detection
- **Compute:** Idle EC2 (<5% CPU), stopped instances, over-provisioned resources
- **Storage:** Unattached EBS volumes, old snapshots (90+ days), unused EIPs
- **Database:** Idle RDS instances, underutilized capacity
- **Network:** Unused NAT Gateways, data transfer inefficiencies

### Optimization Engine
- Right-sizing recommendations (CPU/Memory analysis)
- Reserved Instance & Savings Plan optimization
- Storage class recommendations (S3, EBS)
- Architecture improvements (serverless migration candidates)
- Graviton2/3 migration opportunities

### Cost Forecasting
- ML-based predictions (3/6/12/24 month forecasts)
- Scenario modeling (baseline, conservative, aggressive optimization)
- Growth impact analysis
- Confidence intervals

### Governance & Control
- Tag compliance checking
- Budget threshold alerts
- Policy violation detection
- Anomaly detection (unusual spend spikes)
- Auto-remediation capabilities

### Professional Reporting
- Executive summaries (PDF/HTML)
- Detailed analysis reports
- CSV export for automation
- Action plans with ROI calculations

---

## Quick Start

```bash
# Clone the repository
git clone https://github.com/aliihashmiii/aws-finops-platform.git
cd aws-finops-platform

# Install dependencies
pip install -r requirements.txt

# Run in DEMO mode (no AWS credentials needed!)
python finops.py --demo

# Or analyze your real AWS account
aws configure  # Configure AWS credentials first
python finops.py --analyze
```

---

## Sample Output

```
═══════════════════════════════════════════════════════════════
AWS FINOPS ANALYSIS REPORT
═══════════════════════════════════════════════════════════════

💰 EXECUTIVE SUMMARY
Current Monthly Spend: $45,234.50
Identified Waste: $13,450.00 (29.7%)
Annual Impact: $161,400.00

TOP WASTE SOURCES
1. Idle EC2 Instances (12)          → $4,200/month
2. Unattached EBS Volumes (45)      → $1,800/month
3. Over-provisioned RDS (5)         → $3,250/month
4. Old Snapshots (280)              → $2,850/month

QUICK WINS (This Week)
✓ Terminate idle instances          → $4,200/month
✓ Delete unattached volumes         → $1,800/month
✓ Right-size RDS databases          → $3,250/month

Total 30-Day Impact: $9,250/month ($111,000/year)

12-MONTH FORECAST
Baseline (no optimization):         $652,000
With optimization (30%):            $456,000
Projected Savings:                  $196,000
═══════════════════════════════════════════════════════════════
```

---

## Architecture

```
aws-finops-platform/
├── finops.py                  # Main CLI (single entry point)
├── requirements.txt           # Python dependencies
├── config.yaml               # Configuration file
│
├── src/
│   ├── collectors/           # AWS data collection
│   │   ├── cost_data.py      # Cost Explorer integration
│   │   ├── resource_data.py  # EC2, EBS, RDS, etc.
│   │   └── metrics_data.py   # CloudWatch metrics
│   │
│   ├── analyzers/            # Analysis engines
│   │   ├── cost_analyzer.py  # Cost visibility
│   │   ├── waste_detector.py # Waste identification
│   │   ├── optimizer.py      # Optimization recommendations
│   │   └── forecaster.py     # ML-based forecasting
│   │
│   ├── reporting/            # Report generation
│   │   ├── text_report.py    # Console output
│   │   ├── pdf_report.py     # PDF generation
│   │   └── html_report.py    # HTML dashboards
│   │
│   └── utils/                # Utilities
│       ├── aws_pricing.py    # AWS pricing data
│       └── helpers.py        # Common functions
│
├── tests/                    # Test suite
│   └── test_*.py            # Unit tests
│
└── docs/                     # Documentation
    ├── INSTALLATION.md       # Setup guide
    ├── USAGE.md             # User manual
    └── API.md               # API reference
```

---

## Usage

### Basic Commands

```bash
# Full analysis
python finops.py --analyze

# Cost visibility only
python finops.py --visibility

# Waste detection
python finops.py --waste

# 12-month forecast
python finops.py --forecast 12

# Generate PDF report
python finops.py --analyze --format pdf --output report.pdf
```

### Advanced Options

```bash
# Specific region
python finops.py --analyze --region us-east-1

# Filter by tag
python finops.py --analyze --tag Environment=Production

# Export JSON
python finops.py --analyze --format json --output data.json

# Demo mode (no AWS credentials)
python finops.py --demo
```

---

## 🔧 Configuration

Edit `config.yaml`:

```yaml
aws:
  regions:
    - us-east-1
    - us-west-2
  
analysis:
  idle_cpu_threshold: 5.0
  idle_days: 7
  snapshot_age_days: 90

budgets:
  engineering: 20000
  data_science: 18000
  infrastructure: 8000

tagging:
  required_tags:
    - Environment
    - Team
    - CostCenter
```

---

## Documentation

- **[Installation Guide](docs/INSTALLATION.md)** - Setup instructions
- **[Usage Guide](docs/USAGE.md)** - Complete user manual
- **[API Reference](docs/API.md)** - Developer documentation
- **[Examples](examples/)** - Sample outputs and use cases

---

## Use Cases

### For Startups
- Track burn rate and extend runway
- Optimize cost per customer
- Prepare for investor meetings

### For Enterprises
- Multi-account cost allocation
- Showback/chargeback reporting
- Compliance and governance

### For Consultants
- Client cost audits
- ROI demonstration
- Ongoing optimization services

---

## Security

- **Read-only AWS access** - Never modifies infrastructure
- **No data storage** - Analysis happens on-demand
- **Credential security** - Uses standard AWS SDK authentication
- **IAM best practices** - Minimal required permissions

### Required IAM Permissions

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "ce:GetCostAndUsage",
        "ce:GetCostForecast",
        "ec2:Describe*",
        "rds:Describe*",
        "s3:ListBucket",
        "cloudwatch:GetMetricStatistics"
      ],
      "Resource": "*"
    }
  ]
}
```

---

## Contributing

Contributions welcome! Please read [CONTRIBUTING.md](CONTRIBUTING.md) first.

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## 📄 License

This project is licensed under the MIT License - see [LICENSE](LICENSE) file.

---

## 🙏 Acknowledgments

Built with insights from:
- [FinOps Foundation](https://www.finops.org/) best practices
- [AWS Cost Optimization](https://aws.amazon.com/aws-cost-management/) resources
- Open-source FinOps community tools

---

## 📞 Support

- **Issues:** [GitHub Issues](https://github.com/aliihashmiii/aws-finops-platform/issues)
- **Discussions:** [GitHub Discussions](https://github.com/aliihashmiii/aws-finops-platform/discussions)
- **Email:** alihashmi.1@outlook.com

---

## Roadmap

- [x] Core FinOps engine (6 capabilities)
- [x] CLI interface
- [x] Demo mode
- [ ] Web dashboard (React)
- [ ] Multi-account support (AWS Organizations)
- [ ] Azure & GCP support
- [ ] Slack/Teams integration
- [ ] API server mode
- [ ] Terraform integration

---

## Why This Project?

Cloud costs can spiral out of control quickly. Most companies waste 20-40% of their cloud budget on:
- Resources left running 24/7 when only needed 8 hours
- Over-provisioned instances (paying for capacity you don't use)
- Orphaned resources (volumes, snapshots from deleted instances)
- Lack of Reserved Instance/Savings Plan optimization

This platform helps you take control through:
- **Automated detection** of waste
- **Data-driven recommendations** 
- **Financial forecasting** to prevent surprises
- **Governance enforcement** to prevent future waste

---

<div align="center">

### ⭐ If this saves you money, please star the repo! ⭐

**Built as a self product while learning**

</div>
