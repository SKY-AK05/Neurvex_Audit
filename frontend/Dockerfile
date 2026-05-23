# ── Stage 1: Build the Vue app ────────────────────────────────────────────────
# node_modules is excluded via .dockerignore — npm ci runs fresh inside Linux
# so all node_modules/.bin symlinks have correct execute permissions
FROM node:20-alpine AS build

WORKDIR /app

# Set production environment to optimize install
ENV NODE_ENV=production

# Copy package files first (cached Docker layer)
COPY package*.json ./

# Clean install inside Linux — fixes tsc/vite permission errors from Windows builds
RUN npm ci --include=dev

# Copy source files (node_modules excluded via .dockerignore)
COPY . .

# Build the app — uses `vite build` directly (tsc noEmit:true means it doesn't output anyway)
RUN npm run build

# ── Stage 2: Serve with nginx (lean production image) ────────────────────────
FROM nginx:1.27-alpine

# Remove default nginx page
RUN rm -rf /usr/share/nginx/html/*

# Copy the built Vue dist files from Stage 1
COPY --from=build /app/dist /usr/share/nginx/html

# Copy our custom nginx config
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
