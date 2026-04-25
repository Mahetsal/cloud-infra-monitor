"""
Cost Monitor using AWS Cost Explorer.
Tracks daily spend, monthly forecasts, and identifies
anomalies or budget breaches.
"""

import boto3
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


class CostMonitor:
    """Analyze AWS costs and usage."""
    
    def __init__(self, region: str = "us-east-1"):
        # Cost Explorer is a global service, but we specify a region
        self.ce = boto3.client("ce", region_name=region)
        self.region = region
    
    def get_daily_costs(self, days: int = 7) -> list[dict]:
        """Get daily costs for the last N days."""
        end_date = datetime.utcnow().date()
        start_date = end_date - timedelta(days=days)
        
        response = self.ce.get_cost_and_usage(
            TimePeriod={
                "Start": start_date.isoformat(),
                "End": end_date.isoformat()
            },
            Granularity="DAILY",
            Metrics=["UnblendedCost"]
        )
        
        results = []
        for day in response["ResultsByTime"]:
            amount = float(day["Total"]["UnblendedCost"]["Amount"])
            unit = day["Total"]["UnblendedCost"]["Unit"]
            results.append({
                "date": day["TimePeriod"]["Start"],
                "amount": round(amount, 2),
                "unit": unit
            })
        
        return results
    
    def get_monthly_forecast(self) -> dict:
        """Forecast cost for the remainder of the current month."""
        today = datetime.utcnow().date()
        if today.day == 1:
            return {"forecast": 0, "unit": "USD"}
            
        # End of current month
        if today.month == 12:
            end_of_month = today.replace(year=today.year + 1, month=1, day=1)
        else:
            end_of_month = today.replace(month=today.month + 1, day=1)
            
        try:
            response = self.ce.get_cost_forecast(
                TimePeriod={
                    "Start": (today + timedelta(days=1)).isoformat(),
                    "End": end_of_month.isoformat()
                },
                Metric="UNBLENDED_COST",
                Granularity="MONTHLY"
            )
            
            return {
                "forecast": round(float(response["Total"]["Amount"]), 2),
                "unit": response["Total"]["Unit"]
            }
        except Exception as e:
            logger.error(f"Could not get forecast: {e}")
            return {"forecast": None, "error": str(e)}
    
    def get_service_breakdown(self, days: int = 30) -> list[dict]:
        """Break down costs by AWS service."""
        end_date = datetime.utcnow().date()
        start_date = end_date - timedelta(days=days)
        
        response = self.ce.get_cost_and_usage(
            TimePeriod={
                "Start": start_date.isoformat(),
                "End": end_date.isoformat()
            },
            Granularity="MONTHLY",
            Metrics=["UnblendedCost"],
            GroupBy=[{"Type": "DIMENSION", "Key": "SERVICE"}]
        )
        
        breakdown = []
        for result in response["ResultsByTime"]:
            for group in result["Groups"]:
                service_name = group["Keys"][0]
                amount = float(group["Metrics"]["UnblendedCost"]["Amount"])
                if amount > 0.01:  # Only include services with actual cost
                    breakdown.append({
                        "service": service_name,
                        "cost": round(amount, 2)
                    })
        
        # Sort by cost descending
        breakdown.sort(key=lambda x: x["cost"], reverse=True)
        return breakdown
