#!/bin/bash

# QFieldCloud CSRF Fix Script
# Run this on a machine that has SSH access to the VF Server

echo "==========================================="
echo "QFieldCloud CSRF Fix Script"
echo "==========================================="
echo ""
echo "This script will fix the CSRF error for https://qfield.fibreflow.app"
echo ""

# Server details
SERVER="100.96.203.105"
USER="velo"

echo "Connecting to VF Server ($USER@$SERVER)..."
echo "You will be prompted for the password (2025)"
echo ""

# Create the CSRF fix file locally first
cat > /tmp/csrf_local_settings.py << 'EOF'
# QFieldCloud CSRF Fix - Applied $(date)
# This fixes the 403 Forbidden CSRF verification failed error

print("Loading CSRF fix for qfield.fibreflow.app...")

CSRF_TRUSTED_ORIGINS = [
    'https://qfield.fibreflow.app',
    'https://srv1083126.hstgr.cloud',
    'http://localhost:8082',
    'http://100.96.203.105:8082'
]

print(f"CSRF_TRUSTED_ORIGINS set to: {CSRF_TRUSTED_ORIGINS}")
print("Local settings loaded successfully")
EOF

# SSH command to apply the fix
ssh $USER@$SERVER << 'SSHEOF'

echo "Connected to VF Server"
cd /opt/qfieldcloud

echo ""
echo "Creating CSRF fix file..."

# Create the local settings file on the server
cat > /tmp/local_settings.py << 'PYEOF'
# QFieldCloud CSRF Fix
print("Loading CSRF fix for qfield.fibreflow.app...")

CSRF_TRUSTED_ORIGINS = [
    'https://qfield.fibreflow.app',
    'https://srv1083126.hstgr.cloud',
    'http://localhost:8082',
    'http://100.96.203.105:8082'
]

print(f"CSRF_TRUSTED_ORIGINS set to: {CSRF_TRUSTED_ORIGINS}")
print("Local settings loaded successfully")
PYEOF

echo "Copying fix into Docker container..."
sudo docker cp /tmp/local_settings.py qfieldcloud-app-1:/usr/src/app/qfieldcloud/local_settings.py

echo ""
echo "Restarting app container..."
sudo docker-compose restart app

echo ""
echo "Waiting for container to restart (30 seconds)..."
sleep 30

echo ""
echo "Verifying the fix..."
sudo docker-compose exec -T app python -c "
try:
    from qfieldcloud.local_settings import CSRF_TRUSTED_ORIGINS
    print('✓ CSRF fix loaded successfully!')
    print(f'  Trusted origins: {CSRF_TRUSTED_ORIGINS}')
except Exception as e:
    print(f'✗ Error loading CSRF fix: {e}')
"

echo ""
echo "==========================================="
echo "CSRF FIX COMPLETED!"
echo "==========================================="
echo ""
echo "Tell Juan to:"
echo "1. Clear browser cache (Ctrl+Shift+Delete)"
echo "2. Try accessing https://qfield.fibreflow.app again"
echo "3. The web interface should now work without CSRF errors"
echo ""

SSHEOF

echo "Script completed!"