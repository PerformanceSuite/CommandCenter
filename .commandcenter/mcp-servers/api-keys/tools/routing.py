"""
Multi-provider AI routing tools
"""

from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from collections import defaultdict

from .storage import get_storage
from .validate import get_validator
from ..config import load_routing_config, save_routing_config


class ProviderRouter:
    """Intelligent routing to AI providers"""

    def __init__(self):
        self.storage = get_storage()
        self.validator = get_validator()
        self.routing_config = load_routing_config()
        self.provider_health: Dict[str, Dict] = {}

    def _is_provider_available(self, provider: str) -> tuple[bool, str]:
        """
        Check if provider is available

        Args:
            provider: Provider name

        Returns:
            Tuple of (is_available, reason)
        """
        # Check if provider is enabled
        provider_config = self.routing_config["providers"].get(provider, {})
        if not provider_config.get("enabled", False):
            return False, "Provider is disabled"

        # Check if API key exists (except for local)
        if provider != "local":
            if provider not in self.storage.list_providers():
                return False, "No API key configured"

        # Check health status
        health = self.provider_health.get(provider, {})
        if health.get("status") == "unhealthy":
            # Check if enough time has passed for retry
            last_check = health.get("last_check")
            if last_check:
                last_check_time = datetime.fromisoformat(last_check)
                if datetime.utcnow() - last_check_time < timedelta(minutes=5):
                    return False, "Provider recently failed health check"

        return True, "Provider available"

    def update_provider_health(
        self,
        provider: str,
        status: str,
        error: Optional[str] = None
    ) -> None:
        """
        Update provider health status

        Args:
            provider: Provider name
            status: 'healthy' or 'unhealthy'
            error: Optional error message
        """
        self.provider_health[provider] = {
            "status": status,
            "last_check": datetime.utcnow().isoformat(),
            "error": error
        }

    def route_request(
        self,
        task_type: str,
        preferred_provider: Optional[str] = None,
        model: Optional[str] = None,
        enable_fallback: bool = True
    ) -> Dict[str, Any]:
        """
        Route a request to the best available provider

        Args:
            task_type: Type of task (code_generation, embeddings, analysis, etc.)
            preferred_provider: Preferred provider (overrides routing config)
            model: Specific model to use
            enable_fallback: Enable fallback to other providers

        Returns:
            Routing decision
        """
        routing_map = self.routing_config.get("routing", {})
        fallback_order = self.routing_config.get("fallback_order", [])

        # Determine primary provider
        if preferred_provider:
            primary_provider = preferred_provider
        else:
            primary_provider = routing_map.get(task_type)
            if not primary_provider:
                # Default to first available provider
                primary_provider = fallback_order[0] if fallback_order else "anthropic"

        # Try primary provider
        is_available, reason = self._is_provider_available(primary_provider)
        if is_available:
            provider_config = self.routing_config["providers"][primary_provider]
            selected_model = model or provider_config.get("models", [])[0]

            return {
                "success": True,
                "provider": primary_provider,
                "model": selected_model,
                "reason": f"Primary provider for {task_type}",
                "is_fallback": False,
                "task_type": task_type
            }

        # Try fallback if enabled
        if enable_fallback:
            for fallback_provider in fallback_order:
                if fallback_provider == primary_provider:
                    continue  # Skip primary we already tried

                is_available, reason = self._is_provider_available(fallback_provider)
                if is_available:
                    provider_config = self.routing_config["providers"][fallback_provider]
                    selected_model = model or provider_config.get("models", [])[0]

                    return {
                        "success": True,
                        "provider": fallback_provider,
                        "model": selected_model,
                        "reason": f"Fallback (primary {primary_provider} unavailable: {reason})",
                        "is_fallback": True,
                        "task_type": task_type,
                        "original_provider": primary_provider
                    }

        # No providers available
        return {
            "success": False,
            "error": f"No available providers for {task_type}",
            "task_type": task_type,
            "attempted_providers": [primary_provider] + fallback_order
        }

    def get_best_provider_for_cost(
        self,
        task_type: str,
        estimated_tokens: int
    ) -> Dict[str, Any]:
        """
        Get the most cost-effective provider for a task

        Args:
            task_type: Type of task
            estimated_tokens: Estimated total tokens

        Returns:
            Best provider for cost optimization
        """
        available_providers = []

        for provider, config in self.routing_config["providers"].items():
            if not config.get("enabled", False):
                continue

            is_available, _ = self._is_provider_available(provider)
            if not is_available:
                continue

            # Calculate estimated cost (using average of input/output rates)
            avg_cost_rate = (
                config.get("cost_per_1k_input_tokens", 0) +
                config.get("cost_per_1k_output_tokens", 0)
            ) / 2
            estimated_cost = (estimated_tokens / 1000) * avg_cost_rate

            available_providers.append({
                "provider": provider,
                "estimated_cost": estimated_cost,
                "cost_rate": avg_cost_rate
            })

        if not available_providers:
            return {
                "success": False,
                "error": "No available providers"
            }

        # Sort by cost
        available_providers.sort(key=lambda x: x["estimated_cost"])
        best_provider = available_providers[0]

        return {
            "success": True,
            "provider": best_provider["provider"],
            "estimated_cost": best_provider["estimated_cost"],
            "reason": "Most cost-effective option",
            "alternatives": available_providers[1:3]  # Show top 3
        }

    def get_routing_recommendations(self) -> Dict[str, Any]:
        """
        Get routing recommendations based on current configuration

        Returns:
            Routing recommendations
        """
        recommendations = []
        warnings = []

        # Check if all task types have providers
        routing_map = self.routing_config.get("routing", {})
        for task_type, provider in routing_map.items():
            is_available, reason = self._is_provider_available(provider)
            if not is_available:
                warnings.append({
                    "type": "unavailable_provider",
                    "task_type": task_type,
                    "provider": provider,
                    "reason": reason
                })

        # Check for cost optimization opportunities
        providers_by_cost = []
        for provider, config in self.routing_config["providers"].items():
            if config.get("enabled", False):
                avg_cost = (
                    config.get("cost_per_1k_input_tokens", 0) +
                    config.get("cost_per_1k_output_tokens", 0)
                ) / 2
                providers_by_cost.append({
                    "provider": provider,
                    "avg_cost": avg_cost
                })

        providers_by_cost.sort(key=lambda x: x["avg_cost"])

        if providers_by_cost:
            cheapest = providers_by_cost[0]
            if cheapest["avg_cost"] == 0:
                recommendations.append({
                    "type": "cost_optimization",
                    "message": f"Consider using {cheapest['provider']} for cost-free operations",
                    "provider": cheapest["provider"]
                })

        # Check fallback configuration
        fallback_order = self.routing_config.get("fallback_order", [])
        available_fallbacks = 0
        for provider in fallback_order:
            is_available, _ = self._is_provider_available(provider)
            if is_available:
                available_fallbacks += 1

        if available_fallbacks < 2:
            warnings.append({
                "type": "limited_fallbacks",
                "message": "Only one fallback provider available",
                "available_count": available_fallbacks
            })

        return {
            "success": True,
            "recommendations": recommendations,
            "warnings": warnings,
            "available_providers": self._get_available_providers(),
            "routing_health": "healthy" if not warnings else "degraded"
        }

    def _get_available_providers(self) -> List[str]:
        """Get list of currently available providers"""
        available = []
        for provider in self.routing_config["providers"].keys():
            is_available, _ = self._is_provider_available(provider)
            if is_available:
                available.append(provider)
        return available

    def update_routing_config(
        self,
        task_type: str,
        provider: str
    ) -> Dict[str, Any]:
        """
        Update routing configuration for a task type

        Args:
            task_type: Task type to configure
            provider: Provider to route to

        Returns:
            Result
        """
        if provider not in self.routing_config["providers"]:
            return {
                "success": False,
                "error": f"Unknown provider: {provider}"
            }

        routing_map = self.routing_config.get("routing", {})
        routing_map[task_type] = provider
        self.routing_config["routing"] = routing_map

        save_routing_config(self.routing_config)

        return {
            "success": True,
            "message": f"Routing for {task_type} updated to {provider}",
            "task_type": task_type,
            "provider": provider
        }

    def get_provider_stats(self) -> Dict[str, Any]:
        """
        Get statistics about all providers

        Returns:
            Provider statistics
        """
        stats = []

        for provider, config in self.routing_config["providers"].items():
            is_available, reason = self._is_provider_available(provider)
            health = self.provider_health.get(provider, {})

            provider_stat = {
                "provider": provider,
                "enabled": config.get("enabled", False),
                "available": is_available,
                "availability_reason": reason,
                "models": config.get("models", []),
                "rate_limit": config.get("rate_limit", 0),
                "cost_per_1k_input": config.get("cost_per_1k_input_tokens", 0),
                "cost_per_1k_output": config.get("cost_per_1k_output_tokens", 0),
                "health_status": health.get("status", "unknown"),
                "last_health_check": health.get("last_check")
            }

            stats.append(provider_stat)

        return {
            "success": True,
            "providers": stats,
            "total_providers": len(stats),
            "available_providers": sum(1 for s in stats if s["available"]),
            "enabled_providers": sum(1 for s in stats if s["enabled"])
        }


# Singleton
_router = None


def get_router() -> ProviderRouter:
    """Get singleton router instance"""
    global _router
    if _router is None:
        _router = ProviderRouter()
    return _router
