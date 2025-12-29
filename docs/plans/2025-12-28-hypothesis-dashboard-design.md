# Hypothesis Dashboard Design

**Date**: 2025-12-28
**Status**: Ready for Implementation
**Phase**: 5.1-5.3 of AI Arena Implementation

---

## Overview

Build a Hypothesis Dashboard UI in the Hub frontend that displays hypotheses from CommandCenter, allows triggering validation debates, and shows results. This is the primary user interface for the AI Arena hypothesis validation system.

---

## Architecture

### Data Flow

```
Hub Frontend (React)
    ↓ fetch /api/v1/hypotheses
CommandCenter Backend (FastAPI)
    ↓ HypothesisRouter
    ↓ HypothesisService
    ↓ HypothesisRegistry + HypothesisValidator
AI Arena libs (backend/libs/ai_arena/)
```

### New Backend Components

| File | Purpose |
|------|---------|
| `backend/app/routers/hypotheses.py` | REST API endpoints |
| `backend/app/services/hypothesis_service.py` | Business logic bridge to ai_arena libs |
| `backend/app/schemas/hypothesis.py` | Pydantic request/response models |

### New Frontend Components

| File | Purpose |
|------|---------|
| `hub/frontend/src/pages/HypothesesPage.tsx` | Main dashboard page |
| `hub/frontend/src/components/HypothesisDashboard/index.tsx` | Dashboard container |
| `hub/frontend/src/components/HypothesisDashboard/HypothesisCard.tsx` | Single hypothesis row |
| `hub/frontend/src/components/HypothesisDashboard/StatsBar.tsx` | Summary statistics |
| `hub/frontend/src/components/HypothesisDashboard/ValidationModal.tsx` | Validation config and progress |
| `hub/frontend/src/services/hypothesesApi.ts` | API client |
| `hub/frontend/src/types/hypothesis.ts` | TypeScript types |

---

## API Design

### Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/hypotheses` | List hypotheses with filtering |
| GET | `/api/v1/hypotheses/{id}` | Get single hypothesis with details |
| POST | `/api/v1/hypotheses/{id}/validate` | Trigger async validation |
| GET | `/api/v1/hypotheses/{id}/validation-status` | Poll validation progress |
| GET | `/api/v1/hypotheses/stats` | Dashboard statistics |

### Request/Response Examples

**GET /api/v1/hypotheses**
```
Query: ?status=untested&category=pricing&limit=20&offset=0

Response:
{
  "items": [
    {
      "id": "hyp_abc123",
      "statement": "Enterprise customers will pay $2K/month",
      "category": "pricing",
      "status": "untested",
      "priority_score": 85,
      "evidence_count": 0,
      "validation_score": null,
      "created_at": "2025-12-28T10:00:00Z"
    }
  ],
  "total": 12,
  "limit": 20,
  "offset": 0
}
```

**POST /api/v1/hypotheses/{id}/validate**
```
Body:
{
  "max_rounds": 3,
  "agents": ["analyst", "researcher", "critic"]
}

Response:
{
  "task_id": "val_xyz789",
  "status": "started"
}
```

**GET /api/v1/hypotheses/{id}/validation-status**
```
Response:
{
  "status": "running",  // running | completed | failed
  "current_round": 2,
  "max_rounds": 3,
  "responses_count": 6,
  "consensus_level": "weak",
  "started_at": "2025-12-28T10:05:00Z"
}
```

---

## UI Design

### Page Layout

```
┌─────────────────────────────────────────────────────────┐
│ Hypotheses                              [Stats Summary] │
├─────────────────────────────────────────────────────────┤
│ Filters: [Status ▼] [Category ▼]        [Search...]    │
├─────────────────────────────────────────────────────────┤
│ ┌─────────────────────────────────────────────────────┐ │
│ │ ● Enterprise customers will pay $2K/mo    Score: 85 │ │
│ │   PRICING · VALIDATED · 3 evidence items            │ │
│ │                                    [View] [Validate]│ │
│ └─────────────────────────────────────────────────────┘ │
│ ┌─────────────────────────────────────────────────────┐ │
│ │ ○ SMB market prefers monthly billing      Score: 72 │ │
│ │   PRICING · UNTESTED · 0 evidence items             │ │
│ │                                    [View] [Validate]│ │
│ └─────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────┘
```

### Stats Bar

Shows counts: Total | Untested | Validating | Validated | Invalidated | Needs Data

### Hypothesis Card

- Status indicator (colored dot)
- Statement text (truncated)
- Priority score badge
- Category tag
- Status tag
- Evidence count
- Action buttons: View, Validate

### Validation Modal

**Config state:**
- Max rounds slider (1-5, default 3)
- Agent checkboxes (analyst, researcher, strategist, critic)
- "Start Validation" button

**Progress state:**
- Progress bar (rounds completed / max)
- Current round indicator
- Agent response count
- Consensus level indicator
- Elapsed time

**Complete state:**
- Final status (validated/invalidated/needs_more_data)
- Validation score with gauge
- Final answer summary
- Recommendation text
- "Close" button

---

## Validation Flow

1. User clicks "Validate" on hypothesis card
2. Modal opens with configuration options
3. User clicks "Start Validation"
4. POST `/api/v1/hypotheses/{id}/validate` returns `task_id`
5. Modal switches to progress view
6. Poll `/api/v1/hypotheses/{id}/validation-status` every 2 seconds
7. On completion, show results in modal
8. User clicks "Close", hypothesis card refreshes with new status

### Error Handling

| Error | Handling |
|-------|----------|
| Validation timeout (5 min) | Show "timed out" with partial results |
| API error on start | Toast error, keep modal open to retry |
| API error during poll | Retry 3x, then show error state |
| No agents available | Disable "Start" button, show message |

---

## Implementation Order

1. **Backend API** (router, service, schemas)
2. **Frontend types** (TypeScript interfaces)
3. **API client** (hypothesesApi.ts)
4. **StatsBar component**
5. **HypothesisCard component**
6. **HypothesisDashboard container**
7. **ValidationModal component**
8. **HypothesesPage** and routing
9. **Integration testing**

---

## Future Enhancements (Not in Scope)

- WebSocket for real-time progress (replace polling)
- Create/Edit hypothesis in UI
- Evidence explorer component
- Cost tracking dashboard
- Debate visualization (DebateViewer)
