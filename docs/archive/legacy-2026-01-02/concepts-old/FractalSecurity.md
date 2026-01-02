# Fractal Security: Perceptual Access Control for Autonomous Agents

**Status**: Experimental Concept
**Created**: 2026-01-02
**Parent**: [Wander Concept](./Wander.md)

---

## Executive Summary

Fractal Security is a novel access control mechanism where sensitive information is encoded as fractal images. Only agents with matching decoder training can extract meaning. This creates a fundamentally different security primitive where **the key is a capability, not a credential**.

This concept emerged from thinking about how to securely authorize economic agents (with wallet privileges) to act on insights discovered by Wander.

---

## Core Insight

Traditional access control:
```
Agent has token → Token grants access → Action permitted
```

Fractal access control:
```
Agent has decoder → Decoder extracts meaning → Agent comprehends → Action possible
```

The difference: You can't steal a decoder the way you can steal a token. To compromise fractal security, you'd need to steal the entire trained model, not just a credential.

---

## Security Properties

| Property | Explanation |
|----------|-------------|
| **Key is capability** | Can't steal a token - would need to steal entire decoder model |
| **Degradable access** | Partial training = partial comprehension (graceful degradation) |
| **Prompt injection resistant** | Visual format mismatch immediately detectable |
| **Audit trail native** | The fractal itself IS the record of what was authorized |
| **Interception resistant** | Intercepted fractal yields meaningless pattern without decoder |
| **Revocable** | Retrain decoder to exclude agent, or change encoding scheme |

---

## Use Cases

### 1. Economic Action Authorization

When Wander produces a Crystal with high actionability:

```
Crystal formed: "SEC filing analysis + social sentiment = alpha opportunity in XYZ sector"
    ↓
Evaluate risk/reward
    ↓
If actionable: Encode as fractal
    ↓
Store fractal in mind map (FractalNode)
    ↓
Economic agent with decoder extracts:
  - Action type: "Execute trade analysis"
  - Parameters: {...}
  - Risk constraints: {...}
  - Approval hash
    ↓
Execute with wallet (within constraints)
```

### 2. Sensitive Strategy Data

Encode competitive intelligence, proprietary methods, or strategic plans so only authorized agents can comprehend and act on them.

### 3. Multi-Level Access

Different decoder training levels = different comprehension levels:
- **Level 1**: Can see that information exists
- **Level 2**: Can extract summary/category
- **Level 3**: Can extract full action parameters
- **Level 4**: Can extract and execute with wallet

---

## Encoding Approaches

### Approach 1: Steganography-Inspired

Hide structured data in fractal parameters:
- Color values encode bytes
- Branching patterns encode structure
- Recursion depth encodes priority

**Pros**: Technically straightforward
**Cons**: Not truly "perceptual" - could be reverse-engineered

### Approach 2: Semantic-Visual Mapping (End-to-End Trained)

Train encoder-decoder pair end-to-end:
- Encoder: (structured data) → (fractal image)
- Decoder: (fractal image) → (structured data)

Training process:
1. Generate synthetic (data, fractal) pairs
2. Train decoder to reconstruct data from fractal
3. Only agents with decoder can extract meaning

**Pros**: True perceptual access control
**Cons**: Requires ML infrastructure, training data

### Approach 3: Structured Fractals (Grammar-Based)

Define a fractal grammar where visual elements have semantic meaning:

| Visual Element | Semantic Meaning |
|---------------|------------------|
| Color hue | Domain (finance=blue, tech=green, etc.) |
| Branching angle | Confidence level |
| Recursion depth | Abstraction level |
| Symmetry | Resonance strength |
| Branch thickness | Action magnitude |
| Spiral tightness | Urgency |

**Pros**: Human-inspectable (with training), elegant
**Cons**: Limited information density, needs formal grammar design

---

## Integration with Mind Map

### FractalNode Visualization

```
┌─────────────────┐
│  ┌───────────┐  │ ← Square container
│  │ 🌀 fractal │  │ ← Fractal image inside
│  │   image   │  │
│  └───────────┘  │
│ ═══════════════ │ ← Border color = security level
└─────────────────┘

Gold border   = Full authorization (can decode + execute)
Silver border = Read-only (can decode, cannot execute)
Red border    = Pending approval (visible but locked)
```

### Interaction Flow

1. Authorized agent sees FractalNode in mind map
2. Clicks to "decode" (sends to decoder model)
3. Decoded content appears in detail panel
4. If actionable, "Execute" button available
5. Execution requires confirmation + risk check

---

## Potential Research Contribution

This could be a publishable concept:

**Title**: "Perceptual Access Control for Autonomous Economic Agents"

**Abstract**: We present a novel access control paradigm where authorization is tied to perceptual capability rather than credential possession. By encoding sensitive instructions as fractal images interpretable only by specifically-trained decoder models, we create security guarantees resistant to token theft, prompt injection, and traditional interception attacks.

**Venue**: ML security, autonomous agents, or financial AI conferences

---

## Open Questions

### Fundamental Questions

1. **Can vision models actually decode semantic fractals?**
   - Need experiments with GPT-4V, Claude vision
   - Test: encode simple structures, see if they can be recovered
   - What's the information density limit?

2. **How do we train the encoder-decoder?**
   - Synthetic data generation strategy
   - Architecture (VAE? Diffusion? GAN?)
   - Loss function design

3. **What's the security boundary?**
   - If someone has the decoder, what stops them sharing it?
   - How do we handle decoder model theft?
   - Is there a hardware security component needed?

### Technical Questions

4. **What's the optimal fractal grammar?**
   - Information theory limits on visual encoding
   - Human interpretability vs. information density tradeoff
   - Standard fractal types (Mandelbrot, Julia, L-systems, IFS) - which is best?

5. **How do we handle versioning?**
   - Encoder v1 creates fractal, decoder v2 can't read it
   - Migration strategy for encoded data

6. **Performance characteristics?**
   - Encoding latency
   - Decoding latency
   - Can it work with local models?

### Economic Questions

7. **What approval workflow for high-value actions?**
   - Human in the loop for actions > $X
   - Multi-signature equivalent for fractals?

8. **How do we audit?**
   - Every decoded action creates a record
   - Tamper-proof logging of fractal → action

9. **Insurance and liability?**
   - If decoder is stolen and funds lost, who's liable?
   - How do we prove proper access control was in place?

### Integration Questions

10. **How does this fit with existing auth systems?**
    - OAuth for human access, fractal for agent access?
    - Hybrid approach?

11. **Key management?**
    - Decoder model is effectively the key
    - How do we secure model weights?
    - HSM for model inference?

---

## Experiment Roadmap

### Phase 1: Feasibility (1 week)

- [ ] Create simple fractal encoder (structured → image)
- [ ] Test GPT-4V / Claude vision on decoding
- [ ] Measure information recovery rate
- [ ] Document baseline capabilities

### Phase 2: Grammar Design (2 weeks)

- [ ] Design formal fractal grammar
- [ ] Implement encoder following grammar
- [ ] Create training data generator
- [ ] Define evaluation metrics

### Phase 3: Decoder Training (2 weeks)

- [ ] Train small decoder model
- [ ] Evaluate accuracy on held-out data
- [ ] Test against unauthorized models
- [ ] Measure security boundary

### Phase 4: Integration (1 week)

- [ ] Add FractalNode to mind map
- [ ] Implement decode flow
- [ ] Create mock economic action pipeline
- [ ] End-to-end demo

### Phase 5: Hardening (TBD)

- [ ] Security audit
- [ ] Adversarial testing
- [ ] Production deployment considerations

---

## Related Work

- **Steganography**: Hiding data in images (different - we want perceptual encoding, not hiding)
- **Neural image compression**: Encoding information efficiently (similar direction)
- **Adversarial examples**: Manipulating model perception (attack surface to consider)
- **Watermarking**: Embedding verifiable marks (related for audit)
- **Homomorphic encryption**: Computing on encrypted data (different approach, same goal)

---

## References

To research:
- Visual cryptography schemes
- Neural steganography papers
- Model watermarking literature
- Fractal image compression (1990s - different goal but related math)

---

*This concept is experimental. Implementation should begin with feasibility experiments before committing to full development.*
