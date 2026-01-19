#!/bin/bash
# QFieldCloud VF Server Health Check
# Deploy to VF Server: ~/qfieldcloud/scripts/health_check.sh

echo "======================================="
echo "QFieldCloud Health Check - VF Server"
echo "$(date)"
echo "======================================="
echo ""

# Container Status
echo "=== Docker Containers (12 expected) ==="
cd ~/qfieldcloud/source
RUNNING_COUNT=$(docker ps | grep qfieldcloud | wc -l)

if [ "$RUNNING_COUNT" -eq 12 ]; then
    echo "✅ All containers running ($RUNNING_COUNT/12)"
else
    echo "⚠️  Some containers down ($RUNNING_COUNT/12)"
    docker-compose ps | grep -v "Up" | grep qfield
fi
echo ""

# Database Health
echo "=== Database Health ==="
DB_STATUS=$(docker exec qfieldcloud-db-1 psql -U qfieldcloud_db_admin qfieldcloud_db -c "SELECT 1;" 2>&1)
if echo "$DB_STATUS" | grep -q "1 row"; then
    echo "✅ Database responding"

    # Check record counts
    USER_COUNT=$(docker exec qfieldcloud-db-1 psql -U qfieldcloud_db_admin qfieldcloud_db -t -c "SELECT COUNT(*) FROM auth_user;" 2>/dev/null | tr -d " ")
    echo "   Users: $USER_COUNT"

    PROJECT_COUNT=$(docker exec qfieldcloud-db-1 psql -U qfieldcloud_db_admin qfieldcloud_db -t -c "SELECT COUNT(*) FROM qfieldcloud_project;" 2>/dev/null | tr -d " ")
    echo "   Projects: $PROJECT_COUNT"
else
    echo "❌ Database not responding"
fi
echo ""

# App Response Time
echo "=== Application Response ==="
APP_IP=$(docker inspect qfieldcloud-app-1 -f "{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}")
START_TIME=$(date +%s%N)
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" -H "Host: qfield.fibreflow.app" http://$APP_IP:8000/ 2>/dev/null)
END_TIME=$(date +%s%N)
RESPONSE_MS=$(( ($END_TIME - $START_TIME) / 1000000 ))

if [ "$HTTP_CODE" = "302" ] || [ "$HTTP_CODE" = "200" ]; then
    echo "✅ App responding (HTTP $HTTP_CODE)"
    echo "   Response time: ${RESPONSE_MS}ms"
    echo "   Container IP: $APP_IP"
else
    echo "❌ App not responding (HTTP $HTTP_CODE)"
fi
echo ""

# Cloudflare Tunnel
echo "=== Cloudflare Tunnel ==="
TUNNEL_COUNT=$(ps aux | grep -c "[c]loudflared")
if [ "$TUNNEL_COUNT" -gt 0 ]; then
    echo "✅ Tunnel running ($TUNNEL_COUNT processes)"

    # Check recent connections
    RECENT_ERRORS=$(tail -50 /tmp/cloudflared.log 2>/dev/null | grep -c "ERR")
    if [ "$RECENT_ERRORS" -eq 0 ]; then
        echo "   No recent errors"
    else
        echo "   ⚠️  $RECENT_ERRORS errors in last 50 log lines"
    fi
else
    echo "❌ Tunnel not running"
fi
echo ""

# Disk Space
echo "=== Disk Space ==="
DISK_USAGE=$(df -h /srv/data | tail -1 | awk '{print $5}' | sed 's/%//')
if [ "$DISK_USAGE" -lt 80 ]; then
    echo "✅ Disk space OK (${DISK_USAGE}% used)"
else
    echo "⚠️  Disk space high (${DISK_USAGE}% used)"
fi

# Docker volumes
DOCKER_USAGE=$(du -sh ~/qfieldcloud/source 2>/dev/null | awk '{print $1}')
echo "   QFieldCloud: $DOCKER_USAGE"
echo ""

# Memory Usage
echo "=== Memory Usage ==="
MEM_TOTAL=$(free -h | grep Mem | awk '{print $2}')
MEM_USED=$(free -h | grep Mem | awk '{print $3}')
MEM_PERCENT=$(free | grep Mem | awk '{printf("%.0f", $3/$2 * 100)}')

if [ "$MEM_PERCENT" -lt 80 ]; then
    echo "✅ Memory OK (${MEM_PERCENT}% used: $MEM_USED / $MEM_TOTAL)"
else
    echo "⚠️  Memory high (${MEM_PERCENT}% used: $MEM_USED / $MEM_TOTAL)"
fi
echo ""

# Recent Errors
echo "=== Recent Application Errors ==="
ERROR_COUNT=$(docker logs qfieldcloud-app-1 --since 1h 2>&1 | grep -i "error" | wc -l)
if [ "$ERROR_COUNT" -eq 0 ]; then
    echo "✅ No errors in last hour"
else
    echo "⚠️  $ERROR_COUNT errors in last hour"
    echo "   Check logs: docker logs qfieldcloud-app-1"
fi
echo ""

# Summary
echo "======================================="
echo "Overall Status:"
if [ "$RUNNING_COUNT" -eq 12 ] && [ "$HTTP_CODE" = "302" ] && [ "$TUNNEL_COUNT" -gt 0 ] && [ "$DISK_USAGE" -lt 80 ]; then
    echo "✅ ALL SYSTEMS OPERATIONAL"
else
    echo "⚠️  SOME ISSUES DETECTED - Review above"
fi
echo "======================================="
