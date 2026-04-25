"""
S3 Bucket Monitor.
Tracks bucket sizes, object counts, access patterns,
and identifies cost optimization opportunities.
"""

import boto3
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class S3Monitor:
    """Monitor S3 buckets for size, cost, and security."""
    
    def __init__(self, region: str = "us-east-1"):
        self.s3 = boto3.client("s3", region_name=region)
        self.cloudwatch = boto3.client("cloudwatch", region_name=region)
        self.region = region
    
    def list_buckets(self) -> list[dict]:
        """List all S3 buckets with basic metadata."""
        response = self.s3.list_buckets()
        
        buckets = []
        for bucket in response.get("Buckets", []):
            buckets.append({
                "name": bucket["Name"],
                "created": bucket["CreationDate"].isoformat(),
            })
        
        return buckets
    
    def get_bucket_size(self, bucket_name: str) -> dict:
        """
        Calculate total size and object count for a bucket.
        Uses CloudWatch metrics for efficiency on large buckets.
        """
        try:
            # Use CloudWatch for bucket-level metrics
            response = self.cloudwatch.get_metric_statistics(
                Namespace="AWS/S3",
                MetricName="BucketSizeBytes",
                Dimensions=[
                    {"Name": "BucketName", "Value": bucket_name},
                    {"Name": "StorageType", "Value": "StandardStorage"},
                ],
                StartTime=datetime.utcnow().replace(hour=0, minute=0, second=0),
                EndTime=datetime.utcnow(),
                Period=86400,
                Statistics=["Average"],
            )
            
            datapoints = response.get("Datapoints", [])
            size_bytes = datapoints[0]["Average"] if datapoints else 0
            
            # Get object count
            count_response = self.cloudwatch.get_metric_statistics(
                Namespace="AWS/S3",
                MetricName="NumberOfObjects",
                Dimensions=[
                    {"Name": "BucketName", "Value": bucket_name},
                    {"Name": "StorageType", "Value": "AllStorageTypes"},
                ],
                StartTime=datetime.utcnow().replace(hour=0, minute=0, second=0),
                EndTime=datetime.utcnow(),
                Period=86400,
                Statistics=["Average"],
            )
            
            count_datapoints = count_response.get("Datapoints", [])
            object_count = int(count_datapoints[0]["Average"]) if count_datapoints else 0
            
            return {
                "bucket": bucket_name,
                "size_bytes": size_bytes,
                "size_gb": round(size_bytes / (1024 ** 3), 2),
                "object_count": object_count,
            }
            
        except Exception as e:
            logger.error(f"Error getting size for {bucket_name}: {e}")
            return {
                "bucket": bucket_name,
                "size_bytes": 0,
                "size_gb": 0,
                "object_count": 0,
                "error": str(e),
            }
    
    def check_public_access(self, bucket_name: str) -> dict:
        """Check if a bucket has public access enabled (security check)."""
        try:
            acl = self.s3.get_bucket_acl(Bucket=bucket_name)
            
            is_public = False
            for grant in acl.get("Grants", []):
                grantee = grant.get("Grantee", {})
                uri = grantee.get("URI", "")
                if "AllUsers" in uri or "AuthenticatedUsers" in uri:
                    is_public = True
                    break
            
            return {
                "bucket": bucket_name,
                "is_public": is_public,
                "risk_level": "HIGH" if is_public else "LOW",
            }
            
        except Exception as e:
            return {
                "bucket": bucket_name,
                "is_public": None,
                "error": str(e),
            }
    
    def check_versioning(self, bucket_name: str) -> dict:
        """Check bucket versioning status."""
        try:
            response = self.s3.get_bucket_versioning(Bucket=bucket_name)
            status = response.get("Status", "Disabled")
            
            return {
                "bucket": bucket_name,
                "versioning": status,
                "recommendation": (
                    "Enable versioning for data protection"
                    if status != "Enabled" else "Versioning is properly configured"
                ),
            }
        except Exception as e:
            return {"bucket": bucket_name, "error": str(e)}
    
    def get_summary(self) -> dict:
        """Get overview of all S3 buckets."""
        buckets = self.list_buckets()
        total_size = 0
        total_objects = 0
        public_buckets = []
        
        for bucket in buckets:
            size_info = self.get_bucket_size(bucket["name"])
            total_size += size_info.get("size_bytes", 0)
            total_objects += size_info.get("object_count", 0)
            
            access = self.check_public_access(bucket["name"])
            if access.get("is_public"):
                public_buckets.append(bucket["name"])
        
        return {
            "total_buckets": len(buckets),
            "total_size_gb": round(total_size / (1024 ** 3), 2),
            "total_objects": total_objects,
            "public_buckets": public_buckets,
            "security_alerts": len(public_buckets),
            "timestamp": datetime.utcnow().isoformat(),
  }
