# Hub CLI Usage Guide

The Hub CLI provides tools for querying and monitoring CommandCenter Hub events.

## Installation

```bash
cd hub/backend
pip install -e .
```

Verify installation:
```bash
hub --version
```

## Commands

### query - Query Historical Events

Search events stored in PostgreSQL database.

**Basic usage:**
```bash
hub query                          # Last 100 events
hub query --limit 20               # Last 20 events
hub query --format json            # JSON output
```

**Filtering:**
```bash
# By subject (NATS wildcards)
hub query --subject "hub.test.*"
hub query --subject "hub.>"

# By time range
hub query --since "1h"             # Last hour
hub query --since "yesterday"      # Since yesterday
hub query --since "2025-11-04"     # Since specific date

# By correlation ID
hub query --correlation-id "abc123-..."

# Combined filters
hub query --subject "hub.test.*" --since "1h" --limit 50
```

**Output formats:**
- `table` (default): Rich terminal table
- `json`: JSON array for scripting

### follow - Stream Live Events

Watch events in real-time as they occur.

**Basic usage:**
```bash
hub follow                         # All hub events
hub follow --subject "hub.test.*"  # Filtered
hub follow --format json           # JSON output
```

**Output formats:**
- `compact` (default): One-line per event
- `json`: Full JSON per event
- `table`: Live-updating table (last 20 events)

**Stop streaming:** Press `Ctrl+C`

## Examples

**Monitor all project events:**
```bash
hub follow --subject "hub.*.project.*"
```

**Debug specific request:**
```bash
# Get correlation ID from API response header
curl -I http://localhost:9001/api/projects

# Query all events for that request
hub query --correlation-id "<correlation-id>"
```

**Export events to file:**
```bash
hub query --format json --since "24h" > events.json
```

**Continuous monitoring:**
```bash
hub follow --subject "hub.>" | grep ERROR
```

## Time Formats

Supports multiple formats:

**Relative:**
- `1h`, `2h`, `24h` - Hours ago
- `30m`, `45m` - Minutes ago
- `1d`, `7d` - Days ago

**Natural language:**
- `yesterday`
- `last Monday`
- `2 hours ago`
- `last week`

**ISO 8601:**
- `2025-11-04T10:30:00Z`
- `2025-11-04`

## Subject Patterns

NATS wildcard syntax:

- `*` - Single token (e.g., `hub.*.project` matches `hub.local.project`)
- `>` - Multiple tokens (e.g., `hub.test.>` matches `hub.test.foo.bar`)

**Examples:**
- `hub.*.health.*` - Health events from any hub
- `hub.local.>` - All events from local hub
- `hub.*.project.created` - Project creation from any hub

## Troubleshooting

**Connection errors:**
```bash
# Check NATS is running
curl http://localhost:8222/varz

# Check database connection
psql $DATABASE_URL -c "SELECT COUNT(*) FROM events"
```

**No events returned:**
- Verify events exist: `hub query --limit 1000`
- Check subject pattern matches actual subjects
- Verify time range includes events

**CLI not found:**
```bash
# Reinstall in development mode
cd hub/backend
pip install -e .
```
