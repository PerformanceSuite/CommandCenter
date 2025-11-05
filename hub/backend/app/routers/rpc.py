"""JSON-RPC endpoint for external tool integration.

The RPC endpoint provides a standardized interface for external tools
to interact with the Hub's event bus and services.

Supported Methods:
    - bus.publish: Publish event to NATS
    - bus.subscribe: Get recent events by subject
    - hub.info: Get Hub metadata
    - hub.health: Get Hub health status
"""
import logging
from typing import Any, Optional, Dict, Literal
from uuid import UUID, uuid4

from fastapi import APIRouter, Request, HTTPException, Depends
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.events.bridge import NATSBridge
from app.events.service import EventService
from app.config import get_nats_url, get_hub_id

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/rpc", tags=["rpc"])


# JSON-RPC 2.0 Schemas
class JSONRPCRequest(BaseModel):
    """JSON-RPC 2.0 request schema."""
    jsonrpc: Literal["2.0"] = Field(default="2.0")
    id: Optional[Any] = Field(None, description="Request ID (string, number, or null)")
    method: str = Field(..., description="Method name (e.g., 'bus.publish')")
    params: Optional[Dict] = Field(None, description="Method parameters")


class JSONRPCError(BaseModel):
    """JSON-RPC 2.0 error object."""
    code: int = Field(..., description="Error code")
    message: str = Field(..., description="Error message")
    data: Optional[Any] = Field(None, description="Additional error data")


class JSONRPCResponse(BaseModel):
    """JSON-RPC 2.0 response schema."""
    jsonrpc: Literal["2.0"] = Field(default="2.0")
    id: Optional[Any] = Field(None, description="Request ID (matches request)")
    result: Optional[Any] = Field(None, description="Result object (present on success)")
    error: Optional[JSONRPCError] = Field(None, description="Error object (present on failure)")


# JSON-RPC Error Codes (following spec)
PARSE_ERROR = -32700
INVALID_REQUEST = -32600
METHOD_NOT_FOUND = -32601
INVALID_PARAMS = -32602
INTERNAL_ERROR = -32603


# Dependency for NATSBridge
_bridge_instance: Optional[NATSBridge] = None


async def get_bridge() -> NATSBridge:
    """Get or create NATSBridge singleton."""
    global _bridge_instance

    if _bridge_instance is None:
        _bridge_instance = NATSBridge(nats_url=get_nats_url())
        try:
            await _bridge_instance.connect()
        except Exception as e:
            logger.error(f"Failed to connect NATSBridge: {e}")
            raise

    return _bridge_instance


# RPC Method Handlers
async def rpc_bus_publish(params: dict, bridge: NATSBridge) -> dict:
    """Publish event to NATS bus.

    Params:
        topic: NATS subject (e.g., 'hub.local-hub.project.created')
        payload: Event data as dictionary
        correlation_id: Optional correlation UUID

    Returns:
        { "published": true, "subject": "...", "correlation_id": "..." }
    """
    if not params or "topic" not in params or "payload" not in params:
        raise ValueError("Missing required params: 'topic' and 'payload'")

    topic = params["topic"]
    payload = params["payload"]
    correlation_id = params.get("correlation_id")

    if correlation_id:
        try:
            correlation_id = UUID(correlation_id)
        except ValueError:
            raise ValueError(f"Invalid correlation_id format: {correlation_id}")
    else:
        correlation_id = uuid4()

    # Publish to NATS
    await bridge.publish_internal_to_nats(
        subject=topic,
        payload=payload,
        correlation_id=correlation_id
    )

    return {
        "published": True,
        "subject": topic,
        "correlation_id": str(correlation_id)
    }


async def rpc_bus_subscribe(params: dict, event_service: EventService) -> dict:
    """Get recent events by subject filter.

    Params:
        subject: Subject pattern (supports NATS wildcards: *, >)
        limit: Maximum events to return (default 100)

    Returns:
        { "events": [...], "count": N }
    """
    if not params or "subject" not in params:
        raise ValueError("Missing required param: 'subject'")

    subject = params["subject"]
    limit = params.get("limit", 100)

    # Query events
    events = await event_service.query_events(subject=subject, limit=limit)

    return {
        "events": [
            {
                "id": str(event.id),
                "subject": event.subject,
                "origin": event.origin,
                "correlation_id": str(event.correlation_id),
                "payload": event.payload,
                "timestamp": event.timestamp.isoformat()
            }
            for event in events
        ],
        "count": len(events)
    }


async def rpc_hub_info(params: Optional[dict]) -> dict:
    """Get Hub metadata.

    Returns:
        { "hub_id": "...", "version": "...", "status": "..." }
    """
    return {
        "hub_id": get_hub_id(),
        "version": "1.0.0",  # TODO: Read from package metadata
        "status": "running"
    }


async def rpc_hub_health(params: Optional[dict], bridge: NATSBridge) -> dict:
    """Get Hub health status.

    Returns:
        { "status": "healthy|degraded|unhealthy", "services": {...} }
    """
    services = {
        "nats": "unknown",
        "database": "unknown"
    }

    # Check NATS connection
    if bridge.nc and not bridge.nc.is_closed:
        services["nats"] = "healthy"
    else:
        services["nats"] = "unhealthy"

    # Overall status
    unhealthy_count = sum(1 for status in services.values() if status == "unhealthy")
    if unhealthy_count == 0:
        overall_status = "healthy"
    elif unhealthy_count < len(services):
        overall_status = "degraded"
    else:
        overall_status = "unhealthy"

    return {
        "status": overall_status,
        "services": services
    }


# Main RPC Endpoint
@router.post("", response_model=JSONRPCResponse)
async def handle_rpc(
    request: JSONRPCRequest,
    db: AsyncSession = Depends(get_db),
    bridge: NATSBridge = Depends(get_bridge)
) -> JSONRPCResponse:
    """Handle JSON-RPC 2.0 requests.

    Example Request:
        POST /rpc
        {
          "jsonrpc": "2.0",
          "id": 1,
          "method": "bus.publish",
          "params": {
            "topic": "hub.local-hub.project.created",
            "payload": {"project_id": "123"}
          }
        }

    Example Response:
        {
          "jsonrpc": "2.0",
          "id": 1,
          "result": {
            "published": true,
            "subject": "hub.local-hub.project.created",
            "correlation_id": "..."
          }
        }
    """
    request_id = request.id

    try:
        # Validate JSON-RPC version
        if request.jsonrpc != "2.0":
            return JSONRPCResponse(
                id=request_id,
                error=JSONRPCError(
                    code=INVALID_REQUEST,
                    message="Invalid JSON-RPC version. Expected '2.0'."
                )
            )

        # Create event service for methods that need it
        event_service = EventService(nats_url=get_nats_url(), db_session=db)
        try:
            await event_service.connect()
        except Exception:
            logger.warning("EventService failed to connect to NATS")

        # Route to method handler
        method = request.method
        params = request.params or {}

        try:
            if method == "bus.publish":
                result = await rpc_bus_publish(params, bridge)
            elif method == "bus.subscribe":
                result = await rpc_bus_subscribe(params, event_service)
            elif method == "hub.info":
                result = await rpc_hub_info(params)
            elif method == "hub.health":
                result = await rpc_hub_health(params, bridge)
            else:
                return JSONRPCResponse(
                    id=request_id,
                    error=JSONRPCError(
                        code=METHOD_NOT_FOUND,
                        message=f"Method not found: {method}",
                        data={"available_methods": ["bus.publish", "bus.subscribe", "hub.info", "hub.health"]}
                    )
                )

            # Success response
            return JSONRPCResponse(id=request_id, result=result)

        except ValueError as e:
            # Invalid params
            return JSONRPCResponse(
                id=request_id,
                error=JSONRPCError(
                    code=INVALID_PARAMS,
                    message=str(e)
                )
            )
        except Exception as e:
            # Internal error
            logger.exception(f"Internal error in RPC method {method}")
            return JSONRPCResponse(
                id=request_id,
                error=JSONRPCError(
                    code=INTERNAL_ERROR,
                    message="Internal error",
                    data={"details": str(e)}
                )
            )
        finally:
            await event_service.disconnect()

    except Exception as e:
        # Unexpected error
        logger.exception("Unexpected error in RPC handler")
        return JSONRPCResponse(
            id=request_id,
            error=JSONRPCError(
                code=INTERNAL_ERROR,
                message="Internal server error",
                data={"details": str(e)}
            )
        )


# Helper endpoint to list available methods
@router.get("/methods")
async def list_methods() -> dict:
    """List available RPC methods.

    Returns:
        { "methods": [...] }
    """
    return {
        "methods": [
            {
                "name": "bus.publish",
                "description": "Publish event to NATS bus",
                "params": ["topic", "payload", "correlation_id?"]
            },
            {
                "name": "bus.subscribe",
                "description": "Get recent events by subject filter",
                "params": ["subject", "limit?"]
            },
            {
                "name": "hub.info",
                "description": "Get Hub metadata",
                "params": []
            },
            {
                "name": "hub.health",
                "description": "Get Hub health status",
                "params": []
            }
        ]
    }
