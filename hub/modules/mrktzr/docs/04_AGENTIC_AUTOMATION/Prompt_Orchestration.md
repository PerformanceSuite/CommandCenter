# Prompt Orchestration (Patterns)

- **ResearchAgent**: Summarize top N themes from last 7 days (sources X,Y). Output: title, summary (≤120w), topics[], keywords[], persona_hints[], compliance notes, citations.
- **CreativeAgent**: For each TopicBrief × Persona, generate A/B variants per channel with CTA, alt text, thumbnail prompt.
- **FeedbackAgent**: Given metrics for campaign X, estimate uplift per (topic, format, CTA) with Bayesian update; propose next-cycle adjustments.
