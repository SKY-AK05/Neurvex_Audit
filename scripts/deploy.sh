#!/bin/bash
set -e

# NIWI Deployment Script
# Deploys the latest code to taiga.orchvate.com:8080

echo "🚀 NIWI Deployment Script"
echo "========================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
CONTAINER_NAME="niwi"
IMAGE_NAME="niwi"
PORT_MAPPING="8080:80"
ENV_FILE=".env"
TIMEZONE="Asia/Kolkata"

echo -e "${BLUE}📁 Current directory: $(pwd)${NC}"
echo ""

# Step 1: Sync with GitHub (force update to match GitHub exactly)
echo -e "${YELLOW}📥 Step 1/7: Syncing with GitHub (force update)...${NC}"
git fetch origin
git reset --hard origin/main
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Code synced successfully${NC}"
else
    echo -e "${RED}❌ Failed to sync code${NC}"
    exit 1
fi
echo ""

# Show recent commits
echo -e "${BLUE}📋 Recent commits:${NC}"
git log -3 --oneline --decorate
echo ""

# Step 2: Build Docker image
echo -e "${YELLOW}🏗️  Step 2/7: Building Docker image...${NC}"
sudo docker build -t $IMAGE_NAME -f Dockerfile .
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Docker image built successfully${NC}"
else
    echo -e "${RED}❌ Failed to build Docker image${NC}"
    exit 1
fi
echo ""

# Step 3: Stop old container
echo -e "${YELLOW}🛑 Step 3/7: Stopping old container...${NC}"
if sudo docker ps | grep -q $CONTAINER_NAME; then
    sudo docker stop $CONTAINER_NAME
    echo -e "${GREEN}✅ Container stopped${NC}"
else
    echo -e "${BLUE}ℹ️  Container was not running${NC}"
fi
echo ""

# Step 4: Remove old container
echo -e "${YELLOW}🗑️  Step 4/7: Removing old container...${NC}"
if sudo docker ps -a | grep -q $CONTAINER_NAME; then
    sudo docker rm $CONTAINER_NAME
    echo -e "${GREEN}✅ Container removed${NC}"
else
    echo -e "${BLUE}ℹ️  No container to remove${NC}"
fi
echo ""

# Step 5: Start new container
echo -e "${YELLOW}🚀 Step 5/7: Starting new container...${NC}"
sudo docker run -d \
  --name $CONTAINER_NAME \
  -p $PORT_MAPPING \
  --env-file $ENV_FILE \
  -e TZ=$TIMEZONE \
  --restart unless-stopped \
  $IMAGE_NAME

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Container started successfully${NC}"
else
    echo -e "${RED}❌ Failed to start container${NC}"
    exit 1
fi
echo ""

# Step 6: Verify container is running
echo -e "${YELLOW}🔍 Step 6/7: Verifying container status...${NC}"
sleep 3
if sudo docker ps | grep -q $CONTAINER_NAME; then
    echo -e "${GREEN}✅ Container is running${NC}"
    sudo docker ps | grep $CONTAINER_NAME
else
    echo -e "${RED}❌ Container is not running${NC}"
    exit 1
fi
echo ""

# Step 7: Show recent logs
echo -e "${YELLOW}📝 Step 7/7: Checking logs...${NC}"
sudo docker logs --tail 30 $CONTAINER_NAME
echo ""

# Summary
echo -e "${GREEN}================================${NC}"
echo -e "${GREEN}✅ Deployment completed successfully!${NC}"
echo -e "${GREEN}================================${NC}"
echo ""
echo -e "${BLUE}🌐 Application URL: http://taiga.orchvate.com:8080${NC}"
echo ""
echo -e "${YELLOW}💡 Useful commands:${NC}"
echo -e "  View logs:      sudo docker logs -f $CONTAINER_NAME"
echo -e "  Restart:        sudo docker restart $CONTAINER_NAME"
echo -e "  Stop:           sudo docker stop $CONTAINER_NAME"
echo -e "  Container info: sudo docker inspect $CONTAINER_NAME"
echo ""
