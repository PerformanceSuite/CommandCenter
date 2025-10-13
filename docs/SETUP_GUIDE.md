# CommandCenter Setup Guide

**Version:** 2.0
**Last Updated:** 2025-10-12

This document provides a comprehensive guide to configuring, deploying, and managing a CommandCenter instance. It covers everything from initial setup and basic Docker deployment to advanced configurations for multi-project environments.

## Table of Contents

1.  [**Prerequisites**](#1-prerequisites)
2.  [**Initial Configuration**](#2-initial-configuration)
    *   [Environment Variables](#environment-variables)
    *   [Core Configuration](#core-configuration)
    *   [Security Configuration](#security-configuration)
    *   [Optional API Keys](#optional-api-keys)
3.  [**Standard Docker Deployment**](#3-standard-docker-deployment)
    *   [Starting Services](#starting-services)
    *   [Accessing the Application](#accessing-the-application)
    *   [Port Management & Conflict Resolution](#port-management--conflict-resolution)
    *   [Useful Docker Commands](#useful-docker-commands)
4.  [**Advanced Deployment with Traefik**](#4-advanced-deployment-with-traefik)
    *   [Why Use Traefik?](#why-use-traefik)
    *   [One-Time Traefik Setup](#one-time-traefik-setup)
    *   [Configuring CommandCenter for Traefik](#configuring-commandcenter-for-traefik)
5.  [**Production Deployment**](#5-production-deployment)
    *   [Production Best Practices](#production-best-practices)
    *   [Database Management](#database-management)
    *   [Backup and Recovery](#backup-and-recovery)
6.  [**Docling (RAG) Setup**](#6-docling-rag-setup)
    *   [How it Works](#how-it-works)
    *   [Configuration](#configuration)
    *   [Data Storage and Backups](#data-storage-and-backups)

---

## 1. Prerequisites

### System Requirements
-   **Minimum:** 2 CPU cores, 4GB RAM, 20GB disk space.
-   **Recommended:** 4+ CPU cores, 8GB+ RAM, 50GB+ disk space.

### Software
-   **Docker:** Version 20.10+
-   **Docker Compose:** Version 2.0+

Verify your installations with `docker --version` and `docker compose version`.

---

## 2. Initial Configuration

All configuration for CommandCenter is managed through a `.env` file in the root of the project.

### Environment Variables

1.  **Copy the Template:** If you don't have a `.env` file, create one from the template.
    ```bash
    cp .env.template .env
    ```
2.  **Edit the File:** Open the `.env` file in your favorite editor to modify the values.

### Core Configuration

These are the essential variables you need to set.

```bash
# .env

# --- Port Configuration ---
# Change these if you have conflicts with other services.
BACKEND_PORT=8000
FRONTEND_PORT=3000
POSTGRES_PORT=5432
REDIS_PORT=6379

# --- Database Configuration ---
# The password for the PostgreSQL database.
# IMPORTANT: Change this to a strong, unique password in production.
DB_PASSWORD=changeme
```

### Security Configuration

These variables are critical for securing your instance.

```bash
# .env

# --- Project Isolation ---
# MUST be unique for each project instance to ensure data isolation.
COMPOSE_PROJECT_NAME=commandcenter-project-a

# --- Security ---
# A long, random string used for signing tokens and encrypting data.
# Generate one with: openssl rand -hex 32
SECRET_KEY=your-super-secret-and-long-random-string-here

# Set to true to encrypt GitHub tokens in the database. Highly recommended.
ENCRYPT_TOKENS=true
```

### Optional API Keys

These keys enable advanced features like the RAG knowledge base and GitHub integration.

```bash
# .env

# --- AI/ML API Keys (for RAG features) ---
ANTHROPIC_API_KEY=sk-ant-...
OPENAI_API_KEY=sk-...

# --- GitHub Integration ---
# A Personal Access Token for fetching repository data.
GITHUB_TOKEN=ghp_...
```

---

## 3. Standard Docker Deployment

This is the simplest way to get CommandCenter running for a single project.

### Starting Services

1.  **Check for Port Conflicts:** Before starting, run the provided script to ensure the default ports are free.
    ```bash
    ./scripts/check-ports.sh
    ```
2.  **Start the Application:**
    ```bash
    docker compose up -d
    ```
    This command will build the container images (if they don't exist) and start all services in the background.

### Accessing the Application

-   **Frontend:** `http://localhost:3000`
-   **Backend API:** `http://localhost:8000`
-   **API Docs (Swagger):** `http://localhost:8000/docs`

### Port Management & Conflict Resolution

If the `check-ports.sh` script finds a conflict, you have two options:

1.  **Stop the Conflicting Service:** The script will offer to automatically kill the process that is using the required port.
2.  **Change the Port in `.env`:** Open your `.env` file and change the conflicting port number (e.g., change `FRONTEND_PORT=3000` to `FRONTEND_PORT=3001`). Then, restart the application with `docker compose up -d`.

### Useful Docker Commands

-   **View Logs:** `docker compose logs -f`
-   **Stop Services:** `docker compose down`
-   **Restart Services:** `docker compose restart`
-   **View Service Status:** `docker compose ps`
-   **Execute a Command in a Container:** `docker compose exec backend bash`

---

## 4. Advanced Deployment with Traefik

If you run many Docker-based projects, Traefik is a reverse proxy that eliminates port conflicts entirely.

### Why Use Traefik?

-   **Zero Port Conflicts:** Only Traefik uses ports 80 and 443.
-   **Clean URLs:** Access projects via hostnames like `http://project-a.localhost` instead of `http://localhost:3001`.
-   **Automatic Routing:** Traefik automatically discovers and routes traffic to your containers.

### One-Time Traefik Setup

You only need to do this once for your machine.

1.  **Create Traefik Directory & Files:**
    ```bash
    mkdir -p ~/traefik
    cd ~/traefik
    # Create docker-compose.yml and traefik.yml as specified in the detailed guide.
    # (See docs/TRAEFIK_SETUP.md for the full file contents)
    ```
2.  **Create the Public Network:**
    ```bash
    docker network create traefik-public
    ```
3.  **Start Traefik:**
    ```bash
    docker compose up -d
    ```
    You can now access the Traefik dashboard at `http://traefik.localhost:8080`.

### Configuring CommandCenter for Traefik

1.  **Create `docker-compose.traefik.yml`:** In your CommandCenter project directory, create a file named `docker-compose.traefik.yml`. This file will override the default configuration to work with Traefik.
    *(See the original `docs/TRAEFIK_SETUP.md` for the full file content.)*

    **Key Changes in this file:**
    -   Removes the `ports` definitions from the `frontend` and `backend` services.
    -   Adds `labels` to each service to tell Traefik how to route traffic to them.
    -   Connects the services to the external `traefik-public` network.
    -   Sets the `VITE_API_URL` for the frontend to use the Traefik route (e.g., `http://api.project-a.localhost`).

2.  **Start CommandCenter with Traefik:**
    ```bash
    # Make sure your COMPOSE_PROJECT_NAME is set in .env (e.g., project-a)
    docker compose -f docker-compose.traefik.yml up -d
    ```

3.  **Access the Application:**
    -   **Frontend:** `http://project-a.localhost`
    -   **Backend:** `http://api.project-a.localhost`

---

## 5. Production Deployment

### Production Best Practices

-   **Use Strong Secrets:** Generate long, random strings for `SECRET_KEY` and `DB_PASSWORD`.
-   **Enable HTTPS:** Use Traefik with Let's Encrypt for automatic SSL.
-   **Disable Debug Mode:** Ensure `DEBUG=false` in your production `.env` file.
-   **Set Resource Limits:** Configure CPU and memory limits in your `docker-compose.prod.yml` to prevent resource exhaustion.
-   **Configure Restart Policies:** Set `restart: unless-stopped` on your services to ensure they restart automatically after a crash or server reboot.

### Database Management

Database migrations are handled by Alembic.

-   **Apply Migrations:** Migrations are applied automatically when the backend container starts. To apply them manually:
    ```bash
    docker compose exec backend alembic upgrade head
    ```
-   **Create a New Migration:** If you change the database models, you'll need to create a new migration file:
    ```bash
    docker compose exec backend alembic revision --autogenerate -m "Your migration message"
    ```

### Backup and Recovery

It is critical to back up your data regularly.

-   **Database Backup:**
    ```bash
    docker compose exec -T postgres pg_dump -U commandcenter commandcenter | gzip > db_backup.sql.gz
    ```
-   **RAG Storage Backup:** The `rag_storage` volume contains all uploaded documents and the vector database.
    ```bash
    docker run --rm -v yourproject_rag_storage:/data -v $(pwd):/backup alpine tar czf /backup/rag_backup.tar.gz /data
    ```
-   **Automate:** Use a cron job to run these backup commands on a regular schedule.

---

## 6. Docling (RAG) Setup

Docling is the document processing library that powers the RAG knowledge base. It is automatically installed and configured in the backend Docker container.

### How it Works

1.  **Upload:** A user uploads a document (PDF, DOCX, MD, etc.) via the API.
2.  **Extraction:** Docling extracts text, tables, and metadata from the document.
3.  **Processing:** The extracted content is chunked, converted to vector embeddings, and stored in the project's isolated ChromaDB vector store.
4.  **Search:** The content is now fully searchable via the knowledge base's natural language query interface.

### Configuration

Docling's behavior can be tuned via environment variables in the `.env` file.

```bash
# .env

# The path inside the container where documents are stored.
# This is mounted to a Docker volume for persistence.
RAG_STORAGE_PATH=/app/rag_storage

# Maximum file size in MB for document uploads.
DOCLING_MAX_FILE_SIZE=50

# Timeout in seconds for processing a single file.
DOCLING_TIMEOUT=300
```

### Data Storage and Backups

All RAG-related data is stored in the `rag_storage` Docker volume. This includes original uploads, processed files, and the ChromaDB vector database. **This volume must be included in your backup strategy** alongside the PostgreSQL database to ensure a complete restoration of your knowledge base.
