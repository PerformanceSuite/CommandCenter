# LLM Agent Design

- **ResearchAgent (CC)**: synthesize TopicBriefs with citations; RAG within tenant corpus only.
- **CreativeAgent (MR)**: generate channel-specific variants; enforce persona+compliance notes.
- **SchedulerAgent (MR)**: optimal posting windows per channel; history + heuristics.
- **FeedbackAgent (MR→CC)**: aggregate metrics; Bayesian updates for uplift per feature.
- **HabitCoach (CC)**: proactive triggers for re-briefs and backlog grooming.
