# AI Tools UI Integration

## 🚀 Overview
The CommandCenter now includes a comprehensive AI Tools management interface that allows you to control all your AI development tools from a unified web UI.

## 🎯 Features

### 1. **Dashboard Overview**
- Real-time status of all AI tools
- Quick stats (active tools, security patches, projects)
- One-click quick actions for common tasks

### 2. **Tools Management**
- **Gemini API**: Query Google's Gemini AI directly from the UI
- **UI Testing**: Automated UI testing with Gemini integration
- **CodeMender**: Prepared for Google DeepMind's security agent
- **NLTK Data**: Natural language processing toolkit management

### 3. **Security Scanning**
- Run security scans on any project
- View vulnerability reports
- Track security metrics
- CodeMender integration ready

### 4. **AI Console**
- Interactive terminal in the browser
- Execute AI tool commands
- Query Gemini with visual feedback
- Command history and shortcuts

## 🔧 Getting Started

### Quick Start
```bash
cd ~/Projects/CommandCenter
./start-dev.sh
```

Then navigate to: http://localhost:5173/ai-tools

### Manual Start
```bash
# Terminal 1: Start Backend
cd ~/Projects/CommandCenter/backend
source venv/bin/activate
python -m uvicorn app.main:app --reload

# Terminal 2: Start Frontend
cd ~/Projects/CommandCenter/frontend
npm install
npm run dev
```

## 📍 UI Navigation

1. Click **AI Tools** in the sidebar
2. Use tabs to navigate between:
   - **Overview**: Quick stats and actions
   - **Tools**: Manage individual AI tools
   - **Security**: Run security scans
   - **Console**: Interactive command execution

## 🔌 API Endpoints

The backend provides these endpoints for the UI:

- `GET /api/ai-tools/status` - Get status of all tools
- `POST /api/ai-tools/gemini` - Query Gemini API
- `POST /api/ai-tools/security-scan` - Run security scan
- `POST /api/ai-tools/execute` - Execute commands
- `GET /api/ai-tools/projects` - List available projects
- `GET /api/ai-tools/codemender/info` - CodeMender information

## 🛡️ CodeMender Integration

The UI is fully prepared for Google DeepMind's CodeMender:

**Current Status**: Structure ready, awaiting public release

**When Available**:
- Automatic vulnerability detection
- AI-generated security patches
- Proactive code hardening
- Support for 4.5M+ lines of code

**Learn More**: [DeepMind Blog](https://deepmind.google/discover/blog/introducing-codemender-an-ai-agent-for-code-security/)

## 🎨 UI Components

### Status Badges
- **Active** (green): Tool is configured and working
- **Pending** (yellow): Tool awaiting setup or release
- **Error** (red): Configuration or connection issue

### Quick Actions
- **Run Security Scan**: Immediate vulnerability check
- **Query Gemini**: AI-powered assistance
- **Run UI Tests**: Automated testing

### Console Commands
Available commands in the UI console:
- `security-scan` - Run security analysis
- `ui-test` - Execute UI tests
- `ai-help` - Show available commands

## 🔧 Configuration

### Environment Variables
Set in `backend/.env`:
```env
GEMINI_API_KEY=your_api_key_here
```

### Project Paths
Projects are configured in the backend router:
- Veria: `~/Projects/Active Projects/Veria`
- Performia: `~/Projects/Active Projects/Performia`
- DC Music Plan: `~/Projects/Active Projects/DC Music Plan`
- CommandCenter: `~/Projects/CommandCenter`

## 📊 Architecture

```
CommandCenter UI
    ├── Frontend (React + TypeScript)
    │   ├── AIToolsView Component
    │   ├── Status Dashboard
    │   ├── Security Scanner
    │   └── AI Console
    │
    ├── Backend (FastAPI)
    │   ├── AI Tools Router
    │   ├── Command Execution
    │   ├── Gemini Integration
    │   └── Security Scanning
    │
    └── AI Tools Directory
        ├── gemini/
        ├── codemender/
        └── nlp/
```

## 🚨 Troubleshooting

### Tools Not Found
- Ensure AI tools are in `~/Projects/CommandCenter/ai-tools/`
- Run organization script: `~/organize-ai-tools.sh`

### Gemini Not Working
- Check API key in backend `.env`
- Verify node_modules in gemini/api-tools

### Backend Connection Failed
- Ensure backend is running on port 8000
- Check CORS settings in backend

## 📈 Future Enhancements

- [ ] Real-time vulnerability monitoring
- [ ] Automated patch application
- [ ] CI/CD integration
- [ ] Multi-project batch scanning
- [ ] AI-powered code review
- [ ] Custom security rule definitions

## 📝 Notes

- The UI currently shows placeholder data for demonstration
- Full functionality requires backend API integration
- CodeMender features will activate upon public release
- All commands are sandboxed for security

---

Built with ❤️ for the CommandCenter project
