# CommandCenter Hub Backend Dockerfile

FROM python:3.11-slim

WORKDIR /app

# Install system dependencies for docker-compose and git
RUN apt-get update && apt-get install -y \
    git \
    docker-compose \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY app ./app

# Create data directory for SQLite
RUN mkdir -p /app/data

# Expose port
EXPOSE 9001

# Run with uvicorn
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "9001"]
