"""
Cloud Infrastructure Monitor Main Entry Point.
Orchestrates the monitoring of various AWS resources
and generates reports/alerts.
"""

import argparse
import logging
import sys
from datetime import datetime

from monitors.ec2_monitor import EC2Monitor
from monitors.s3_monitor import S3Monitor
from monitors.cost_monitor import CostMonitor

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('monitor.log')
    ]
)
logger = logging.getLogger(__name__)


def run_monitoring(region="us-east-1", services=None):
    """Run monitoring tasks for specified services."""
    if not services:
        services = ["ec2", "s3", "cost"]
    
    logger.info(f"Starting cloud monitoring in region {region} for services: {services}")
    report = {
        "timestamp": datetime.utcnow().isoformat(),
        "region": region,
        "results": {}
    }

    if "ec2" in services:
        logger.info("Monitoring EC2 instances...")
        ec2 = EC2Monitor(region=region)
        report["results"]["ec2"] = ec2.get_summary()
        
        # Check for idle instances
        idle = ec2.find_idle_instances()
        if idle:
            logger.warning(f"Found {len(idle)} idle EC2 instances")
            report["results"]["ec2"]["alerts"] = [
                f"Instance {i['id']} is idle" for i in idle
            ]

    if "s3" in services:
        logger.info("Monitoring S3 buckets...")
        s3 = S3Monitor(region=region)
        report["results"]["s3"] = s3.get_summary()

    if "cost" in services:
        logger.info("Analyzing AWS costs...")
        cost = CostMonitor(region=region)
        report["results"]["cost"] = {
            "daily_costs": cost.get_daily_costs(7),
            "forecast": cost.get_monthly_forecast(),
            "service_breakdown": cost.get_service_breakdown()
        }

    logger.info("Monitoring cycle complete.")
    return report


def main():
    parser = argparse.ArgumentParser(description="Cloud Infrastructure Monitor")
    parser.add_argument(
        "--region", 
        default="us-east-1", 
        help="AWS region to monitor"
    )
    parser.add_argument(
        "--services", 
        nargs="*", 
        help="Specific services to monitor (ec2, s3, cost)"
    )
    
    args = parser.parse_args()
    
    try:
        report = run_monitoring(region=args.region, services=args.services)
        print("
--- Monitoring Report ---")
        print(f"Time: {report['timestamp']}")
        print(f"Region: {report['region']}")
        
        if "ec2" in report["results"]:
            ec2 = report["results"]["ec2"]
            print(f"EC2: {ec2['total_instances']} total, {ec2['state_breakdown'].get('running', 0)} running")
            
        if "s3" in report["results"]:
            s3 = report["results"]["s3"]
            print(f"S3: {s3['total_buckets']} buckets, {s3['total_size_gb']} GB total")
            
    except Exception as e:
        logger.error(f"Monitoring failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
