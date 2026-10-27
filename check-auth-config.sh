#!/bin/bash

# NIWI Auth Configuration Checker
# Run this on your VM to diagnose authentication issues

echo "🔍 NIWI Authentication Configuration Checker"
echo "============================================"
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Check if .env file exists
echo -e "${BLUE}1. Checking .env file...${NC}"
if [ -f .env ]; then
    echo -e "${GREEN}✅ .env file exists${NC}"
    
    # Check ENTRA_CLIENT_ID
    if grep -q "ENTRA_CLIENT_ID=your-azure-ad-application-client-id" .env; then
        echo -e "${RED}❌ ENTRA_CLIENT_ID is still a placeholder${NC}"
    elif grep -q "ENTRA_CLIENT_ID=" .env; then
        CLIENT_ID=$(grep "ENTRA_CLIENT_ID=" .env | cut -d '=' -f2)
        if [ -n "$CLIENT_ID" ]; then
            echo -e "${GREEN}✅ ENTRA_CLIENT_ID is set${NC}"
        else
            echo -e "${RED}❌ ENTRA_CLIENT_ID is empty${NC}"
        fi
    else
        echo -e "${RED}❌ ENTRA_CLIENT_ID not found in .env${NC}"
    fi
    
    # Check ENTRA_TENANT_ID
    if grep -q "ENTRA_TENANT_ID=your-azure-ad-tenant-id" .env; then
        echo -e "${RED}❌ ENTRA_TENANT_ID is still a placeholder${NC}"
    elif grep -q "ENTRA_TENANT_ID=" .env; then
        TENANT_ID=$(grep "ENTRA_TENANT_ID=" .env | cut -d '=' -f2)
        if [ -n "$TENANT_ID" ]; then
            echo -e "${GREEN}✅ ENTRA_TENANT_ID is set${NC}"
        else
            echo -e "${RED}❌ ENTRA_TENANT_ID is empty${NC}"
        fi
    else
        echo -e "${RED}❌ ENTRA_TENANT_ID not found in .env${NC}"
    fi
else
    echo -e "${RED}❌ .env file not found${NC}"
fi
echo ""

# Check if container is running
echo -e "${BLUE}2. Checking container status...${NC}"
if sudo docker ps | grep -q niwi; then
    echo -e "${GREEN}✅ Container 'niwi' is running${NC}"
    
    # Check environment variables in container
    echo -e "${BLUE}3. Checking container environment variables...${NC}"
    CLIENT_IN_CONTAINER=$(sudo docker exec niwi env | grep "ENTRA_CLIENT_ID=" | cut -d '=' -f2)
    TENANT_IN_CONTAINER=$(sudo docker exec niwi env | grep "ENTRA_TENANT_ID=" | cut -d '=' -f2)
    
    if [[ "$CLIENT_IN_CONTAINER" == "your-azure-ad-application-client-id" ]] || [ -z "$CLIENT_IN_CONTAINER" ]; then
        echo -e "${RED}❌ ENTRA_CLIENT_ID not properly set in container${NC}"
    else
        echo -e "${GREEN}✅ ENTRA_CLIENT_ID is loaded in container${NC}"
    fi
    
    if [[ "$TENANT_IN_CONTAINER" == "your-azure-ad-tenant-id" ]] || [ -z "$TENANT_IN_CONTAINER" ]; then
        echo -e "${RED}❌ ENTRA_TENANT_ID not properly set in container${NC}"
    else
        echo -e "${GREEN}✅ ENTRA_TENANT_ID is loaded in container${NC}"
    fi
else
    echo -e "${RED}❌ Container 'niwi' is not running${NC}"
    exit 1
fi
echo ""

# Test the API endpoint
echo -e "${BLUE}4. Testing /api/auth/config endpoint...${NC}"
AUTH_RESPONSE=$(curl -s http://localhost:8080/api/auth/config 2>/dev/null)
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ API endpoint is accessible${NC}"
    echo -e "${YELLOW}Response:${NC}"
    echo "$AUTH_RESPONSE" | python3 -m json.tool 2>/dev/null || echo "$AUTH_RESPONSE"
    
    # Check if response contains valid IDs
    if echo "$AUTH_RESPONSE" | grep -q '"clientId": null' || echo "$AUTH_RESPONSE" | grep -q '"tenantId": null'; then
        echo -e "${RED}❌ API is returning null values - Azure AD is not configured${NC}"
    else
        echo -e "${GREEN}✅ API is returning configuration${NC}"
    fi
else
    echo -e "${RED}❌ Cannot reach API endpoint${NC}"
fi
echo ""

# Check recent logs
echo -e "${BLUE}5. Recent container logs (last 20 lines):${NC}"
sudo docker logs --tail 20 niwi
echo ""

# Summary and recommendations
echo -e "${YELLOW}================================${NC}"
echo -e "${YELLOW}Summary and Recommendations${NC}"
echo -e "${YELLOW}================================${NC}"
echo ""

if [[ "$CLIENT_IN_CONTAINER" == "your-azure-ad-application-client-id" ]] || [ -z "$CLIENT_IN_CONTAINER" ]; then
    echo -e "${RED}🔧 ACTION REQUIRED:${NC}"
    echo "1. Set up Azure AD App Registration (see AZURE_AD_SETUP.md)"
    echo "2. Update .env file with actual ENTRA_CLIENT_ID and ENTRA_TENANT_ID"
    echo "3. Redeploy using ./deploy.sh"
else
    echo -e "${GREEN}✅ Azure AD configuration looks good${NC}"
    echo ""
    echo "If authentication still fails, check:"
    echo "- Admin users are added to database: SELECT * FROM admin_users;"
    echo "- Azure AD redirect URIs include: https://niwi.orchvate.in/portal"
    echo "- Check browser console for detailed error messages"
fi
echo ""
