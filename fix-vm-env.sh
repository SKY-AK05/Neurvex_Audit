#!/bin/bash

# Script to fix CORS and FRONTEND_URL on VM
# The issue: VM has neuromark.orchvate.in but should be niwi.orchvate.in

echo "🔧 Fixing .env configuration on VM"
echo "===================================="
echo ""

# Backup current .env
echo "📋 Creating backup..."
cp .env .env.backup.$(date +%Y%m%d_%H%M%S)

# Fix CORS_ORIGINS
echo "🔄 Updating CORS_ORIGINS..."
sed -i 's|CORS_ORIGINS=.*|CORS_ORIGINS=https://niwi.orchvate.in|g' .env

# Fix FRONTEND_URL
echo "🔄 Updating FRONTEND_URL..."
sed -i 's|FRONTEND_URL=.*|FRONTEND_URL=https://niwi.orchvate.in|g' .env

# Show changes
echo ""
echo "✅ Updated values:"
grep "CORS_ORIGINS=" .env
grep "FRONTEND_URL=" .env
echo ""

echo "📊 Current configuration:"
echo "------------------------"
cat .env | grep -v "PASSWORD\|CONNECTION_STRING\|JWT_SECRET\|accesskey"
echo ""

read -p "Deploy with these changes? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo ""
    echo "🚀 Deploying..."
    ./deploy.sh
else
    echo "❌ Cancelled. Run ./deploy.sh manually when ready."
fi
