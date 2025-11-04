#!/usr/bin/env python3
"""Example event consumer for CommandCenter Hub.

This script demonstrates how to:
- Connect to NATS
- Subscribe to Hub events
- Handle events with async callbacks
- Implement graceful shutdown

Usage:
    python examples/event_consumer.py --subject "hub.*.project.*"
"""
import asyncio
import argparse
import json
import logging
from datetime import datetime
from typing import Optional

import nats
from nats.aio.client import Client as NATS

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)


class EventConsumer:
    """Example event consumer for Hub events."""

    def __init__(self, nats_url: str, subject: str):
        """Initialize event consumer.

        Args:
            nats_url: NATS server URL (e.g., 'nats://localhost:4222')
            subject: NATS subject pattern to subscribe (supports wildcards)
        """
        self.nats_url = nats_url
        self.subject = subject
        self.nc: Optional[NATS] = None
        self.event_count = 0

    async def connect(self):
        """Connect to NATS server."""
        try:
            self.nc = await nats.connect(self.nats_url)
            logger.info(f"Connected to NATS at {self.nats_url}")
        except Exception as e:
            logger.error(f"Failed to connect: {e}")
            raise

    async def handle_event(self, msg):
        """Handle received event.

        Args:
            msg: NATS message object
        """
        try:
            data = json.loads(msg.data.decode())
            self.event_count += 1

            logger.info(f"[{self.event_count}] Event received")
            logger.info(f"  Subject: {msg.subject}")
            logger.info(f"  Payload: {json.dumps(data, indent=2)}")

            # Custom logic here
            # Example: Alert on project failures
            if "error" in data.get("payload", {}):
                logger.warning(f"  Error detected in {msg.subject}: {data['payload']['error']}")

        except Exception as e:
            logger.error(f"Error handling event: {e}")

    async def subscribe(self):
        """Subscribe to NATS subject."""
        if not self.nc:
            raise RuntimeError("Not connected. Call connect() first.")

        logger.info(f"Subscribing to: {self.subject}")
        await self.nc.subscribe(self.subject, cb=self.handle_event)
        logger.info("Subscription active. Waiting for events...")

    async def run(self):
        """Run consumer until interrupted."""
        await self.connect()
        await self.subscribe()

        try:
            # Keep running until interrupted
            while True:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            logger.info(f"\nShutting down. Processed {self.event_count} events.")
        finally:
            if self.nc:
                await self.nc.close()


async def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Hub Event Consumer")
    parser.add_argument(
        "--nats-url",
        default="nats://localhost:4222",
        help="NATS server URL (default: nats://localhost:4222)"
    )
    parser.add_argument(
        "--subject",
        default="hub.>",
        help="NATS subject pattern (default: hub.>, supports wildcards)"
    )
    args = parser.parse_args()

    consumer = EventConsumer(
        nats_url=args.nats_url,
        subject=args.subject
    )

    await consumer.run()


if __name__ == "__main__":
    asyncio.run(main())
