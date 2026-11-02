#!/bin/bash
# Test script to verify Azure Key Vault access from Docker container
# Run this on your server to test before deploying

echo "🧪 Testing Azure Key Vault Access from Docker Container"
echo "========================================================"
echo ""

# Check if KEY_VAULT_NAME is set
if [ -z "$KEY_VAULT_NAME" ]; then
    echo "❌ KEY_VAULT_NAME is not set"
    echo "Set it with: export KEY_VAULT_NAME=niwi-prod-kv"
    exit 1
fi

echo "✓ KEY_VAULT_NAME: $KEY_VAULT_NAME"
echo ""

# Create test Python script
cat > /tmp/test_kv.py << 'PYTHON_SCRIPT'
import sys
import os

print("=" * 60)
print("Azure Key Vault Docker Test")
print("=" * 60)
print()

# Test 1: Check environment
print("Test 1: Environment Variables")
print("-" * 60)
vault_name = os.environ.get("KEY_VAULT_NAME", "NOT SET")
print(f"KEY_VAULT_NAME: {vault_name}")
print(f"APP_ENV: {os.environ.get('APP_ENV', 'NOT SET')}")
print()

# Test 2: Check Azure SDK
print("Test 2: Azure SDK Import")
print("-" * 60)
try:
    from azure.identity import DefaultAzureCredential, ManagedIdentityCredential
    from azure.keyvault.secrets import SecretClient
    print("✓ Azure SDK imported successfully")
except ImportError as e:
    print(f"✗ Azure SDK import failed: {e}")
    sys.exit(1)
print()

# Test 3: Test Managed Identity
print("Test 3: Managed Identity Authentication")
print("-" * 60)
try:
    credential = DefaultAzureCredential()
    print("✓ DefaultAzureCredential created")
    
    # Try to get a token
    token = credential.get_token("https://vault.azure.net/.default")
    print("✓ Successfully obtained token from Azure")
    print(f"  Token type: {type(token)}")
except Exception as e:
    print(f"✗ Managed Identity authentication failed:")
    print(f"  {type(e).__name__}: {e}")
    sys.exit(1)
print()

# Test 4: Connect to Key Vault
print("Test 4: Key Vault Connection")
print("-" * 60)
try:
    vault_url = f"https://{vault_name}.vault.azure.net/"
    print(f"Vault URL: {vault_url}")
    
    client = SecretClient(vault_url=vault_url, credential=credential)
    print("✓ SecretClient created")
    
    # Try to get a secret
    secret = client.get_secret("PGHOST")
    print("✓ Successfully retrieved secret 'PGHOST'")
    print(f"  Secret value exists: {bool(secret.value)}")
    print(f"  Secret value length: {len(secret.value) if secret.value else 0}")
    
except Exception as e:
    print(f"✗ Key Vault connection failed:")
    print(f"  {type(e).__name__}: {e}")
    sys.exit(1)
print()

print("=" * 60)
print("✅ ALL TESTS PASSED!")
print("=" * 60)
print()
print("Your application SHOULD work with Azure Key Vault in Docker.")
PYTHON_SCRIPT

echo "Test script created: /tmp/test_kv.py"
echo ""

# Test with host network mode
echo "Test A: Running in Docker with --network=host"
echo "------------------------------------------------------------"
sudo docker run --rm \
  --network=host \
  -e KEY_VAULT_NAME="$KEY_VAULT_NAME" \
  -e APP_ENV=production \
  -v /tmp/test_kv.py:/test_kv.py:ro \
  python:3.11-slim \
  bash -c "pip install -q azure-identity azure-keyvault-secrets && python /test_kv.py"

TEST_A_RESULT=$?
echo ""

if [ $TEST_A_RESULT -eq 0 ]; then
    echo "✅ Test A PASSED: Key Vault works with --network=host"
    echo ""
    echo "Your deployment SHOULD work! Deploy with:"
    echo "  export KEY_VAULT_NAME=$KEY_VAULT_NAME"
    echo "  ./deploy.sh"
else
    echo "❌ Test A FAILED: Key Vault doesn't work with --network=host"
    echo ""
    
    # Test without host network
    echo "Test B: Running in Docker with bridge network"
    echo "------------------------------------------------------------"
    sudo docker run --rm \
      -e KEY_VAULT_NAME="$KEY_VAULT_NAME" \
      -e APP_ENV=production \
      -v /tmp/test_kv.py:/test_kv.py:ro \
      python:3.11-slim \
      bash -c "pip install -q azure-identity azure-keyvault-secrets && python /test_kv.py"
    
    TEST_B_RESULT=$?
    echo ""
    
    if [ $TEST_B_RESULT -eq 0 ]; then
        echo "✅ Test B PASSED: Key Vault works with bridge network"
        echo ""
        echo "Remove --network=host from deploy.sh and deploy"
    else
        echo "❌ Test B FAILED: Managed Identity not working in Docker"
        echo ""
        echo "Possible issues:"
        echo "1. VM doesn't have Managed Identity enabled"
        echo "2. Managed Identity doesn't have Key Vault permissions"
        echo "3. Docker container can't access Azure metadata endpoint"
        echo ""
        echo "Recommended: Use .env file instead of Key Vault"
        echo ""
        echo "Check Managed Identity status:"
        echo "  curl -H Metadata:true 'http://169.254.169.254/metadata/identity/oauth2/token?api-version=2018-02-01&resource=https://vault.azure.net'"
    fi
fi

# Cleanup
rm -f /tmp/test_kv.py

echo ""
echo "Test complete!"
