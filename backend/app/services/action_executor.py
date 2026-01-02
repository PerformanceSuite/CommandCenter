"""
ActionExecutor - Execute actions triggered by agents or users.

Phase 3, Task 3.4: Action Execution Service

This service executes the actions (affordances) that agents and users
can take on entities. It handles dispatching to the appropriate
handler based on action type and returning structured responses.
"""

import logging
import uuid
from typing import Any

from app.schemas.query import Affordance

logger = logging.getLogger(__name__)


class ActionResult:
    """Result of executing an action."""

    def __init__(
        self,
        status: str,
        message: str,
        job_id: str | None = None,
        redirect_query: dict[str, Any] | None = None,
        data: dict[str, Any] | None = None,
    ):
        self.status = status
        self.message = message
        self.job_id = job_id
        self.redirect_query = redirect_query
        self.data = data

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON response."""
        result: dict[str, Any] = {
            "status": self.status,
            "message": self.message,
        }
        if self.job_id:
            result["job_id"] = self.job_id
        if self.redirect_query:
            result["redirect_query"] = self.redirect_query
        if self.data:
            result["data"] = self.data
        return result


class ActionExecutor:
    """Execute actions triggered by agents or users.

    This service is the bridge between affordances and actual operations.
    When an agent or user wants to perform an action on an entity,
    the affordance is passed to this executor which dispatches to
    the appropriate handler.

    Examples:
        >>> executor = ActionExecutor()
        >>> affordance = Affordance(
        ...     action="trigger_audit",
        ...     target=EntityRef(type="symbol", id="123"),
        ...     description="Run audit"
        ... )
        >>> result = await executor.execute(affordance)
        >>> print(result["status"])  # "queued"
    """

    async def execute(self, affordance: Affordance) -> dict[str, Any]:
        """Execute an affordance and return the result.

        Args:
            affordance: The affordance to execute

        Returns:
            Dictionary with status, message, and action-specific data
        """
        handler_name = f"_handle_{affordance.action}"
        handler = getattr(self, handler_name, None)

        if not handler:
            logger.warning(f"Unknown action: {affordance.action}")
            return ActionResult(
                status="error",
                message=f"Unknown action: {affordance.action}",
            ).to_dict()

        try:
            result = await handler(affordance)
            return result.to_dict()
        except Exception as e:
            logger.exception(f"Error executing action {affordance.action}: {e}")
            return ActionResult(
                status="error",
                message=f"Failed to execute {affordance.action}: {str(e)}",
            ).to_dict()

    async def _handle_trigger_audit(self, affordance: Affordance) -> ActionResult:
        """Queue an audit job for an entity.

        In a full implementation, this would integrate with the actual
        audit service to queue code analysis.
        """
        job_id = str(uuid.uuid4())
        audit_type = (affordance.parameters or {}).get("audit_type", "general")

        # TODO: Integrate with actual audit service
        logger.info(
            f"Queued {audit_type} audit for {affordance.target.type} "
            f"{affordance.target.id} (job: {job_id})"
        )

        return ActionResult(
            status="queued",
            message=f"Audit queued for {affordance.target.type} {affordance.target.id}",
            job_id=job_id,
        )

    async def _handle_drill_down(self, affordance: Affordance) -> ActionResult:
        """Return a query for drilling down into an entity.

        Instead of directly navigating, this returns a composed query
        that the client can execute to get detailed information.
        """
        redirect_query = {
            "entities": [
                {
                    "type": affordance.target.type,
                    "id": affordance.target.id,
                }
            ],
            "relationships": [
                {"type": "all", "direction": "both", "depth": 1},
            ],
        }

        return ActionResult(
            status="completed",
            message=f"Drill-down query for {affordance.target.type} {affordance.target.id}",
            redirect_query=redirect_query,
        )

    async def _handle_view_dependencies(self, affordance: Affordance) -> ActionResult:
        """Return a query for viewing dependencies of an entity."""
        redirect_query = {
            "entities": [
                {
                    "type": affordance.target.type,
                    "id": affordance.target.id,
                }
            ],
            "relationships": [
                {"type": "dependency", "direction": "outbound", "depth": 2},
            ],
        }

        return ActionResult(
            status="completed",
            message=f"Dependency query for {affordance.target.type} {affordance.target.id}",
            redirect_query=redirect_query,
        )

    async def _handle_view_callers(self, affordance: Affordance) -> ActionResult:
        """Return a query for viewing callers of an entity."""
        redirect_query = {
            "entities": [
                {
                    "type": affordance.target.type,
                    "id": affordance.target.id,
                }
            ],
            "relationships": [
                {"type": "caller", "direction": "inbound", "depth": 2},
            ],
        }

        return ActionResult(
            status="completed",
            message=f"Caller query for {affordance.target.type} {affordance.target.id}",
            redirect_query=redirect_query,
        )

    async def _handle_open_in_editor(self, affordance: Affordance) -> ActionResult:
        """Return information for opening an entity in an editor.

        In a full implementation, this would integrate with VS Code
        extension or similar to open the file at the correct location.
        """
        return ActionResult(
            status="completed",
            message=f"Editor link for {affordance.target.type} {affordance.target.id}",
            data={
                "entity_type": affordance.target.type,
                "entity_id": affordance.target.id,
                "action": "open_in_editor",
            },
        )

    async def _handle_create_task(self, affordance: Affordance) -> ActionResult:
        """Queue creation of a task related to an entity.

        In a full implementation, this would create a task in the
        task management system.
        """
        job_id = str(uuid.uuid4())
        title = (affordance.parameters or {}).get(
            "title", f"Review {affordance.target.type} {affordance.target.id}"
        )

        # TODO: Integrate with task service
        logger.info(
            f"Queued task creation '{title}' for {affordance.target.type} "
            f"{affordance.target.id} (job: {job_id})"
        )

        return ActionResult(
            status="queued",
            message=f"Task creation queued for {affordance.target.type} {affordance.target.id}",
            job_id=job_id,
        )

    async def _handle_run_indexer(self, affordance: Affordance) -> ActionResult:
        """Queue re-indexing of a repository.

        In a full implementation, this would trigger the indexer
        to re-process the repository.
        """
        job_id = str(uuid.uuid4())

        # TODO: Integrate with indexer service
        logger.info(
            f"Queued re-indexing for {affordance.target.type} "
            f"{affordance.target.id} (job: {job_id})"
        )

        return ActionResult(
            status="queued",
            message=f"Indexing queued for {affordance.target.type} {affordance.target.id}",
            job_id=job_id,
        )
