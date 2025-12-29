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
