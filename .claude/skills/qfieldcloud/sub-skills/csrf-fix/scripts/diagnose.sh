#!/bin/bash
# QFieldCloud CSRF Diagnosis

echo "================================================"
echo "CSRF Configuration Check"
echo "================================================"

# Check if fix already applied
echo "1. Checking if CSRF fix is in settings.py..."
docker exec qfieldcloud-app-1 grep -q "CSRF Fix" /usr/src/app/qfieldcloud/settings.py 2>/dev/null

if [ $? -eq 0 ]; then
    echo "✅ CSRF fix found in settings.py"
else
    echo "❌ CSRF fix NOT in settings.py - needs fixing!"
fi

# Check environment
echo ""
echo "2. Checking environment variables..."
docker-compose exec -T app env | grep CSRF || echo "❌ No CSRF in environment"

# Check logs
echo ""
echo "3. Recent CSRF messages in logs..."
docker-compose logs --tail=50 app 2>/dev/null | grep -i csrf | tail -5 || echo "No CSRF messages"

# Test login page
echo ""
echo "4. Testing login page..."
curl -s -I https://qfield.fibreflow.app/admin/login/ | head -3

echo ""
echo "================================================"
echo "Diagnosis Complete"
echo "================================================"