# Observer Implementation - Full Context Document

**Date:** October 12, 2025
**Status:** Ready to implement
**Location:** CommandCenter integrated module

---

## Session Summary

This document captures the complete context from our planning session for implementing the AI Work Observer feature in CommandCenter.

---

## The Vision

**AI Work Observer** that:
- Monitors screen, terminal, and files passively
- Detects inefficiencies and patterns in real-time
- Intervenes with proactive suggestions
- Uses local AI models for privacy
- Integrates deeply with CommandCenter's existing features

**Key Innovation:** Privacy-first passive observation that makes CommandCenter 10x more valuable.

---

## Why Build in CommandCenter (Not Standalone)

### Decision Rationale:
1. **Existing Infrastructure** - FastAPI, React, PostgreSQL, Redis, AI routing already built
2. **Faster Time to Value** - 2-3 weeks vs 3+ months
3. **Natural Integration** - Observer knows your research context, technologies, knowledge base
4. **Instant Users** - You + Performia instance immediately
5. **Can Extract Later** - If observer becomes standalone product, architecture supports it

### Architecture Decision:
**Build as CommandCenter module NOW, evaluate extraction after 3 months of usage.**

---

## Technical Architecture

### Module Structure

```
commandcenter/
  backend/
    app/
      observer/                    # NEW MODULE
        ├── __init__.py
        ├── screen_monitor.py      # Screen capture + vision analysis
        ├── terminal_monitor.py    # Terminal log watching
        ├── file_watcher.py        # File change detection
        ├── pattern_analyzer.py    # Detect stuck/inefficient patterns
        ├── intervention_engine.py # Decide when to suggest
        ├── vision_service.py      # Local LLaVA + Cloud models
        └── models.py              # DB models for observations

      api/
        └── observer.py            # NEW ROUTER - /api/observer/*

      services/
        └── observer_service.py    # Business logic

  frontend/
    src/
      features/
        observer/                  # NEW FEATURE
          ├── ObserverDashboard.tsx
          ├── ActivityFeed.tsx
          ├── InterventionCard.tsx
          ├── ObserverSettings.tsx
          └── types.ts
```

### Technology Stack

**Vision Models:**
- **Local (Free/Pro):** LLaVA 1.6 Mistral 7B (via MLX on Mac)
- **Cloud (Pro/Enterprise):** Claude 3.5 Sonnet Vision, GPT-4V
- **Lightweight:** Moondream2 for real-time monitoring

**Monitoring:**
- **Screen:** mss (Python) or Quartz (macOS native)
- **Terminal:** Watch `~/.terminal-logs/` (already logging!)
- **Files:** watchdog (Python) for file change events

**Backend:**
- FastAPI async endpoints
- PostgreSQL for observations/patterns
- Redis for real-time state

**Frontend:**
- React 18 + TypeScript
- Real-time updates via WebSocket
- Activity feed component

---

## Hardware Setup

### Your Infrastructure:
- **Mac Studio** - Main development machine
- **Mac Mini** - Can run as dedicated observer server

### Distributed Architecture Option:
```
Mac Studio:                    Mac Mini:
- Captures screen/terminal    - Runs LLaVA vision model
- Sends to Mac Mini           - Analyzes frames
- Receives suggestions        - Sends interventions back
- Shows notifications          - Always-on observer daemon
```

**For MVP:** Start with Mac Studio only (all-in-one), add Mac Mini distribution later.

---

## Implementation Phases

### Week 1: Core Observer (MVP)

**Goals:**
- Screen monitoring with local LLaVA
- Terminal log watching
- Basic pattern detection
- Simple notification system

**Deliverables:**
- Observer runs in background
- Captures screen every 30s
- Analyzes with LLaVA
- Logs observations to database
- Sends test notification when "stuck" detected

**Files to Create:**
```python
# backend/app/observer/screen_monitor.py
class ScreenMonitor:
    def __init__(self):
        self.model = load_llava_model()

    async def capture_and_analyze(self):
        screen = capture_screen()
        analysis = self.model.analyze(screen)
        return analysis

# backend/app/observer/terminal_monitor.py
class TerminalMonitor:
    def watch_logs(self):
        # Tail ~/.terminal-logs/*.log
        # Detect error patterns
        pass

# backend/app/observer/intervention_engine.py
class InterventionEngine:
    def should_intervene(self, patterns):
        # Decide when to notify user
        pass
```

### Week 2: Intelligence Layer

**Goals:**
- Cloud model integration (Claude Vision)
- Pattern detection engine
- Dashboard UI
- Settings page

**Features:**
- Hybrid model selection (local vs cloud)
- Stuck detection (same error 5x)
- Context rot detection (long AI conversations)
- Fatigue detection (degrading commit quality)
- Activity summary dashboard

### Week 3: Polish & Integration

**Goals:**
- Integration with CommandCenter features
- Voice assistant (basic)
- Mac Mini distribution
- Beta testing

**Integration Points:**
- Link observations to Research Tasks
- Suggest technologies from observation
- Reference Knowledge Base in suggestions
- Use existing AI router for model selection

---

## Database Schema

### New Models

```python
# backend/app/observer/models.py

class Observation(Base):
    """Single observation from monitoring"""
    id: int
    timestamp: datetime
    source: str  # 'screen', 'terminal', 'files'
    content: str  # What was observed
    analysis: str  # AI's interpretation
    confidence: float
    user_id: int

class Pattern(Base):
    """Detected behavioral pattern"""
    id: int
    pattern_type: str  # 'stuck', 'context_rot', 'fatigue'
    detected_at: datetime
    observations: list[Observation]  # Related observations
    severity: str  # 'low', 'medium', 'high'
    user_id: int

class Intervention(Base):
    """Suggestion sent to user"""
    id: int
    pattern_id: int
    message: str
    delivered_at: datetime
    accepted: bool  # Did user follow suggestion?
    feedback: str  # User's response
    user_id: int
```

### API Endpoints

```
GET  /api/observer/status          # Is observer running?
POST /api/observer/start           # Start monitoring
POST /api/observer/stop            # Stop monitoring
GET  /api/observer/observations    # Recent observations
GET  /api/observer/patterns        # Detected patterns
GET  /api/observer/interventions   # Suggestion history
PUT  /api/observer/settings        # Update config
POST /api/observer/feedback        # User feedback on suggestion
```

---

## Configuration

### Environment Variables

```toml
# config.toml - Add to existing file

[observer]
enabled = false  # Enable observer module

# Monitoring settings
screen_capture_fps = 0.0333  # 1 frame per 30 seconds
terminal_monitoring = true
file_monitoring = true

# Vision model
vision_model = "llava-1.6-mistral-7b"  # local | llava | claude | gpt4v
model_location = "local"  # local | cloud | hybrid

# Intervention settings
intervention_threshold = "medium"  # low | medium | high
notification_method = "macos"  # macos | slack | email | terminal

# Privacy
blur_sensitive = true  # Auto-blur passwords, API keys
save_screenshots = false  # Never save to disk
data_retention_days = 7  # Delete old observations

# Distributed (Mac Mini)
distributed = false
observer_host = "mac-mini.local"
observer_port = 8765
```

---

## Installation Steps

### 1. Install Dependencies

```bash
cd ~/Projects/CommandCenter/backend

# Add to requirements.txt
echo "mlx-vlm>=0.1.0" >> requirements.txt
echo "mss>=9.0.0" >> requirements.txt
echo "watchdog>=3.0.0" >> requirements.txt
echo "whisper>=1.1.10" >> requirements.txt  # For future voice

# Install
pip install -r requirements.txt

# Download LLaVA model (one-time, ~4GB)
python -c "from mlx_vlm import load; load('mlx-community/llava-v1.6-mistral-7b-4bit')"
```

### 2. Database Migration

```bash
cd backend

# Create migration
alembic revision --autogenerate -m "add observer tables"

# Apply
alembic upgrade head
```

### 3. Start Observer

```bash
# Backend with observer enabled
OBSERVER_ENABLED=true uvicorn app.main:app --reload

# Frontend (existing)
cd frontend && npm run dev
```

---

## Development Workflow

### Day 1: Screen Monitoring Proof of Concept

**Goal:** Capture screen, analyze with LLaVA, log to console

```python
# Quick test script
from mlx_vlm import load, generate
import mss

# Load model
model, processor = load("mlx-community/llava-v1.6-mistral-7b-4bit")

# Capture screen
with mss.mss() as sct:
    screenshot = sct.grab(sct.monitors[0])

# Analyze
result = generate(
    model, processor, screenshot,
    "What is the developer working on? Any issues visible?"
)

print(result)
```

**Success Criteria:** See accurate description of what's on screen.

### Day 2: Terminal Monitoring

**Goal:** Watch terminal logs, detect error patterns

```python
import os
from pathlib import Path

terminal_log_dir = Path.home() / ".terminal-logs"

for log_file in terminal_log_dir.glob("*.log"):
    # Tail logs
    # Detect error patterns
    # Flag repeated errors
    pass
```

### Day 3: Pattern Detection

**Goal:** Detect "stuck" pattern (same error 5x)

```python
class PatternDetector:
    def __init__(self):
        self.recent_errors = []

    def detect_stuck(self, error_msg):
        self.recent_errors.append(error_msg)

        # Check for repeated errors
        if self.recent_errors.count(error_msg) >= 5:
            return True
        return False
```

### Day 4: Intervention Engine

**Goal:** Send macOS notification when stuck

```python
import subprocess

def send_notification(title, message):
    subprocess.run([
        'osascript', '-e',
        f'display notification "{message}" with title "{title}"'
    ])

# Usage
if pattern_detector.detect_stuck(error):
    send_notification(
        "CommandCenter Observer",
        "You've encountered this error 5 times. Want help?"
    )
```

### Day 5: Dashboard UI

**Goal:** React component showing observations

```typescript
// frontend/src/features/observer/ObserverDashboard.tsx

interface Observation {
  timestamp: string;
  source: 'screen' | 'terminal' | 'files';
  content: string;
  analysis: string;
}

export function ObserverDashboard() {
  const [observations, setObservations] = useState<Observation[]>([]);

  // Fetch observations from API
  useEffect(() => {
    fetch('/api/observer/observations')
      .then(res => res.json())
      .then(setObservations);
  }, []);

  return (
    <div className="observer-dashboard">
      <h2>Activity Feed</h2>
      {observations.map(obs => (
        <ObservationCard key={obs.timestamp} observation={obs} />
      ))}
    </div>
  );
}
```

---

## Integration with Existing CommandCenter Features

### 1. Research Tasks Integration

**When observer detects stuck pattern:**
```python
# Check if user has active research task
active_task = get_active_research_task(user_id)

if active_task:
    # Link observation to task
    observation.research_task_id = active_task.id

    # Suggest: "You're stuck on X. Check your research notes for similar issues"
```

### 2. Knowledge Base Integration

**When suggesting help:**
```python
# Search knowledge base for relevant context
similar_docs = knowledge_base.search(error_pattern)

suggestion = f"You've hit this error before. See: {similar_docs[0].title}"
```

### 3. Technology Tracking Integration

**When detecting outdated tech:**
```python
# Check against technology radar
if "using webpack" in screen_analysis:
    newer_tech = technologies.find(
        domain="bundlers",
        status="recommended"
    )

    suggest(f"Consider migrating to {newer_tech.title}")
```

### 4. Marketing Automation Integration

**Observer insights → Marketing content:**
```python
# When user completes difficult task
if pattern.type == "breakthrough_after_struggle":
    # Suggest creating content
    marketing.suggest_content(
        title=f"How I solved {pattern.problem}",
        type="blog_post"
    )
```

---

## Privacy & Security

### Privacy-First Design

**Core Principles:**
1. **Local by Default:** Free tier uses only local models
2. **No Persistence:** Screenshots never saved to disk (RAM only)
3. **User Control:** Easy on/off toggle, configurable monitoring
4. **Transparency:** Audit log shows everything observed
5. **Opt-In:** Observer disabled by default

### Security Measures

**Sensitive Data Protection:**
```python
# Blur sensitive regions before analysis
def blur_sensitive_regions(screenshot):
    # Detect password fields
    # Detect API keys (sk-*, ghp_*)
    # Blur credit card numbers
    # Return sanitized screenshot
    pass
```

**Data Retention:**
```python
# Auto-delete old observations
async def cleanup_old_data():
    retention_days = config.observer.data_retention_days
    cutoff = datetime.now() - timedelta(days=retention_days)

    await Observation.delete().where(
        Observation.timestamp < cutoff
    )
```

---

## Testing Plan

### Unit Tests

```python
# tests/test_observer/test_pattern_detector.py

def test_stuck_detection():
    detector = PatternDetector()

    # Simulate repeated errors
    for _ in range(5):
        detector.add_observation("Error: Cannot find module 'x'")

    assert detector.is_stuck() == True

def test_context_rot_detection():
    detector = PatternDetector()

    # Simulate long AI conversation
    for i in range(150):
        detector.add_observation(f"AI message {i}")

    assert detector.detect_context_rot() == True
```

### Integration Tests

```python
# tests/test_observer/test_integration.py

async def test_full_observation_cycle():
    # Start observer
    observer = Observer()
    await observer.start()

    # Simulate activity
    await simulate_terminal_error()

    # Wait for detection
    await asyncio.sleep(5)

    # Check intervention sent
    interventions = await get_interventions()
    assert len(interventions) > 0
```

---

## Performance Considerations

### Resource Usage

**Screen Monitoring:**
- 1 frame per 30 seconds = 120 frames/hour
- LLaVA inference: ~2 seconds per frame
- Total CPU time: ~4 minutes/hour (6.6%)

**Memory:**
- LLaVA model: ~4-6GB RAM
- Screenshot buffer: ~10MB (transient)
- Total: ~6GB RAM overhead

**Optimization:**
```python
# Only analyze when screen changes significantly
def should_analyze(current_frame, previous_frame):
    diff = compute_frame_diff(current_frame, previous_frame)
    return diff > threshold  # Skip if screen unchanged
```

---

## Rollout Plan

### Phase 1: Internal Dogfooding (Week 1-2)
- You use it daily
- Fix obvious bugs
- Tune intervention thresholds
- Document issues

### Phase 2: Closed Beta (Week 3-4)
- Invite 5-10 beta testers
- Gather feedback
- Measure acceptance rate
- Iterate

### Phase 3: CommandCenter Feature Launch (Month 2)
- Announce as new feature
- Write blog post
- Update pricing (optional)
- Monitor usage

### Phase 4: Evaluate Extraction (Month 3)
- Analyze usage data
- If observer is THE feature → extract to standalone
- If integrated is better → keep as-is
- Add more profession packs

---

## Success Metrics

### Week 1 Goals:
- [ ] Observer running continuously
- [ ] 10+ observations logged per hour
- [ ] 1+ successful intervention per day
- [ ] No crashes or performance issues

### Month 1 Goals:
- [ ] 80%+ weekly active usage (you)
- [ ] 5+ interventions accepted per day
- [ ] Detect at least one "genuinely helpful" pattern
- [ ] Dashboard showing useful insights

### Month 3 Goals:
- [ ] 5+ beta users actively using
- [ ] 60%+ intervention acceptance rate
- [ ] Positive qualitative feedback
- [ ] Decision: Extract or keep integrated

---

## Next Steps (Immediate)

### When You Open CommandCenter:

1. **Create Module Structure:**
```bash
cd ~/Projects/CommandCenter/backend/app
mkdir observer
touch observer/__init__.py
touch observer/screen_monitor.py
touch observer/terminal_monitor.py
touch observer/models.py
```

2. **Install Dependencies:**
```bash
pip install mlx-vlm mss watchdog
python -c "from mlx_vlm import load; load('mlx-community/llava-v1.6-mistral-7b-4bit')"
```

3. **Test LLaVA:**
```bash
# Create test script
python backend/app/observer/test_vision.py
```

4. **Review This Document:**
Read through completely, ask questions, clarify anything unclear.

---

## Questions to Answer in Next Session

1. **Model Selection:** Start with LLaVA or Moondream2?
2. **Notification Method:** macOS notifications or in-app only?
3. **Mac Mini:** Set up distributed now or later?
4. **Voice:** Include in MVP or wait for Week 2?
5. **Dashboard:** Separate page or sidebar widget?

---

## Related Documents

- **Master Plan:** `docs/WORKFLOWGUARD_MASTER_PLAN.md` (complete product vision)
- **Marketing Automation:** `docs/AUTOMATED_MARKETING_ORCHESTRATOR.md` (can integrate with observer)
- **Architecture:** `docs/ARCHITECTURE.md` (existing CommandCenter architecture)
- **API Docs:** `docs/API.md` (add observer endpoints here)

---

## Your Hardware

- **Mac Studio:** M1/M2 Max/Ultra (your main development machine)
- **Mac Mini:** M1/M2 (can run as observer server)
- **Network:** Both machines networked and accessible

**Recommendation:** Start all-in-one on Mac Studio, add Mac Mini distribution in Week 2-3.

---

## Key Insights from Session

1. **Port Management System:** We built comprehensive port allocation system (`~/.config/dev-ports/`) during this session. All projects now have unique ports.

2. **CommandCenter is Framework:** Multi-instance architecture via `COMPOSE_PROJECT_NAME`. Can run multiple isolated instances.

3. **KnowledgeBeast:** Not standalone - integrated Python library in CommandCenter.

4. **Project Ecosystem:** CommandCenter, Veria, Performia, Rollizr all benefit from shared observer.

5. **Business Opportunity:** Potentially $100M+ business with profession-specific packs.

---

## Final Thought

**You're not just building a feature - you're building the future of work intelligence.**

The observer makes CommandCenter transformative. It's the difference between:
- "A tool to track research" → "An AI that watches and learns from your research"
- "A knowledge base" → "An assistant that knows when to surface knowledge"
- "A productivity app" → "A coach that improves how you work"

**This is the killer feature.**

---

**Status:** Ready to implement
**Next:** Create module structure, install dependencies, build screen monitor POC
**Timeline:** Working prototype in 7 days

Let's build this. 🚀
