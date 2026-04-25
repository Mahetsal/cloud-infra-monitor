# ☁️ Cloud Infrastructure Monitor

A Python-based AWS infrastructure monitoring toolkit that tracks EC2 instances, S3 buckets, Lambda functions, and costs — with automated alerts and a clean dashboard.

![Python](https://img.shields.io/badge/Python-3.11-blue?logo=python)
![AWS](https://img.shields.io/badge/AWS-EC2%20%7C%20S3%20%7C%20Lambda-orange?logo=amazon-aws)
![Docker](https://img.shields.io/badge/Docker-Ready-blue?logo=docker)
![License](https://img.shields.io/badge/License-MIT-green)

## 🏗️ Architecture

```
┌───────────────────────────────────────────────┐
│              Cloud Infra Monitor              │
├─────────────┬─────────────┬───────────────────┤
│  EC2 Monitor│  S3 Monitor │  Lambda Monitor   │
│  - Status   │  - Size     │  - Invocations    │
│  - CPU/Mem  │  - Objects  │  - Errors         │
│  - Costs    │  - Costs    │  - Duration       │
├─────────────┴─────────────┴───────────────────┤
│              Cost Analyzer                    │
│  - Daily/Monthly spend tracking               │
│  - Budget alerts via SNS                      │
│  - Cost optimization recommendations          │
├───────────────────────────────────────────────┤
│              Dashboard (HTML/JS)              │
│  - Real-time resource overview                │
│  - Cost graphs and trends                     │
│  - Alert history                              │
└───────────────────────────────────────────────┘
```

## ✨ Features

- **Multi-service monitoring** — EC2, S3, Lambda, RDS, and CloudWatch metrics
- **Cost tracking** — Daily and monthly spend analysis with budget alerts
- **Smart alerts** — SNS notifications for threshold breaches
- **Cost optimization** — Identifies idle resources, oversized instances, unused volumes
- **Dashboard** — Lightweight HTML dashboard with auto-refresh
- **Docker support** — Run as a containerized service
- **Exportable reports** — JSON and CSV report generation

## 📁 Project Structure

```
cloud-infra-monitor/
├── monitors/
│   ├── __init__.py
│   ├── ec2_monitor.py          # EC2 instance monitoring
│   ├── s3_monitor.py           # S3 bucket analysis
│   ├── lambda_monitor.py       # Lambda function metrics
│   └── cost_monitor.py         # Cost Explorer integration
├── alerts/
│   ├── __init__.py
│   └── sns_alerter.py          # SNS notification system
├── dashboard/
│   ├── index.html              # Monitoring dashboard
│   ├── style.css               # Dashboard styling
│   └── dashboard.js            # Real-time updates
├── reports/
│   └── report_generator.py     # CSV/JSON report export
├── main.py                     # Entry point / scheduler
├── config.yaml                 # Configuration file
├── requirements.txt
├── Dockerfile
├── .gitignore
├── LICENSE
└── README.md
```

## 🚀 Quick Start

```bash
# Clone
git clone https://github.com/saleh-alkhrisat/cloud-infra-monitor.git
cd cloud-infra-monitor

# Install dependencies
pip install -r requirements.txt

# Configure
cp config.yaml.example config.yaml
# Edit config.yaml with your AWS settings

# Run
python main.py

# Or run with Docker
docker build -t cloud-monitor .
docker run -e AWS_ACCESS_KEY_ID=xxx -e AWS_SECRET_ACCESS_KEY=xxx cloud-monitor
```

## 🔧 Configuration

```yaml
# config.yaml
aws:
  region: us-east-1
  profile: default

monitoring:
  interval_minutes: 5
  
  ec2:
    enabled: true
    cpu_threshold: 80
    memory_threshold: 85
    
  s3:
    enabled: true
    size_alert_gb: 100
    
  lambda:
    enabled: true
    error_rate_threshold: 5
    duration_threshold_ms: 10000

alerts:
  sns_topic_arn: arn:aws:sns:us-east-1:123456789:infra-alerts
  email: admin@example.com

costs:
  monthly_budget: 500
  alert_at_percentage: 80
```

## 📝 License

MIT License — see [LICENSE](LICENSE) for details.
