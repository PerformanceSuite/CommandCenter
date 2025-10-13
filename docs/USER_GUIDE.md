# CommandCenter User Guide

**Version:** 2.0
**Last Updated:** 2025-10-12

This guide provides a comprehensive overview of how to use the features of CommandCenter, from core workflows to advanced integrations.

## Table of Contents

1.  [**Core Concept: The Research Workflow**](#1-core-concept-the-research-workflow)
2.  [**Using the CLI**](#2-using-the-cli)
    *   [Installation & Configuration](#installation--configuration)
    *   [Core CLI Commands](#core-cli-commands)
3.  [**Integrations**](#3-integrations)
    *   [GitHub Integration](#github-integration)
    *   [Model Context Protocol (MCP)](#model-context-protocol-mcp)
4.  [**Automation**](#4-automation)
    *   [Scheduling Automated Tasks](#scheduling-automated-tasks)
    *   [Using Webhooks](#using-webhooks)
5.  [**AI Models**](#5-ai-models)
    *   [Supported Models](#supported-models)
    *   [Configuration](#configuration)

---

## 1. Core Concept: The Research Workflow

CommandCenter is designed to streamline the entire R&D process, from initial idea to final integration. The central workflow is as follows:

1.  **Extract Research Topics:** Start by identifying technologies and research areas from strategic documents, competitor analysis, or team brainstorming. CommandCenter can help automate this by extracting entities from uploaded documents.
2.  **Track Technologies:** Add the identified technologies to the **Technology Radar**. This allows you to track their status (e.g., `Evaluating`, `Adopted`) and relevance to your projects.
3.  **Create Research Tasks:** For each technology that requires investigation, create a **Research Task**. This is the central unit of work in CommandCenter.
4.  **Launch Research Agents:** Assign AI-powered agents to your research tasks. These agents can perform literature reviews, competitive analysis, and even create prototype code, depositing their findings directly into the task.
5.  **Review and Query Results:** All findings are stored in a structured format and automatically indexed into the **Knowledge Base**. You can then use natural language to ask questions across all completed research.
6.  **Automate & Monitor:** Use the scheduling and webhook systems to monitor for new developments (e.g., new papers on arXiv, trending GitHub repos) and trigger new research tasks automatically.

This workflow transforms scattered R&D efforts into a structured, searchable, and automated process.

---

## 2. Using the CLI

The CommandCenter CLI is a powerful tool for interacting with your instance from the command line, ideal for scripting and automation.

### Installation & Configuration

1.  **Installation:**
    ```bash
    cd backend
    pip install -e .
    ```
2.  **Initial Configuration:** Create a default configuration file.
    ```bash
    commandcenter config init
    ```
    This will create a file at `~/.commandcenter/config.yaml`. You should edit this file to set your API URL and authentication token.
    ```yaml
    api:
      url: http://localhost:8000
    auth:
      token: your-api-token-here
    ```

### Core CLI Commands

-   **Analyze a Project:**
    ```bash
    # Analyze a local directory
    commandcenter analyze project /path/to/your/project

    # Analyze a GitHub repository
    commandcenter analyze project --github owner/repo
    ```

-   **Search the Knowledge Base:**
    ```bash
    commandcenter search "What are the best practices for RAG implementation?"
    ```

-   **Manage Agents:**
    ```bash
    # Launch a workflow
    commandcenter agents launch --workflow analyze-only

    # Check the status of a running workflow
    commandcenter agents status <orchestration-id> --watch
    ```

-   **Shell Completion:** For `bash`, `zsh`, or `fish`, you can enable tab completion:
    ```bash
    # Add to your .zshrc or .bashrc
    eval "$(commandcenter completion zsh)"
    ```

---

## 3. Integrations

CommandCenter is designed to integrate seamlessly with your existing development ecosystem.

### GitHub Integration

Connect CommandCenter to your GitHub repositories to enable powerful automations.

-   **Features:**
    -   **Issue Sync:** Automatically create Research Tasks from GitHub Issues and keep their statuses synchronized.
    -   **PR Analysis:** Use the provided GitHub Action to analyze new pull requests, detect technologies, and post summaries as comments.
    -   **Webhook Support:** Receive events for pushes, issues, and pull requests to keep repository data fresh.
-   **Setup:**
    1.  Create a GitHub Personal Access Token with `repo`, `read:org`, and `admin:repo_hook` scopes.
    2.  Add a new GitHub integration in the CommandCenter UI, providing the token.
    3.  Configure a webhook in your GitHub repository settings, pointing to your CommandCenter instance's webhook URL.

### Model Context Protocol (MCP)

MCP allows AI assistants (like in Claude Code or Cursor) to interact directly with CommandCenter.

-   **How it Works:** CommandCenter acts as an MCP server, exposing its data and actions through a standardized protocol.
-   **Capabilities:**
    -   **Resources:** An AI can read data like the list of projects, technologies on the radar, and active research tasks.
    -   **Tools:** An AI can perform actions, such as creating a new research task or adding a technology to the radar.
    -   **Prompts:** Provides templates to guide the AI through complex workflows like technology evaluation.
-   **Use Case:** Inside an MCP-compatible IDE, you could type `/research "find documents related to spatial audio"` and the AI would use CommandCenter's knowledge base to answer, all within your editor.

---

## 4. Automation

### Scheduling Automated Tasks

The scheduling system allows you to run recurring tasks automatically, powered by Celery Beat in the background.

-   **Schedule Types:**
    -   `once`: Run a task at a specific time.
    -   `hourly`, `daily`, `weekly`, `monthly`: Run at fixed intervals.
    -   `cron`: Define a custom schedule using a cron expression (e.g., `"0 9 * * 1-5"` for every weekday at 9 AM).
-   **Task Types:**
    -   Automated code analysis of a repository.
    -   Scheduled data exports.
    -   Periodic delivery of webhooks.
-   **Creating a Schedule (via API):**
    ```bash
    curl -X POST http://localhost:8000/api/v1/schedules \
      -H "Content-Type: application/json" \
      -d '{
        "name": "Daily Security Scan",
        "task_type": "analysis",
        "frequency": "daily",
        "timezone": "America/New_York",
        "task_parameters": {
            "repository_id": 42,
            "analysis_type": "security"
        }
    }'
    ```

### Using Webhooks

Webhooks notify external systems when events occur in CommandCenter.

-   **Features:**
    -   **Event Filtering:** Subscribe to specific events (e.g., `analysis.complete`) or use wildcards (`analysis.*`).
    -   **Automatic Retries:** Failed deliveries are automatically retried with exponential backoff.
    -   **Secure Delivery:** Payloads are signed with an HMAC-SHA256 signature for verification.
-   **Example Events:**
    -   `analysis.started`
    -   `analysis.complete`
    -   `export.failed`
-   **Receiving a Webhook:**
    1.  Create an endpoint in your external service to receive POST requests.
    2.  Verify the `X-Hub-Signature-256` header to ensure the request is genuinely from CommandCenter.
    3.  Process the event payload. It's best practice to respond with a `200 OK` immediately and process the payload in the background.

---

## 5. AI Models

CommandCenter is designed to be model-agnostic, allowing you to choose the best AI provider and model for your needs.

### Supported Models

CommandCenter supports a wide range of models from major providers. As of October 2025, the recommended models are:

| Provider | Recommended Model | Best For |
|---|---|---|
| **Anthropic** | `claude-sonnet-4-5` | The best all-around model for coding, complex agentic tasks, and computer use. **(Default)** |
| **OpenAI** | `gpt-5` | State-of-the-art coding and reasoning. |
| **Google** | `gemini-2.5-flash` | The best balance of price and performance, ideal for agentic use cases. |

### Configuration

You can configure the default AI provider and model in your `.env` file.

-   **Single Provider:**
    ```bash
    # .env
    DEFAULT_AI_PROVIDER=anthropic
    DEFAULT_MODEL=claude-sonnet-4-5-20250929
    ANTHROPIC_API_KEY=your-key-here
    ```
-   **Multi-Provider (via OpenRouter):** For maximum flexibility, you can use a service like OpenRouter to access models from all providers with a single API key.
    ```bash
    # .env
    DEFAULT_AI_PROVIDER=openrouter
    # Note the provider namespace in the model name
    DEFAULT_MODEL=anthropic/claude-sonnet-4-5
    OPENROUTER_API_KEY=your-key-here
    ```
This allows you to easily switch between models from different providers without changing your code or managing multiple API keys.
