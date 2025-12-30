# AI Arena + Research Hub Integration Plan

> **Created**: 2025-12-30
> **Status**: Planning Required
> **Priority**: High

## Current State

- **AI Arena** (`/arena`): Hypothesis validation via multi-model AI debates
  - Create hypotheses with quick input
  - Run validation debates (Analyst, Researcher, Strategist, Critic agents)
  - View evidence and results

- **Research Hub** (`/research`): R&D task management
  - Tasks linked to repositories and technologies
  - Status tracking, priorities
  - No connection to AI Arena

## The Problem

These features are isolated but should work together:
- Research generates questions/hypotheses that need validation
- Validated hypotheses should inform research priorities
- Evidence from debates should link back to research context

## Integration Options

### Option A: Embedded (Research Hub owns hypotheses)
- Add hypothesis creation directly in Research Hub
- Validation triggers from research task context
- Results displayed inline with research tasks
- **Pro**: Seamless UX, single workflow
- **Con**: Tight coupling, complex UI

### Option B: Linked (Bidirectional references)
- Research tasks can link to hypotheses
- Hypotheses can reference source research tasks
- Navigate between views via links
- **Pro**: Loose coupling, simpler implementation
- **Con**: Context switching, two places to look

### Option C: Workflow (Pipeline approach)
- Research task status includes "needs validation"
- One-click "Create Hypothesis" from research task
- Validation results automatically update research task
- **Pro**: Clear flow, maintains separation
- **Con**: More backend work, state management

## Recommended Approach

**Option C (Workflow)** seems best:

1. Add `hypothesis_id` field to ResearchTask model
2. Add "Validate" button on research tasks that creates linked hypothesis
3. When hypothesis validation completes, update research task status
4. Show validation summary on research task detail view

## Data Model Changes

```python
# ResearchTask additions
hypothesis_id: Optional[str]  # Link to hypothesis
validation_status: Optional[str]  # pending, validated, invalidated
validation_summary: Optional[str]  # Brief result from AI Arena
```

## UI Changes

1. **Research Hub Task Card**: Add "Validate" action button
2. **Research Hub Task Detail**: Show validation status/summary if linked
3. **AI Arena**: Show source research task if hypothesis was created from one

## API Changes

```
POST /api/v1/research-tasks/{id}/create-hypothesis
  -> Creates hypothesis linked to research task
  -> Returns hypothesis_id

PATCH /api/v1/hypotheses/{id}/validation-complete
  -> Webhook/callback when validation finishes
  -> Updates linked research task
```

## Next Session Tasks

1. Review this plan
2. Decide on integration approach
3. Create detailed implementation plan
4. Start with data model changes
5. Implement API endpoints
6. Update UI components

## Questions to Resolve

- Should all research tasks be validatable, or only certain types?
- How to handle multiple hypotheses per research task?
- Should validation be automatic or manual trigger?
- How to surface AI Arena insights in Research Hub dashboard?
