"""
HTTP transport for MCP servers.

Implements HTTP-based communication for MCP protocol using FastAPI.
"""

import asyncio
from typing import Optional

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse

from app.mcp.server import MCPServer
from app.mcp.utils import get_mcp_logger

logger = get_mcp_logger(__name__)


class HTTPTransport:
    """
    HTTP transport for MCP.

    Provides RESTful HTTP endpoints for MCP protocol communication.
    Each HTTP request creates a new ephemeral session.
    """

    def __init__(self, server: MCPServer, app: Optional[FastAPI] = None):
        """
        Initialize HTTP transport.

        Args:
            server: MCP server instance
            app: Optional FastAPI app instance (creates new if not provided)
        """
        self.server = server
        self.app = app or FastAPI(title=f"MCP Server: {server.server_info.name}")
        self._running = False
        self._logger = logger

        # Register routes
        self._register_routes()

    def _register_routes(self) -> None:
        """Register HTTP routes for MCP endpoints."""

        @self.app.post("/mcp/v1/rpc")
        async def handle_rpc(request: Request):
            """
            Handle JSON-RPC request.

            Accepts JSON-RPC 2.0 messages and returns responses.
            """
            try:
                # Parse request body
                body = await request.body()
                message = body.decode("utf-8")

                # Create ephemeral session for this request
                session = await self.server.create_session()

                try:
                    # Handle message
                    response = await self.server.handle_message(session.session_id, message)

                    if not response:
                        # Notification - no response
                        return JSONResponse(content={}, status_code=204)

                    # Return response
                    import json

                    return JSONResponse(content=json.loads(response))

                finally:
                    # Close session after request
                    await self.server.close_session(session.session_id)

            except Exception as e:
                self._logger.exception(f"Error handling RPC request: {e}")
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.get("/mcp/v1/health")
        async def health_check():
            """Health check endpoint."""
            return {
                "status": "healthy",
                "server": self.server.server_info.name,
                "version": self.server.server_info.version,
                "running": self.server.is_running(),
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
        Start the HTTP transport.

        Note: This method initializes the server but does not start
        the HTTP server itself. Use uvicorn to run the FastAPI app.
        """
        if self._running:
            self._logger.warning("Transport already running")
            return

        # Initialize server if not already done
        if not self.server.is_initialized():
            await self.server.initialize()

        await self.server.start()

        self._running = True
        self._logger.info("HTTP transport started")

    async def stop(self) -> None:
        """Stop the HTTP transport and cleanup."""
        if not self._running:
            return

        self._running = False
        self._logger.info("Stopping HTTP transport")

        # Shutdown server
        await self.server.shutdown()

        self._logger.info("HTTP transport stopped")

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


def create_http_app(server: MCPServer) -> FastAPI:
    """
    Convenience function to create FastAPI app for MCP server.

    Args:
        server: MCP server instance

    Returns:
        FastAPI application

    Example:
        ```python
        from app.mcp import MCPServer
        from app.mcp.config import MCPServerConfig, MCPServerInfo
        from app.mcp.transports import create_http_app

        config = MCPServerConfig(
            server_info=MCPServerInfo(
                name="my-mcp-server",
                version="1.0.0"
            )
        )

        server = MCPServer(config)
        # Register providers here...

        app = create_http_app(server)
        # Run with: uvicorn app:app --host 0.0.0.0 --port 8000
        ```
    """
    transport = HTTPTransport(server)
    asyncio.create_task(transport.start())
    return transport.get_app()
