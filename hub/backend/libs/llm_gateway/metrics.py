"""
Prometheus Metrics for LLM Gateway

Provides observability for multi-provider LLM requests including:
- Request counts by provider and status
- Latency histograms
- Token usage
- Cost tracking
"""

from prometheus_client import REGISTRY, Counter, Histogram


def _get_or_create_counter(name: str, description: str, labels: list[str]) -> Counter:
    """Get existing counter or create new one."""
    try:
        return Counter(name, description, labels)
    except ValueError:
        # Already registered, get from registry
        return REGISTRY._names_to_collectors.get(name)


def _get_or_create_histogram(
    name: str, description: str, labels: list[str], buckets: tuple
) -> Histogram:
    """Get existing histogram or create new one."""
    try:
        return Histogram(name, description, labels, buckets=buckets)
    except ValueError:
        # Already registered, get from registry
        return REGISTRY._names_to_collectors.get(name)


# Request counter - tracks total requests by provider and status
llm_requests_total = _get_or_create_counter(
    "llm_requests_total",
    "Total LLM requests by provider and status",
    ["provider", "status"],
)

# Latency histogram - tracks request duration by provider
llm_request_duration_seconds = _get_or_create_histogram(
    "llm_request_duration_seconds",
    "LLM request duration in seconds by provider",
    ["provider"],
    buckets=(0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0, 30.0, 60.0, 120.0),
)

# Token counter - tracks token usage by provider and direction
llm_tokens_total = _get_or_create_counter(
    "llm_tokens_total",
    "Total tokens processed by provider and direction",
    ["provider", "direction"],  # direction: "input" or "output"
)

# Cost counter - tracks cost in dollars by provider
llm_cost_dollars_total = _get_or_create_counter(
    "llm_cost_dollars_total",
    "Total LLM cost in dollars by provider",
    ["provider"],
)


def record_request_success(provider: str, duration_seconds: float) -> None:
    """
    Record a successful LLM request.

    Args:
        provider: Provider alias (e.g., 'claude', 'gpt')
        duration_seconds: Request duration in seconds
    """
    llm_requests_total.labels(provider=provider, status="success").inc()
    llm_request_duration_seconds.labels(provider=provider).observe(duration_seconds)


def record_request_failure(provider: str, duration_seconds: float) -> None:
    """
    Record a failed LLM request.

    Args:
        provider: Provider alias (e.g., 'claude', 'gpt')
        duration_seconds: Request duration in seconds
    """
    llm_requests_total.labels(provider=provider, status="error").inc()
    llm_request_duration_seconds.labels(provider=provider).observe(duration_seconds)


def record_tokens(provider: str, input_tokens: int, output_tokens: int) -> None:
    """
    Record token usage for a request.

    Args:
        provider: Provider alias (e.g., 'claude', 'gpt')
        input_tokens: Number of input/prompt tokens
        output_tokens: Number of output/completion tokens
    """
    llm_tokens_total.labels(provider=provider, direction="input").inc(input_tokens)
    llm_tokens_total.labels(provider=provider, direction="output").inc(output_tokens)


def record_cost(provider: str, cost_dollars: float) -> None:
    """
    Record cost for a request.

    Args:
        provider: Provider alias (e.g., 'claude', 'gpt')
        cost_dollars: Cost in US dollars
    """
    llm_cost_dollars_total.labels(provider=provider).inc(cost_dollars)


def get_cost_statistics() -> dict:
    """
    Get aggregated cost and usage statistics from Prometheus metrics.

    Returns:
        Dictionary with cost, token, and request statistics by provider.
    """
    cost_by_provider = {}
    tokens_by_provider = {}
    requests_by_provider = {}

    total_cost = 0.0
    total_input_tokens = 0
    total_output_tokens = 0
    total_requests = 0

    # Aggregate cost metrics
    for metric in llm_cost_dollars_total.collect():
        for sample in metric.samples:
            if sample.name.endswith("_total"):
                provider = sample.labels.get("provider", "unknown")
                value = sample.value
                cost_by_provider[provider] = value
                total_cost += value

    # Aggregate token metrics
    for metric in llm_tokens_total.collect():
        for sample in metric.samples:
            if sample.name.endswith("_total"):
                provider = sample.labels.get("provider", "unknown")
                direction = sample.labels.get("direction", "unknown")
                value = int(sample.value)

                if provider not in tokens_by_provider:
                    tokens_by_provider[provider] = {"input": 0, "output": 0}
                tokens_by_provider[provider][direction] = value

                if direction == "input":
                    total_input_tokens += value
                elif direction == "output":
                    total_output_tokens += value

    # Aggregate request metrics
    for metric in llm_requests_total.collect():
        for sample in metric.samples:
            if sample.name.endswith("_total"):
                provider = sample.labels.get("provider", "unknown")
                value = int(sample.value)

                if provider not in requests_by_provider:
                    requests_by_provider[provider] = 0
                requests_by_provider[provider] += value
                total_requests += value

    return {
        "total_cost": total_cost,
        "total_input_tokens": total_input_tokens,
        "total_output_tokens": total_output_tokens,
        "total_tokens": total_input_tokens + total_output_tokens,
        "total_requests": total_requests,
        "cost_by_provider": cost_by_provider,
        "tokens_by_provider": tokens_by_provider,
        "requests_by_provider": requests_by_provider,
    }
