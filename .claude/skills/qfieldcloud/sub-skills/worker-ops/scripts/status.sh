#!/bin/bash
# QFieldCloud Worker Status Check

echo "================================================"
echo "QFieldCloud Worker Status"
echo "================================================"

# Count running workers
WORKER_COUNT=$(docker ps | grep -c "worker_wrapper.*Up" 2>/dev/null)

echo "Workers running: $WORKER_COUNT / 8"
echo ""

if [ "$WORKER_COUNT" -eq 8 ]; then
    echo "✅ All workers operational"
elif [ "$WORKER_COUNT" -gt 0 ]; then
    echo "⚠️  Only $WORKER_COUNT workers running (expected 8)"
else
    echo "❌ CRITICAL: No workers running!"
fi

echo ""
echo "Worker Details:"
echo "----------------------------------------"

# Show worker status with uptime
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Image}}" | grep worker_wrapper | sort

echo ""
echo "Worker Resource Usage:"
echo "----------------------------------------"

# Show CPU and memory usage
docker stats --no-stream --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}" | grep worker_wrapper

echo ""
echo "QGIS Image Status:"
if docker images | grep -q "qfieldcloud-qgis.*latest"; then
    echo "✅ QGIS image present"
else
    echo "❌ QGIS image missing! Workers cannot process jobs"
    echo "   Run: ../qgis-image/scripts/restore.sh"
fi

echo ""
echo "Recent Worker Activity:"
echo "----------------------------------------"
# Show last successful job
docker-compose logs --tail=100 worker_wrapper 2>/dev/null | grep "Finished execution with code 0" | tail -1 || echo "No recent successful jobs"