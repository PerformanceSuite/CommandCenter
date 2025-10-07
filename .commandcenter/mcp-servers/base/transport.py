"""MCP Transport Layer

Implements stdio (standard input/output) transport for MCP servers.
Supports line-delimited JSON messages over stdin/stdout.
"""

import sys
import json
import asyncio
from typing import Callable, Optional, Awaitable
from .utils import get_logger

logger = get_logger(__name__)


class StdioTransport:
    """Stdio Transport for MCP

    Handles communication over stdin/stdout using line-delimited JSON.
    Each message is a single line of JSON followed by a newline character.
    """

    def __init__(self):
        self.running = False
        self.message_handler: Optional[Callable[[str], Awaitable[str]]] = None

    def set_message_handler(self, handler: Callable[[str], Awaitable[str]]) -> None:
        """Set the message handler callback

        Args:
            handler: Async function that takes a message string and returns a response string
        """
        self.message_handler = handler

    async def start(self) -> None:
        """Start the transport and begin processing messages"""
        if self.message_handler is None:
            raise ValueError("Message handler not set")

        self.running = True
        logger.info("MCP stdio transport started")

        try:
            # Read from stdin line by line
            loop = asyncio.get_event_loop()
            reader = asyncio.StreamReader()
            protocol = asyncio.StreamReaderProtocol(reader)
            await loop.connect_read_pipe(lambda: protocol, sys.stdin)

            while self.running:
                try:
                    # Read one line (one JSON message)
                    line = await reader.readline()
                    if not line:
                        # EOF reached
                        logger.info("EOF received, shutting down")
                        break

                    message = line.decode('utf-8').strip()
                    if not message:
                        continue

                    logger.debug(f"Received message: {message[:100]}...")

                    # Process message
                    try:
                        response = await self.message_handler(message)
                        if response:
                            await self.send_message(response)
                    except Exception as e:
                        logger.error(f"Error handling message: {e}", exc_info=True)
                        # Send error response
                        error_response = {
                            'jsonrpc': '2.0',
                            'id': None,
                            'error': {
                                'code': -32603,
                                'message': 'Internal error',
                                'data': str(e)
                            }
                        }
                        await self.send_message(json.dumps(error_response))

                except asyncio.CancelledError:
                    logger.info("Transport cancelled")
                    break
                except Exception as e:
                    logger.error(f"Error in message loop: {e}", exc_info=True)

        finally:
            self.running = False
            logger.info("MCP stdio transport stopped")

    async def send_message(self, message: str) -> None:
        """Send a message to stdout

        Args:
            message: JSON string to send
        """
        try:
            # Write message followed by newline
            sys.stdout.write(message + '\n')
            sys.stdout.flush()
            logger.debug(f"Sent message: {message[:100]}...")
        except Exception as e:
            logger.error(f"Error sending message: {e}", exc_info=True)
            raise

    def stop(self) -> None:
        """Stop the transport"""
        self.running = False
        logger.info("Stopping stdio transport")

    def send_notification(self, method: str, params: dict) -> None:
        """Send a notification (request without id)

        Args:
            method: Notification method name
            params: Notification parameters
        """
        notification = {
            'jsonrpc': '2.0',
            'method': method,
            'params': params
        }
        # Use asyncio to send in sync context
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                asyncio.create_task(self.send_message(json.dumps(notification)))
            else:
                loop.run_until_complete(self.send_message(json.dumps(notification)))
        except Exception as e:
            logger.error(f"Error sending notification: {e}", exc_info=True)


class TransportError(Exception):
    """Transport-level error"""
    pass


class ConnectionClosedError(TransportError):
    """Connection was closed"""
    pass
