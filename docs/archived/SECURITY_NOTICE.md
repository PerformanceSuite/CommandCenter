# 🔒 SECURITY NOTICE

## Critical: One Instance Per Project

**CommandCenter MUST be deployed separately for each project.**

### Why?

CommandCenter stores:
- GitHub access tokens (encrypted)
- Proprietary research documents
- RAG knowledge embeddings
- Repository commit history
- Technology assessments

**Sharing an instance = Data breach risk**

### Correct Setup

```
✅ CORRECT - Isolated instances:

~/projects/
├── performia/commandcenter/          # Performia data only
├── client-x/commandcenter/           # Client X data only  
└── internal-research/commandcenter/  # Internal data only
```

```
❌ WRONG - Shared instance:

~/commandcenter/  # Tracking ALL projects = security violation
```

### Quick Isolation Checklist

For each new project:

1. Clone CommandCenter to project directory
2. Set unique `COMPOSE_PROJECT_NAME` in `.env`
3. Generate unique `SECRET_KEY`
4. Use project-specific API keys
5. Configure unique ports (if running multiple)

### Full Documentation

See [docs/DATA_ISOLATION.md](./docs/DATA_ISOLATION.md) for:
- Complete isolation architecture
- Multi-instance setup guide
- Security best practices
- Compliance considerations

### Questions?

- Security issues: [Private Security Advisory](https://github.com/PerformanceSuite/CommandCenter/security/advisories/new)
- General questions: [GitHub Discussions](https://github.com/PerformanceSuite/CommandCenter/discussions)

---

**Remember:** Your research data is valuable. Protect it with proper isolation.
