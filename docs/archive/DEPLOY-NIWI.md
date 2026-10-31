# NiWI Container Deployment Guide

## 🎯 Overview

The `niwi` container (port 8080) is **NOT managed by docker-compose.yml**. It must be rebuilt and redeployed **manually** whenever code changes are pushed to GitHub.

The `orchvate-audit` container (port 3600) IS managed by docker-compose and rebuilds automatically with `docker-compose up -d --build`.

---

## 🚀 Deploy Updated Code to NiWI Container

### Prerequisites
- SSH access to VM: `taiga.orchvate.com`
- User: `aakash.padyachi@orchvate.com`
- Project path: `~/apps/niwi/Audit`

### Deployment Steps

```bash
# Navigate to project directory
cd ~/apps/niwi/Audit

# 1. Pull latest code from GitHub
git pull origin main

# 2. Verify what was pulled
git log -3 --oneline

# 3. Rebuild the niwi Docker image with new code
sudo docker build -t niwi -f Dockerfile .

# 4. Stop the old niwi container
sudo docker stop niwi

# 5. Remove the old niwi container
sudo docker rm niwi

# 6. Start new niwi container with same settings
sudo docker run -d \
  --name niwi \
  -p 8080:80 \
  --env-file .env \
  -e TZ=Asia/Kolkata \
  --restart unless-stopped \
  niwi

# 7. Verify it's running
sudo docker ps | grep niwi

# 8. Check the logs for errors
sudo docker logs -f niwi
# Press Ctrl+C to exit logs
```

---

## 📋 Container Information

### NiWI Container (Production)
- **Container Name:** `niwi`
- **Image:** `niwi` (custom built)
- **Port Mapping:** `8080:80` (external:internal)
- **Access URL:** `http://taiga.orchvate.com:8080`
- **Restart Policy:** `unless-stopped`
- **Environment:** Uses `.env` file + `TZ=Asia/Kolkata`
- **Management:** Manual (not in docker-compose.yml)

### Orchvate-Audit Container (Dev/Test)
- **Container Name:** `orchvate-audit`
- **Port Mapping:** `3600:80`
- **Access URL:** `http://taiga.orchvate.com:3600`
- **Management:** Automated via docker-compose.yml

---

## 🔍 Useful Commands

### Check Container Status
```bash
# List all running containers
sudo docker ps

# Check specific container
sudo docker ps | grep niwi

# View container details
sudo docker inspect niwi
```

### View Logs
```bash
# Live tail logs
sudo docker logs -f niwi

# Last 100 lines
sudo docker logs --tail 100 niwi

# Logs since last hour
sudo docker logs --since 1h niwi
```

### Restart Without Rebuild
```bash
# Quick restart (no code changes)
sudo docker restart niwi
```

### Access Container Shell
```bash
# Open bash inside container
sudo docker exec -it niwi bash

# Check files inside container
sudo docker exec niwi ls -la /app/dist
```

---

## 🐛 Troubleshooting

### Container Won't Start
```bash
# Check logs for errors
sudo docker logs niwi

# Check if port 8080 is already in use
sudo netstat -tulpn | grep 8080
# OR
sudo ss -tulpn | grep 8080
```

### Database Connection Errors
```
ERROR: connection to server at "generative-ai.postgres.database.azure.com"
```
- Check `.env` file has correct `PGHOST`, `PGPORT`, `PGDATABASE`, `PGUSER`, `PGPASSWORD`
- Verify Azure PostgreSQL firewall allows VM IP address

### Frontend Not Updating
```bash
# Verify build date inside container
sudo docker exec niwi ls -lh /app/dist

# Force rebuild without cache
sudo docker build --no-cache -t niwi -f Dockerfile .
```

---

## 📝 Important Notes

1. **Always pull from GitHub before rebuilding** - The container builds from local files, not directly from GitHub
2. **Check logs after deployment** - Ensure no startup errors
3. **Frontend is built during Docker build** - Changes to Vue files require full rebuild
4. **Environment variables** - Stored in `.env` file, mounted at runtime
5. **Database errors are non-critical** - The email worker DB connection error doesn't affect main application

---

## 🔄 Full Rebuild Process (Clean Slate)

If you need to completely reset:

```bash
# Stop and remove container
sudo docker stop niwi
sudo docker rm niwi

# Remove old image
sudo docker rmi niwi

# Pull latest code
cd ~/apps/niwi/Audit
git pull origin main

# Rebuild from scratch
sudo docker build --no-cache -t niwi -f Dockerfile .

# Start fresh container
sudo docker run -d \
  --name niwi \
  -p 8080:80 \
  --env-file .env \
  -e TZ=Asia/Kolkata \
  --restart unless-stopped \
  niwi
```

---

## 📞 Deployment Checklist

- [ ] SSH into VM: `ssh aakash.padyachi@orchvate.com@taiga.orchvate.com`
- [ ] Navigate to project: `cd ~/apps/niwi/Audit`
- [ ] Pull latest code: `git pull origin main`
- [ ] Rebuild image: `sudo docker build -t niwi -f Dockerfile .`
- [ ] Stop old container: `sudo docker stop niwi`
- [ ] Remove old container: `sudo docker rm niwi`
- [ ] Start new container: `sudo docker run -d --name niwi -p 8080:80 --env-file .env -e TZ=Asia/Kolkata --restart unless-stopped niwi`
- [ ] Verify running: `sudo docker ps | grep niwi`
- [ ] Check logs: `sudo docker logs -f niwi`
- [ ] Test in browser: `http://taiga.orchvate.com:8080`

---

## 🏗️ Architecture

```
GitHub (SKY-AK05/Neurvex_Audit)
    ↓ git pull
Local Files (~/apps/niwi/Audit)
    ↓ docker build
Docker Image (niwi)
    ↓ docker run
Docker Container (niwi)
    ↓ port 8080
Production (taiga.orchvate.com:8080)
```

---

**Last Updated:** June 4, 2026  
**Maintained By:** Orchvate Team
