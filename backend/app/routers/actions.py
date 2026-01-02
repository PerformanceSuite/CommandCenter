"""
Actions API Router - Phase 3 Agent Parity

Provides endpoints for executing affordances, enabling agents
to take the same actions available in the UI.
"""

from typing import Any

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.project_context import get_current_project_id
from app.database import get_db
from app.schemas.query import Affordance
from app.services.action_executor import ActionExecutor

router = APIRouter(prefix="/api/v1/actions", tags=["actions"])


@router.post("/execute")
async def execute_action(
    affordance: Affordance,
    db: AsyncSession = Depends(get_db),
    current_project_id: int = Depends(get_current_project_id),
) -> dict[str, Any]:
    """
    Execute an affordance action on an entity.

    This endpoint enables agent parity - any action a user can take
    in the UI, an agent can also invoke via this API.

    **Action Types:**
    - `trigger_audit`: Queue code analysis for the entity
    - `drill_down`: Get detailed view of the entity
    - `view_dependencies`: View outbound dependencies
    - `view_callers`: View inbound callers
    - `open_in_editor`: Get editor link for the entity
    - `create_task`: Create a related task
    - `run_indexer`: Re-index a repository

    **Response Structure:**
    - `status`: "queued", "completed", or "error"
    - `message`: Human-readable description
    - `job_id`: (optional) ID for tracking async jobs
    - `redirect_query`: (optional) Query to execute for drill-down actions
    - `data`: (optional) Additional action-specific data

    **Example Request:**
    ```json
    {
      "action": "trigger_audit",
      "target": {"type": "symbol", "id": "123"},
      "description": "Run security audit",
      "parameters": {"audit_type": "security"}
    }
    ```

    **Example Response (queued action):**
    ```json
    {
      "status": "queued",
      "message": "Audit queued for symbol 123",
      "job_id": "550e8400-e29b-41d4-a716-446655440000"
    }
    ```

    **Example Response (drill-down action):**
    ```json
    {
      "status": "completed",
      "message": "Drill-down query for symbol 123",
      "redirect_query": {
        "entities": [{"type": "symbol", "id": "123"}],
        "relationships": [{"type": "all", "direction": "both", "depth": 1}]
      }
    }
    ```
    """
    executor = ActionExecutor()
    return await executor.execute(affordance)
