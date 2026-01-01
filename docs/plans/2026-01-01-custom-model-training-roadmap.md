# CommandCenter Custom Model Training Roadmap

**Date:** January 1, 2026
**Status:** Planning
**Inspiration:** [nanochat](https://github.com/karpathy/nanochat) by Andrej Karpathy

---

## Executive Summary

CommandCenter will integrate custom model training capabilities, enabling clients to have AI that genuinely understands their business - not just retrieves information about it.

**Key Insight:** With nanochat demonstrating $100-1000 custom LLM training, it's now economically viable for every significant client deployment to include a domain-specific model.

---

## The Model Stack

```
┌─────────────────────────────────────────────────────────────────────┐
│                    COMMANDCENTER MODEL STACK                         │
│                                                                      │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │  ROUTING LAYER                                               │   │
│  │  Decides which model handles each request based on:          │   │
│  │  - Data sensitivity                                          │   │
│  │  - Domain specificity                                        │   │
│  │  - Required capability                                       │   │
│  └─────────────────────────────────────────────────────────────┘   │
│           │                   │                   │                  │
│           ▼                   ▼                   ▼                  │
│  ┌─────────────┐     ┌─────────────┐     ┌─────────────┐           │
│  │  FRONTIER   │     │  DOMAIN     │     │  SECURE     │           │
│  │  (Claude/   │     │  (Fine-tuned│     │  (Custom    │           │
│  │   GPT)      │     │   or Custom)│     │   Private)  │           │
│  │             │     │             │     │             │           │
│  │  General    │     │  Company-   │     │  Sensitive  │           │
│  │  tasks,     │     │  specific   │     │  data,      │           │
│  │  coding,    │     │  concepts,  │     │  regulated  │           │
│  │  analysis   │     │  workflows  │     │  industries │           │
│  └─────────────┘     └─────────────┘     └─────────────┘           │
│                                                                      │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │  KNOWLEDGEBEAST (RAG) - Provides context to ALL models       │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                                                                      │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │  GRAPH-SERVICE - Stores concepts, relationships, patterns    │   │
│  └─────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Why Custom Models?

### The Difference

| Approach | How it handles "What is Veria?" |
|----------|--------------------------------|
| **API + RAG** | Retrieves docs about Veria, synthesizes answer. Context needed every time. |
| **Fine-tuned** | Knows Veria terminology, responds more naturally. Still needs some context. |
| **Custom trained** | Veria is in the weights. Intrinsic understanding. Connects concepts automatically. |

### The Value Proposition

> "We don't just analyze your documents. We train an AI that UNDERSTANDS your business."

**Client Onboarding:**
1. Upload docs (contracts, wiki, emails, presentations)
2. Document Intelligence extracts concepts and requirements
3. Custom model trained on client data (nanochat-style)
4. CommandCenter now KNOWS the business intrinsically

**Results:**
- Proactive monitors understand company context
- Workflows use company terminology natively
- Compliance checks know YOUR rules
- System gets smarter with usage

---

## Implementation Phases

### Phase 1: API + RAG (Current - Q1 2026)
**Status:** Implemented

- Claude/GPT for general intelligence
- KnowledgeBeast for document retrieval
- Document Intelligence via API calls

**Limitations:**
- Context window constraints
- Data leaves your control
- Generic responses require constant context

### Phase 2: Fine-Tuning Layer (Q2 2026)
**Status:** Planned

**Goals:**
- Fine-tune open models (Llama 3, Mistral) on extracted concepts
- Better company-specific terminology handling
- Self-hostable for sensitive clients

**Technical Approach:**
```yaml
fine_tuning:
  base_models:
    - llama-3-8b
    - mistral-7b
    - phi-3-mini

  training_data:
    sources:
      - extracted_concepts  # From Document Intelligence
      - graph_relationships  # From Graph-Service
      - synthetic_qa  # Generated from docs

  deployment:
    options:
      - e2b_sandbox  # For development/testing
      - client_cloud  # AWS/GCP/Azure
      - on_premise  # For regulated industries
```

**Deliverables:**
- Fine-tuning pipeline integrated with Document Intelligence
- Model registry in CommandCenter
- Deployment automation (Docker/K8s)

### Phase 3: Custom Training Pipeline (Q3 2026)
**Status:** Planned

**Goals:**
- Full nanochat-style training from scratch
- For premium clients: "Your own AI"
- Competitive moat and lock-in

**Technical Approach:**
```yaml
custom_training:
  pipeline:
    tokenization:
      - Train custom BPE tokenizer on client corpus
      - Include domain-specific vocabulary

    pretraining:
      - Base training on client documents
      - Mix with general knowledge (filtered web data)
      - Target: 1-10B tokens depending on corpus size

    midtraining:
      - Inject client identity and style
      - Synthetic data for specific capabilities

    sft:
      - Fine-tune on conversation patterns
      - Client-specific response style

    evaluation:
      - Custom benchmarks for client domain
      - A/B testing against general models

  infrastructure:
    compute:
      - 8x H100 node ($24/hr) for training
      - Total cost: $100-1000 depending on model size
    hosting:
      - Options: cloud, on-premise, hybrid
      - Inference: vLLM, TensorRT-LLM
```

**Deliverables:**
- Training orchestration in CommandCenter
- Model versioning and rollback
- A/B testing infrastructure
- Cost tracking and optimization

### Phase 4: Hybrid Intelligence (Q4 2026)
**Status:** Planned

**Goals:**
- Seamless routing between model types
- Automatic escalation/delegation
- Cost optimization

**Technical Approach:**
```yaml
routing:
  rules:
    - condition: "contains_pii OR data_classification == 'confidential'"
      model: "secure_custom"

    - condition: "uses_company_terminology"
      model: "domain_finetuned"

    - condition: "requires_frontier_capability"
      model: "claude_sonnet"

    - default: "domain_finetuned"  # Cheapest capable option

  optimization:
    - Cache common queries
    - Batch similar requests
    - Precompute embeddings for frequent patterns
```

---

## Primitive Integration

Custom models become primitives in the CommandCenter ecosystem:

```yaml
primitive:
  name: "model.query"
  category: "intelligence"

  params:
    query: string
    model_preference: frontier | domain | secure | auto
    context_sources: string[]  # KnowledgeBeast collections

  execution:
    router:
      evaluates: [sensitivity, domain_match, capability_required]
      selects: appropriate_model

  output:
    response: string
    model_used: string
    confidence: float
    sources: Reference[]

  affordances:
    - "refine_with_context"
    - "escalate_to_frontier"
    - "explain_reasoning"
```

---

## Client Tiers

| Tier | Model Stack | Training | Cost |
|------|-------------|----------|------|
| **Free** | API only (Claude) | None | $0 + API costs |
| **Pro** | API + Fine-tuned | Monthly fine-tune updates | $500/month |
| **Enterprise** | Full hybrid stack | Custom trained model | $5000+ setup, $1000/month |
| **Regulated** | Self-hosted only | On-premise custom | Custom pricing |

---

## Success Metrics

### Technical
- Model response latency < 500ms (p95)
- Custom model accuracy > 90% on domain tasks
- Training pipeline < 24 hours for standard deployment

### Business
- 50% reduction in context needed for accurate responses
- 3x improvement in domain-specific task completion
- Client retention > 95% after custom model deployment

---

## Risks and Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Training cost volatility | High | Reserved compute, cost caps |
| Model quality variance | High | Standardized eval suite, human review |
| Data privacy concerns | Critical | On-premise option, data encryption |
| Compute availability | Medium | Multi-cloud strategy, spot instances |
| Maintenance burden | Medium | Automated retraining, monitoring |

---

## References

- [nanochat](https://github.com/karpathy/nanochat) - Karpathy's $100 ChatGPT
- [nanoGPT](https://github.com/karpathy/nanoGPT) - Training foundation
- [LLM101n](https://github.com/karpathy/LLM101n) - Educational context

---

*This capability transforms CommandCenter from "a tool that uses AI" to "a platform that creates AI for your business."*
