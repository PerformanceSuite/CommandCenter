"""
MCP (Model Context Protocol) API endpoints.

Provides HTTP and WebSocket endpoints for MCP server access.
"""

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Request,
    WebSocket,
    WebSocketDisconnect,
)
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.mcp.server import MCPServer
from app.mcp.config import MCPServerConfig, MCPServerInfo, MCPCapabilities
from app.mcp.utils import get_mcp_logger

logger = get_mcp_logger(__name__)

# Create router
router = APIRouter(prefix="/api/v1/mcp", tags=["mcp"])

# Global MCP server instance (initialized on startup)
_mcp_server: MCPServer | None = None


def get_mcp_server() -> MCPServer:
    """
    Get or create MCP server instance.

    Returns:
        MCP server instance

    Raises:
        HTTPException: If server is not initialized
    """
    global _mcp_server

    if _mcp_server is None:
        # Create default server configuration
        config = MCPServerConfig(
            server_info=MCPServerInfo(
                name="commandcenter-mcp",
                version="1.0.0",
                description="CommandCenter MCP Server for R&D Management",
            ),
            capabilities=MCPCapabilities(
                resources=True,
                tools=True,
                prompts=True,
            ),
        )

        _mcp_server = MCPServer(config)

    return _mcp_server


@router.post("/rpc")
async def handle_rpc(request: Request, db: Session = Depends(get_db)):
    """
    Handle JSON-RPC request.

    Accepts JSON-RPC 2.0 messages and returns responses.
    Each request creates an ephemeral session.

    Example:
        ```bash
        curl -X POST http://localhost:8000/api/v1/mcp/rpc \\
          -H "Content-Type: application/json" \\
          -d '{"jsonrpc":"2.0","id":1,"method":"resources/list","params":{}}'
        ```
    """
    server = get_mcp_server()

    try:
        # Parse request body
        body = await request.body()
        message = body.decode("utf-8")

        # Create ephemeral session for this request
        session = await server.create_session()

        try:
            # Handle message
            response = await server.handle_message(session.session_id, message)

            if not response:
                # Notification - no response
                return JSONResponse(content={}, status_code=204)

            # Return response
            import json

            return JSONResponse(content=json.loads(response))

        finally:
            # Close session after request
            await server.close_session(session.session_id)

    except Exception as e:
        logger.exception(f"Error handling RPC request: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """
    WebSocket endpoint for MCP protocol.

    Maintains a persistent connection with its own session.
    Messages are JSON-RPC 2.0 formatted.

    Example (JavaScript):
        ```javascript
        const ws = new WebSocket('ws://localhost:8000/api/v1/mcp/ws');

        ws.onopen = () => {
          ws.send(JSON.stringify({
            jsonrpc: "2.0",
            id: 1,
            method: "resources/list",
            params: {}
          }));
        };

        ws.onmessage = (event) => {
          const response = JSON.parse(event.data);
          console.log('Response:', response);
        };
        ```
    """
    server = get_mcp_server()

    # Accept connection
    await websocket.accept()
    session = None

    try:
        # Create session for this connection
        session = await server.create_session()
        session_id = session.session_id

        logger.info(f"WebSocket connected: {session_id}")

        # Send connection confirmation
        await websocket.send_json(
            {
                "type": "connection",
                "session_id": session_id,
                "message": "Connected to MCP server",
            }
        )

        # Message loop
        while True:
            try:
                # Receive message
                message = await websocket.receive_text()

                if not message:
                    continue

                # Handle message
                response = await server.handle_message(session_id, message)

                # Send response (if not a notification)
                if response:
                    await websocket.send_text(response)

            except WebSocketDisconnect:
                logger.info(f"WebSocket disconnected: {session_id}")
                break
            except Exception as e:
                logger.exception(f"Error processing message: {e}")
                # Send error response
                error_response = {
                    "jsonrpc": "2.0",
                    "id": None,
                    "error": {
                        "code": -32603,
                        "message": "Internal error",
                        "data": str(e),
                    },
                }
                await websocket.send_json(error_response)

    except Exception as e:
        logger.exception(f"WebSocket error: {e}")

    finally:
        # Cleanup
        if session:
            await server.close_session(session.session_id)
            logger.info(f"Session closed: {session.session_id}")


@router.get("/health")
async def health_check():
    """
    Health check endpoint.

    Returns server status and basic information.
    """
    server = get_mcp_server()

    return {
        "status": "healthy",
        "server": server.server_info.name,
        "version": server.server_info.version,
        "running": server.is_running(),
    }


@router.get("/info")
async def server_info():
    """
    Get server information and capabilities.

    Returns:
        Server info, capabilities, and statistics
    """
    server = get_mcp_server()

    return {
        "server_info": server.get_server_info().model_dump(),
        "capabilities": server.get_capabilities().model_dump(),
        "stats": server.get_stats(),
    }


@router.get("/resources")
async def list_resources(db: Session = Depends(get_db)):
    """
    List available MCP resources.

    This is a convenience HTTP GET endpoint that wraps the
    MCP resources/list JSON-RPC method.

    Returns:
        List of available resources
    """
    server = get_mcp_server()

    # Create ephemeral session
    session = await server.create_session()

    try:
        # Build JSON-RPC request
        import json

        request_message = json.dumps(
            {"jsonrpc": "2.0", "id": 1, "method": "resources/list", "params": {}}
        )

        # Handle request
        response = await server.handle_message(session.session_id, request_message)

        if response:
            response_data = json.loads(response)
            return response_data.get("result", {})

        return {"resources": []}

    finally:
        await server.close_session(session.session_id)


@router.get("/tools")
async def list_tools(db: Session = Depends(get_db)):
    """
    List available MCP tools.

    This is a convenience HTTP GET endpoint that wraps the
    MCP tools/list JSON-RPC method.

    Returns:
        List of available tools
    """
    server = get_mcp_server()

    # Create ephemeral session
    session = await server.create_session()

    try:
        # Build JSON-RPC request
        import json

        request_message = json.dumps(
            {"jsonrpc": "2.0", "id": 1, "method": "tools/list", "params": {}}
        )

        # Handle request
        response = await server.handle_message(session.session_id, request_message)

        if response:
            response_data = json.loads(response)
            return response_data.get("result", {})

        return {"tools": []}

    finally:
        await server.close_session(session.session_id)


@router.get("/prompts")
async def list_prompts(db: Session = Depends(get_db)):
    """
    List available MCP prompts.

    This is a convenience HTTP GET endpoint that wraps the
    MCP prompts/list JSON-RPC method.

    Returns:
        List of available prompts
    """
    server = get_mcp_server()

    # Create ephemeral session
    session = await server.create_session()

    try:
        # Build JSON-RPC request
        import json

        request_message = json.dumps(
            {"jsonrpc": "2.0", "id": 1, "method": "prompts/list", "params": {}}
        )

        # Handle request
        response = await server.handle_message(session.session_id, request_message)

        if response:
            response_data = json.loads(response)
            return response_data.get("result", {})

        return {"prompts": []}

    finally:
        await server.close_session(session.session_id)


# Startup event handler to initialize MCP server
async def initialize_mcp_server():
    """Initialize MCP server on application startup."""
    from app.database import AsyncSessionLocal as async_session
    from app.mcp.providers.commandcenter_resources import CommandCenterResourceProvider
    from app.mcp.providers.commandcenter_tools import CommandCenterToolProvider
    from app.mcp.providers.commandcenter_prompts import CommandCenterPromptProvider

    server = get_mcp_server()

    if not server.is_initialized():
        # Create database session for providers
        async with async_session() as db:
            # Register CommandCenter resource provider
            resource_provider = CommandCenterResourceProvider(db)
            server.register_resource_provider(resource_provider)
            logger.info("Registered CommandCenter resource provider")

            # Register CommandCenter tool provider
            tool_provider = CommandCenterToolProvider(db)
            server.register_tool_provider(tool_provider)
            logger.info("Registered CommandCenter tool provider")

        # Register CommandCenter prompt provider (no DB needed)
        prompt_provider = CommandCenterPromptProvider()
        server.register_prompt_provider(prompt_provider)
        logger.info("Registered CommandCenter prompt provider")

        await server.initialize()
        await server.start()
        logger.info("MCP server initialized and started")


# Shutdown event handler
async def shutdown_mcp_server():
    """Shutdown MCP server on application shutdown."""
    if _mcp_server:
        await _mcp_server.shutdown()
        logger.info("MCP server shutdown complete")
