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

# Copy only requirements to leverage Docker cache
COPY requirements.txt .

# Install dependencies
RUN pip install --user --no-cache-dir -r requirements.txt

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

# Copy the application code
COPY --chown=appuser:appuser . .

# Create necessary directories and set permissions
# No need for chmod +x if scripts/startup.sh is checked in with correct permissions
RUN mkdir -p /app/logs /app/data && \
    chown -R appuser:appuser /app

# Switch to the non-root user
USER appuser

# Add the user's local bin to the PATH
ENV PATH=/home/appuser/.local/bin:$PATH

# Expose the application port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD ["python", "-c", "import urllib.request; urllib.request.urlopen('http://localhost:8000/health').read()"]

# Make startup script executable
RUN chmod +x /app/scripts/startup.sh

# Run the application
CMD ["/app/scripts/startup.sh"]
