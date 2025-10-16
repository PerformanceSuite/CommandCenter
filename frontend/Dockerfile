# -----------------------------------------------------------------------------
# 1. Builder Stage: Build the React application
# -----------------------------------------------------------------------------
FROM node:20-alpine AS builder

WORKDIR /app

# Copy package manager files first to leverage Docker cache
COPY package.json package-lock.json ./

# Install dependencies securely and efficiently
RUN npm ci

# Copy the rest of the application source code
COPY . .

# Accept build arguments for Vite environment variables
ARG VITE_PROJECT_NAME
ARG VITE_API_BASE_URL

# Set environment variables for the build
ENV VITE_PROJECT_NAME=${VITE_PROJECT_NAME}
ENV VITE_API_BASE_URL=${VITE_API_BASE_URL}

# Build the application for production
RUN npm run build

# -----------------------------------------------------------------------------
# 2. Production Stage: Serve the static files with Nginx
# -----------------------------------------------------------------------------
FROM nginx:alpine AS production

# Copy the built static files from the builder stage
COPY --from=builder /app/dist /usr/share/nginx/html

# Copy the custom Nginx configuration
# This config is crucial for routing all requests to index.html for a React SPA
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Copy entrypoint script for runtime configuration
COPY docker-entrypoint.sh /docker-entrypoint.sh
RUN chmod +x /docker-entrypoint.sh

# Expose the port Nginx listens on
EXPOSE 80

# Use entrypoint to inject runtime config
ENTRYPOINT ["/docker-entrypoint.sh"]
CMD ["nginx", "-g", "daemon off;"]
