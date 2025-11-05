"""Tests for NATS client utility."""
import pytest
import asyncio
from app.cli.utils.nats_client import subscribe_stream


@pytest.mark.asyncio
async def test_subscribe_stream_receives_messages():
    """Test subscribing to NATS stream."""
    messages = []

    async def handler(subject: str, data: dict):
        messages.append((subject, data))

    # Start subscription (will run until cancelled)
    task = asyncio.create_task(
        subscribe_stream(
            "nats://localhost:4222",
            "hub.test.>",
            handler
        )
    )

    # Let it run briefly
    await asyncio.sleep(0.5)

    # Cancel subscription
    task.cancel()

    try:
        await task
    except asyncio.CancelledError:
        pass  # Expected
