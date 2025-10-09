"""Developer Tools Hub API Router

Comprehensive integration for all development tools including:
- Multiple AI model providers
- MCP servers
- Code assistants
- GitHub operations
- Security scanning
- Workflow automation
"""

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from pydantic import BaseModel
from typing import Dict, Any, Optional, List
import subprocess
import os
import json
import asyncio
import aiohttp
from pathlib import Path
from datetime import datetime

router = APIRouter(prefix="/dev-tools", tags=["dev-tools"])

# Configuration paths
HOME = Path.home()
MCP_CONFIG = HOME / ".mcp.json"
CLAUDE_CONFIG = HOME / ".claude.json"
PROJECTS_DIR = HOME / "Projects"

# API Keys from environment
API_KEYS = {
    "openai": os.getenv("OPENAI_API_KEY", ""),
    "anthropic": os.getenv("ANTHROPIC_API_KEY", ""),
    "gemini": os.getenv("GEMINI_API_KEY", ""),
    "github": os.getenv("GITHUB_TOKEN", ""),
    "brave": os.getenv("BRAVE_API_KEY", "")
}

# Request/Response Models
class ModelQueryRequest(BaseModel):
    provider: str  # claude, openai, gemini, ollama, lmstudio
    model: str
    prompt: str
    max_tokens: Optional[int] = 1000
    temperature: Optional[float] = 0.7
    system_prompt: Optional[str] = None

class CommandRequest(BaseModel):
    command: str
    args: Optional[List[str]] = []
    cwd: Optional[str] = None

class WorkflowRequest(BaseModel):
    name: str
    steps: List[str]
    tools: List[str]
    auto_run: bool = False

class GitHubActionRequest(BaseModel):
    action: str  # create_repo, create_pr, create_issue, etc.
    params: Dict[str, Any]

class MCPServerRequest(BaseModel):
    server: str
    action: str
    params: Optional[Dict[str, Any]] = {}

# Helper Functions
async def execute_shell_command(command: str, args: List[str] = [], cwd: str = None) -> Dict[str, Any]:
    """Execute shell command safely"""
    try:
        cmd = [command] + args if args else command
        result = subprocess.run(
            cmd,
            shell=isinstance(cmd, str),
            capture_output=True,
            text=True,
            timeout=30,
            cwd=cwd or str(HOME)
        )
        return {
            "success": result.returncode == 0,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "returncode": result.returncode
        }
    except subprocess.TimeoutExpired:
        return {"success": False, "error": "Command timed out"}
    except Exception as e:
        return {"success": False, "error": str(e)}

# API Endpoints

@router.get("/status")
async def get_system_status():
    """Get comprehensive status of all dev tools"""
    
    status = {
        "timestamp": datetime.now().isoformat(),
        "model_providers": {},
        "mcp_servers": {},
        "code_assistants": {},
        "github": {},
        "system": {}
    }
    
    # Check model providers
    status["model_providers"] = {
        "claude": {
            "configured": bool(API_KEYS["anthropic"]),
            "claude_code": (HOME / ".claude_code").exists(),
            "projects": len(list((HOME / ".claude").glob("*"))) if (HOME / ".claude").exists() else 0
        },
        "openai": {
            "configured": bool(API_KEYS["openai"])
        },
        "gemini": {
            "configured": bool(API_KEYS["gemini"]),
            "tools_installed": (PROJECTS_DIR / "CommandCenter" / "ai-tools" / "gemini").exists()
        },
        "ollama": {
            "installed": (HOME / ".ollama").exists(),
            "models": await get_ollama_models()
        },
        "lmstudio": {
            "installed": (HOME / ".lmstudio").exists()
        }
    }
    
    # Check MCP servers
    if MCP_CONFIG.exists():
        with open(MCP_CONFIG) as f:
            mcp_data = json.load(f)
            status["mcp_servers"] = {
                server: {"configured": True, "status": "ready"}
                for server in mcp_data.get("mcpServers", {}).keys()
            }
    
    # Check code assistants
    status["code_assistants"] = {
        "claude_code": {
            "installed": await check_command_exists("claude-code"),
            "config": (HOME / ".claude_code").exists()
        },
        "goose": {
            "installed": await check_command_exists("goose"),
            "config": (HOME / ".goose").exists()
        },
        "codex": {
            "installed": await check_command_exists("codex"),
            "config": (HOME / ".codex").exists()
        },
        "jules": {
            "installed": (HOME / ".jules").exists(),
            "functions": ["jules_task", "jules_list", "jules_repos"]
        }
    }
    
    # GitHub status
    status["github"] = {
        "authenticated": bool(API_KEYS["github"]),
        "mcp_configured": "github" in status["mcp_servers"]
    }
    
    # System info
    status["system"] = {
        "projects_count": len(list(PROJECTS_DIR.glob("*"))) if PROJECTS_DIR.exists() else 0,
        "active_projects": get_active_projects()
    }
    
    return status

@router.post("/query-model")
async def query_ai_model(request: ModelQueryRequest):
    """Query any AI model provider"""
    
    if request.provider == "claude":
        return await query_claude(request)
    elif request.provider == "openai":
        return await query_openai(request)
    elif request.provider == "gemini":
        return await query_gemini(request)
    elif request.provider == "ollama":
        return await query_ollama(request)
    elif request.provider == "lmstudio":
        return await query_lmstudio(request)
    else:
        raise HTTPException(status_code=400, detail=f"Unknown provider: {request.provider}")

@router.post("/mcp-server")
async def interact_with_mcp_server(request: MCPServerRequest):
    """Interact with MCP servers"""
    
    # For filesystem operations
    if request.server == "filesystem":
        if request.action == "read_file":
            path = Path(request.params.get("path", ""))
            if path.exists():
                return {"content": path.read_text()}
            return {"error": "File not found"}
        
        elif request.action == "write_file":
            path = Path(request.params.get("path", ""))
            content = request.params.get("content", "")
            path.write_text(content)
            return {"success": True}
        
        elif request.action == "list_directory":
            path = Path(request.params.get("path", HOME))
            if path.exists():
                items = [{"name": p.name, "type": "dir" if p.is_dir() else "file"} 
                        for p in path.iterdir()]
                return {"items": items}
            return {"error": "Directory not found"}
    
    # For GitHub operations via MCP
    elif request.server == "github":
        # This would interact with the GitHub MCP server
        # For now, redirect to GitHub router
        return {"message": "Use /github endpoints for GitHub operations"}
    
    # For other MCP servers
    return {"message": f"MCP server {request.server} interaction placeholder"}

@router.post("/execute-assistant")
async def execute_code_assistant(command: CommandRequest):
    """Execute code assistant commands"""
    
    assistants = {
        "claude-code": "claude-code",
        "goose": "goose",
        "codex": "codex",
        "jules": "source ~/.jules/jules-helper.sh && ",
    }
    
    if command.command not in assistants:
        raise HTTPException(status_code=400, detail=f"Unknown assistant: {command.command}")
    
    cmd = assistants[command.command]
    if command.command == "jules":
        cmd += " ".join(command.args) if command.args else "jules_help"
    else:
        cmd = [cmd] + (command.args or [])
    
    result = await execute_shell_command(cmd, cwd=command.cwd)
    return result

@router.post("/github-action")
async def perform_github_action(request: GitHubActionRequest):
    """Perform GitHub actions via API"""
    
    if not API_KEYS["github"]:
        raise HTTPException(status_code=401, detail="GitHub token not configured")
    
    headers = {
        "Authorization": f"Bearer {API_KEYS['github']}",
        "Accept": "application/vnd.github.v3+json"
    }
    
    async with aiohttp.ClientSession() as session:
        if request.action == "create_repo":
            url = "https://api.github.com/user/repos"
            async with session.post(url, json=request.params, headers=headers) as resp:
                return await resp.json()
        
        elif request.action == "create_pr":
            owner = request.params.get("owner")
            repo = request.params.get("repo")
            url = f"https://api.github.com/repos/{owner}/{repo}/pulls"
            async with session.post(url, json=request.params, headers=headers) as resp:
                return await resp.json()
        
        elif request.action == "list_repos":
            url = "https://api.github.com/user/repos"
            async with session.get(url, headers=headers) as resp:
                repos = await resp.json()
                return {"repos": [{"name": r["name"], "url": r["html_url"]} for r in repos]}
        
        else:
            return {"error": f"Unknown action: {request.action}"}

@router.post("/workflow")
async def create_or_run_workflow(request: WorkflowRequest, background_tasks: BackgroundTasks):
    """Create or run a development workflow"""
    
    workflow = {
        "id": f"workflow_{datetime.now().timestamp()}",
        "name": request.name,
        "steps": request.steps,
        "tools": request.tools,
        "status": "created",
        "created_at": datetime.now().isoformat()
    }
    
    if request.auto_run:
        background_tasks.add_task(run_workflow_async, workflow)
        workflow["status"] = "running"
    
    return workflow

@router.get("/projects")
async def list_projects():
    """List all projects with their tool configurations"""
    
    projects = []
    active_dirs = [
        PROJECTS_DIR / "Active Projects",
        PROJECTS_DIR / "CommandCenter",
        PROJECTS_DIR
    ]
    
    for base_dir in active_dirs:
        if not base_dir.exists():
            continue
            
        for project_path in base_dir.glob("*"):
            if project_path.is_dir() and not project_path.name.startswith("."):
                project_info = {
                    "name": project_path.name,
                    "path": str(project_path),
                    "has_git": (project_path / ".git").exists(),
                    "has_package_json": (project_path / "package.json").exists(),
                    "has_requirements": (project_path / "requirements.txt").exists(),
                    "has_dockerfile": (project_path / "Dockerfile").exists(),
                    "has_readme": (project_path / "README.md").exists()
                }
                projects.append(project_info)
    
    return {"projects": projects}

@router.get("/console/history")
async def get_console_history():
    """Get console command history"""
    
    history_files = [
        HOME / ".zsh_history",
        HOME / ".bash_history",
        HOME / ".claude_code" / "history.json"
    ]
    
    history = []
    for hist_file in history_files:
        if hist_file.exists():
            if hist_file.suffix == ".json":
                with open(hist_file) as f:
                    data = json.load(f)
                    history.extend(data.get("commands", []))
            else:
                # Parse shell history format
                with open(hist_file, "r", encoding="utf-8", errors="ignore") as f:
                    lines = f.readlines()[-100:]  # Last 100 commands
                    history.extend([line.strip() for line in lines if line.strip()])
    
    return {"history": history[-50:]}  # Return last 50 commands

# Helper functions

async def check_command_exists(command: str) -> bool:
    """Check if a command exists in the system"""
    result = await execute_shell_command(f"which {command}")
    return result["success"]

async def get_ollama_models() -> List[str]:
    """Get list of Ollama models"""
    result = await execute_shell_command("ollama list")
    if result["success"]:
        lines = result["stdout"].strip().split("\n")[1:]  # Skip header
        return [line.split()[0] for line in lines if line]
    return []

def get_active_projects() -> List[str]:
    """Get list of active projects"""
    active = []
    active_dir = PROJECTS_DIR / "Active Projects"
    if active_dir.exists():
        active = [p.name for p in active_dir.iterdir() if p.is_dir()]
    return active

async def run_workflow_async(workflow: Dict[str, Any]):
    """Run a workflow asynchronously"""
    # This would implement actual workflow execution
    # For now, it's a placeholder
    await asyncio.sleep(1)
    workflow["status"] = "completed"
    return workflow

# Model-specific query functions

async def query_claude(request: ModelQueryRequest) -> Dict[str, Any]:
    """Query Claude via API"""
    if not API_KEYS["anthropic"]:
        return {"error": "Anthropic API key not configured"}
    
    # Would implement actual Claude API call
    return {"response": f"Claude response placeholder for: {request.prompt}"}

async def query_openai(request: ModelQueryRequest) -> Dict[str, Any]:
    """Query OpenAI via API"""
    if not API_KEYS["openai"]:
        return {"error": "OpenAI API key not configured"}
    
    # Would implement actual OpenAI API call
    return {"response": f"OpenAI response placeholder for: {request.prompt}"}

async def query_gemini(request: ModelQueryRequest) -> Dict[str, Any]:
    """Query Gemini via API"""
    if not API_KEYS["gemini"]:
        return {"error": "Gemini API key not configured"}
    
    # Use the existing Gemini CLI if available
    gemini_cli = PROJECTS_DIR / "CommandCenter" / "ai-tools" / "gemini" / "api-tools" / "gemini-cli.js"
    if gemini_cli.exists():
        result = await execute_shell_command(
            f"node {gemini_cli} '{request.prompt}'",
            cwd=str(gemini_cli.parent)
        )
        return {"response": result["stdout"] if result["success"] else result["error"]}
    
    return {"response": f"Gemini response placeholder for: {request.prompt}"}

async def query_ollama(request: ModelQueryRequest) -> Dict[str, Any]:
    """Query Ollama local models"""
    result = await execute_shell_command(
        f"ollama run {request.model} '{request.prompt}'"
    )
    return {"response": result["stdout"] if result["success"] else result["error"]}

async def query_lmstudio(request: ModelQueryRequest) -> Dict[str, Any]:
    """Query LM Studio local server"""
    # LM Studio typically runs on localhost:1234
    try:
        async with aiohttp.ClientSession() as session:
            url = "http://localhost:1234/v1/completions"
            payload = {
                "prompt": request.prompt,
                "max_tokens": request.max_tokens,
                "temperature": request.temperature
            }
            async with session.post(url, json=payload) as resp:
                data = await resp.json()
                return {"response": data.get("choices", [{}])[0].get("text", "")}
    except:
        return {"error": "LM Studio server not running or not accessible"}
