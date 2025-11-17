"""
Drift Audit Agent - Phase 7 Milestone 1 Stub

Subscribes to audit.requested.drift events and responds with stub results.
For Milestone 1, this is a minimal stub that simulates audit completion.

Full implementation in later milestones will check:
- Code divergence from SpecItems (TODO comments vs implementation)
- GraphTask completion vs actual file changes
- Service health vs expected state (Phase 6 integration)
"""

import asyncio
import logging
import sys
from pathlib import Path

# Add parent directory to path for imports  # noqa: E402
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.config import settings  # noqa: E402
from app.models.graph import AuditStatus  # noqa: E402
from app.nats_client import NATSClient  # noqa: E402
from app.schemas.graph_events import AuditRequestedEvent, AuditResultEvent  # noqa: E402

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class DriftAuditAgent:
    """Stub audit agent for drift detection"""

    def __init__(self, nats_url: str):
        self.nats_client = NATSClient(nats_url)

    async def start(self):
        """Start audit agent and subscribe to events"""
        await self.nats_client.connect()
        logger.info("Drift audit agent connected to NATS")

        # Subscribe to drift audit requests
        await self.nats_client.subscribe("audit.requested.drift", self.handle_audit_request)
        logger.info("Subscribed to audit.requested.drift")

        # Keep running
        logger.info("Drift audit agent ready - waiting for requests...")
        try:
            # Run forever (until interrupted)
            while True:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            logger.info("Received interrupt signal")
        finally:
            await self.nats_client.disconnect()
            logger.info("Disconnected from NATS")

    async def handle_audit_request(self, subject: str, data: dict):
        """Handle audit.requested.drift events"""
        try:
            event = AuditRequestedEvent(**data)
            logger.info(
                f"Received drift audit request: audit_id={event.audit_id}, "
                f"target={event.target_entity}:{event.target_id}"
            )

            # Simulate audit processing (stub for Milestone 1)
            await asyncio.sleep(0.5)  # Simulate work

            # For Milestone 1, always return success with stub score
            result = AuditResultEvent(
                audit_id=event.audit_id,
                status=AuditStatus.OK,
                summary="[STUB] Drift audit completed successfully",
                score=7.5,  # Stub score
                findings={
                    "stub": True,
                    "message": "This is a stub implementation for Milestone 1",
                    "checks_performed": [
                        "Code vs SpecItem drift (stub)",
                        "Task completion drift (stub)",
                        "Service state drift (stub)",
                    ],
                },
                correlation_id=event.correlation_id,
            )

            # Publish result
            await self.nats_client.publish(
                f"audit.result.{event.kind.value}", result.model_dump(mode="json")
            )
            logger.info(
                f"Published drift audit result: audit_id={event.audit_id}, score={result.score}"
            )

        except Exception as e:
            logger.error(f"Error processing audit request: {e}")


async def main():
    """Main entry point"""
    agent = DriftAuditAgent(settings.nats_url)
    await agent.start()


if __name__ == "__main__":
    asyncio.run(main())
