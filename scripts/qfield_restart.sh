#!/bin/bash
# QFieldCloud Quick Restart Script
# Deploy to: ~/qfieldcloud/scripts/restart.sh

echo "🔄 Restarting QFieldCloud services..."
cd ~/qfieldcloud/source

# Restart all services
docker-compose restart

# Wait for services to stabilize
echo "⏳ Waiting 10 seconds for services to start..."
sleep 10

# Check status
echo ""
echo "=== Container Status ==="
docker-compose ps | grep qfield | head -15

echo ""
echo "=== Quick Health Check ==="

# App response
APP_IP=$(docker inspect qfieldcloud-app-1 -f "{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}")
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" -H "Host: qfield.fibreflow.app" http://$APP_IP:8000/ 2>/dev/null)

if [ "$HTTP_CODE" = "302" ]; then
    echo "✅ App responding (HTTP $HTTP_CODE)"
else
    echo "⚠️  App status: HTTP $HTTP_CODE"
fi

# Database
DB_TEST=$(docker exec qfieldcloud-db-1 psql -U qfieldcloud_db_admin qfieldcloud_db -c "SELECT 1;" 2>&1 | grep -c "1 row")
if [ "$DB_TEST" -eq 1 ]; then
    echo "✅ Database responding"
else
    echo "⚠️  Database not responding"
fi

echo ""
echo "✅ Restart complete"
echo "Run full health check: ~/qfieldcloud/scripts/health_check.sh"
