"""
Usage statistics resource
"""

from typing import Dict, Any
import json
from datetime import datetime, timedelta

from ..tools.usage import get_tracker
from ..config import load_usage_stats


def get_usage_stats_resource() -> str:
    """
    Get usage statistics resource content

    Returns:
        JSON string with usage statistics
    """
    tracker = get_tracker()
    stats = load_usage_stats()

    # Calculate daily and monthly stats
    today = datetime.utcnow().date().isoformat()
    this_month = datetime.utcnow().strftime("%Y-%m")

    daily_stats = {
        "requests": 0,
        "input_tokens": 0,
        "output_tokens": 0,
        "cost": 0.0
    }

    monthly_stats = {
        "requests": 0,
        "input_tokens": 0,
        "output_tokens": 0,
        "cost": 0.0
    }

    provider_breakdown = []

    for provider, provider_stats in stats.get("providers", {}).items():
        provider_daily = 0.0
        provider_monthly = 0.0

        for date, date_stats in provider_stats.get("requests_by_date", {}).items():
            if date == today:
                daily_stats["requests"] += date_stats["requests"]
                daily_stats["input_tokens"] += date_stats["input_tokens"]
                daily_stats["output_tokens"] += date_stats["output_tokens"]
                daily_stats["cost"] += date_stats["cost"]
                provider_daily = date_stats["cost"]

            if date.startswith(this_month):
                monthly_stats["requests"] += date_stats["requests"]
                monthly_stats["input_tokens"] += date_stats["input_tokens"]
                monthly_stats["output_tokens"] += date_stats["output_tokens"]
                monthly_stats["cost"] += date_stats["cost"]
                provider_monthly += date_stats["cost"]

        provider_breakdown.append({
            "provider": provider,
            "total_requests": provider_stats["total_requests"],
            "total_cost": provider_stats["total_cost"],
            "daily_cost": provider_daily,
            "monthly_cost": provider_monthly,
            "success_rate": (
                provider_stats["successes"] / provider_stats["total_requests"] * 100
                if provider_stats["total_requests"] > 0 else 0
            )
        })

    # Get budget status
    budget_status = tracker.check_budget()

    result = {
        "summary": {
            "total_requests": stats.get("total_requests", 0),
            "total_input_tokens": stats.get("total_input_tokens", 0),
            "total_output_tokens": stats.get("total_output_tokens", 0),
            "total_cost": stats.get("total_cost", 0.0),
            "last_reset": stats.get("last_reset")
        },
        "daily": daily_stats,
        "monthly": monthly_stats,
        "providers": provider_breakdown,
        "budget": budget_status if budget_status.get("budget_enabled") else None,
        "generated_at": datetime.utcnow().isoformat()
    }

    return json.dumps(result, indent=2)
