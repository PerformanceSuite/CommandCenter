"""
WebSocket transport for MCP servers.

Implements WebSocket-based communication for MCP protocol.
"""

import asyncio
import json
from typing import Dict, Optional
from fastapi import FastAPI, WebSocket, WebSocketDisconnect

from app.mcp.server import MCPServer
from app.mcp.utils import get_mcp_logger

logger = get_mcp_logger(__name__)


class WebSocketTransport:
    """
    WebSocket transport for MCP.

    Provides persistent WebSocket connections for MCP protocol communication.
    Each WebSocket connection maintains its own session.
    """

    def __init__(self, server: MCPServer, app: Optional[FastAPI] = None):
        """
        Initialize WebSocket transport.

        Args:
            server: MCP server instance
            app: Optional FastAPI app instance (creates new if not provided)
        """
        self.server = server
        self.app = app or FastAPI(title=f"MCP WebSocket Server: {server.server_info.name}")
        self._running = False
        self._logger = logger
        self._active_connections: Dict[str, WebSocket] = {}

        # Register routes
        self._register_routes()

    def _register_routes(self) -> None:
        """Register WebSocket routes for MCP endpoints."""

        @self.app.websocket("/mcp/v1/ws")
        async def websocket_endpoint(websocket: WebSocket):
            """
            WebSocket endpoint for MCP protocol.

            Maintains a persistent connection with its own session.
            """
            # Accept connection
            await websocket.accept()
            session = None

            try:
                # Create session for this connection
                session = await self.server.create_session()
                session_id = session.session_id

                self._active_connections[session_id] = websocket
                self._logger.info(f"WebSocket connected: {session_id}")

                # Send connection confirmation
                await websocket.send_json({
                    "type": "connection",
                    "session_id": session_id,
                    "message": "Connected to MCP server"
                })

                # Message loop
                while True:
                    try:
                        # Receive message
                        message = await websocket.receive_text()

                        if not message:
                            continue

                        # Handle message
                        response = await self.server.handle_message(
                            session_id, message
                        )

                        # Send response (if not a notification)
                        if response:
                            await websocket.send_text(response)

                    except WebSocketDisconnect:
                        self._logger.info(f"WebSocket disconnected: {session_id}")
                        break
                    except Exception as e:
                        self._logger.exception(f"Error processing message: {e}")
                        # Send error response
                        error_response = {
                            "jsonrpc": "2.0",
                            "id": None,
                            "error": {
                                "code": -32603,
                                "message": "Internal error",
                                "data": str(e)
                            }
                        }
                        await websocket.send_json(error_response)

            except Exception as e:
                self._logger.exception(f"WebSocket error: {e}")

            finally:
                # Cleanup
                if session:
                    session_id = session.session_id
                    if session_id in self._active_connections:
                        del self._active_connections[session_id]
                    await self.server.close_session(session_id)
                    self._logger.info(f"Session closed: {session_id}")

        @self.app.get("/mcp/v1/health")
        async def health_check():
            """Health check endpoint."""
            return {
                "status": "healthy",
                "server": self.server.server_info.name,
                "version": self.server.server_info.version,
                "running": self.server.is_running(),
                "active_connections": len(self._active_connections),
            }

        @self.app.get("/mcp/v1/info")
        async def server_info():
            """Get server information and capabilities."""
            return {
                "server_info": self.server.get_server_info().model_dump(),
                "capabilities": self.server.get_capabilities().model_dump(),
                "stats": self.server.get_stats(),
            }

    async def start(self) -> None:
        """
        Start the WebSocket transport.

        Note: This method initializes the server but does not start
        the WebSocket server itself. Use uvicorn to run the FastAPI app.
        """
        if self._running:
            self._logger.warning("Transport already running")
            return

        # Initialize server if not already done
        if not self.server.is_initialized():
            await self.server.initialize()

        await self.server.start()

        self._running = True
        self._logger.info("WebSocket transport started")

    async def stop(self) -> None:
        """Stop the WebSocket transport and cleanup."""
        if not self._running:
            return

        self._running = False
        self._logger.info("Stopping WebSocket transport")

        # Close all active connections
        for session_id, websocket in list(self._active_connections.items()):
            try:
                await websocket.close()
                await self.server.close_session(session_id)
            except Exception as e:
                self._logger.error(f"Error closing connection {session_id}: {e}")

        self._active_connections.clear()

        # Shutdown server
        await self.server.shutdown()

        self._logger.info("WebSocket transport stopped")

    def is_running(self) -> bool:
        """Check if transport is running."""
        return self._running

    def get_app(self) -> FastAPI:
        """
        Get FastAPI application.

        Returns:
            FastAPI app instance
        """
        return self.app

    def get_active_connections(self) -> int:
        """
        Get number of active WebSocket connections.

        Returns:
            Number of active connections
        """
        return len(self._active_connections)

    async def broadcast(self, message: Dict) -> None:
        """
        Broadcast message to all connected clients.

        Args:
            message: Message to broadcast
        """
        disconnected = []

        for session_id, websocket in self._active_connections.items():
            try:
                await websocket.send_json(message)
            except Exception as e:
                self._logger.error(
                    f"Error broadcasting to {session_id}: {e}"
                )
                disconnected.append(session_id)

        # Cleanup disconnected clients
        for session_id in disconnected:
            if session_id in self._active_connections:
                del self._active_connections[session_id]
            try:
                await self.server.close_session(session_id)
            except Exception:
                pass


def create_websocket_app(server: MCPServer) -> FastAPI:
    """
    Convenience function to create FastAPI app with WebSocket support for MCP server.

    Args:
        server: MCP server instance

    Returns:
        FastAPI application

    Example:
        ```python
        from app.mcp import MCPServer
        from app.mcp.config import MCPServerConfig, MCPServerInfo
        from app.mcp.transports import create_websocket_app

        config = MCPServerConfig(
            server_info=MCPServerInfo(
                name="my-mcp-server",
                version="1.0.0"
            )
        )

        server = MCPServer(config)
        # Register providers here...

        app = create_websocket_app(server)
        # Run with: uvicorn app:app --host 0.0.0.0 --port 8000
        ```
    """
    transport = WebSocketTransport(server)
    asyncio.create_task(transport.start())
    return transport.get_app()
