# Feedback Loop Design

- **Bandits**: per-channel Thompson Sampling over creative variants.
- **Cold Start**: seed priors from heuristics; decay over time.
- **Guardrails**: compliance regex/LLM moderation; forbidden topics per tenant.
- **Control**: idempotent publish, retries with backoff, dead-letter queues.
