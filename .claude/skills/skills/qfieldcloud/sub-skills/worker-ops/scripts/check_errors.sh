#!/bin/bash
# QFieldCloud Worker Error Analysis

echo "================================================"
echo "QFieldCloud Worker Error Analysis"
echo "================================================"

cd /opt/qfieldcloud

# Check for critical errors
echo "Checking for critical issues..."
echo ""

# 1. QGIS Image Missing
echo "1. QGIS Image Errors:"
echo "----------------------------------------"
IMAGE_ERRORS=$(docker-compose logs --since=24h worker_wrapper 2>&1 | grep -c "ImageNotFound\|pull access denied\|No such image: qfieldcloud-qgis")

if [ "$IMAGE_ERRORS" -gt 0 ]; then
    echo "❌ CRITICAL: $IMAGE_ERRORS QGIS image errors in last 24h"
    echo "   Fix: ../qgis-image/scripts/restore.sh"

    # Show sample error
    echo ""
    echo "Sample error:"
    docker-compose logs --since=24h worker_wrapper 2>&1 | grep -m1 "ImageNotFound\|pull access denied"
else
    echo "✅ No QGIS image errors"
fi

echo ""
echo "2. Database Connection Errors:"
echo "----------------------------------------"
DB_ERRORS=$(docker-compose logs --since=24h worker_wrapper 2>&1 | grep -c "psycopg2\|could not connect\|connection refused")

if [ "$DB_ERRORS" -gt 0 ]; then
    echo "⚠️  WARNING: $DB_ERRORS database errors in last 24h"
    echo "   Check: docker-compose ps db"
else
    echo "✅ No database errors"
fi

echo ""
echo "3. Memory/Resource Errors:"
echo "----------------------------------------"
MEM_ERRORS=$(docker-compose logs --since=24h worker_wrapper 2>&1 | grep -c "MemoryError\|Cannot allocate memory\|No space left")

if [ "$MEM_ERRORS" -gt 0 ]; then
    echo "⚠️  WARNING: $MEM_ERRORS memory/disk errors in last 24h"
    echo "   Check: df -h && free -h"
else
    echo "✅ No resource errors"
fi

echo ""
echo "4. Recent Failed Jobs:"
echo "----------------------------------------"
# Show recent failures
docker-compose logs --since=1h worker_wrapper 2>&1 | \
    grep -E "Failed job run|ERROR|error_origin" | \
    tail -5 || echo "No recent failures"

echo ""
echo "5. Worker Health:"
echo "----------------------------------------"
RUNNING=$(docker ps | grep -c "worker_wrapper.*Up")
echo "Workers running: $RUNNING/8"

if [ "$RUNNING" -lt 8 ]; then
    echo "⚠️  Not all workers running. Run: ./restart.sh"
fi

# Check if workers are processing
RECENT_SUCCESS=$(docker-compose logs --since=10m worker_wrapper 2>&1 | grep -c "Finished execution with code 0")
if [ "$RECENT_SUCCESS" -gt 0 ]; then
    echo "✅ Workers actively processing ($RECENT_SUCCESS jobs in last 10 min)"
else
    echo "⚠️  No successful jobs in last 10 minutes"
fi

echo ""
echo "================================================"
echo "Recommendations:"
echo "================================================"

if [ "$IMAGE_ERRORS" -gt 0 ]; then
    echo "1. URGENT: Restore QGIS image with ../qgis-image/scripts/restore.sh"
fi

if [ "$RUNNING" -lt 8 ]; then
    echo "2. Restart workers with ./restart.sh"
fi

if [ "$DB_ERRORS" -gt 0 ]; then
    echo "3. Check database status: docker-compose ps db"
fi

if [ "$MEM_ERRORS" -gt 0 ]; then
    echo "4. Check server resources: df -h && free -h"
fi

echo ""
echo "For detailed logs run: ./logs.sh 100"