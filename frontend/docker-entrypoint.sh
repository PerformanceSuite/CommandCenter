#!/bin/sh
# Docker entrypoint for frontend
# Injects runtime environment variables into the built static files

set -e

# Default values
PROJECT_NAME="${VITE_PROJECT_NAME:-Command Center}"
API_URL="${VITE_API_URL:-http://localhost:8000}"

# Create runtime config file that JavaScript can load
cat > /usr/share/nginx/html/config.js <<EOF
window.RUNTIME_CONFIG = {
  PROJECT_NAME: "${PROJECT_NAME}",
  API_BASE_URL: "${API_URL}",
};
EOF

echo "Runtime config injected:"
echo "  PROJECT_NAME: ${PROJECT_NAME}"
echo "  API_BASE_URL: ${API_URL}"

# Execute the original command (start nginx)
exec "$@"
