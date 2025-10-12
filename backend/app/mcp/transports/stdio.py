"""
Stdio transport for MCP servers.

Implements stdin/stdout based communication for MCP protocol.
"""

import asyncio
import sys
from typing import Optional

from app.mcp.server import MCPServer
from app.mcp.utils import get_mcp_logger

logger = get_mcp_logger(__name__)


class StdioTransport:
    """
    Standard input/output transport for MCP.

    Reads JSON-RPC messages from stdin and writes responses to stdout.
    This is the primary transport method for MCP servers.
    """

    def __init__(self, server: MCPServer):
        """
        Initialize stdio transport.

        Args:
            server: MCP server instance
        """
        self.server = server
        self._session_id: Optional[str] = None
        self._running = False
        self._logger = logger

    async def start(self) -> None:
        """
        Start the stdio transport.

        Reads from stdin line by line and processes MCP requests.
        """
        if self._running:
            self._logger.warning("Transport already running")
            return

        # Initialize server if not already done
        if not self.server.is_initialized():
            await self.server.initialize()

        await self.server.start()

        # Create session for this connection
        session = await self.server.create_session()
        self._session_id = session.session_id

        self._running = True
        self._logger.info("Stdio transport started")

        try:
            # Create async reader for stdin
            reader = asyncio.StreamReader()
            protocol = asyncio.StreamReaderProtocol(reader)

            loop = asyncio.get_event_loop()
            await loop.connect_read_pipe(lambda: protocol, sys.stdin)

            # Process messages line by line
            while self._running:
                try:
                    # Read line from stdin
                    line = await reader.readline()

                    if not line:
                        # EOF reached
                        self._logger.info("EOF on stdin, shutting down")
                        break

                    message = line.decode("utf-8").strip()

                    if not message:
                        continue

                    # Handle message
                    response = await self.server.handle_message(
                        self._session_id, message
                    )

                    # Write response to stdout (if not a notification)
                    if response:
                        sys.stdout.write(response + "\n")
                        sys.stdout.flush()

                except Exception as e:
                    self._logger.exception(f"Error processing message: {e}")
                    # Continue processing next message

        finally:
            await self.stop()

    async def stop(self) -> None:
        """Stop the stdio transport and cleanup."""
        if not self._running:
            return

        self._running = False
        self._logger.info("Stopping stdio transport")

        # Close session if exists
        if self._session_id:
            await self.server.close_session(self._session_id)
            self._session_id = None

        # Shutdown server
        await self.server.shutdown()

        self._logger.info("Stdio transport stopped")

    def is_running(self) -> bool:
        """Check if transport is running."""
        return self._running


async def run_stdio_server(server: MCPServer) -> None:
    """
    Convenience function to run MCP server with stdio transport.

    Args:
        server: MCP server instance

    Example:
        ```python
        from app.mcp import MCPServer
        from app.mcp.config import MCPServerConfig, MCPServerInfo
        from app.mcp.transports import run_stdio_server

        config = MCPServerConfig(
            server_info=MCPServerInfo(
                name="my-mcp-server",
                version="1.0.0"
            )
        )

        server = MCPServer(config)
        # Register providers here...

        await run_stdio_server(server)
        ```
    """
    transport = StdioTransport(server)
    try:
        await transport.start()
    except KeyboardInterrupt:
        logger.info("Received interrupt, shutting down")
    except Exception as e:
        logger.exception(f"Server error: {e}")
    finally:
        await transport.stop()
