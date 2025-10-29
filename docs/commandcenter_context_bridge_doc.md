# 🧠 CommandCenter Context Bridge & RAG Hub Overview

**Date:** October 27 2025  
**Author:** Daniel Connolly  

---

## 🌟 Purpose

CommandCenter serves as the **central coordination hub** for all projects in the PROACTIVA ecosystem.  
It manages AI context, communication, and isolated retrieval-augmented-generation (RAG) engines for each connected project.

This document explains the **Context Bridge** architecture, how it integrates with **Codex** and **ChatGPT**, and how the system can expand to include isolated RAGs per project.

---

## 🧩 Architecture Summary

```
      ┌───────────────────────────┐
      │         ChatGPT            │
      │ Conversational Memory + AI │
      └───────────┬───────────┘
                   │  REST / JSON
                   ▼
      ┌───────────────────────┐
      │     CommandCenter Hub      │
      │  FastAPI Context Bridge    │
      │  + RAG Registry / Control  │
      └───────────┬───────────┘
                   │
   ┌─────────┬─────────┬─────────┬─────────┐
   │               │                        │
   ▼               ▼                        ▼
 Veria-RAG      MRKTZR-RAG              Performia-RAG
 (Compliance)   (Marketing)             (Creative AI)
```

---

## ⚙️ Components

| Component | Location | Description |
|------------|-----------|-------------|
| **`context_api.py`** | `commandcenter/` | FastAPI microservice exposing `/projects` and `/context/{repo}` endpoints for context sync. |
| **`_project-index.json`** | `~/Projects/` | Global index of all active projects. |
| **`.chat/context.json`** | Per-project | Local context file containing branch, last task, and status. |
| **`sync_chat_context.sh`** | `scripts/` | CLI utility to push project context to CommandCenter. |
| **`start_commandcenter.sh`** | `scripts/` | Launches the Context Bridge API and prepares the RAG environment. |
| **Aliases (`ccup`, `ccdown`, `commandcenter`)** | `~/.zshrc` | Shell helpers for quick start/stop and background execution. |

---

## 🧠 CommandCenter as the Hub

- Provides a **shared memory layer** between ChatGPT and local tools (Codex, Cursor).  
- Manages **per-project isolation** so Veria, MRKTZR, Performia, etc., maintain independent contexts.  
- Hosts a REST API accessible at `http://127.0.0.1:5050`.  
- Can later manage **MCP or agent registration** and **RAG engine initialization** for each project.

---

## 🪄 Developer Commands

### Start or Restart the Bridge
```bash
ccup
```
Starts the FastAPI service and activates the virtual environment.

### Stop the Bridge
```bash
ccdown
```
Stops any Uvicorn process running on port 5050.

### Background Start via Hub
```bash
commandcenter
```
Runs `scripts/start_commandcenter.sh`, which:
1. Kills old instances  
2. Activates the `.venv`  
3. Starts the Context Bridge API in background mode  
4. Logs to `commandcenter.log`

### Verify Service
```bash
curl http://127.0.0.1:5050/projects | jq
curl http://127.0.0.1:5050/context/Performia | jq
```

---

## 🧩 Directory Structure

```
~/Projects/Core/CommandCenter/
├── commandcenter/
│   ├── context_api.py
│   └── __init__.py
├── scripts/
│   ├── sync_chat_context.sh
│   └── start_commandcenter.sh
├── templates/
│   ├── context.json
│   └── project-index.json
├── .venv/
└── README_ContextBridge.md
```

Global workspace file:
```
~/Projects/_project-index.json
```

---

## 🗱 Isolated RAG Architecture (Planned)

Each project will have its own vector store, embeddings, and retriever configuration:

| Project | RAG Location | Backend | Purpose |
|----------|--------------|----------|----------|
| **Veria** | `~/Projects/Intelligence/Veria-RAG/` | FAISS / Supabase | Compliance knowledge |
| **MRKTZR** | `~/Projects/Intelligence/MRKTZR-RAG/` | Qdrant | Marketing datasets |
| **ROLLIZR** | `~/Projects/Intelligence/ROLLIZR-RAG/` | Chroma | Partner & roll-up data |
| **FRACTLZR** | `~/Projects/Intelligence/FRACTLZR-RAG/` | FAISS | Encrypted fractal data |
| **Performia** | `~/Projects/Creative/Performia-RAG/` | Local Vector DB | Musical/creative context |

A future module (`init_rag.py`) will:
- Scan `_project-index.json`
- Initialize or connect each RAG engine
- Register them under a unified `/rag/{project}/query` endpoint

---

## 🖯 Next Steps

1. Verify `_project-index.json` lives at `~/Projects/`.  
2. Use `ccup` / `ccdown` for quick control.  
3. Confirm `curl http://127.0.0.1:5050/projects` returns JSON.  
4. Develop `init_rag.py` for automatic RAG bootstrapping.  
5. Expand dashboard view in CommandCenter to display:
   - Connected projects  
   - Context sync status  
   - RAG health / embedding count  

---

## 📘 References

- [FastAPI Documentation](https://fastapi.tiangolo.com/)  
- [Uvicorn Server Guide](https://www.uvicorn.org/)  
- [FAISS](https://github.com/facebookresearch/faiss)  
- [Qdrant](https://qdrant.tech/)  

---

**End of Document**  
> This specification can be added directly as a GitHub Issue titled:  
> “🧩 Integrate CommandCenter Context Bridge & Multi-Project RAG Hub”

