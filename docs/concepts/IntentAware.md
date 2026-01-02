# Intent-Aware Agents: Bridging the Intent Gap

**Status**: Design Principle
**Created**: 2026-01-02
**Source**: Internal research paper "Bridging the Intent Gap"

---

## The Core Problem

The most significant barrier to reliable AI agent deployment is not capability, but **intent inference**. The challenge is not what agents *can* do, but ensuring they do what we *mean*.

> "This feeling of an agent being smart, fast, and subtly wrong is not an edge case; it is the center of the agent problem."

### The Intent Gap

When an agent has tool access (files, calendars, code, wallets), a wrong guess has high-cost, irreversible consequences. Tool use turns "fluent completion into a real-world commitment."

**Critical insight**: "Intent is not in the text the way context is."
- Context can be engineered with facts and instructions
- Intent is hidden in subtext, priorities, trade-offs, "invisible guardrails"

### Root Causes

| Cause | Explanation |
|-------|-------------|
| **Next-token optimization** | LLMs produce plausible-sounding text, not consequence-aware actions |
| **Language underspecification** | Humans infer latent intent; LLMs require explicit specification |

### Human vs LLM Interpretation

| Human Communication | LLM Interpretation |
|---------------------|-------------------|
| Infers priorities from sparse information | Requires explicit declaration of priorities |
| Senses "invisible guardrails" and social context | Needs guardrails made visible and codified |
| Simulates consequences before acting ("second pass") | Executes confidently on single interpretation |

---

## Current Workarounds (Reactive)

These are necessary for shipping agents today, but fundamentally limited:

1. **Explicit Prompt Engineering**: Encode priorities, constraints, failure modes in prompts
2. **Codified Business Logic**: Move critical logic out of prompts into deterministic code
3. **Agent Harnesses**: Traces, constrained permissions, planning states, evaluations

> "They place an enormous burden on the developer to anticipate every ambiguity."

---

## Future Directions (Architectural)

The breakthrough will come from treating intent as a first-class, verifiable system component.

### 1. Active Task Disambiguation

Design systems that reduce uncertainty *before* committing to action:
- Ask targeted clarifying questions
- Maximize information gain
- Transform ambiguity from failure mode to interaction opportunity

**Key**: Apply surgically for high-stakes actions, not universally (defeats automation purpose).

### 2. Probabilistic Goal Formulation

Treat intent as probabilistic, not deterministic:
- Maintain distribution of plausible goals
- Update distribution as interaction progresses
- Allow understanding to **crystallize over time**
- Prevent premature commitment to wrong interpretation

### 3. Explicit Intent Interfaces

Treat intent as a separate, externalized artifact ("semantic commit"):
- **Decoupled from prompt**
- **Versioned and updateable**
- Documents: Goals, Failure Conditions, Trade-offs, Priorities

> "Transforms intent from a difficult inference problem into a manageable interface problem."

### 4. Separate Interpretation from Execution

Create checkpoints where interpretation can be inspected/verified *before* tools engage:
- Catch misunderstandings before real-world consequences
- Model's interpretation becomes testable artifact

---

## Practical Framework

### Four Recommendations for Intent-Aware Agents

1. **Separate Interpretation from Execution**
   - Inspect/test model's interpretation before tool engagement
   - Create critical checkpoint for catching misunderstandings

2. **Embrace Ambiguity in Evaluation**
   - Test with purposefully ambiguous prompts
   - Grade handling of uncertainty, not just final output

3. **Implement Disambiguation Mindset**
   - For high-stakes/destructive actions: surface interpretation + clarifying question
   - Apply selectively where intent MUST be right

4. **Externalize Intent as Artifact**
   - "Living requirements page" separate from agent logic
   - Codify intent in accessible, updateable format

---

## DeFi Parallel

Decentralized finance has evolved toward "intent-based" designs:
- Separate **WHAT** (user's desired outcome) from **HOW** (execution strategy)
- Explicit intent representations
- Solver-checker mechanisms

> "When execution is high-stakes, systems naturally evolve to make intent explicit and verifiable."

---

## Application to CommandCenter Systems

### Wander: Intent-Aware by Design

Wander implements the intent-aware framework:

| Principle | Wander Implementation |
|-----------|----------------------|
| Probabilistic → Crystallization | Resonances strengthen over time, graduate to Crystals when validated |
| Explicit Intent Interfaces | Attractor (goal), Fences (constraints), Session config |
| Separate Interpretation/Execution | Dwelling (interpret encounter) vs Crystallization (commit insight) |
| Active Disambiguation | Human checkpoints, inject/fence intervention |
| Externalized Intent | Session constraints as typed configuration |

### Veria: High-Stakes Intent Verification

For economic actions with real consequences:

| Principle | Veria Implementation |
|-----------|---------------------|
| Checkpoint before execution | Crystal → Evaluate → Human approval for high-value |
| Intent as artifact | Trade proposal encoded separately from execution |
| Solver-checker pattern | Fractal encoding + authorized decoder |

### RLM Pattern: Intent Through Interaction

The Recursive Language Model pattern enables:
- Intent refined through iterative REPL interaction
- Sub-LLM queries for disambiguation
- Explicit code shows what agent accessed (auditability)

---

## Key Takeaways

1. **Intent ≠ Context**: Can't just engineer it into prompts
2. **Crystallization over time**: Don't force premature commitment
3. **Separate interpretation from execution**: Create verifiable checkpoints
4. **High-stakes = explicit intent**: Systems naturally evolve this way
5. **Intent as artifact**: Externalize, version, manage separately

> "The winners in the agentic systems landscape will be those who master the art to design agents that can carry intent clearly all the way to executable work."

---

## References

- Internal paper: "Bridging the Intent Gap: A Framework for Reliable AI Agentic Systems"
- [Wander Concept](./Wander.md) - Implementation of intent-aware exploration
- [Veria](./Veria.md) - High-stakes economic action with intent verification
- [Fractal Security](./FractalSecurity.md) - Perceptual access control for authorized execution

---

*This document captures design principles that inform all CommandCenter agent architectures.*
