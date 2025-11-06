"""Prometheus metrics for health monitoring."""
from typing import Dict, List, Any
from datetime import datetime
from enum import Enum

from app.models.service import HealthStatus, ServiceType


class MetricType(str, Enum):
    """Prometheus metric types."""
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    SUMMARY = "summary"


class HealthMetrics:
    """Collect and format health metrics for Prometheus export."""

    def __init__(self):
        """Initialize metrics collector."""
        self._metrics: Dict[str, Any] = {}
        self._reset_metrics()

    def _reset_metrics(self):
        """Reset all metrics to initial state."""
        self._metrics = {
            "health_checks_total": 0,
            "health_checks_failed_total": 0,
            "health_check_duration_seconds": [],
            "services_up": 0,
            "services_down": 0,
            "services_degraded": 0,
            "circuit_breaker_open": 0,
            "rate_limit_exceeded_total": 0,
        }

    def record_health_check(
        self,
        service_name: str,
        status: HealthStatus,
        duration_seconds: float
    ):
        """Record a health check result.

        Args:
            service_name: Name of the service
            status: Health status result
            duration_seconds: Check duration in seconds
        """
        self._metrics["health_checks_total"] += 1

        if status == HealthStatus.DOWN:
            self._metrics["health_checks_failed_total"] += 1

        self._metrics["health_check_duration_seconds"].append({
            "service": service_name,
            "duration": duration_seconds,
            "timestamp": datetime.utcnow().isoformat()
        })

    def update_service_counts(
        self,
        up: int,
        down: int,
        degraded: int
    ):
        """Update service status counts.

        Args:
            up: Number of healthy services
            down: Number of down services
            degraded: Number of degraded services
        """
        self._metrics["services_up"] = up
        self._metrics["services_down"] = down
        self._metrics["services_degraded"] = degraded

    def record_circuit_breaker_open(self, count: int):
        """Record number of open circuit breakers.

        Args:
            count: Number of open circuit breakers
        """
        self._metrics["circuit_breaker_open"] = count

    def record_rate_limit_exceeded(self):
        """Record rate limit exceeded event."""
        self._metrics["rate_limit_exceeded_total"] += 1

    def format_prometheus(self) -> str:
        """Format metrics in Prometheus text format.

        Returns:
            Prometheus formatted metrics string
        """
        lines = []

        # Health check total
        lines.append("# HELP health_checks_total Total number of health checks performed")
        lines.append("# TYPE health_checks_total counter")
        lines.append(f"health_checks_total {self._metrics['health_checks_total']}")

        # Failed health checks
        lines.append("# HELP health_checks_failed_total Total number of failed health checks")
        lines.append("# TYPE health_checks_failed_total counter")
        lines.append(f"health_checks_failed_total {self._metrics['health_checks_failed_total']}")

        # Service status gauges
        lines.append("# HELP services_up Number of healthy services")
        lines.append("# TYPE services_up gauge")
        lines.append(f"services_up {self._metrics['services_up']}")

        lines.append("# HELP services_down Number of down services")
        lines.append("# TYPE services_down gauge")
        lines.append(f"services_down {self._metrics['services_down']}")

        lines.append("# HELP services_degraded Number of degraded services")
        lines.append("# TYPE services_degraded gauge")
        lines.append(f"services_degraded {self._metrics['services_degraded']}")

        # Circuit breaker
        lines.append("# HELP circuit_breaker_open Number of open circuit breakers")
        lines.append("# TYPE circuit_breaker_open gauge")
        lines.append(f"circuit_breaker_open {self._metrics['circuit_breaker_open']}")

        # Rate limiting
        lines.append("# HELP rate_limit_exceeded_total Total rate limit exceeded events")
        lines.append("# TYPE rate_limit_exceeded_total counter")
        lines.append(f"rate_limit_exceeded_total {self._metrics['rate_limit_exceeded_total']}")

        # Health check duration histogram (simplified)
        if self._metrics["health_check_duration_seconds"]:
            durations = [d["duration"] for d in self._metrics["health_check_duration_seconds"][-100:]]
            avg_duration = sum(durations) / len(durations)

            lines.append("# HELP health_check_duration_seconds Health check duration")
            lines.append("# TYPE health_check_duration_seconds summary")
            lines.append(f"health_check_duration_seconds_sum {sum(durations)}")
            lines.append(f"health_check_duration_seconds_count {len(durations)}")
            lines.append(f'health_check_duration_seconds{{quantile="0.5"}} {sorted(durations)[len(durations)//2]}')
            lines.append(f'health_check_duration_seconds{{quantile="0.99"}} {sorted(durations)[int(len(durations)*0.99)]}')

        return "\n".join(lines) + "\n"

    def get_metrics_json(self) -> Dict[str, Any]:
        """Get metrics as JSON.

        Returns:
            Metrics dictionary
        """
        return self._metrics.copy()


# Global metrics instance
metrics = HealthMetrics()
