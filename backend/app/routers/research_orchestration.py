"""
Research Orchestration API Router

Provides endpoints for multi-agent research workflow:
- Technology deep dive with parallel agents
- Custom multi-agent task launching
- Technology monitoring (HackerNews, GitHub, arXiv)
- Model selection and provider management
"""

import logging
import uuid
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.models.technology import Technology
from app.schemas.research import (
    TechnologyDeepDiveRequest,
    MultiAgentLaunchRequest,
    ResearchOrchestrationResponse,
    TechnologyMonitorRequest,
    TechnologyMonitorResponse,
    AvailableModelsResponse,
    ResearchSummaryResponse,
    AgentResult,
    AgentResultMetadata,
    MonitoringAlert,
    ModelInfo,
)
from app.services.research_agent_orchestrator import (
    research_orchestrator,
    AgentRole,
)
from app.services.hackernews_service import HackerNewsService
from app.services.ai_router import ai_router, AIProvider, ModelTier

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/research", tags=["research"])

# In-memory task storage (TODO: Move to Redis or database)
research_tasks = {}


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
        research_tasks[task_id] = task_record

        # Launch research in background
        async def run_deep_dive():
            try:
                research_tasks[task_id]["status"] = "running"

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
                research_tasks[task_id].update({
                    "status": "completed",
                    "completed_at": datetime.utcnow(),
                    "results": results,
                    "summary": report.get("summary"),
                })

                logger.info(f"✅ Deep dive completed for {request.technology_name}: {task_id}")

            except Exception as e:
                logger.error(f"❌ Deep dive failed for {request.technology_name}: {e}")
                research_tasks[task_id].update({
                    "status": "failed",
                    "completed_at": datetime.utcnow(),
                    "error": str(e),
                })

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
        research_tasks[task_id] = task_record

        # Launch agents in background
        async def run_agents():
            try:
                research_tasks[task_id]["status"] = "running"

                # Convert request to orchestrator format
                tasks = []
                for task_req in request.tasks:
                    tasks.append({
                        "role": task_req.role,
                        "prompt": task_req.prompt,
                        "model": task_req.model,
                        "provider": task_req.provider,
                        "temperature": task_req.temperature,
                        "max_tokens": task_req.max_tokens,
                    })

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
                research_tasks[task_id].update({
                    "status": "completed",
                    "completed_at": datetime.utcnow(),
                    "results": results,
                    "summary": f"Completed {len(results)} agent tasks",
                })

                logger.info(f"✅ Multi-agent research completed: {task_id}")

            except Exception as e:
                logger.error(f"❌ Multi-agent research failed: {e}")
                research_tasks[task_id].update({
                    "status": "failed",
                    "completed_at": datetime.utcnow(),
                    "error": str(e),
                })

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
    if task_id not in research_tasks:
        raise HTTPException(status_code=404, detail="Research task not found")

    return ResearchOrchestrationResponse(**research_tasks[task_id])


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
        result = await db.execute(
            select(Technology).filter(Technology.id == technology_id)
        )
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
                    keywords=[technology.title, technology.vendor] if technology.vendor else [technology.title],
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
                    provider_models.append({
                        "model_id": model_id,
                        "tier": model_info["tier"].value,
                        "cost_per_1m_tokens": model_info.get("cost_per_1m_tokens"),
                        "max_tokens": model_info.get("max_tokens", 4096),
                        "description": model_info.get("description"),
                    })

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
        total_tasks = len(research_tasks)
        completed_tasks = sum(1 for task in research_tasks.values() if task["status"] == "completed")
        failed_tasks = sum(1 for task in research_tasks.values() if task["status"] == "failed")

        # Count total agents deployed
        agents_deployed = 0
        total_execution_time = 0.0
        execution_count = 0

        for task in research_tasks.values():
            if task.get("results"):
                agents_deployed += len(task["results"])
                for result in task["results"]:
                    if result.metadata and result.metadata.execution_time_seconds:
                        total_execution_time += result.metadata.execution_time_seconds
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
