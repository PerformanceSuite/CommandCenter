# Fractlzr

**Fractal Encoding and Perceptual Security**

Fractlzr uses fractal geometry as a cryptographic and steganographic medium. It enables secure, aesthetic encoding of information that only authorized agents can decode.

## Overview

Fractlzr embeds meaningful information within fractal images:
- Secure encoding of sensitive data
- Identity signatures and trust markers
- Compliance watermarks
- Audit trails in visual form

The key insight: fractal parameters create infinite visual complexity from finite data. Reversing the encoding requires knowing the generation rules.

## Perceptual Access Control

Traditional access control: "Does this user have permission?"

Perceptual access control: "Can this agent perceive the information?"

Fractlzr encodes information such that:
- Authorized agents decode meaningful data
- Unauthorized agents see only abstract art
- The encoding itself is the access control

## Use Cases

### Trade Proposal Encoding
Veria encodes trade proposals as fractals:
- Only authorized trading agents can decode
- Visual audit trail of all proposals
- Tamper-evident (changes break the fractal)

### Compliance Watermarks
Veria documents carry Fractlzr watermarks:
- Proves document authenticity
- Encodes compliance metadata
- Visible but not intrusive

### Identity Signatures
Agents have fractal identity signatures:
- Unique visual representation
- Embeds capabilities and permissions
- Verifiable without central authority

### Campaign Collateral
MRKTZR watermarks proposals and media:
- Attribution tracking
- Unauthorized use detection
- Rights management

## Components

### Fractal Generator
Creates multi-layer fractal patterns:
- Mandelbrot, Julia, custom IFS
- Parameter space mapping
- Deterministic from seed

### Information Encoder
Maps structured data to fractal parameters:
- JSON → parameter vector
- Includes error correction
- Compression for efficiency

### AI Decoder
Reconstructs data from visual input:
- Trained on encoding scheme
- Handles noise and distortion
- Confidence scoring

### Compliance Mode
Verifiable watermarking:
- Visible watermark layer
- Hidden data layer
- Timestamping

## Integration Points

| Module | Integration |
|--------|-------------|
| Veria | Trade proposal encoding, compliance watermarks |
| MRKTZR | Campaign collateral watermarking |
| KnowledgeBeast | Stores fractal-encoded sensitive data |
| VISLZR | Displays fractals as node representations |

## Technical Approach

```
Encoding:
  data → JSON → compress → params → fractal_render → image

Decoding:
  image → fractal_analyze → params → decompress → JSON → data

Security:
  - Encoding scheme is the "key"
  - Without scheme, image is just art
  - Scheme can be agent-specific
```

## Data Model

```
FractalEncoding
├── id, created_by_agent
├── fractal_type (mandelbrot|julia|ifs)
├── parameters{} (generation params)
├── encoded_data_hash
├── image_url
├── authorized_decoders[]
└── created_at

DecodingAttempt
├── id, encoding_id
├── agent_id
├── success: bool
├── decoded_data_hash (if success)
└── timestamp
```

## Actions (VISLZR node)

- encode data
- decode image
- verify watermark
- view audit trail
- generate identity

## Status

🧪 **Experimental** - Concept proven, production implementation pending
