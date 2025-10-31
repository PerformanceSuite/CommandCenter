# MRKTZR ↔ CommandCenter Integration — Post-Install Validation

## ✅ 1. Directory Structure
Ensure:
```
mrktzr-integration/
├── README.md
├── VALIDATE.md
├── install_mrktzr_integration.sh
├── 01_STRATEGY/
├── 02_TECH_BLUEPRINT/
├── 03_ROADMAP/
├── 04_AGENTIC_AUTOMATION/
└── 05_APPENDIX/
```

## ✅ 2. Diagram Render
If you passed default flags (render enabled), confirm:
```
02_TECH_BLUEPRINT/Integration_Architecture.png
```
If missing, install mermaid-cli then re-run:
```bash
npm install -g @mermaid-js/mermaid-cli
bash make_bundle.sh --force
```

## ✅ 3. Docs Index Link
Check `../README.md` contains:
```
- [MRKTZR Integration](./mrktzr-integration/README.md)
```

## ✅ 4. API Spec Preview
Preview locally with Docker:
```bash
docker run -p 8080:8080 -v $(pwd)/mrktzr-integration/02_TECH_BLUEPRINT/OpenAPI.yaml:/api.yaml swaggerapi/swagger-ui
docker run -p 8081:8080 -v $(pwd)/mrktzr-integration/02_TECH_BLUEPRINT/AsyncAPI.yaml:/asyncapi.yaml asyncapi/studio
```

## ✅ 5. Commit
```bash
git add mrktzr-integration
git commit -m "docs: add MRKTZR↔CommandCenter integration (v1)"
git push
```
