# CommandCenter Validation Checklist (v1)

- [ ] Replace template manifest if present:
      - Create `tools/<id>/manifest.json`
      - Delete `tools/_TEMPLATE_`
- [ ] Add at least one snapshot JSON under `snapshots/<env>/<tool>/<kind>/<YYYY>/<MM>/<DD>/`.
- [ ] Run:
      chmod +x scripts/verify-schemas.sh scripts/cc-ci-gate.sh
      ./scripts/verify-schemas.sh
      ./scripts/cc-ci-gate.sh
