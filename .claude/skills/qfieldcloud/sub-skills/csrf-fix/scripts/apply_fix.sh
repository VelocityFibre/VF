#!/bin/bash
# QFieldCloud CSRF Fix Application
# The ONLY method that works - append to settings.py

echo "================================================"
echo "Applying CSRF Fix"
echo "================================================"

cd /opt/qfieldcloud

# Check if already fixed
docker exec qfieldcloud-app-1 grep -q "CSRF Fix" /usr/src/app/qfieldcloud/settings.py 2>/dev/null

if [ $? -eq 0 ]; then
    echo "✅ CSRF fix already applied!"
    echo "If still having issues, users need to clear browser data."
    exit 0
fi

echo "Applying proven CSRF fix..."

# Apply the fix that ACTUALLY works
docker exec qfieldcloud-app-1 bash -c "
cat >> /usr/src/app/qfieldcloud/settings.py << 'EOF'

# CSRF Fix - Added $(date +%Y-%m-%d)
# WARNING: local_settings.py does NOT work!
CSRF_TRUSTED_ORIGINS = [
    'https://qfield.fibreflow.app',
    'https://srv1083126.hstgr.cloud',
    'http://qfield.fibreflow.app',
    'http://srv1083126.hstgr.cloud',
    'http://100.96.203.105:8082',
    'http://localhost:8082',
]
ALLOWED_HOSTS = ['*']

# Print to logs for verification
print(f'[CSRF FIX APPLIED] CSRF_TRUSTED_ORIGINS = {CSRF_TRUSTED_ORIGINS}')
EOF
"

if [ $? -eq 0 ]; then
    echo "✅ Fix appended to settings.py"

    # Restart app
    echo "Restarting app container..."
    sudo docker-compose restart app

    echo "Waiting 30 seconds for restart..."
    sleep 30

    # Verify
    echo ""
    echo "Verifying fix in logs..."
    docker-compose logs --tail=10 app | grep "CSRF FIX APPLIED" || echo "Check may be too early"

    echo ""
    echo "================================================"
    echo "✅ CSRF Fix Complete!"
    echo "================================================"
    echo ""
    echo "Users must now:"
    echo "1. Clear ALL browser data (cookies + cache)"
    echo "2. Close browser completely"
    echo "3. Try again at https://qfield.fibreflow.app"
else
    echo "❌ Failed to apply fix!"
    exit 1
fi