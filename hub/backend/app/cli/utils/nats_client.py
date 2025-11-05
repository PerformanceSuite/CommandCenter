"""Direct NATS client for CLI streaming.

Provides lightweight NATS subscription without database dependencies.
"""
import json
import logging
from typing import Callable, Awaitable

import nats
from nats.aio.client import Client as NATS

logger = logging.getLogger(__name__)


async def subscribe_stream(
    nats_url: str,
    subject: str,
    handler: Callable[[str, dict], Awaitable[None]],
    timeout: float = None
):
    """Subscribe to NATS subject and call handler for each message.

    Args:
        nats_url: NATS server URL (e.g., 'nats://localhost:4222')
        subject: NATS subject pattern (supports wildcards)
        handler: Async function called with (subject, data) for each message
        timeout: Optional timeout in seconds (None = run forever)

    Raises:
        Exception: If connection fails or handler errors

    Example:
        async def print_event(subject: str, data: dict):
            print(f"{subject}: {data}")

        await subscribe_stream(
            "nats://localhost:4222",
            "hub.>",
            print_event
        )
    """
    nc: NATS = None

    try:
        # Connect to NATS
        nc = await nats.connect(nats_url)
        logger.info(f"Connected to NATS at {nats_url}")

        async def message_handler(msg):
            """Handle incoming NATS message."""
            try:
                # Decode JSON payload
                data = json.loads(msg.data.decode())

                # Call user handler
                await handler(msg.subject, data)

            except json.JSONDecodeError:
                logger.error(f"Invalid JSON in message: {msg.data}")
            except Exception as e:
                logger.error(f"Handler error: {e}", exc_info=True)

        # Subscribe to subject
        subscription = await nc.subscribe(subject, cb=message_handler)
        logger.info(f"Subscribed to {subject}")

        # Run until timeout or cancellation
        if timeout:
            import asyncio
            await asyncio.sleep(timeout)
        else:
            # Run forever (until cancelled)
            while True:
                import asyncio
                await asyncio.sleep(1)

    except Exception as e:
        logger.error(f"NATS subscription error: {e}", exc_info=True)
        raise
    finally:
        if nc:
            await nc.close()
            logger.info("Disconnected from NATS")
