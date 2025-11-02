# CommandCenter Schema & CI Validation Guide (v1)

## Purpose
This package enforces the CommandCenter JSON contract layer across all tool manifests, event fixtures, and snapshot artifacts.
It begins in warn mode and automatically flips to full enforcement after the policy date (default: 2025-11-15).

## Directory Overview
```
/CommandCenter
  /schemas/
  /fixtures/
  /tools/graphvis/manifest.json
  /snapshots/dev/.../graphvis-topology.json
  /scripts/
    verify-schemas.sh
    cc-ci-gate.sh
  /.cc/validation-policy.json
  /.github/workflows/verify.yml
  CHECKLIST.md
```
## Local Validation
```
chmod +x scripts/verify-schemas.sh scripts/cc-ci-gate.sh
./scripts/verify-schemas.sh
./scripts/cc-ci-gate.sh
```

## Enforcement Phases
| Date | Phase | Description |
|------|------|-------------|
| Before 2025-11-15 | Warn | Only events enforced; manifests/snapshots warn if missing. |
| On/after 2025-11-15 | Enforce | CI fails unless ≥1 manifest and ≥1 snapshot exist & validate. |

## Quick Reference
- `./scripts/verify-schemas.sh` — fast fixtures validation
- `./scripts/cc-ci-gate.sh` — full policy gate (same checks as CI)

## Next Phase Prompt (copy into a new chat)
We’re continuing the CommandCenter build, moving from the Validation-Seed bundle to the Hub-Prototype-v1 phase.
Context: Validation-Seed is installed and passing CI.
Goal: implement a lightweight Hub prototype with discovery, registry, Mesh-Bus simulator, and a web console.
Deliverable: CommandCenter-Hub-Prototype-v1.zip with instructions and minimal run scripts.
Proceed step-by-step: design structure, discovery scripts, mock-bus, console scaffolds, local start commands, bundle prep.