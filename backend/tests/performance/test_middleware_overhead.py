"""Performance tests for Correlation ID Middleware.

Validates that middleware overhead is < 1ms per request.
Uses statistical analysis over 1000+ iterations for accuracy.
"""

import time
import statistics
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.middleware.correlation import CorrelationIDMiddleware


def measure_latency(client: TestClient, endpoint: str, iterations: int = 1000) -> dict:
    """Measure endpoint latency over multiple iterations.

    Args:
        client: TestClient instance
        endpoint: API endpoint to test
        iterations: Number of requests to make

    Returns:
        dict with latency statistics (mean, median, p95, p99)
    """
    latencies = []

    for _ in range(iterations):
        start = time.perf_counter()
        response = client.get(endpoint)
        end = time.perf_counter()

        # Only record successful requests
        if response.status_code == 200:
            latencies.append((end - start) * 1000)  # Convert to milliseconds

    return {
        "mean": statistics.mean(latencies),
        "median": statistics.median(latencies),
        "p95": statistics.quantiles(latencies, n=20)[18],  # 95th percentile
        "p99": statistics.quantiles(latencies, n=100)[98],  # 99th percentile
        "min": min(latencies),
        "max": max(latencies),
        "iterations": len(latencies),
    }


@pytest.fixture
def baseline_app():
    """FastAPI app WITHOUT correlation middleware (baseline)."""
    app = FastAPI()

    @app.get("/health")
    async def health():
        return {"status": "healthy"}

    return app


@pytest.fixture
def middleware_app():
    """FastAPI app WITH correlation middleware."""
    app = FastAPI()
    app.add_middleware(CorrelationIDMiddleware)

    @app.get("/health")
    async def health():
        return {"status": "healthy"}

    return app


def test_correlation_middleware_overhead(baseline_app, middleware_app):
    """Test that correlation middleware adds < 1ms overhead."""
    iterations = 1000

    # Measure baseline (no middleware)
    baseline_client = TestClient(baseline_app)
    baseline_stats = measure_latency(baseline_client, "/health", iterations)

    # Measure with middleware
    middleware_client = TestClient(middleware_app)
    middleware_stats = measure_latency(middleware_client, "/health", iterations)

    # Calculate overhead
    mean_overhead = middleware_stats["mean"] - baseline_stats["mean"]
    p95_overhead = middleware_stats["p95"] - baseline_stats["p95"]

    # Report results
    print(f"\n{'='*60}")
    print("Middleware Performance Test Results")
    print(f"{'='*60}")
    print(f"Iterations: {iterations}")
    print(f"\nBaseline (no middleware):")
    print(f"  Mean:   {baseline_stats['mean']:.3f}ms")
    print(f"  Median: {baseline_stats['median']:.3f}ms")
    print(f"  P95:    {baseline_stats['p95']:.3f}ms")
    print(f"\nWith Correlation Middleware:")
    print(f"  Mean:   {middleware_stats['mean']:.3f}ms")
    print(f"  Median: {middleware_stats['median']:.3f}ms")
    print(f"  P95:    {middleware_stats['p95']:.3f}ms")
    print(f"\nOverhead:")
    print(f"  Mean:   {mean_overhead:.3f}ms")
    print(f"  P95:    {p95_overhead:.3f}ms")
    print(f"{'='*60}\n")

    # Assert overhead < 1ms
    assert mean_overhead < 1.0, (
        f"Middleware overhead ({mean_overhead:.3f}ms) exceeds 1ms threshold"
    )

    # Also check P95 overhead
    assert p95_overhead < 2.0, (
        f"P95 overhead ({p95_overhead:.3f}ms) exceeds 2ms threshold"
    )


def test_middleware_scales_linearly(middleware_app):
    """Test that middleware performance is consistent across load."""
    client = TestClient(middleware_app)

    # Test at different request volumes
    test_sizes = [100, 500, 1000]
    overhead_per_size = []

    for size in test_sizes:
        stats = measure_latency(client, "/health", iterations=size)
        overhead_per_size.append(stats["mean"])

    # Calculate coefficient of variation (should be low if consistent)
    cv = statistics.stdev(overhead_per_size) / statistics.mean(overhead_per_size)

    print(f"\nScalability Test:")
    print(f"  Latencies: {[f'{x:.3f}ms' for x in overhead_per_size]}")
    print(f"  Coefficient of Variation: {cv:.3f}")

    # CV should be < 0.3 (30% variation) for consistent performance
    assert cv < 0.3, f"Performance not consistent across load (CV: {cv:.3f})"


def test_middleware_with_custom_header(middleware_app):
    """Test middleware performance when extracting existing header."""
    client = TestClient(middleware_app)
    iterations = 1000

    # Measure with client-provided request IDs
    latencies = []
    for i in range(iterations):
        start = time.perf_counter()
        response = client.get(
            "/health",
            headers={"X-Request-ID": f"test-{i}"}
        )
        end = time.perf_counter()

        if response.status_code == 200:
            latencies.append((end - start) * 1000)

    mean_latency = statistics.mean(latencies)

    print(f"\nHeader Extraction Performance:")
    print(f"  Mean latency: {mean_latency:.3f}ms")

    # Should still be fast
    assert mean_latency < 5.0, (
        f"Header extraction latency ({mean_latency:.3f}ms) too high"
    )


@pytest.mark.benchmark
def test_middleware_concurrent_performance(middleware_app):
    """Test middleware under concurrent load (optional benchmark)."""
    import concurrent.futures

    client = TestClient(middleware_app)
    iterations_per_thread = 100
    num_threads = 10

    def make_requests(thread_id: int):
        """Worker function for concurrent requests."""
        latencies = []
        for i in range(iterations_per_thread):
            start = time.perf_counter()
            response = client.get(
                "/health",
                headers={"X-Request-ID": f"thread-{thread_id}-req-{i}"}
            )
            end = time.perf_counter()

            if response.status_code == 200:
                latencies.append((end - start) * 1000)

        return latencies

    # Run concurrent requests
    with concurrent.futures.ThreadPoolExecutor(max_workers=num_threads) as executor:
        futures = [
            executor.submit(make_requests, i)
            for i in range(num_threads)
        ]

        all_latencies = []
        for future in concurrent.futures.as_completed(futures):
            all_latencies.extend(future.result())

    # Analyze concurrent performance
    concurrent_stats = {
        "mean": statistics.mean(all_latencies),
        "median": statistics.median(all_latencies),
        "p95": statistics.quantiles(all_latencies, n=20)[18],
        "max": max(all_latencies),
    }

    print(f"\nConcurrent Performance ({num_threads} threads):")
    print(f"  Mean:   {concurrent_stats['mean']:.3f}ms")
    print(f"  Median: {concurrent_stats['median']:.3f}ms")
    print(f"  P95:    {concurrent_stats['p95']:.3f}ms")
    print(f"  Max:    {concurrent_stats['max']:.3f}ms")

    # Under concurrent load, mean should still be reasonable
    assert concurrent_stats["mean"] < 10.0, (
        f"Concurrent mean latency ({concurrent_stats['mean']:.3f}ms) too high"
    )
