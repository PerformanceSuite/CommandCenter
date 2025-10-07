"""
Usage tracking and cost estimation tools
"""

from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from collections import defaultdict

from ..config import load_usage_stats, save_usage_stats, load_routing_config


class UsageTracker:
    """Track API usage and estimate costs"""

    def __init__(self):
        self.stats = load_usage_stats()
        self.routing_config = load_routing_config()

    def _ensure_provider_stats(self, provider: str) -> None:
        """Ensure provider exists in stats"""
        if provider not in self.stats["providers"]:
            self.stats["providers"][provider] = {
                "total_requests": 0,
                "total_input_tokens": 0,
                "total_output_tokens": 0,
                "total_cost": 0.0,
                "first_request": datetime.utcnow().isoformat(),
                "last_request": None,
                "requests_by_date": {},
                "errors": 0,
                "successes": 0
            }

    def track_request(
        self,
        provider: str,
        input_tokens: int,
        output_tokens: int,
        model: str,
        success: bool = True
    ) -> Dict[str, Any]:
        """
        Track an API request

        Args:
            provider: Provider name
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens
            model: Model name used
            success: Whether request was successful

        Returns:
            Updated stats
        """
        self._ensure_provider_stats(provider)

        # Get cost rates
        provider_config = self.routing_config["providers"].get(provider, {})
        input_cost_rate = provider_config.get("cost_per_1k_input_tokens", 0.0)
        output_cost_rate = provider_config.get("cost_per_1k_output_tokens", 0.0)

        # Calculate cost
        input_cost = (input_tokens / 1000) * input_cost_rate
        output_cost = (output_tokens / 1000) * output_cost_rate
        total_cost = input_cost + output_cost

        # Update provider stats
        provider_stats = self.stats["providers"][provider]
        provider_stats["total_requests"] += 1
        provider_stats["total_input_tokens"] += input_tokens
        provider_stats["total_output_tokens"] += output_tokens
        provider_stats["total_cost"] += total_cost
        provider_stats["last_request"] = datetime.utcnow().isoformat()

        if success:
            provider_stats["successes"] += 1
        else:
            provider_stats["errors"] += 1

        # Track by date
        today = datetime.utcnow().date().isoformat()
        if today not in provider_stats["requests_by_date"]:
            provider_stats["requests_by_date"][today] = {
                "requests": 0,
                "input_tokens": 0,
                "output_tokens": 0,
                "cost": 0.0
            }

        daily_stats = provider_stats["requests_by_date"][today]
        daily_stats["requests"] += 1
        daily_stats["input_tokens"] += input_tokens
        daily_stats["output_tokens"] += output_tokens
        daily_stats["cost"] += total_cost

        # Update global stats
        self.stats["total_requests"] += 1
        self.stats["total_input_tokens"] += input_tokens
        self.stats["total_output_tokens"] += output_tokens
        self.stats["total_cost"] += total_cost

        # Save stats
        save_usage_stats(self.stats)

        return {
            "success": True,
            "provider": provider,
            "model": model,
            "tokens_used": input_tokens + output_tokens,
            "cost": total_cost,
            "total_cost_to_date": provider_stats["total_cost"]
        }

    def get_usage_stats(
        self,
        provider: Optional[str] = None,
        days: int = 30
    ) -> Dict[str, Any]:
        """
        Get usage statistics

        Args:
            provider: Filter by provider (None for all)
            days: Number of days to include in recent stats

        Returns:
            Usage statistics
        """
        cutoff_date = (datetime.utcnow() - timedelta(days=days)).date().isoformat()

        if provider:
            if provider not in self.stats["providers"]:
                return {
                    "success": False,
                    "error": f"No usage data for provider: {provider}"
                }

            provider_stats = self.stats["providers"][provider]

            # Calculate recent stats
            recent_requests = 0
            recent_input_tokens = 0
            recent_output_tokens = 0
            recent_cost = 0.0

            for date, daily_stats in provider_stats.get("requests_by_date", {}).items():
                if date >= cutoff_date:
                    recent_requests += daily_stats["requests"]
                    recent_input_tokens += daily_stats["input_tokens"]
                    recent_output_tokens += daily_stats["output_tokens"]
                    recent_cost += daily_stats["cost"]

            return {
                "success": True,
                "provider": provider,
                "total_requests": provider_stats["total_requests"],
                "total_input_tokens": provider_stats["total_input_tokens"],
                "total_output_tokens": provider_stats["total_output_tokens"],
                "total_cost": provider_stats["total_cost"],
                "recent_stats": {
                    "days": days,
                    "requests": recent_requests,
                    "input_tokens": recent_input_tokens,
                    "output_tokens": recent_output_tokens,
                    "cost": recent_cost
                },
                "success_rate": (
                    provider_stats["successes"] / provider_stats["total_requests"] * 100
                    if provider_stats["total_requests"] > 0 else 0
                ),
                "first_request": provider_stats.get("first_request"),
                "last_request": provider_stats.get("last_request")
            }
        else:
            # All providers summary
            providers_summary = []
            for prov, prov_stats in self.stats["providers"].items():
                providers_summary.append({
                    "provider": prov,
                    "total_requests": prov_stats["total_requests"],
                    "total_cost": prov_stats["total_cost"],
                    "success_rate": (
                        prov_stats["successes"] / prov_stats["total_requests"] * 100
                        if prov_stats["total_requests"] > 0 else 0
                    )
                })

            return {
                "success": True,
                "total_requests": self.stats["total_requests"],
                "total_input_tokens": self.stats["total_input_tokens"],
                "total_output_tokens": self.stats["total_output_tokens"],
                "total_cost": self.stats["total_cost"],
                "providers": providers_summary,
                "provider_count": len(self.stats["providers"])
            }

    def estimate_cost(
        self,
        provider: str,
        input_tokens: int,
        output_tokens: int,
        model: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Estimate cost for a request

        Args:
            provider: Provider name
            input_tokens: Estimated input tokens
            output_tokens: Estimated output tokens
            model: Model name (optional)

        Returns:
            Cost estimation
        """
        if provider not in self.routing_config["providers"]:
            return {
                "success": False,
                "error": f"Unknown provider: {provider}"
            }

        provider_config = self.routing_config["providers"][provider]
        input_cost_rate = provider_config.get("cost_per_1k_input_tokens", 0.0)
        output_cost_rate = provider_config.get("cost_per_1k_output_tokens", 0.0)

        input_cost = (input_tokens / 1000) * input_cost_rate
        output_cost = (output_tokens / 1000) * output_cost_rate
        total_cost = input_cost + output_cost

        return {
            "success": True,
            "provider": provider,
            "model": model or provider_config.get("models", ["default"])[0],
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "total_tokens": input_tokens + output_tokens,
            "cost_breakdown": {
                "input_cost": input_cost,
                "output_cost": output_cost,
                "total_cost": total_cost
            },
            "rates": {
                "input_rate_per_1k": input_cost_rate,
                "output_rate_per_1k": output_cost_rate
            }
        }

    def check_budget(self) -> Dict[str, Any]:
        """
        Check budget status

        Returns:
            Budget status
        """
        budget_config = self.routing_config.get("budget", {})
        if not budget_config.get("enabled", False):
            return {
                "success": True,
                "budget_enabled": False,
                "message": "Budget tracking is disabled"
            }

        daily_limit = budget_config.get("daily_limit", 0.0)
        monthly_limit = budget_config.get("monthly_limit", 0.0)
        alert_threshold = budget_config.get("alert_threshold", 0.8)

        # Calculate daily and monthly costs
        today = datetime.utcnow().date().isoformat()
        this_month = datetime.utcnow().strftime("%Y-%m")

        daily_cost = 0.0
        monthly_cost = 0.0

        for provider_stats in self.stats["providers"].values():
            for date, daily_stats in provider_stats.get("requests_by_date", {}).items():
                if date == today:
                    daily_cost += daily_stats["cost"]
                if date.startswith(this_month):
                    monthly_cost += daily_stats["cost"]

        # Check alerts
        daily_alert = daily_cost >= (daily_limit * alert_threshold)
        monthly_alert = monthly_cost >= (monthly_limit * alert_threshold)
        daily_exceeded = daily_cost >= daily_limit
        monthly_exceeded = monthly_cost >= monthly_limit

        return {
            "success": True,
            "budget_enabled": True,
            "daily": {
                "spent": daily_cost,
                "limit": daily_limit,
                "remaining": max(0, daily_limit - daily_cost),
                "percentage": (daily_cost / daily_limit * 100) if daily_limit > 0 else 0,
                "alert": daily_alert,
                "exceeded": daily_exceeded
            },
            "monthly": {
                "spent": monthly_cost,
                "limit": monthly_limit,
                "remaining": max(0, monthly_limit - monthly_cost),
                "percentage": (monthly_cost / monthly_limit * 100) if monthly_limit > 0 else 0,
                "alert": monthly_alert,
                "exceeded": monthly_exceeded
            },
            "alert_threshold": alert_threshold
        }

    def reset_stats(self, provider: Optional[str] = None) -> Dict[str, Any]:
        """
        Reset usage statistics

        Args:
            provider: Reset specific provider (None for all)

        Returns:
            Result
        """
        if provider:
            if provider in self.stats["providers"]:
                del self.stats["providers"][provider]
                save_usage_stats(self.stats)
                return {
                    "success": True,
                    "message": f"Statistics reset for {provider}"
                }
            else:
                return {
                    "success": False,
                    "error": f"No statistics found for {provider}"
                }
        else:
            # Reset all
            self.stats = {
                "providers": {},
                "total_requests": 0,
                "total_input_tokens": 0,
                "total_output_tokens": 0,
                "total_cost": 0.0,
                "last_reset": datetime.utcnow().isoformat()
            }
            save_usage_stats(self.stats)
            return {
                "success": True,
                "message": "All statistics reset"
            }


# Singleton
_tracker = None


def get_tracker() -> UsageTracker:
    """Get singleton tracker instance"""
    global _tracker
    if _tracker is None:
        _tracker = UsageTracker()
    return _tracker
