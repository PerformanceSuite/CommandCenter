# Command Center Architecture

**Version:** 2.0
**Last Updated:** 2025-10-12

This document provides a comprehensive overview of Command Center's system architecture, design patterns, data models, and deployment strategies. It consolidates information from multiple architectural documents into a single source of truth.

## Table of Contents

1.  [**Core Architecture**](#1-core-architecture)
    *   [System Overview](#system-overview)
    *   [Technology Stack](#technology-stack)
    *   [Architecture Layers](#architecture-layers)
2.  [**Data and Security Model**](#2-data-and-security-model)
    *   [Data Layer](#data-layer)
    *   [Database Schema](#database-schema)
    *   [Critical: Data Isolation](#critical-data-isolation)
    *   [Security Model](#security-model)
3.  [**Application Architecture**](#3-application-architecture)
    *   [Backend Architecture](#backend-architecture)
    *   [Frontend Architecture](#frontend-architecture)
    *   [RAG Pipeline](#rag-pipeline)
    *   [API Design](#api-design)
4.  [**Deployment & Operations**](#4-deployment--operations)
    *   [Dual-Instance Strategy](#dual-instance-strategy)
    *   [Global CommandCenter Instance](#global-commandcenter-instance)
    *   [Per-Project CommandCenter Instance](#per-project-commandcenter-instance)
    *   [Deployment Architecture](#deployment-architecture)
5.  [**Advanced Integrations**](#5-advanced-integrations)
    *   [AI Provider Routing Architecture](#ai-provider-routing-architecture)
    *   [Model Context Protocol (MCP) Architecture](#model-context-protocol-mcp-architecture)
6.  [**Repository Structure**](#6-repository-structure)
7.  [**Future Vision**](#7-future-vision)
    *   [Scalability Considerations](#scalability-considerations)
    *   [Planned Enhancements](#planned-enhancements)

---

## 1. Core Architecture

### System Overview

Command Center is a full-stack application for R&D management and knowledge discovery. It follows a modern three-tier architecture with a clear separation of concerns between the frontend, backend, and data layers.

```
┌─────────────────────────────────────────────────────┐
│              Browser/Client Layer                    │
│         React SPA (TypeScript + Vite)               │
└────────────────────┬────────────────────────────────┘
                     │ HTTP/REST API
┌────────────────────▼────────────────────────────────┐
│            Application Layer (FastAPI)               │
│  ┌──────────┬──────────┬──────────┬──────────┐     │
│  │  Routers │ Services │ Schemas  │  Models  │     │
│  └──────────┴──────────┴──────────┴──────────┘     │
└────────────────────┬────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────┐
│                Data Layer                            │
│  ┌──────────┬──────────┬──────────────────────┐    │
│  │PostgreSQL│  Redis   │  ChromaDB (Vectors)  │    │
│  └──────────┴──────────┴──────────────────────┘    │
└─────────────────────────────────────────────────────┘
```

### Technology Stack

-   **Backend:** Python 3.11+, FastAPI, SQLAlchemy 2.0 (async), Alembic, Pydantic v2
-   **Frontend:** React 18, TypeScript 5, Vite 5, Tailwind CSS 3
-   **Data Layer:** PostgreSQL 16, Redis 7, ChromaDB
-   **AI/ML:** `sentence-transformers` for local embeddings, Docling for document processing, flexible routing to providers like Anthropic, OpenAI, and Google.
-   **Infrastructure:** Docker, Docker Compose, Traefik (optional)

### Architecture Layers

1.  **Presentation Layer (Frontend):** A React Single-Page Application (SPA) responsible for the user interface and experience.
2.  **Application Layer (Backend):** A FastAPI application that handles business logic, API endpoints, and integrations.
3.  **Data Layer:** Responsible for data persistence and retrieval, using PostgreSQL for relational data, Redis for caching, and ChromaDB for vector embeddings.

---

## 2. Data and Security Model

### Data Layer

The data layer is designed for robustness and scalability, consisting of:
-   **PostgreSQL:** The primary database for all relational data, including projects, users, technologies, and research tasks.
-   **Redis:** Used for caching expensive queries, session management, and as a message broker for background tasks.
-   **ChromaDB:** A vector store for managing embeddings generated from research documents, enabling powerful semantic search for the RAG pipeline.

### Database Schema

The database schema is designed around core entities like `Repository`, `Technology`, `ResearchTask`, and `KnowledgeEntry`. All tables in the global instance are keyed with a `project_id` to ensure data is properly scoped.

*(For a detailed Entity Relationship Diagram, see the original `ARCHITECTURE.md` content.)*

### Critical: Data Isolation

**The single most important security principle in CommandCenter is that each project MUST have its own isolated instance.** Sharing an instance across projects with different security requirements is strictly prohibited.

**Isolation Architecture:**
-   **`COMPOSE_PROJECT_NAME`:** The primary mechanism for isolation. Docker Compose uses this variable to namespace all containers, volumes, and networks, preventing collisions.
-   **Separate Docker Resources:** Each instance gets its own PostgreSQL database, ChromaDB vector store, Redis cache, and Docker volumes. There is no shared data layer between instances.
-   **Unique Credentials:** Each instance must have a unique `SECRET_KEY`, database password, and project-specific API tokens.

This strict isolation prevents data leakage, unauthorized repository access, and cross-contamination of knowledge bases.

### Security Model

-   **Token Encryption:** All sensitive tokens (e.g., GitHub access tokens) are encrypted at rest in the database using the Fernet symmetric encryption scheme, keyed by the instance's `SECRET_KEY`.
-   **Environment Variables:** All secrets and sensitive configurations are managed via a `.env` file and are never committed to version control.
-   **Data in Transit:** All communication should be secured with HTTPS in a production environment.
-   **CORS:** The backend enforces a strict Cross-Origin Resource Sharing (CORS) policy, allowing requests only from whitelisted origins.

---

## 3. Application Architecture

### Backend Architecture

The backend is built with FastAPI and follows a clean, modular structure.

-   **Directory Structure:** Code is organized by function into `models`, `routers`, `schemas`, and `services`.
-   **Core Patterns:**
    -   **Service Layer:** Encapsulates business logic, separating it from the API routing layer.
    -   **Dependency Injection:** FastAPI's DI system is used extensively to manage database sessions and service dependencies.
    -   **Async/Await:** All I/O-bound operations (database queries, external API calls) are fully asynchronous for high performance.
    -   **Schema Validation:** Pydantic schemas are used for robust validation of all incoming and outgoing data.

### Frontend Architecture

The frontend is a modern React SPA built with Vite and TypeScript.

-   **Component-Based:** The UI is built from a hierarchy of reusable components.
-   **Custom Hooks:** State management and data-fetching logic are encapsulated in custom hooks (e.g., `useRepositories`).
-   **Service Layer:** API interactions are abstracted into a dedicated service layer, keeping components clean.
-   **Type Safety:** TypeScript ensures type safety between the frontend and the backend API.

### RAG Pipeline

The Retrieval-Augmented Generation (RAG) pipeline is central to the knowledge base feature.

1.  **Ingestion:** Documents (PDF, MD, TXT) are processed using **Docling** to extract clean text and structure.
2.  **Chunking:** The extracted text is split into smaller, semantically coherent chunks.
3.  **Embedding:** Each chunk is converted into a vector embedding using a local `sentence-transformers` model. This happens on-device, ensuring privacy and zero API cost.
4.  **Storage:** The embeddings are stored in a **ChromaDB** collection specific to the project.
5.  **Retrieval:** When a user queries the knowledge base, the query is embedded, and a similarity search is performed in ChromaDB to find the most relevant chunks of text.
6.  **Generation (Future):** The retrieved chunks are then passed to a Large Language Model (LLM) to generate a natural language answer.

---

## 4. Deployment & Operations

### Dual-Instance Strategy

CommandCenter is designed with a dual-instance architecture to serve two distinct purposes:

1.  **Global CommandCenter:** A single, centralized instance for organization-wide portfolio management, accessed via a web UI.
2.  **Per-Project CommandCenter:** Multiple, isolated instances embedded within individual project repositories, accessed via CLI, IDE integrations, and the Model Context Protocol (MCP).

### Global CommandCenter Instance

-   **Purpose:** A single source of truth for managers and team leads to get a high-level view of all R&D activities across the organization.
-   **Database:** A single multi-tenant PostgreSQL database where all data is partitioned by a `project_id`.
-   **UI:** A web-based interface with a project switcher to filter views.
-   **Status:** This is the currently implemented version of CommandCenter.

### Per-Project CommandCenter Instance

-   **Purpose:** Developer-centric tooling embedded directly within a project's codebase for seamless, in-context access.
-   **Deployment:** Lives in a `.commandcenter/` directory within a project's repository.
-   **Data:** Each instance has its own completely isolated database and knowledge store (e.g., SQLite and a local ChromaDB folder).
-   **Access:** Primarily through a `commandcenter` CLI tool and MCP servers that integrate with AI assistants in IDEs like Claude Code or Cursor.
-   **Status:** Planned for a future phase of development.

### Deployment Architecture

-   **Development:** A simple `docker-compose up` workflow using the `docker-compose.yml` file.
-   **Production:** It is recommended to use the `docker-compose.prod.yml` file, which is optimized for production use. For multi-instance deployments, **Traefik** is the recommended reverse proxy to manage routing and eliminate port conflicts. Traefik can route traffic to different CommandCenter instances based on hostnames (e.g., `project-a.localhost`, `project-b.localhost`).

---

## 5. Advanced Integrations

### AI Provider Routing Architecture

To avoid vendor lock-in and optimize for cost and performance, CommandCenter uses a flexible AI provider routing strategy.

-   **Problem:** Different AI models excel at different tasks, and relying on a single provider is risky and expensive.
-   **Solution:** Integrate with a routing service like **OpenRouter** or a self-hosted solution like **LiteLLM**.
    -   **OpenRouter:** A managed service that provides a single API endpoint to access over 200 models from all major providers. This is the recommended starting point for simplicity.
    -   **LiteLLM:** An open-source, self-hosted proxy that provides the same benefits as OpenRouter but gives the user full control and avoids any price markup.
-   **Implementation:** The UI allows users to select the desired model, tier (e.g., premium, economy), and fallbacks for each research task, enabling fine-grained control over AI usage.

### Model Context Protocol (MCP) Architecture

MCP is a standard protocol that allows AI assistants to securely access external tools and data. CommandCenter will act as an MCP server to expose its functionality to IDEs and other AI agents.

-   **Core Components:** The implementation includes a `MCPServer` that manages providers for `resources` (read-only data like projects), `tools` (actions like creating a task), and `prompts`.
-   **Transport:** The primary transport mechanism is `stdio`, as is standard for MCP servers that are managed by IDE extensions.
-   **Use Case:** This will allow a developer inside their IDE to use an AI assistant (e.g., Claude Code) to directly query their project's knowledge base, create research tasks, or track technologies by typing commands like `/research "how did we implement spatial audio?"`.

---

## 6. Repository Structure

The repository is organized to follow industry best practices while prioritizing ease of use with standard tools like Docker Compose and Make.

-   **Root Directory:** Contains top-level configuration files that are essential for infrastructure and tooling to work out-of-the-box. This includes `docker-compose.yml`, `.env` templates, and the `Makefile`. Placing these in the root is a standard convention that ensures commands like `docker-compose up` work without extra flags.
-   **`backend/` and `frontend/`:** Contain the source code for the respective services, each with its own `Dockerfile` for building container images.
-   **`docs/`:** Contains all project documentation.
-   **`scripts/`:** Contains operational and utility scripts for tasks like backups, port checks, and maintenance. These are project-wide scripts, not specific to the backend or frontend.

This structure provides a clear separation of concerns between infrastructure configuration (root), application code (`backend/`, `frontend/`), and operational tooling (`scripts/`).

---

## 7. Future Vision

### Scalability Considerations

-   **Horizontal Scaling:** The backend is stateless, allowing for multiple instances to be run behind a load balancer.
-   **Database Scaling:** PostgreSQL can be scaled using read replicas to handle increased read loads.
-   **Background Jobs:** For long-running tasks like large document ingestion or repository analysis, a background job queue using Celery and Redis can be implemented.

### Planned Enhancements

-   **Microservices:** For very large-scale deployments, the backend could be broken down into smaller microservices (e.g., Repository Service, Technology Service, RAG Service) managed by an API Gateway.
-   **Real-time Updates:** A WebSocket server could be added to push real-time updates to the frontend for a more collaborative experience.
-   **Authentication & Authorization:** A full-fledged JWT-based authentication system with role-based access control is planned.
-   **Machine Learning:** Advanced ML features could be added, such as technology clustering, trend analysis, and duplicate research detection.
