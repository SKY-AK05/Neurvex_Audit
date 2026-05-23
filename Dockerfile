# =============================================================================
# Single-container build: Vue frontend + FastAPI backend + nginx
# =============================================================================
# Stage 1: Build the Vue/Vite frontend
# =============================================================================
FROM node:20-alpine AS frontend-build

WORKDIR /frontend

# Install dependencies (cached layer)
COPY frontend/package*.json ./
RUN npm ci --include=dev

# Copy source and build
# VITE_MSAL_CLIENT_ID and VITE_MSAL_TENANT_ID are baked in at build time.
# Pass them as build args if you need to override (e.g. in CI):
#   docker build --build-arg VITE_MSAL_CLIENT_ID=xxx ...
ARG VITE_MSAL_CLIENT_ID
ARG VITE_MSAL_TENANT_ID
ENV VITE_MSAL_CLIENT_ID=$VITE_MSAL_CLIENT_ID
ENV VITE_MSAL_TENANT_ID=$VITE_MSAL_TENANT_ID

COPY frontend/ .
RUN npm run build

# =============================================================================
# Stage 2: Final image — Python + nginx + supervisord
# =============================================================================
FROM python:3.11-slim

# Install nginx and supervisord
RUN apt-get update && apt-get install -y --no-install-recommends \
    nginx \
    supervisor \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend source
COPY app/ app/

# Copy built Vue dist from Stage 1
COPY --from=frontend-build /frontend/dist /app/dist

# Copy nginx config — points to /app/dist and proxies /api/ to 127.0.0.1:8000
COPY frontend/nginx.conf /etc/nginx/conf.d/default.conf
# Remove the default nginx site
RUN rm -f /etc/nginx/sites-enabled/default

# Copy supervisord config
COPY supervisord.conf /etc/supervisor/conf.d/supervisord.conf

# ACA only exposes one port — nginx listens here and routes internally
EXPOSE 80

# supervisord starts both nginx and uvicorn
CMD ["/usr/bin/supervisord", "-c", "/etc/supervisor/conf.d/supervisord.conf"]
