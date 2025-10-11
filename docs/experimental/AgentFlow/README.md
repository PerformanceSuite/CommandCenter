# AgentFlow - Autonomous Multi-Agent Claude Code System

A sophisticated orchestration system for running multiple Claude Code agents in parallel with automated review, testing, and deployment workflows.

## 🚀 Quick Start

```bash
# 1. Install dependencies
npm install

# 2. Configure your project
npm run setup

# 3. Launch the web interface
npm run web

# OR run directly via CLI
./scripts/agentflow.sh --project my-project --agents 5
```

## 📁 Project Structure

```
AgentFlow/
├── agents/              # Agent-specific configurations and prompts
│   ├── backend/
│   ├── frontend/
│   ├── database/
│   ├── testing/
│   ├── security/
│   └── ...
├── config/              # Configuration files
│   ├── default.json     # Default configuration
│   ├── agents.json      # Agent definitions
│   └── workflows.json   # Workflow templates
├── prompts/             # Reusable prompt templates
│   ├── base.md          # Base agent prompt
│   ├── review.md        # Review prompt template
│   └── coordinate.md    # Coordination agent prompt
├── scripts/             # Executable scripts
│   ├── agentflow.sh     # Main orchestration script
│   ├── setup.sh         # Initial setup script
│   ├── monitor.sh       # Real-time monitoring
│   └── utils/           # Utility functions
├── templates/           # Project templates
│   ├── fullstack/
│   ├── backend/
│   ├── frontend/
│   └── microservices/
├── web/                 # Web interface
│   ├── index.html       # Setup wizard UI
│   ├── dashboard.html   # Monitoring dashboard
│   └── assets/          # CSS, JS, images
└── package.json         # Node.js dependencies

```

## 🎯 Features

### Multi-Agent System
- **15+ Specialized Agents**: Each with domain expertise
- **Parallel Execution**: Using git worktrees for isolation
- **Smart Coordination**: Dependency-aware merge ordering
- **10/10 Review System**: Rigorous quality gates

### Workflow Automation
- **Automated PR Creation**: Each agent creates detailed PRs
- **Iterative Reviews**: Continuous improvement until quality threshold
- **Conflict Resolution**: Automatic detection and resolution
- **Rollback Protection**: Safe deployment with validation

### Monitoring & Control
- **Real-time Dashboard**: Track all agent statuses
- **Detailed Logging**: Per-agent execution logs
- **Progress Tracking**: Visual progress indicators
- **Manual Intervention**: Override controls when needed

## 🤖 Available Agents

### Core Development
- **Backend Agent**: API, business logic, server-side
- **Frontend Agent**: UI components, state management
- **Database Agent**: Schema, migrations, optimization
- **Testing Agent**: Unit, integration, E2E tests
- **Infrastructure Agent**: Docker, K8s, CI/CD

### Quality Assurance
- **UI/UX Agent** (Opus 4.1): Visual validation with vision
- **Security Agent**: Vulnerability scanning, best practices
- **Performance Agent**: Optimization, profiling
- **Best Practices Agent**: Code standards, patterns
- **Dependencies Agent**: Package management, security

### Specialized
- **Documentation Agent**: README, API docs, comments
- **Localization Agent**: i18n, translations
- **Monitoring Agent**: Logging, telemetry, alerts
- **DevOps Agent**: IaC, pipelines, deployments
- **Data Validation Agent**: Schemas, contracts, quality

## 🔧 Configuration

### Basic Configuration
```json
{
  "project": "my-app",
  "agents": ["backend", "frontend", "testing"],
  "maxParallel": 5,
  "reviewThreshold": 10,
  "mergeStrategy": "squash"
}
```

### Advanced Options
- Custom agent configurations
- Technology-specific rules
- Integration with CI/CD
- Custom review criteria

## 📊 Monitoring

Access the monitoring dashboard:
```bash
npm run dashboard
# Opens at http://localhost:3000
```

Or use CLI monitoring:
```bash
./scripts/monitor.sh --live
```

## 🛠️ Development

### Adding Custom Agents
1. Create agent directory in `agents/`
2. Add configuration to `config/agents.json`
3. Create prompt template in `prompts/`
4. Register in main workflow

### Custom Workflows
Create workflow templates in `templates/` for different project types.

## 📝 License

MIT

## 🤝 Contributing

Contributions welcome! See CONTRIBUTING.md for guidelines.

## 📚 Documentation

Full documentation available at:
- [Setup Guide](docs/setup.md)
- [Agent Development](docs/agents.md)
- [Workflow Customization](docs/workflows.md)
- [API Reference](docs/api.md)

## 🆘 Support

- Issues: Create a GitHub issue
- Discussions: Join our Discord
- Email: support@agentflow.dev
