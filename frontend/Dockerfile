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

# Expose the port Nginx listens on
EXPOSE 80

# Start Nginx in the foreground
CMD ["nginx", "-g", "daemon off;"]
