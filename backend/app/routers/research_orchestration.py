"""
Research Orchestration API Router

Provides endpoints for multi-agent research workflow:
- Technology deep dive with parallel agents
- Custom multi-agent task launching
- Technology monitoring (HackerNews, GitHub, arXiv)
- Model selection and provider management
"""

import json
import logging
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.technology import Technology
from app.schemas.research import (
    AgentResult,
    AgentResultMetadata,
    AvailableModelsResponse,
    MonitoringAlert,
    MultiAgentLaunchRequest,
    ResearchOrchestrationResponse,
    ResearchSummaryResponse,
    TechnologyDeepDiveRequest,
    TechnologyMonitorRequest,
    TechnologyMonitorResponse,
)
from app.services.ai_router import AIProvider, ai_router
from app.services.hackernews_service import HackerNewsService
from app.services.redis_service import redis_service
from app.services.research_agent_orchestrator import research_orchestrator

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/research", tags=["research"])


class ResearchTaskStorage:
    """
    Redis-backed storage for research tasks.
    Falls back to in-memory storage if Redis is unavailable.
    """

    PREFIX = "research_task:"
    INDEX_KEY = "research_tasks:index"
    TTL = 86400 * 7  # 7 days

    # Fallback in-memory storage (used when Redis unavailable)
    _memory_fallback: Dict[str, Any] = {}

    @classmethod
    def _serialize_task(cls, task: Dict[str, Any]) -> str:
        """Serialize task data to JSON, handling datetime objects."""

        def json_serializer(obj):
            if isinstance(obj, datetime):
                return obj.isoformat()
            if hasattr(obj, "model_dump"):  # Pydantic model
                return obj.model_dump()
            if hasattr(obj, "__dict__"):
                return obj.__dict__
            raise TypeError(f"Object of type {type(obj)} is not JSON serializable")

        return json.dumps(task, default=json_serializer)

    @classmethod
    def _deserialize_task(cls, data: str) -> Dict[str, Any]:
        """Deserialize task data from JSON."""
        task = json.loads(data)
        # Convert ISO date strings back to datetime
        for key in ["created_at", "completed_at"]:
            if task.get(key):
                task[key] = datetime.fromisoformat(task[key])
        return task

    @classmethod
    async def get(cls, task_id: str) -> Optional[Dict[str, Any]]:
        """Get task by ID."""
        if redis_service.enabled:
            data = await redis_service.get(f"{cls.PREFIX}{task_id}")
            if data:
                return cls._deserialize_task(json.dumps(data)) if isinstance(data, dict) else None
        return cls._memory_fallback.get(task_id)

    @classmethod
    async def set(cls, task_id: str, task_data: Dict[str, Any]) -> None:
        """Set task data."""
        if redis_service.enabled:
            serialized = cls._serialize_task(task_data)
            await redis_service.redis_client.setex(f"{cls.PREFIX}{task_id}", cls.TTL, serialized)
            # Add to index for listing
            await redis_service.redis_client.sadd(cls.INDEX_KEY, task_id)
        else:
            cls._memory_fallback[task_id] = task_data

    @classmethod
    async def update(cls, task_id: str, updates: Dict[str, Any]) -> None:
        """Update specific fields of a task."""
        task = await cls.get(task_id)
        if task:
            task.update(updates)
            await cls.set(task_id, task)

    @classmethod
    async def delete(cls, task_id: str) -> None:
        """Delete a task."""
        if redis_service.enabled:
            await redis_service.delete(f"{cls.PREFIX}{task_id}")
            await redis_service.redis_client.srem(cls.INDEX_KEY, task_id)
        else:
            cls._memory_fallback.pop(task_id, None)

    @classmethod
    async def get_all(cls) -> List[Dict[str, Any]]:
        """Get all tasks."""
        tasks = []
        if redis_service.enabled:
            # Get all task IDs from index
            task_ids = await redis_service.redis_client.smembers(cls.INDEX_KEY)
            for task_id in task_ids:
                task = await cls.get(task_id)
                if task:
                    tasks.append(task)
        else:
            tasks = list(cls._memory_fallback.values())
        return tasks

    @classmethod
    async def exists(cls, task_id: str) -> bool:
        """Check if task exists."""
        if redis_service.enabled:
            return await redis_service.exists(f"{cls.PREFIX}{task_id}")
        return task_id in cls._memory_fallback


@router.post("/technology-deep-dive", response_model=ResearchOrchestrationResponse)
async def technology_deep_dive(
    request: TechnologyDeepDiveRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    """
    Launch comprehensive technology research with 3 parallel agents:
    - Deep Researcher: Technical analysis, performance, cost
    - Integrator: Integration feasibility assessment
    - Monitor: Current status from HackerNews, GitHub

    This endpoint returns immediately with a task_id. Use GET /research/tasks/{task_id}
    to retrieve results once completed.
    """
    try:
        # Generate task ID
        task_id = str(uuid.uuid4())

        # Create initial task record
        task_record = {
            "task_id": task_id,
            "status": "pending",
            "technology": request.technology_name,
            "created_at": datetime.utcnow(),
            "completed_at": None,
            "results": None,
            "summary": None,
            "error": None,
        }
        await ResearchTaskStorage.set(task_id, task_record)

        # Launch research in background
        async def run_deep_dive():
            try:
                await ResearchTaskStorage.update(task_id, {"status": "running"})

                # Execute research
                report = await research_orchestrator.technology_deep_dive(
                    technology_name=request.technology_name,
                    research_questions=request.research_questions,
                )

                # Convert to API response format
                results = []
                for finding in report.get("research_findings", []):
                    metadata = finding.get("_metadata")
                    result = AgentResult(
                        data=finding,
                        metadata=AgentResultMetadata(**metadata) if metadata else None,
                        error=finding.get("error"),
                    )
                    results.append(result)

                # Update task record
                await ResearchTaskStorage.update(
                    task_id,
                    {
                        "status": "completed",
                        "completed_at": datetime.utcnow(),
                        "results": results,
                        "summary": report.get("summary"),
                    },
                )

                logger.info(f"✅ Deep dive completed for {request.technology_name}: {task_id}")

            except Exception as e:
                logger.error(f"❌ Deep dive failed for {request.technology_name}: {e}")
                await ResearchTaskStorage.update(
                    task_id,
                    {
                        "status": "failed",
                        "completed_at": datetime.utcnow(),
                        "error": str(e),
                    },
                )

        # Add to background tasks
        background_tasks.add_task(run_deep_dive)

        return ResearchOrchestrationResponse(**task_record)

    except Exception as e:
        logger.error(f"Failed to launch technology deep dive: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/launch-agents", response_model=ResearchOrchestrationResponse)
async def launch_multi_agent_research(
    request: MultiAgentLaunchRequest,
    background_tasks: BackgroundTasks,
):
    """
    Launch multiple custom research agents in parallel.

    Allows fine-grained control over agent roles, prompts, and AI models.

    Example request:
    ```json
    {
        "tasks": [
            {
                "role": "deep_researcher",
                "prompt": "Research Rust for audio DSP",
                "model": "anthropic/claude-3.5-sonnet",
                "provider": "openrouter"
            },
            {
                "role": "comparator",
                "prompt": "Compare Rust vs C++ for low-latency audio",
                "model": "openai/gpt-4-turbo"
            }
        ],
        "max_concurrent": 2,
        "project_id": 1
    }
    ```
    """
    try:
        task_id = str(uuid.uuid4())

        # Create initial task record
        task_record = {
            "task_id": task_id,
            "status": "pending",
            "technology": None,
            "created_at": datetime.utcnow(),
            "completed_at": None,
            "results": None,
            "summary": None,
            "error": None,
        }
        await ResearchTaskStorage.set(task_id, task_record)

        # Launch agents in background
        async def run_agents():
            try:
                await ResearchTaskStorage.update(task_id, {"status": "running"})

                # Convert request to orchestrator format
                tasks = []
                for task_req in request.tasks:
                    tasks.append(
                        {
                            "role": task_req.role,
                            "prompt": task_req.prompt,
                            "model": task_req.model,
                            "provider": task_req.provider,
                            "temperature": task_req.temperature,
                            "max_tokens": task_req.max_tokens,
                        }
                    )

                # Execute research
                findings = await research_orchestrator.launch_parallel_research(
                    tasks=tasks,
                    max_concurrent=request.max_concurrent,
                )

                # Convert to API response format
                results = []
                for finding in findings:
                    metadata = finding.get("_metadata")
                    result = AgentResult(
                        data=finding,
                        metadata=AgentResultMetadata(**metadata) if metadata else None,
                        error=finding.get("error"),
                    )
                    results.append(result)

                # Update task record
                await ResearchTaskStorage.update(
                    task_id,
                    {
                        "status": "completed",
                        "completed_at": datetime.utcnow(),
                        "results": results,
                        "summary": f"Completed {len(results)} agent tasks",
                    },
                )

                logger.info(f"✅ Multi-agent research completed: {task_id}")

            except Exception as e:
                logger.error(f"❌ Multi-agent research failed: {e}")
                await ResearchTaskStorage.update(
                    task_id,
                    {
                        "status": "failed",
                        "completed_at": datetime.utcnow(),
                        "error": str(e),
                    },
                )

        background_tasks.add_task(run_agents)

        return ResearchOrchestrationResponse(**task_record)

    except Exception as e:
        logger.error(f"Failed to launch multi-agent research: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/tasks/{task_id}", response_model=ResearchOrchestrationResponse)
async def get_research_task_status(task_id: str):
    """
    Get status and results of a research task.

    Returns task status (pending|running|completed|failed) and results when available.
    """
    task = await ResearchTaskStorage.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Research task not found")

    return ResearchOrchestrationResponse(**task)


@router.post("/technologies/{technology_id}/monitor", response_model=TechnologyMonitorResponse)
async def monitor_technology(
    technology_id: int,
    request: TechnologyMonitorRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Monitor a technology across multiple sources (HackerNews, GitHub, arXiv).

    Returns current monitoring report with alerts for significant events.
    """
    try:
        # Get technology from database
        result = await db.execute(select(Technology).filter(Technology.id == technology_id))
        technology = result.scalar_one_or_none()

        if not technology:
            raise HTTPException(status_code=404, detail="Technology not found")

        # Initialize monitoring data
        monitoring_data = {
            "technology_id": technology_id,
            "technology_name": technology.title,
            "period": f"Last {request.days_back} days",
            "hackernews": None,
            "github": None,
            "arxiv": None,
            "alerts": [],
            "last_updated": datetime.utcnow(),
        }

        # Monitor HackerNews if requested
        if "hackernews" in request.sources:
            try:
                hn_service = HackerNewsService()
                hn_report = await hn_service.monitor_technology(
                    technology_name=technology.title,
                    keywords=(
                        [technology.title, technology.vendor]
                        if technology.vendor
                        else [technology.title]
                    ),
                    days_back=request.days_back,
                )
                monitoring_data["hackernews"] = hn_report

                # Generate alerts from HN data
                if hn_report.get("mentions", 0) > 10:
                    monitoring_data["alerts"].append(
                        MonitoringAlert(
                            type="opportunity",
                            severity="medium",
                            description=f"High HackerNews activity: {hn_report['mentions']} mentions in {request.days_back} days",
                            action_required="Review trending stories for insights",
                        )
                    )

            except Exception as e:
                logger.error(f"HackerNews monitoring failed: {e}")

        # TODO: Add GitHub monitoring
        if "github" in request.sources:
            monitoring_data["github"] = {
                "status": "not_implemented",
                "message": "GitHub monitoring coming in Phase 2",
            }

        # TODO: Add arXiv monitoring
        if "arxiv" in request.sources:
            monitoring_data["arxiv"] = {
                "status": "not_implemented",
                "message": "arXiv monitoring coming in Phase 2",
            }

        # Update technology monitoring fields
        if monitoring_data["hackernews"]:
            technology.last_hn_mention = datetime.utcnow()
            technology.hn_score_avg = monitoring_data["hackernews"].get("avg_score", 0)
            await db.commit()

        return TechnologyMonitorResponse(**monitoring_data)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to monitor technology: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/models", response_model=AvailableModelsResponse)
async def get_available_models():
    """
    Get list of available AI models from all providers.

    Returns models organized by provider with tier, cost, and capability information.
    """
    try:
        # Get model catalog from AI router
        providers_data = {}

        for provider in AIProvider:
            provider_models = []

            # Get models for this provider from ai_router.MODEL_INFO
            for model_id, model_info in ai_router.MODEL_INFO.items():
                if model_info["provider"] == provider.value:
                    provider_models.append(
                        {
                            "model_id": model_id,
                            "tier": model_info["tier"],  # Already a string in MODEL_INFO
                            "cost_per_1m_tokens": model_info.get("cost_per_1m_tokens"),
                            "max_tokens": model_info.get("max_tokens", 4096),
                            "description": model_info.get("description"),
                        }
                    )

            providers_data[provider.value] = provider_models

        return AvailableModelsResponse(
            providers=providers_data,
            default_provider=ai_router.default_provider.value,
            default_model=ai_router.default_model,
        )

    except Exception as e:
        logger.error(f"Failed to get available models: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/summary", response_model=ResearchSummaryResponse)
async def get_research_summary():
    """
    Get summary statistics for all research activities.

    Returns total tasks, completion rates, cost, and performance metrics.
    """
    try:
        all_tasks = await ResearchTaskStorage.get_all()
        total_tasks = len(all_tasks)
        completed_tasks = sum(1 for task in all_tasks if task.get("status") == "completed")
        failed_tasks = sum(1 for task in all_tasks if task.get("status") == "failed")

        # Count total agents deployed
        agents_deployed = 0
        total_execution_time = 0.0
        execution_count = 0

        for task in all_tasks:
            results = task.get("results")
            if results:
                agents_deployed += len(results)
                for result in results:
                    # Handle both dict and Pydantic model results
                    metadata = (
                        result.get("metadata")
                        if isinstance(result, dict)
                        else getattr(result, "metadata", None)
                    )
                    if metadata:
                        exec_time = (
                            metadata.get("execution_time_seconds")
                            if isinstance(metadata, dict)
                            else getattr(metadata, "execution_time_seconds", None)
                        )
                        if exec_time:
                            total_execution_time += exec_time
                            execution_count += 1

        avg_execution_time = total_execution_time / execution_count if execution_count > 0 else 0.0

        # TODO: Calculate actual cost from usage data
        total_cost_usd = 0.0

        return ResearchSummaryResponse(
            total_tasks=total_tasks,
            completed_tasks=completed_tasks,
            failed_tasks=failed_tasks,
            agents_deployed=agents_deployed,
            total_cost_usd=total_cost_usd,
            avg_execution_time_seconds=avg_execution_time,
        )

    except Exception as e:
        logger.error(f"Failed to get research summary: {e}")
        raise HTTPException(status_code=500, detail=str(e))
