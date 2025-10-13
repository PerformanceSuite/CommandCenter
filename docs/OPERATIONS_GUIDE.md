# CommandCenter Operations Guide

**Version:** 2.0
**Last Updated:** 2025-10-12

This document provides a comprehensive guide for deploying, managing, and monitoring the CommandCenter application in a production environment. It is intended for DevOps engineers, SREs, and system administrators.

## Table of Contents

1.  [**CI/CD Pipeline**](#1-cicd-pipeline)
2.  [**Production Deployment**](#2-production-deployment)
3.  [**Observability: Logging, Metrics & Tracing**](#3-observability-logging-metrics--tracing)
    *   [Health Checks](#health-checks)
    *   [Structured Logging & Tracing](#structured-logging--tracing)
    *   [Prometheus Metrics](#prometheus-metrics)
    *   [Monitoring Setup](#monitoring-setup)
4.  [**Backup & Restore**](#4-backup--restore)
5.  [**Performance Optimization**](#5-performance-optimization)
    *   [Database Optimization](#database-optimization)
    *   [Caching Strategy](#caching-strategy)
    *   [API & Frontend Performance](#api--frontend-performance)
    *   [Background Worker Optimization](#background-worker-optimization)
6.  [**Maintenance & Troubleshooting**](#6-maintenance--troubleshooting)

---

## 1. CI/CD Pipeline

The CI/CD pipeline is managed via GitHub Actions and is configured to run on every push and pull request.

### Pipeline Stages

1.  **Linting & Static Analysis:** Code is checked for formatting (Black), style (Flake8, ESLint), and type safety (MyPy, TypeScript).
2.  **Unit Tests:** Pytest and Vitest are run to ensure individual components are working correctly. Coverage reports are uploaded to Codecov.
3.  **Security Scanning:** The codebase and its dependencies are scanned for vulnerabilities using tools like Bandit, Safety, and Trivy.
4.  **Docker Build:** The `backend` and `frontend` Docker images are built to ensure they are valid.
5.  **Integration Tests:** A full Docker Compose environment is spun up to run end-to-end tests that verify the interaction between services.

To run these checks locally, refer to the `[project-root]/.github/workflows/ci.yml` file for the exact commands.

---

## 2. Production Deployment

### Deployment Strategy

The recommended deployment method is using Docker Compose with a production-specific override file and Traefik as a reverse proxy.

1.  **Environment Configuration:** Create a `.env.prod` file with production-level secrets (strong database password, long `SECRET_KEY`) and configuration (e.g., `ENVIRONMENT=production`, `LOG_LEVEL=INFO`).
2.  **Run Production Compose:**
    ```bash
    docker-compose -f docker-compose.prod.yml --env-file .env.prod up -d
    ```
    The `docker-compose.prod.yml` file is configured for high availability with `restart: unless-stopped` policies and resource limits.
3.  **SSL/TLS:** The production setup uses Traefik to automatically provision and renew SSL certificates from Let's Encrypt, enforce HTTPS, and apply modern security headers.

### Scaling

-   **Horizontal Scaling:** You can scale the number of backend or Celery worker containers directly with Docker Compose:
    ```bash
    docker-compose -f docker-compose.prod.yml up -d --scale backend=3 --scale celery-worker=8
    ```
    Traefik will automatically load-balance requests across the scaled `backend` instances.
-   **Vertical Scaling:** Adjust the CPU and memory reservations and limits for each service in the `docker-compose.prod.yml` file to match your hardware.

---

## 3. Observability: Logging, Metrics & Tracing

CommandCenter is built with observability as a first-class citizen. The `monitoring/` directory contains configurations for a full Prometheus, Grafana, and Loki stack.

### Health Checks

-   **Basic:** `GET /health` - Returns a simple `200 OK` if the application is running. Use this for load balancer health checks.
-   **Detailed:** `GET /health/detailed` - Provides a JSON response with the status of all critical components (Database, Redis, Celery). Returns a `503` if any component is unhealthy.

### Structured Logging & Tracing

-   **JSON Logs:** In production, all logs are emitted in a structured JSON format, which is ideal for aggregation and analysis in tools like Loki or the ELK stack.
-   **Request Tracing:** Every incoming request is assigned a unique `X-Request-ID`. This ID is included in every log line generated during that request's lifecycle, allowing you to trace its path through the API, background jobs, and database queries.

### Prometheus Metrics

The application exposes a `/metrics` endpoint for Prometheus to scrape. Key metrics include:

-   `http_request_duration_seconds`: Latency histograms for API endpoints.
-   `commandcenter_job_operations_total`: Counters for background jobs, tagged by type and status.
-   `commandcenter_job_queue_size`: A gauge showing the number of jobs in the queue, tagged by status.
-   `commandcenter_db_connection_pool_size`: Metrics on the state of the database connection pool.
-   `commandcenter_cache_operations_total`: Cache hit/miss counters.

### Monitoring Setup

-   **Prometheus:** Scrapes the `/metrics` endpoint. The configuration in `monitoring/prometheus.yml` is pre-set.
-   **Loki:** Aggregates logs from all Docker containers.
-   **Grafana:** Provides pre-built dashboards for visualizing metrics and logs. Access it at `https-grafana.your-domain.com`.
-   **Alerting:** Critical alert rules are defined in `monitoring/alerts.yml`. These include alerts for service downtime, high API latency, high error rates, and a growing job queue.

---

## 4. Backup & Restore

Automated backups are essential for data safety.

### Automated Backups

-   **What's Backed Up:**
    1.  The PostgreSQL database.
    2.  The `rag_storage` volume, which contains all uploaded documents and the ChromaDB vector store.
-   **How to Set Up:** Run the provided script to install a cron job that performs daily backups.
    ```bash
    ./scripts/setup-backup-cron.sh
    ```
-   **Backup Location:** Backups are stored locally in the `backups/` directory. For production, you should modify `scripts/backup.sh` to upload these backups to a remote, secure location like AWS S3.

### Restore from Backup

-   **How to Restore:** Use the provided restore script.
    ```bash
    # Restore the latest backup
    ./scripts/restore.sh

    # Restore a specific backup by timestamp
    ./scripts/restore.sh <timestamp>
    ```
    This script handles stopping the services, restoring the data to the correct volumes, and restarting the services.

---

## 5. Performance Optimization

### Database Optimization

-   **Indexing:** All critical foreign keys and frequently queried columns have indexes. For custom query patterns, you may need to add new indexes. Use a `GIN` index for querying `JSONB` fields.
-   **Connection Pooling:** The application uses a connection pool to efficiently manage database connections. You can tune the `pool_size` and `max_overflow` settings in `app/database.py` for high-traffic environments.
-   **Query Analysis:** Use `EXPLAIN ANALYZE` and `pg_stat_statements` to identify and optimize slow queries.

### Caching Strategy

-   **Redis:** Redis is used for caching frequently accessed, slow-to-compute data, such as dashboard statistics or technology lists.
-   **Cache Invalidation:** The application logic is responsible for invalidating cache keys when the underlying data is modified.
-   **Monitoring:** Monitor the cache hit rate (`commandcenter_cache_operations_total`). A low hit rate may indicate that the cache TTLs need tuning or that more caching is needed.

### API & Frontend Performance

-   **Response Compression:** Gzip middleware is enabled to compress large API responses.
-   **Rate Limiting:** Endpoints are rate-limited to prevent abuse.
-   **Code Splitting:** The frontend uses lazy loading for routes to reduce the initial bundle size.
-   **Debouncing:** User inputs (like search bars) are debounced to prevent excessive API calls.

### Background Worker Optimization

-   **Concurrency:** The number of concurrent Celery workers (`CELERY_WORKER_CONCURRENCY`) should be tuned based on the workload. A good starting point is `2 * number_of_cpu_cores`.
-   **Task Routing:** For larger-scale deployments, consider routing different types of tasks to different queues with dedicated workers (e.g., a high-priority queue for short tasks and a low-priority queue for long-running analyses).
-   **Time Limits:** All tasks have soft and hard time limits to prevent them from running indefinitely.

---

## 6. Maintenance & Troubleshooting

### Application Updates

1.  Pull the latest code from the `main` branch.
2.  Rebuild the Docker images: `docker-compose -f docker-compose.prod.yml build`
3.  Restart the services: `docker-compose -f docker-compose.prod.yml up -d`
4.  Apply any new database migrations: `docker-compose -f docker-compose.prod.yml exec backend alembic upgrade head`

### Troubleshooting

-   **High Error Rate:** Check the Grafana dashboard for the error rate panel. Use the `X-Request-ID` from a failing request to trace its logs in Loki.
-   **High API Latency:** Identify the slow endpoint in Grafana. Check the database query performance for that endpoint and look for opportunities to add caching or optimize queries.
-   **Job Queue Growing:** If the `commandcenter_job_queue_size` metric is constantly increasing, it means jobs are being created faster than they can be processed. You may need to scale up the number of `celery-worker` containers.
