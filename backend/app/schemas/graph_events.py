"""
NATS Event Schemas for Phase 7 Graph Service

Defines Pydantic models for events published/consumed via NATS.
Subject naming convention: {domain}.{action}.{kind}
"""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field

from app.models.graph import AuditKind, AuditStatus

# Audit Events


class AuditRequestedEvent(BaseModel):
    """Event published when audit is requested.

    Subject: audit.requested.{kind}
    Published by: GraphService.trigger_audit()
    Consumed by: Audit agents
    """

    audit_id: int = Field(..., description="Database audit ID")
    project_id: int = Field(..., description="Project scope")
    target_entity: str = Field(..., description="Table name (graph_files, graph_symbols, etc)")
    target_id: int = Field(..., description="Entity ID to audit")
    kind: AuditKind = Field(..., description="Audit type (codeReview, security, etc)")
    correlation_id: Optional[UUID] = Field(None, description="Request correlation ID")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Event creation time")


class AuditResultEvent(BaseModel):
    """Event published when audit completes.

    Subject: audit.result.{kind}
    Published by: Audit agents
    Consumed by: GraphService.start_audit_result_consumer()
    """

    audit_id: int = Field(..., description="Database audit ID (from request)")
    status: AuditStatus = Field(..., description="Audit result status (completed, failed)")
    summary: str = Field(..., description="Human-readable audit summary")
    report_path: Optional[str] = Field(None, description="Path to detailed report file")
    score: Optional[float] = Field(None, ge=0.0, le=10.0, description="Quality score (0-10)")
    findings: Optional[dict] = Field(None, description="Structured audit findings")
    correlation_id: Optional[UUID] = Field(None, description="Request correlation ID")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Event creation time")


# Graph Update Events (Real-time UI synchronization)


class GraphIndexedEvent(BaseModel):
    """Event published when code is indexed.

    Subject: graph.indexed.{project_id}
    Published by: graph_indexer CLI
    Consumed by: Frontend WebSocket subscriptions (future)
    """

    project_id: int = Field(..., description="Project scope")
    repo_id: int = Field(..., description="Repository ID")
    files_processed: int = Field(..., description="Number of files indexed")
    symbols_extracted: int = Field(..., description="Number of symbols extracted")
    todos_extracted: int = Field(..., description="Number of TODO/FIXME comments extracted")
    incremental: bool = Field(..., description="Whether this was incremental or full index")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Event creation time")


class GraphSymbolAddedEvent(BaseModel):
    """Event published when new symbol is indexed.

    Subject: graph.symbol.added
    Published by: graph_indexer CLI (optional, high-volume)
    Consumed by: Real-time symbol index updates
    """

    symbol_id: int = Field(..., description="GraphSymbol ID")
    project_id: int = Field(..., description="Project scope")
    qualified_name: str = Field(..., description="Fully qualified symbol name")
    kind: str = Field(..., description="Symbol kind (function, class, etc)")
    file_path: str = Field(..., description="File path relative to repo root")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Event creation time")


class GraphTaskCreatedEvent(BaseModel):
    """Event published when task is created.

    Subject: graph.task.created
    Published by: GraphService.create_task()
    Consumed by: Project tracking systems, notifications
    """

    task_id: int = Field(..., description="GraphTask ID")
    project_id: int = Field(..., description="Project scope")
    title: str = Field(..., description="Task title")
    kind: str = Field(..., description="Task kind (feature, bug, etc)")
    spec_item_id: Optional[int] = Field(None, description="Linked spec item ID")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Event creation time")


class GraphUpdatedEvent(BaseModel):
    """Generic graph update event for cache invalidation.

    Subject: graph.updated.{project_id}
    Published by: Any mutation operation in GraphService
    Consumed by: Frontend cache invalidation, dashboard updates
    """

    project_id: int = Field(..., description="Project scope")
    entity_type: str = Field(
        ..., description="Updated entity type (repo, file, symbol, task, spec, audit)"
    )
    entity_id: int = Field(..., description="Updated entity ID")
    operation: str = Field(..., description="Operation type (created, updated, deleted)")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Event creation time")
