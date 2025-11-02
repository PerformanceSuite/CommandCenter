"""
MCP connection manager - handles client connections and sessions.

Manages multiple client connections and routes requests to appropriate handlers.
"""

from datetime import datetime
from typing import Any, Callable, Dict, Optional
from uuid import uuid4

from app.mcp.protocol import (
    JSONRPCRequest,
    JSONRPCResponse,
    MCPProtocolHandler,
)
from app.mcp.utils import get_mcp_logger

logger = get_mcp_logger(__name__)


class MCPSession:
    """
    Represents a single MCP client session.

    Attributes:
        session_id: Unique session identifier
        client_info: Client information from initialization
        created_at: Session creation timestamp
        last_activity: Last request timestamp
        metadata: Optional session metadata
    """

    def __init__(
        self,
        client_info: Optional[Dict[str, Any]] = None,
    ):
        """
        Initialize MCP session.

        Security: Session ID is always generated server-side to prevent
        session fixation attacks. Clients cannot provide their own session ID.

        Args:
            client_info: Optional client information
        """
        self.session_id = str(uuid4())
        self.client_info = client_info or {}
        self.created_at = datetime.utcnow()
        self.last_activity = datetime.utcnow()
        self.metadata: Dict[str, Any] = {}
        self._initialized = False

    def mark_activity(self) -> None:
        """Update last activity timestamp."""
        self.last_activity = datetime.utcnow()

    def is_initialized(self) -> bool:
        """Check if session has been initialized."""
        return self._initialized

    def set_initialized(self, initialized: bool = True) -> None:
        """Set session initialization status."""
        self._initialized = initialized

    def update_client_info(self, client_info: Dict[str, Any]) -> None:
        """
        Update client information.

        Args:
            client_info: Client information from initialize request
        """
        self.client_info.update(client_info)
        self.set_initialized(True)

    # Context management methods
    def set_context(self, key: str, value: Any) -> None:
        """
        Set a context value for this session.

        Context is preserved across multiple requests within the same session,
        enabling stateful interactions.

        Args:
            key: Context key
            value: Context value (must be JSON serializable)

        Example:
            session.set_context("current_project_id", 1)
            session.set_context("analysis_state", {"step": 2, "items": [1, 2, 3]})
        """
        self.metadata[key] = value

    def get_context(self, key: str, default: Any = None) -> Any:
        """
        Get a context value from this session.

        Args:
            key: Context key
            default: Default value if key not found

        Returns:
            Context value or default

        Example:
            project_id = session.get_context("current_project_id")
            state = session.get_context("analysis_state", {})
        """
        return self.metadata.get(key, default)

    def has_context(self, key: str) -> bool:
        """
        Check if a context key exists.

        Args:
            key: Context key

        Returns:
            True if key exists in context

        Example:
            if session.has_context("current_project_id"):
                project_id = session.get_context("current_project_id")
        """
        return key in self.metadata

    def delete_context(self, key: str) -> bool:
        """
        Delete a context key.

        Args:
            key: Context key to delete

        Returns:
            True if key was deleted, False if key didn't exist

        Example:
            session.delete_context("temporary_data")
        """
        if key in self.metadata:
            del self.metadata[key]
            return True
        return False

    def clear_context(self) -> None:
        """
        Clear all context data for this session.

        Example:
            session.clear_context()  # Reset session state
        """
        self.metadata.clear()

    def get_all_context(self) -> Dict[str, Any]:
        """
        Get all context data for this session.

        Returns:
            Dictionary of all context key-value pairs

        Example:
            context = session.get_all_context()
            print(f"Session has {len(context)} context items")
        """
        return self.metadata.copy()


class MCPConnectionManager:
    """
    Manages MCP client connections and request routing.

    Handles multiple concurrent client sessions and routes requests
    to the appropriate server handlers.
    """

    def __init__(
        self,
        max_connections: int = 10,
        session_timeout: int = 3600,
    ):
        """
        Initialize connection manager.

        Args:
            max_connections: Maximum concurrent connections
            session_timeout: Session timeout in seconds
        """
        self.max_connections = max_connections
        self.session_timeout = session_timeout
        self._sessions: Dict[str, MCPSession] = {}
        self._protocol_handler = MCPProtocolHandler()
        self._request_handlers: Dict[str, Callable] = {}
        self._logger = logger

    def register_handler(self, method: str, handler: Callable) -> None:
        """
        Register request handler for specific method.

        Args:
            method: Method name (e.g., "resources/list")
            handler: Async callable that handles the request
        """
        self._request_handlers[method] = handler
        self._logger.debug(f"Registered handler for method: {method}")

    def unregister_handler(self, method: str) -> None:
        """
        Unregister request handler.

        Args:
            method: Method name to unregister
        """
        if method in self._request_handlers:
            del self._request_handlers[method]
            self._logger.debug(f"Unregistered handler for method: {method}")

    async def create_session(
        self, client_info: Optional[Dict[str, Any]] = None
    ) -> MCPSession:
        """
        Create new client session.

        Args:
            client_info: Optional client information

        Returns:
            New MCPSession

        Raises:
            RuntimeError: If max connections reached
        """
        if len(self._sessions) >= self.max_connections:
            raise RuntimeError(
                f"Maximum connections ({self.max_connections}) reached"
            )

        session = MCPSession(client_info=client_info)
        self._sessions[session.session_id] = session
        self._logger.info(f"Created session: {session.session_id}")
        return session

    async def get_session(self, session_id: str) -> Optional[MCPSession]:
        """
        Get session by ID.

        Args:
            session_id: Session identifier

        Returns:
            MCPSession or None if not found
        """
        return self._sessions.get(session_id)

    async def close_session(self, session_id: str) -> None:
        """
        Close and remove session.

        Args:
            session_id: Session identifier
        """
        if session_id in self._sessions:
            del self._sessions[session_id]
            self._logger.info(f"Closed session: {session_id}")

    async def cleanup_expired_sessions(self) -> int:
        """
        Remove expired sessions based on timeout.

        Returns:
            Number of sessions cleaned up
        """
        now = datetime.utcnow()
        expired = []

        for session_id, session in self._sessions.items():
            age = (now - session.last_activity).total_seconds()
            if age > self.session_timeout:
                expired.append(session_id)

        for session_id in expired:
            await self.close_session(session_id)

        if expired:
            self._logger.info(f"Cleaned up {len(expired)} expired sessions")

        return len(expired)

    async def handle_request(
        self, session_id: str, raw_message: str
    ) -> Optional[str]:
        """
        Handle incoming request for a session.

        Args:
            session_id: Session identifier
            raw_message: Raw JSON-RPC message

        Returns:
            Serialized JSON-RPC response (or None for notifications)

        Raises:
            ValueError: If session not found
        """
        session = await self.get_session(session_id)
        if not session:
            raise ValueError(f"Session {session_id} not found")

        session.mark_activity()

        try:
            # Parse request
            request = await self._protocol_handler.parse_request(raw_message)

            # Check if this is initialize and session isn't initialized
            if request.method != "initialize" and not session.is_initialized():
                response = self._protocol_handler.create_error_response(
                    request.id,
                    -32002,
                    "Session not initialized",
                    "Must call initialize before other methods",
                )
                return self._protocol_handler.serialize_response(response)

            # Route to handler
            response = await self._route_request(request, session)

            # Don't send response for notifications
            if request.is_notification():
                return None

            return self._protocol_handler.serialize_response(response)

        except Exception as e:
            self._logger.exception(f"Error handling request: {e}")
            error_response = await self._protocol_handler.handle_exception(e)
            return self._protocol_handler.serialize_response(error_response)

    async def _route_request(
        self, request: JSONRPCRequest, session: MCPSession
    ) -> JSONRPCResponse:
        """
        Route request to appropriate handler.

        Args:
            request: Parsed JSON-RPC request
            session: Client session

        Returns:
            JSON-RPC response
        """
        method = request.method

        # Check if handler exists
        if method not in self._request_handlers:
            return self._protocol_handler.create_method_not_found_error(
                request.id, method
            )

        try:
            # Call handler
            handler = self._request_handlers[method]
            result = await handler(request, session)

            # Return success response
            return self._protocol_handler.create_response(request.id, result)

        except Exception as e:
            self._logger.exception(f"Handler error for {method}: {e}")
            return await self._protocol_handler.handle_exception(e, request.id)

    def get_active_sessions(self) -> int:
        """
        Get number of active sessions.

        Returns:
            Count of active sessions
        """
        return len(self._sessions)

    def get_session_info(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Get session information.

        Args:
            session_id: Session identifier

        Returns:
            Session info dictionary or None if not found
        """
        session = self._sessions.get(session_id)
        if not session:
            return None

        return {
            "session_id": session.session_id,
            "client_info": session.client_info,
            "created_at": session.created_at.isoformat(),
            "last_activity": session.last_activity.isoformat(),
            "initialized": session.is_initialized(),
            "metadata": session.metadata,
        }

    # Session context management
    async def set_session_context(
        self, session_id: str, key: str, value: Any
    ) -> bool:
        """
        Set context value for a session.

        Args:
            session_id: Session identifier
            key: Context key
            value: Context value

        Returns:
            True if successful, False if session not found
        """
        session = await self.get_session(session_id)
        if not session:
            return False

        session.set_context(key, value)
        return True

    async def get_session_context(
        self, session_id: str, key: str, default: Any = None
    ) -> Any:
        """
        Get context value from a session.

        Args:
            session_id: Session identifier
            key: Context key
            default: Default value if key not found

        Returns:
            Context value, default, or None if session not found
        """
        session = await self.get_session(session_id)
        if not session:
            return None

        return session.get_context(key, default)

    async def has_session_context(self, session_id: str, key: str) -> bool:
        """
        Check if session has a context key.

        Args:
            session_id: Session identifier
            key: Context key

        Returns:
            True if key exists, False otherwise
        """
        session = await self.get_session(session_id)
        if not session:
            return False

        return session.has_context(key)

    async def delete_session_context(self, session_id: str, key: str) -> bool:
        """
        Delete context key from a session.

        Args:
            session_id: Session identifier
            key: Context key

        Returns:
            True if deleted, False if session or key not found
        """
        session = await self.get_session(session_id)
        if not session:
            return False

        return session.delete_context(key)

    async def clear_session_context(self, session_id: str) -> bool:
        """
        Clear all context from a session.

        Args:
            session_id: Session identifier

        Returns:
            True if successful, False if session not found
        """
        session = await self.get_session(session_id)
        if not session:
            return False

        session.clear_context()
        return True

    async def get_all_session_context(
        self, session_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Get all context from a session.

        Args:
            session_id: Session identifier

        Returns:
            Dictionary of context or None if session not found
        """
        session = await self.get_session(session_id)
        if not session:
            return None

        return session.get_all_context()
