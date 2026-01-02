"""
Pipeline Orchestrator - Executes multi-stage agent pipelines.

Pipelines define sequences of persona executions with:
- Sequential and parallel stage execution
- Data passing between stages via templates
- Output aggregation and Graph-Service integration
- Failure handling and retries
"""

from __future__ import annotations

import asyncio
import re
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional

import structlog
import yaml
from jinja2 import BaseLoader, Environment

logger = structlog.get_logger(__name__)

# Default pipelines directory
PIPELINES_DIR = Path(__file__).parent / "pipelines"


@dataclass
class StageResult:
    """Result from executing a pipeline stage."""

    stage_id: str
    success: bool
    output: dict[str, Any]
    duration_seconds: float
    error: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "stage_id": self.stage_id,
            "success": self.success,
            "output": self.output,
            "duration_seconds": self.duration_seconds,
            "error": self.error,
        }


@dataclass
class PipelineResult:
    """Result from executing a pipeline."""

    pipeline_name: str
    success: bool
    stages: dict[str, StageResult]
    output: dict[str, Any]
    duration_seconds: float
    error: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "pipeline_name": self.pipeline_name,
            "success": self.success,
            "stages": {k: v.to_dict() for k, v in self.stages.items()},
            "output": self.output,
            "duration_seconds": self.duration_seconds,
            "error": self.error,
        }


@dataclass
class PipelineStage:
    """Definition of a pipeline stage."""

    id: str
    name: str
    persona: Optional[str] = None
    type: str = "persona"  # persona | action
    description: str = ""
    input_template: str = ""
    output_mapping: dict[str, str] = field(default_factory=dict)
    depends_on: list[str] = field(default_factory=list)
    parallel_with: list[str] = field(default_factory=list)
    timeout_seconds: int = 180
    required: bool = True
    action: Optional[str] = None


@dataclass
class Pipeline:
    """Pipeline definition."""

    name: str
    display_name: str
    description: str
    version: str
    category: str
    config: dict[str, Any]
    input_schema: dict[str, Any]
    output_schema: dict[str, Any]
    stages: list[PipelineStage]
    execution: dict[str, Any]
    hooks: dict[str, list]

    @classmethod
    def from_dict(cls, data: dict) -> "Pipeline":
        """Create Pipeline from dictionary (loaded from YAML)."""
        stages = []
        for s in data.get("stages", []):
            stages.append(
                PipelineStage(
                    id=s["id"],
                    name=s.get("name", s["id"]),
                    persona=s.get("persona"),
                    type=s.get("type", "persona"),
                    description=s.get("description", ""),
                    input_template=s.get("input_template", ""),
                    output_mapping=s.get("output_mapping", {}),
                    depends_on=s.get("depends_on", []),
                    parallel_with=s.get("parallel_with", []),
                    timeout_seconds=s.get("timeout_seconds", 180),
                    required=s.get("required", True),
                    action=s.get("action"),
                )
            )

        return cls(
            name=data["name"],
            display_name=data.get("display_name", data["name"]),
            description=data.get("description", ""),
            version=data.get("version", "1.0.0"),
            category=data.get("category", "custom"),
            config=data.get("config", {}),
            input_schema=data.get("input", {}),
            output_schema=data.get("output", {}),
            stages=stages,
            execution=data.get("execution", {}),
            hooks=data.get("hooks", {}),
        )


class PipelineStore:
    """
    File-based pipeline storage.

    Pipelines are stored as YAML files in a directory.
    """

    def __init__(self, pipelines_dir: Optional[Path] = None):
        self.dir = pipelines_dir or PIPELINES_DIR
        self.dir.mkdir(parents=True, exist_ok=True)

    def list(self, category: Optional[str] = None) -> list[Pipeline]:
        """List all pipelines, optionally filtered by category."""
        pipelines = []
        for f in self.dir.glob("*.yaml"):
            if f.name.startswith("_"):
                continue
            try:
                pipeline = self.get(f.stem)
                if category is None or pipeline.category == category:
                    pipelines.append(pipeline)
            except Exception as e:
                logger.warning("failed_to_load_pipeline", file=f.name, error=str(e))
        return sorted(pipelines, key=lambda p: p.name)

    def get(self, name: str) -> Pipeline:
        """Get a pipeline by name."""
        path = self.dir / f"{name}.yaml"
        if not path.exists():
            raise FileNotFoundError(f"Pipeline not found: {name}")

        with open(path) as f:
            data = yaml.safe_load(f)

        return Pipeline.from_dict(data)

    def exists(self, name: str) -> bool:
        """Check if a pipeline exists."""
        return (self.dir / f"{name}.yaml").exists()


class PipelineExecutor:
    """
    Executes pipelines by orchestrating persona stages.

    Example:
        executor = PipelineExecutor(
            agent_executor=AgentExecutor(repo_url="..."),
        )

        result = await executor.run(
            pipeline="document-intelligence",
            input_data={
                "document_path": "docs/PRD.md",
                "project_id": 1,
            }
        )
    """

    def __init__(
        self,
        pipeline_store: Optional[PipelineStore] = None,
        agent_executor: Optional[Any] = None,  # AgentExecutor
    ):
        self.pipelines = pipeline_store or PipelineStore()
        self.agent_executor = agent_executor
        self.jinja_env = Environment(loader=BaseLoader())

        # Add custom Jinja2 filters
        self.jinja_env.filters["default"] = lambda v, d: v if v is not None else d
        self.jinja_env.filters["length"] = len
        self.jinja_env.filters["join"] = lambda v, sep: sep.join(v) if v else ""

    async def run(
        self,
        pipeline: str,
        input_data: dict[str, Any],
        dry_run: bool = False,
    ) -> PipelineResult:
        """
        Execute a pipeline with the given input data.

        Args:
            pipeline: Pipeline name
            input_data: Input data matching pipeline's input schema
            dry_run: If True, only validate and show execution plan

        Returns:
            PipelineResult with all stage outputs
        """
        start_time = time.time()
        p = self.pipelines.get(pipeline)

        logger.info(
            "pipeline_execution_started",
            pipeline=pipeline,
            stages=len(p.stages),
            input_keys=list(input_data.keys()),
        )

        # Execute on_start hooks
        await self._execute_hooks(p.hooks.get("on_start", []), {"input": input_data})

        # Build execution context
        context = {
            "input": input_data,
            "stages": {},
            "config": p.config,
        }

        stage_results: dict[str, StageResult] = {}
        failed = False
        failed_stage = None

        # Determine execution order
        execution_order = self._compute_execution_order(p)

        for stage_group in execution_order:
            if failed and p.config.get("on_failure") == "stop":
                break

            if isinstance(stage_group, list):
                # Parallel execution
                results = await asyncio.gather(
                    *[
                        self._execute_stage(p, stage_id, context, dry_run)
                        for stage_id in stage_group
                    ],
                    return_exceptions=True,
                )

                for stage_id, result in zip(stage_group, results):
                    if isinstance(result, Exception):
                        stage_results[stage_id] = StageResult(
                            stage_id=stage_id,
                            success=False,
                            output={},
                            duration_seconds=0,
                            error=str(result),
                        )
                        stage = self._get_stage(p, stage_id)
                        if stage and stage.required:
                            failed = True
                            failed_stage = stage_results[stage_id]
                    else:
                        stage_results[stage_id] = result
                        context["stages"][stage_id] = {"output": result.output}
                        if not result.success:
                            stage = self._get_stage(p, stage_id)
                            if stage and stage.required:
                                failed = True
                                failed_stage = result
            else:
                # Sequential execution
                result = await self._execute_stage(p, stage_group, context, dry_run)
                stage_results[stage_group] = result
                context["stages"][stage_group] = {"output": result.output}

                if not result.success:
                    stage = self._get_stage(p, stage_group)
                    if stage and stage.required:
                        failed = True
                        failed_stage = result

                # Execute on_stage_complete hook
                await self._execute_hooks(
                    p.hooks.get("on_stage_complete", []),
                    {**context, "stage": result.to_dict()},
                )

        duration = time.time() - start_time

        # Build final output
        output = self._build_output(p, context)

        # Execute completion hooks
        if failed:
            await self._execute_hooks(
                p.hooks.get("on_failure", []),
                {**context, "failed_stage": failed_stage.to_dict() if failed_stage else {}},
            )
        else:
            await self._execute_hooks(
                p.hooks.get("on_complete", []),
                {**context, "output": output},
            )

        logger.info(
            "pipeline_execution_completed",
            pipeline=pipeline,
            success=not failed,
            duration=duration,
            stages_completed=len(stage_results),
        )

        return PipelineResult(
            pipeline_name=pipeline,
            success=not failed,
            stages=stage_results,
            output=output,
            duration_seconds=duration,
            error=failed_stage.error if failed_stage else None,
        )

    async def _execute_stage(
        self,
        pipeline: Pipeline,
        stage_id: str,
        context: dict[str, Any],
        dry_run: bool,
    ) -> StageResult:
        """Execute a single pipeline stage."""
        stage = self._get_stage(pipeline, stage_id)
        if not stage:
            return StageResult(
                stage_id=stage_id,
                success=False,
                output={},
                duration_seconds=0,
                error=f"Stage not found: {stage_id}",
            )

        start_time = time.time()

        logger.info(
            "stage_execution_started",
            pipeline=pipeline.name,
            stage=stage_id,
            type=stage.type,
        )

        try:
            if dry_run:
                # Just render the input template to validate
                rendered_input = self._render_template(stage.input_template, context)
                return StageResult(
                    stage_id=stage_id,
                    success=True,
                    output={"dry_run": True, "rendered_input": rendered_input[:500]},
                    duration_seconds=time.time() - start_time,
                )

            if stage.type == "persona" and stage.persona:
                # Execute via agent executor
                rendered_input = self._render_template(stage.input_template, context)

                if self.agent_executor:
                    result = await self.agent_executor.run(
                        persona=stage.persona,
                        task=rendered_input,
                        max_turns=30,
                    )
                    output = self._parse_json_output(result.sandbox_result.output)
                else:
                    # No executor - return mock for testing
                    output = {"mock": True, "stage": stage_id}

                # Apply output mapping
                mapped_output = self._apply_output_mapping(output, stage.output_mapping)

                return StageResult(
                    stage_id=stage_id,
                    success=True,
                    output=mapped_output,
                    duration_seconds=time.time() - start_time,
                )

            elif stage.type == "action" and stage.action:
                # Execute action (e.g., graph_service.ingest_document_intelligence)
                rendered_input = self._render_dict_template(stage.input_template, context)
                output = await self._execute_action(stage.action, rendered_input)

                return StageResult(
                    stage_id=stage_id,
                    success=True,
                    output=output,
                    duration_seconds=time.time() - start_time,
                )

            else:
                return StageResult(
                    stage_id=stage_id,
                    success=False,
                    output={},
                    duration_seconds=time.time() - start_time,
                    error="Invalid stage configuration: no persona or action",
                )

        except Exception as e:
            logger.error(
                "stage_execution_failed",
                pipeline=pipeline.name,
                stage=stage_id,
                error=str(e),
            )
            return StageResult(
                stage_id=stage_id,
                success=False,
                output={},
                duration_seconds=time.time() - start_time,
                error=str(e),
            )

    def _get_stage(self, pipeline: Pipeline, stage_id: str) -> Optional[PipelineStage]:
        """Get a stage by ID."""
        for stage in pipeline.stages:
            if stage.id == stage_id:
                return stage
        return None

    def _compute_execution_order(self, pipeline: Pipeline) -> list:
        """
        Compute execution order respecting dependencies.

        Returns a list where each element is either:
        - A string (single stage to execute)
        - A list of strings (stages to execute in parallel)
        """
        # Use explicit order if provided
        if "order" in pipeline.execution:
            return pipeline.execution["order"]

        # Otherwise, compute from dependencies
        executed = set()
        order = []

        while len(executed) < len(pipeline.stages):
            # Find stages ready to execute
            ready = []
            for stage in pipeline.stages:
                if stage.id in executed:
                    continue
                # Check if all dependencies are satisfied
                if all(dep in executed for dep in stage.depends_on):
                    ready.append(stage.id)

            if not ready:
                # No progress - circular dependency or error
                remaining = [s.id for s in pipeline.stages if s.id not in executed]
                logger.warning("pipeline_circular_dependency", remaining=remaining)
                order.extend(remaining)
                break

            # Group stages that can run in parallel
            parallel_group = []
            sequential = []

            for stage_id in ready:
                stage = self._get_stage(pipeline, stage_id)
                if stage and stage.parallel_with:
                    # Check if any parallel_with stages are also ready
                    parallel_partners = [s for s in stage.parallel_with if s in ready]
                    if parallel_partners:
                        parallel_group.append(stage_id)
                    else:
                        sequential.append(stage_id)
                else:
                    sequential.append(stage_id)

            # Add parallel group if any
            if len(parallel_group) > 1:
                order.append(parallel_group)
                executed.update(parallel_group)
            elif parallel_group:
                order.append(parallel_group[0])
                executed.add(parallel_group[0])

            # Add sequential stages
            for stage_id in sequential:
                if stage_id not in executed:
                    order.append(stage_id)
                    executed.add(stage_id)

        return order

    def _render_template(self, template: str, context: dict) -> str:
        """Render a Jinja2 template with the given context."""
        try:
            t = self.jinja_env.from_string(template)
            return t.render(**context)
        except Exception as e:
            logger.warning("template_render_failed", error=str(e))
            return template

    def _render_dict_template(self, template: Any, context: dict) -> Any:
        """Recursively render templates in a dictionary."""
        if isinstance(template, str):
            return self._render_template(template, context)
        elif isinstance(template, dict):
            return {k: self._render_dict_template(v, context) for k, v in template.items()}
        elif isinstance(template, list):
            return [self._render_dict_template(v, context) for v in template]
        else:
            return template

    def _apply_output_mapping(self, output: dict, mapping: dict[str, str]) -> dict[str, Any]:
        """Apply JSONPath-like output mapping."""
        if not mapping:
            return output

        result = {}
        for key, path in mapping.items():
            # Simple JSONPath: $.foo.bar
            value = self._jsonpath_get(output, path)
            if value is not None:
                result[key] = value

        return result

    def _jsonpath_get(self, data: Any, path: str) -> Any:
        """Simple JSONPath getter (supports $.foo.bar syntax)."""
        if not path.startswith("$."):
            return data.get(path) if isinstance(data, dict) else None

        parts = path[2:].split(".")
        current = data

        for part in parts:
            if isinstance(current, dict):
                current = current.get(part)
            elif isinstance(current, list) and part.isdigit():
                idx = int(part)
                current = current[idx] if idx < len(current) else None
            else:
                return None

        return current

    def _parse_json_output(self, output: str) -> dict:
        """Parse JSON from agent output (handles markdown code blocks)."""
        import json

        # Try to extract JSON from markdown code blocks
        json_match = re.search(r"```(?:json)?\s*([\s\S]*?)```", output)
        if json_match:
            try:
                return json.loads(json_match.group(1))
            except json.JSONDecodeError:
                pass

        # Try to parse the whole output as JSON
        try:
            return json.loads(output)
        except json.JSONDecodeError:
            pass

        # Return as-is in a wrapper
        return {"raw_output": output}

    async def _execute_action(self, action: str, input_data: dict) -> dict:
        """Execute a named action (e.g., graph_service.ingest_document_intelligence)."""
        logger.info("executing_action", action=action, input_keys=list(input_data.keys()))

        # Action dispatch - would be expanded with actual implementations
        if action == "graph_service.ingest_document_intelligence":
            # This would call the actual Graph-Service
            return {
                "action": action,
                "status": "success",
                "message": "Document intelligence data ingested",
                "input_received": input_data,
            }
        else:
            return {
                "action": action,
                "status": "unknown_action",
            }

    def _build_output(self, pipeline: Pipeline, context: dict) -> dict[str, Any]:
        """Build the final pipeline output from stage results."""
        output = {}

        for stage_id, stage_data in context.get("stages", {}).items():
            stage_output = stage_data.get("output", {})
            # Merge stage outputs into final output
            output[stage_id] = stage_output

        return output

    async def _execute_hooks(self, hooks: list, context: dict) -> None:
        """Execute pipeline hooks."""
        for hook in hooks:
            if isinstance(hook, dict):
                if "log" in hook:
                    msg = self._render_template(hook["log"], context)
                    logger.info("pipeline_hook", message=msg)
                elif "emit_event" in hook:
                    event = hook["emit_event"]
                    subject = self._render_template(event.get("subject", ""), context)
                    payload = self._render_dict_template(event.get("payload", {}), context)
                    logger.info("pipeline_event", subject=subject, payload=payload)
                    # Would emit to NATS here
