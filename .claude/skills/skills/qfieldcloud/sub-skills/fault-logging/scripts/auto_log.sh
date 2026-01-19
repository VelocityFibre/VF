#!/bin/bash
# QFieldCloud Auto Fault Logger
# Automatically detects and logs issues from system state

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_FAULT="$SCRIPT_DIR/log_fault.sh"

echo "================================================"
echo "QFieldCloud Auto Fault Detection"
echo "Started: $(date '+%Y-%m-%d %H:%M:%S')"
echo "================================================"
echo ""

cd /opt/qfieldcloud 2>/dev/null

ISSUES_FOUND=0

# 1. Check QGIS Image
if ! docker images | grep -q "qfieldcloud-qgis.*latest"; then
    echo "❌ QGIS image missing - logging fault"
    "$LOG_FAULT" "CRITICAL" "qgis-image" "QGIS Docker image missing - all projects will fail" "monitoring"
    ISSUES_FOUND=$((ISSUES_FOUND + 1))
fi

# 2. Check Workers
WORKER_COUNT=$(docker ps | grep -c "worker_wrapper.*Up" 2>/dev/null || echo 0)
if [ "$WORKER_COUNT" -eq 0 ]; then
    echo "❌ No workers running - logging fault"
    "$LOG_FAULT" "CRITICAL" "workers" "No workers running - processing halted" "monitoring"
    ISSUES_FOUND=$((ISSUES_FOUND + 1))
elif [ "$WORKER_COUNT" -lt 8 ]; then
    echo "⚠️  Only $WORKER_COUNT/8 workers - logging fault"
    "$LOG_FAULT" "MAJOR" "workers" "Only $WORKER_COUNT of 8 workers running" "monitoring"
    ISSUES_FOUND=$((ISSUES_FOUND + 1))
fi

# 3. Check Core Services
for service in app nginx db; do
    if ! docker ps --format "{{.Names}}" | grep -qE "^qfieldcloud-${service}(-[0-9]+)?$"; then
        echo "❌ $service is down - logging fault"
        "$LOG_FAULT" "CRITICAL" "$service" "$service container is not running" "monitoring"
        ISSUES_FOUND=$((ISSUES_FOUND + 1))
    fi
done

# 4. Check Web Interface
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" https://qfield.fibreflow.app 2>/dev/null)
if [ "$HTTP_CODE" = "403" ]; then
    echo "⚠️  CSRF errors detected - logging fault"
    "$LOG_FAULT" "MAJOR" "csrf" "Web interface returning 403 CSRF errors" "monitoring"
    ISSUES_FOUND=$((ISSUES_FOUND + 1))
elif [ "$HTTP_CODE" != "200" ] && [ "$HTTP_CODE" != "302" ]; then
    echo "❌ Web interface issue - logging fault"
    "$LOG_FAULT" "MAJOR" "web" "Web interface returning HTTP $HTTP_CODE" "monitoring"
    ISSUES_FOUND=$((ISSUES_FOUND + 1))
fi

# 5. Check Recent Errors in Logs
ERROR_COUNT=$(docker-compose logs --since=1h worker_wrapper 2>&1 | grep -c "ERROR\|ImageNotFound" 2>/dev/null || echo 0)
if [ "$ERROR_COUNT" -gt 20 ]; then
    echo "⚠️  High error rate ($ERROR_COUNT errors/hour) - logging fault"
    "$LOG_FAULT" "MAJOR" "workers" "High error rate: $ERROR_COUNT errors in last hour" "monitoring"
    ISSUES_FOUND=$((ISSUES_FOUND + 1))
fi

# 6. Check Disk Space
DISK_USAGE=$(df -h /opt/qfieldcloud 2>/dev/null | tail -1 | awk '{print $5}' | sed 's/%//' || echo 0)
if [ "$DISK_USAGE" -gt 90 ]; then
    echo "❌ Critical disk space - logging fault"
    "$LOG_FAULT" "CRITICAL" "resources" "Disk usage critical at $DISK_USAGE%" "monitoring"
    ISSUES_FOUND=$((ISSUES_FOUND + 1))
elif [ "$DISK_USAGE" -gt 80 ]; then
    echo "⚠️  High disk usage - logging fault"
    "$LOG_FAULT" "MAJOR" "resources" "Disk usage high at $DISK_USAGE%" "monitoring"
    ISSUES_FOUND=$((ISSUES_FOUND + 1))
fi

# 7. Check Database Connectivity
if ! docker exec qfieldcloud-db-1 pg_isready -U qfieldcloud_db_admin 2>/dev/null | grep -q "accepting"; then
    echo "❌ Database not responding - logging fault"
    "$LOG_FAULT" "CRITICAL" "database" "PostgreSQL not accepting connections" "monitoring"
    ISSUES_FOUND=$((ISSUES_FOUND + 1))
fi

# 8. Check MinIO Storage
if ! curl -s http://100.96.203.105:8010/minio/health/live 2>/dev/null | grep -q ""; then
    echo "⚠️  MinIO health check failed - logging fault"
    "$LOG_FAULT" "MAJOR" "storage" "MinIO storage health check failed" "monitoring"
    ISSUES_FOUND=$((ISSUES_FOUND + 1))
fi

echo ""
echo "================================================"
echo "Auto Fault Detection Complete"
echo "================================================"

if [ "$ISSUES_FOUND" -eq 0 ]; then
    echo "✅ No issues detected"
else
    echo "⚠️  $ISSUES_FOUND issue(s) detected and logged"
    echo ""
    echo "View recent faults with: ../recent_faults.sh"
    echo "Analyze patterns with: ../analyze_faults.sh"
fi

exit $ISSUES_FOUND