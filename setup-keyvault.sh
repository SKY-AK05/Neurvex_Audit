#!/bin/bash
# Setup script for Azure Key Vault configuration
# Run this once on the server to configure Key Vault settings

set -e

echo "🔐 Azure Key Vault Setup for NIWI"
echo "=================================="
echo ""

# Prompt for Key Vault name
read -p "Enter your Azure Key Vault name (e.g., niwi-secrets): " VAULT_NAME

if [ -z "$VAULT_NAME" ]; then
    echo "❌ Key Vault name cannot be empty"
    exit 1
fi

# Export for current session
export KEY_VAULT_NAME="$VAULT_NAME"

# Add to ~/.bashrc for persistence
if ! grep -q "KEY_VAULT_NAME" ~/.bashrc; then
    echo "" >> ~/.bashrc
    echo "# Azure Key Vault for NIWI" >> ~/.bashrc
    echo "export KEY_VAULT_NAME=\"$VAULT_NAME\"" >> ~/.bashrc
    echo "✅ Added KEY_VAULT_NAME to ~/.bashrc"
else
    echo "ℹ️  KEY_VAULT_NAME already exists in ~/.bashrc"
fi

echo ""
echo "✅ Azure Key Vault configured!"
echo ""
echo "Key Vault Name: $VAULT_NAME"
echo "Vault URL: https://${VAULT_NAME}.vault.azure.net/"
echo ""
echo "📋 Next steps:"
echo "1. Ensure your VM has Managed Identity enabled"
echo "2. Grant the Managed Identity 'Key Vault Secrets User' role"
echo "3. Add these secrets to your Key Vault:"
echo "   - pghost"
echo "   - pgport"
echo "   - pgdatabase"
echo "   - pguser"
echo "   - pgpassword"
echo "   - acs-connection-string"
echo "   - acs-sender-address"
echo "   - acs-sender-name"
echo "   - jwt-secret"
echo "   - entra-client-id"
echo "   - entra-tenant-id"
echo ""
echo "4. Run: source ~/.bashrc"
echo "5. Run: ./deploy.sh"
echo ""
