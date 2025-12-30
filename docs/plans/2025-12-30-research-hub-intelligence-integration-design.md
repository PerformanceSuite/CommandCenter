# Research Hub Intelligence Integration Design

> **Created**: 2025-12-30
> **Status**: Approved
> **Priority**: High

## Overview

Integrate AI Arena hypothesis validation into Research Hub as a seamless intelligence system. Research Hub becomes the single home for all research intelligence work. Hypothesis validation is a capability within research context, not a separate feature.

### Design Principles

1. **Research Hub is home base** - all research intelligence work happens here
2. **Everything has a parent** - Project → Research Task → Hypothesis → Evidence/Debates
3. **KnowledgeBeast is the connective tissue** - findings, hypotheses, and evidence indexed for RAG
4. **AI suggests, user confirms** - automation with human control
5. **No orphaned data** - standalone AI Arena route removed entirely

### The Intelligence Loop

```
Research Agents produce Findings
    → Findings indexed in KnowledgeBeast
    → Findings suggest Hypotheses
        → Validation queries KnowledgeBeast for context
        → Debate produces Evidence + Verdict
            → Validated knowledge indexed in KnowledgeBeast
            → Gaps suggest new Research Tasks
                → (cycle continues)
```

---

## Data Model

### New Models

#### Hypothesis

```python
# backend/app/models/hypothesis.py
class Hypothesis(Base):
    __tablename__ = "hypotheses"

    id: Mapped[int] = mapped_column(primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"))
    research_task_id: Mapped[int] = mapped_column(ForeignKey("research_tasks.id", ondelete="CASCADE"))

    statement: Mapped[str]
    category: Mapped[str]  # customer, problem, solution, technical, market, regulatory, competitive, gtm
    status: Mapped[str] = mapped_column(default="untested")  # untested, validating, validated, invalidated, needs_more_data

    impact: Mapped[str] = mapped_column(default="medium")  # high, medium, low
    risk: Mapped[str] = mapped_column(default="medium")  # high, medium, low
    priority_score: Mapped[float] = mapped_column(default=0.0)
    validation_score: Mapped[Optional[float]]

    # KnowledgeBeast reference - indexed when validated
    knowledge_entry_id: Mapped[Optional[str]]

    created_at: Mapped[datetime]
    updated_at: Mapped[datetime]

    # Relationships
    research_task: Mapped["ResearchTask"] = relationship(back_populates="hypotheses")
    evidence: Mapped[List["Evidence"]] = relationship(cascade="all, delete-orphan")
    debates: Mapped[List["Debate"]] = relationship(cascade="all, delete-orphan")
```

#### Evidence

```python
class Evidence(Base):
    __tablename__ = "evidence"

    id: Mapped[int] = mapped_column(primary_key=True)
    hypothesis_id: Mapped[int] = mapped_column(ForeignKey("hypotheses.id", ondelete="CASCADE"))

    content: Mapped[str]
    source_type: Mapped[str]  # research_finding, knowledge_base, manual, external
    source_id: Mapped[Optional[str]]  # finding_id or KB doc ID
    stance: Mapped[str]  # supporting, contradicting, neutral
    confidence: Mapped[float]

    created_at: Mapped[datetime]
```

#### Debate

```python
class Debate(Base):
    __tablename__ = "debates"

    id: Mapped[int] = mapped_column(primary_key=True)
    hypothesis_id: Mapped[int] = mapped_column(ForeignKey("hypotheses.id", ondelete="CASCADE"))

    status: Mapped[str]  # pending, running, completed, failed
    rounds_requested: Mapped[int]
    rounds_completed: Mapped[int] = mapped_column(default=0)
    agents_used: Mapped[List[str]]  # JSON array

    consensus_level: Mapped[Optional[str]]  # strong, moderate, weak, deadlock
    final_verdict: Mapped[Optional[str]]  # validated, invalidated, needs_more_data
    verdict_reasoning: Mapped[Optional[str]]
    gap_analysis: Mapped[Optional[str]]  # JSON - what's missing for validation
    suggested_research: Mapped[Optional[str]]  # JSON - suggested follow-up tasks

    # Full debate transcript stored in KnowledgeBeast for RAG
    knowledge_entry_id: Mapped[Optional[str]]

    started_at: Mapped[datetime]
    completed_at: Mapped[Optional[datetime]]
```

#### ResearchFinding

```python
class ResearchFinding(Base):
    """Individual findings from research agent runs - indexed in KB"""
    __tablename__ = "research_findings"

    id: Mapped[int] = mapped_column(primary_key=True)
    research_task_id: Mapped[int] = mapped_column(ForeignKey("research_tasks.id", ondelete="CASCADE"))

    content: Mapped[str]
    finding_type: Mapped[str]  # fact, claim, insight, question, recommendation
    agent_role: Mapped[str]  # which agent produced this
    confidence: Mapped[float]
    sources: Mapped[Optional[str]]  # JSON array of source URLs/references

    # KnowledgeBeast reference
    knowledge_entry_id: Mapped[Optional[str]]

    created_at: Mapped[datetime]
```

### ResearchTask Modifications

```python
# Add to existing ResearchTask model
hypotheses: Mapped[List["Hypothesis"]] = relationship(back_populates="research_task", cascade="all, delete-orphan")
findings: Mapped[List["ResearchFinding"]] = relationship(cascade="all, delete-orphan")
task_type: Mapped[str] = mapped_column(default="research")  # research, ad_hoc_hypothesis
```

### KnowledgeBeast Collections

Per-project collections:
- `project_{id}_findings` - Research findings from agent runs
- `project_{id}_hypotheses` - Validated hypotheses with debate context
- `project_{id}_evidence` - Evidence corpus

---

## API Design

### Hypothesis Endpoints (under Research Tasks)

```
# List hypotheses for a task
GET /api/v1/research-tasks/{task_id}/hypotheses

# Create hypothesis under a task
POST /api/v1/research-tasks/{task_id}/hypotheses
Body: { statement, category, impact?, risk? }

# Quick hypothesis (auto-creates minimal parent task)
POST /api/v1/projects/{project_id}/quick-hypothesis
Body: { statement, category, context? }
Returns: { hypothesis_id, research_task_id }

# Get hypothesis detail
GET /api/v1/hypotheses/{id}

# Update hypothesis
PATCH /api/v1/hypotheses/{id}

# Delete hypothesis
DELETE /api/v1/hypotheses/{id}
```

### Validation Endpoints

```
# Start validation - queries KnowledgeBeast for context
POST /api/v1/hypotheses/{id}/validate
Body: { agents: ["analyst", "researcher", "strategist", "critic"], rounds: 3 }
Returns: { debate_id, status: "pending" }

# Get debate status/result
GET /api/v1/debates/{id}

# Get suggested research tasks from gap analysis
GET /api/v1/debates/{id}/suggested-tasks

# Create research task from suggestion (one-click)
POST /api/v1/debates/{id}/create-task-from-gap
Body: { suggestion_index: 0 }
Returns: { research_task_id }
```

### Evidence Endpoints

```
# List evidence for hypothesis
GET /api/v1/hypotheses/{id}/evidence

# Add evidence manually
POST /api/v1/hypotheses/{id}/evidence
Body: { content, stance, source_type: "manual" }

# Get AI-suggested evidence (from task findings + KnowledgeBeast)
GET /api/v1/hypotheses/{id}/suggested-evidence

# Accept suggested evidence
POST /api/v1/hypotheses/{id}/evidence/accept
Body: { suggestions: [0, 2, 3] }
```

### Research Findings Endpoints

```
# List findings for a task
GET /api/v1/research-tasks/{task_id}/findings

# Index finding to KnowledgeBeast
POST /api/v1/findings/{id}/index

# Bulk index all task findings
POST /api/v1/research-tasks/{task_id}/index-findings
```

### Intelligence Dashboard Endpoints

```
# Combined stats for project
GET /api/v1/projects/{project_id}/intelligence/summary
Returns: {
  research_tasks: { total, by_status },
  hypotheses: { total, validated, invalidated, needs_data, untested },
  knowledge_base: { documents, findings_indexed, hypotheses_indexed },
  gaps: { open_count, oldest_gap }
}

# All hypotheses needing attention
GET /api/v1/projects/{project_id}/intelligence/needs-attention

# Recent validations
GET /api/v1/projects/{project_id}/intelligence/recent-validations
```

### Removed Endpoints

All `/api/v1/hypotheses/*` standalone routes removed.

---

## Frontend Architecture

### Directory Structure

```
frontend/src/components/ResearchHub/
├── ResearchHubView.tsx              # Main container - updated tabs
├── tabs/
│   ├── DeepDiveTab.tsx              # Existing
│   ├── CustomAgentsTab.tsx          # Existing
│   ├── TaskListTab.tsx              # Enhanced - hypothesis counts
│   └── IntelligenceTab.tsx          # NEW - replaces Summary
├── tasks/
│   ├── ResearchTaskCard.tsx         # Enhanced - hypothesis badge
│   ├── ResearchTaskDetail.tsx       # Enhanced - hypotheses section
│   ├── ResearchTaskForm.tsx         # Existing
│   └── FindingsList.tsx             # NEW
├── hypotheses/
│   ├── HypothesisSection.tsx        # Hypotheses panel in task detail
│   ├── HypothesisCard.tsx           # Migrated from AI Arena
│   ├── HypothesisForm.tsx           # Create/edit
│   ├── QuickHypothesisInput.tsx     # Quick create (auto-parents)
│   └── SuggestedEvidence.tsx        # AI suggestions
├── validation/
│   ├── ValidationModal.tsx          # Configure & launch
│   ├── DebateViewer.tsx             # Migrated - debate rounds
│   ├── GapAnalysis.tsx              # NEW
│   └── SuggestedTasks.tsx           # NEW - one-click creation
├── intelligence/
│   ├── IntelligenceDashboard.tsx    # Combined stats
│   ├── NeedsAttentionList.tsx       # Hypotheses needing work
│   ├── RecentValidations.tsx        # Activity feed
│   ├── KnowledgeStats.tsx           # KB indexing status
│   └── ResearchCycleViz.tsx         # Visual cycle diagram
└── common/
    ├── StatusBadge.tsx
    └── ConfidenceBar.tsx
```

### Tab Structure

```typescript
const tabs = [
  { id: 'deep-dive', label: 'Deep Dive', icon: SearchIcon },
  { id: 'agents', label: 'Custom Agents', icon: BotIcon },
  { id: 'tasks', label: 'Tasks', icon: ListIcon },
  { id: 'intelligence', label: 'Intelligence', icon: BrainIcon },  // NEW
];
```

### Removed

- `/frontend/src/components/AIArena/` - entire directory
- `/frontend/src/services/hypothesesApi.ts`
- `/arena` route from App.tsx
- AI Arena navigation link

---

## Service Layer

### IntelligenceService (NEW)

```python
# backend/app/services/intelligence_service.py
class IntelligenceService:
    """Orchestrates the research → validate → learn cycle"""

    async def suggest_evidence(self, hypothesis_id: int) -> List[EvidenceSuggestion]:
        """
        1. Get hypothesis and its parent task
        2. Query task's findings for relevant content
        3. Query KnowledgeBeast for related knowledge
        4. Rank by relevance to hypothesis statement
        5. Return suggestions with source attribution
        """

    async def prepare_validation_context(self, hypothesis_id: int) -> ValidationContext:
        """
        Build context package for debate agents:
        - Hypothesis statement + metadata
        - Parent task description + findings
        - Linked evidence
        - RAG query to KB for related validated hypotheses
        - RAG query for contradicting evidence
        """

    async def process_validation_result(self, debate: Debate) -> None:
        """
        After debate completes:
        1. Update hypothesis status based on verdict
        2. Parse gap analysis into structured suggestions
        3. If validated: index hypothesis + reasoning to KB
        4. If needs_more_data: prepare suggested research tasks
        """

    async def index_research_findings(self, task_id: int) -> int:
        """
        Parse agent results into discrete findings,
        index each to KnowledgeBeast with metadata.
        Returns count indexed.
        """

    async def create_task_from_gap(self, debate_id: int, suggestion_index: int) -> ResearchTask:
        """
        Create research task from gap analysis suggestion.
        Links back to originating hypothesis.
        """
```

### HypothesisValidator (MODIFIED)

```python
class HypothesisValidator:
    """Multi-agent debate with knowledge context"""

    async def validate(
        self,
        hypothesis: Hypothesis,
        context: ValidationContext,  # NEW - includes KB context
        agents: List[str],
        rounds: int
    ) -> DebateResult:
        """
        Each agent receives:
        - Hypothesis statement
        - Research task context
        - Existing evidence
        - Relevant knowledge from KB (RAG results)

        Agents can cite KB sources in their reasoning.
        """

    async def generate_gap_analysis(self, debate_result: DebateResult) -> GapAnalysis:
        """
        When verdict is 'needs_more_data':
        - Identify specific missing information
        - Generate research task suggestions
        - Estimate effort/complexity
        """
```

### KnowledgeBeastService (ENHANCED)

```python
class KnowledgeBeastService:

    async def index_finding(self, project_id: int, finding: ResearchFinding) -> str:
        """Index single finding, return doc ID"""
        collection = f"project_{project_id}_findings"
        return await self.add_document(
            collection=collection,
            content=finding.content,
            metadata={
                "finding_id": finding.id,
                "task_id": finding.research_task_id,
                "type": finding.finding_type,
                "agent": finding.agent_role,
                "confidence": finding.confidence,
            }
        )

    async def index_validated_hypothesis(
        self,
        project_id: int,
        hypothesis: Hypothesis,
        debate: Debate
    ) -> str:
        """Index hypothesis with debate reasoning"""
        collection = f"project_{project_id}_hypotheses"
        content = f"""
        Hypothesis: {hypothesis.statement}
        Verdict: {debate.final_verdict}
        Confidence: {hypothesis.validation_score}
        Reasoning: {debate.verdict_reasoning}
        """
        return await self.add_document(
            collection=collection,
            content=content,
            metadata={
                "hypothesis_id": hypothesis.id,
                "category": hypothesis.category,
                "status": hypothesis.status,
                "validation_score": hypothesis.validation_score,
            }
        )

    async def query_for_evidence(
        self,
        project_id: int,
        hypothesis_statement: str,
        limit: int = 10
    ) -> List[KBResult]:
        """Search all collections for relevant evidence"""
        results = []
        for collection in ["findings", "hypotheses", "documents"]:
            hits = await self.query(
                collection=f"project_{project_id}_{collection}",
                query=hypothesis_statement,
                limit=limit // 3
            )
            results.extend(hits)
        return sorted(results, key=lambda x: x.score, reverse=True)[:limit]
```

---

## Implementation Phases

### Phase 1: Data Foundation
- [ ] Create Hypothesis, Evidence, Debate, ResearchFinding models
- [ ] Create Alembic migrations
- [ ] Add relationships to ResearchTask model
- [ ] Migrate existing in-memory hypotheses to database (if any worth keeping)
- [ ] Add KB collection initialization for projects

### Phase 2: Core Services
- [ ] Create IntelligenceService with basic methods
- [ ] Modify HypothesisValidator to accept ValidationContext
- [ ] Add KnowledgeBeast indexing methods for findings/hypotheses
- [ ] Create hypothesis CRUD operations under research tasks
- [ ] Implement auto-parent task creation for quick hypotheses

### Phase 3: API Layer
- [ ] Create new hypothesis routes under /research-tasks/{id}/hypotheses
- [ ] Create /projects/{id}/quick-hypothesis endpoint
- [ ] Create evidence suggestion endpoint
- [ ] Create gap analysis → task creation endpoint
- [ ] Create intelligence dashboard endpoints
- [ ] Remove old /api/v1/hypotheses/* routes

### Phase 4: Frontend - Task Integration
- [ ] Create hypotheses/ component directory (migrate from AIArena)
- [ ] Add HypothesisSection to ResearchTaskDetail
- [ ] Add hypothesis count badge to ResearchTaskCard
- [ ] Implement create hypothesis flow from task context
- [ ] Implement validation modal + debate viewer

### Phase 5: Frontend - Evidence & Gaps
- [ ] Implement SuggestedEvidence component
- [ ] Implement evidence accept/reject flow
- [ ] Implement GapAnalysis display
- [ ] Implement SuggestedTasks with one-click creation
- [ ] Wire up KB queries for evidence suggestions

### Phase 6: Intelligence Dashboard
- [ ] Create IntelligenceTab replacing Summary
- [ ] Build IntelligenceDashboard with combined stats
- [ ] Build NeedsAttentionList
- [ ] Build RecentValidations feed
- [ ] Add KnowledgeStats showing indexing status

### Phase 7: Knowledge Flow Automation
- [ ] Auto-index findings when research task completes
- [ ] Auto-index hypothesis when validation completes (if validated)
- [ ] Wire evidence suggestions to query KB
- [ ] Add ValidationContext KB enrichment
- [ ] Test full cycle: research → findings → hypothesis → validate → gaps → research

### Phase 8: Cleanup & Polish
- [ ] Remove /frontend/src/components/AIArena/ directory
- [ ] Remove /arena route from App.tsx
- [ ] Remove hypothesesApi.ts
- [ ] Update navigation (remove AI Arena link)
- [ ] Update any documentation referencing AI Arena
- [ ] Test all flows end-to-end

---

## Risk Areas

| Risk | Mitigation |
|------|------------|
| KB indexing performance with large finding sets | Batch indexing, async processing, progress indicators |
| Debate agent context window with rich KB results | Limit KB results, summarize context, prioritize by relevance |
| Migration of existing hypothesis data | Audit existing data first, create migration script |
| Frontend complexity with embedded validation | Incremental migration, keep components modular |

---

## Success Criteria

1. **Single workspace**: All research intelligence work happens in Research Hub
2. **Seamless flow**: Research → Hypothesis → Validation → Gaps → Research with minimal friction
3. **Knowledge accumulation**: Findings and validated hypotheses build searchable knowledge base
4. **AI assistance**: Evidence suggestions and gap analysis reduce manual work
5. **No orphans**: Every hypothesis has research context, every finding is indexed

---

## Questions Resolved

| Question | Decision |
|----------|----------|
| Should all hypotheses require a parent task? | Yes, via auto-parent for quick hypotheses |
| How should evidence flow? | AI-suggested with user confirmation |
| How should gaps become tasks? | Suggested tasks with one-click creation |
| What happens to /arena? | Removed entirely |
| KnowledgeBeast integration? | Full integration - findings, hypotheses, evidence all indexed |
