# Hub Examples

Example scripts for working with CommandCenter Hub.

## Event Consumer

Subscribe to Hub events in real-time.

**Usage:**
```bash
# Install dependencies
pip install nats-py

# Subscribe to all events
python examples/event_consumer.py

# Subscribe to specific subject
python examples/event_consumer.py --subject "hub.*.project.*"

# Custom NATS URL
python examples/event_consumer.py --nats-url "nats://remote-host:4222"
```

**Example Output:**
```
2025-11-03 12:00:00 [INFO] Connected to NATS at nats://localhost:4222
2025-11-03 12:00:00 [INFO] Subscribing to: hub.>
2025-11-03 12:00:00 [INFO] Subscription active. Waiting for events...
2025-11-03 12:00:05 [INFO] [1] Event received
2025-11-03 12:00:05 [INFO]   Subject: hub.local-hub.project.created
2025-11-03 12:00:05 [INFO]   Payload: {
  "project_id": "123",
  "name": "test-project"
}
```

## Next Examples

Coming in Phase 2-3:
- Event replay script
- Event correlation tracker
- CLI tool for event queries
