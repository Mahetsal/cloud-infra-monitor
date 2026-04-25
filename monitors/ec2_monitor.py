"""
EC2 Instance Monitor.
Tracks instance status, CPU utilization, and cost metrics
using the AWS EC2 and CloudWatch APIs.
"""

import boto3
from datetime import datetime, timedelta
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class EC2Monitor:
    """Monitor EC2 instances for health, performance, and cost."""
    
    def __init__(self, region: str = "us-east-1"):
        self.ec2 = boto3.client("ec2", region_name=region)
        self.cloudwatch = boto3.client("cloudwatch", region_name=region)
        self.region = region
    
    def get_all_instances(self) -> list[dict]:
        """Get status of all EC2 instances in the region."""
        response = self.ec2.describe_instances()
        instances = []
        
        for reservation in response["Reservations"]:
            for instance in reservation["Instances"]:
                name = ""
                for tag in instance.get("Tags", []):
                    if tag["Key"] == "Name":
                        name = tag["Value"]
                        break
                
                instances.append({
                    "id": instance["InstanceId"],
                    "name": name,
                    "type": instance["InstanceType"],
                    "state": instance["State"]["Name"],
                    "launch_time": instance.get("LaunchTime", "").isoformat()
                        if instance.get("LaunchTime") else None,
                    "public_ip": instance.get("PublicIpAddress"),
                    "private_ip": instance.get("PrivateIpAddress"),
                    "vpc_id": instance.get("VpcId"),
                    "subnet_id": instance.get("SubnetId"),
                    "platform": instance.get("Platform", "linux"),
                })
        
        return instances
    
    def get_cpu_utilization(
        self,
        instance_id: str,
        hours: int = 1
    ) -> dict:
        """
        Get CPU utilization metrics for an instance.
        
        Returns:
            Dict with average, max, and min CPU percentages.
        """
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(hours=hours)
        
        response = self.cloudwatch.get_metric_statistics(
            Namespace="AWS/EC2",
            MetricName="CPUUtilization",
            Dimensions=[
                {"Name": "InstanceId", "Value": instance_id}
            ],
            StartTime=start_time,
            EndTime=end_time,
            Period=300,  # 5-minute intervals
            Statistics=["Average", "Maximum", "Minimum"],
        )
        
        datapoints = response.get("Datapoints", [])
        if not datapoints:
            return {"average": 0, "maximum": 0, "minimum": 0, "datapoints": 0}
        
        averages = [dp["Average"] for dp in datapoints]
        maximums = [dp["Maximum"] for dp in datapoints]
        minimums = [dp["Minimum"] for dp in datapoints]
        
        return {"average": round(sum(averages) / len(averages), 2), "maximum": round(max(maximums), 2), "minimum": round(min(minimums), 2), "datapoints": len(datapoints)}
    
    def get_network_metrics(
        self,
        instance_id: str,
        hours: int = 1
    ) -> dict:
        """Get network I/O metrics for an instance."""
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(hours=hours)
        
        metrics = {}
        for metric_name in ["NetworkIn", "NetworkOut"]:
            response = self.cloudwatch.get_metric_statistics(
                Namespace="AWS/EC2",
                MetricName=metric_name,
                Dimensions=[
                    {"Name": "InstanceId", "Value": instance_id}
                ],
                StartTime=start_time,
                EndTime=end_time,
                Period=300,
                Statistics=["Sum"],
            )
            
            datapoints = response.get("Datapoints", [])
            total_bytes = sum(dp["Sum"] for dp in datapoints) if datapoints else 0
            metrics[metric_name.lower()] = round(total_bytes / (1024 * 1024), 2)  # MB
        
        return {"network_in_mb": metrics.get("networkin", 0), "network_out_mb": metrics.get("networkout", 0)}
    
    def find_idle_instances(
        self,
        cpu_threshold: float = 5.0,
        hours: int = 24
    ) -> list[dict]:
        """
        Find instances with consistently low CPU usage.
        These are candidates for downsizing or termination.
        """
        instances = self.get_all_instances()
        idle = []
        
        for instance in instances:
            if instance["state"] != "running":
                continue
            
            cpu = self.get_cpu_utilization(instance["id"], hours=hours)
            if cpu["average"] < cpu_threshold and cpu["datapoints"] > 0:
                idle.append({
                    **instance,
                    "avg_cpu": cpu["average"],
                    "recommendation": "Consider stopping or downsizing this instance",
                })
        
        return idle
    
    def get_summary(self) -> dict:
        """Get a high-level summary of all EC2 resources."""
        instances = self.get_all_instances()
        
        state_counts = {}
        for inst in instances:
            state = inst["state"]
            state_counts[state] = state_counts.get(state, 0) + 1
        
        type_counts = {}
        for inst in instances:
            if inst["state"] == "running":
                itype = inst["type"]
                type_counts[itype] = type_counts.get(itype, 0) + 1
        
        return {
            "total_instances": len(instances),
            "state_breakdown": state_counts,
            "instance_types": type_counts,
            "region": self.region,
            "timestamp": datetime.utcnow().isoformat(),
              }
