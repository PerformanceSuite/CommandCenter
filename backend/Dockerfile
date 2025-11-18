# Multi-stage Dockerfile for Command Center Backend

# -----------------------------------------------------------------------------
# 1. Builder Stage: Install dependencies
# -----------------------------------------------------------------------------
FROM python:3.11-slim AS builder

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install build-time system dependencies
# - gcc, g++, libpq-dev are required to build psycopg2 from source
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy libs directory first (needed for knowledgebeast editable install)
COPY libs/ /app/libs/

# Copy only requirements to leverage Docker cache
COPY backend/requirements.txt .

# Install dependencies (replace relative path with absolute for Docker)
# The -e ../libs/knowledgebeast becomes -e /app/libs/knowledgebeast
RUN sed -i 's|^\-e \.\./libs/knowledgebeast|-e /app/libs/knowledgebeast|' requirements.txt && \
    pip install --user --no-cache-dir -r requirements.txt

# -----------------------------------------------------------------------------
# 2. Runtime Stage: Create the final, lean image
# -----------------------------------------------------------------------------
FROM python:3.11-slim AS runtime

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# Create a non-root user to run the application
RUN useradd -m -u 1000 appuser

WORKDIR /app

# Install runtime-only system dependencies
# - libpq5 is the runtime library for psycopg2
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy installed Python packages from the builder stage
COPY --from=builder --chown=appuser:appuser /root/.local /home/appuser/.local

# Copy libs directory (for editable knowledgebeast install)
COPY --from=builder --chown=appuser:appuser /app/libs /app/libs

# Copy the application code
COPY --chown=appuser:appuser backend/ .

# Create necessary directories and set permissions
RUN mkdir -p /app/logs /app/data && \
    chown -R appuser:appuser /app

# Switch to the non-root user
USER appuser

# Add the user's local bin to the PATH
ENV PATH=/home/appuser/.local/bin:$PATH

# Expose the application port
EXPOSE 8000

# Health check (verify HTTP 200 status)
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD ["python", "-c", "import urllib.request; resp=urllib.request.urlopen('http://localhost:8000/health'); exit(0 if resp.status==200 else 1)"]

# Make startup script executable
RUN chmod +x /app/scripts/startup.sh

# Run the application
CMD ["/app/scripts/startup.sh"]
