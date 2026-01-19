#!/bin/bash
# QFieldCloud Worker Restart

echo "================================================"
echo "Restarting QFieldCloud Workers"
echo "================================================"

cd /opt/qfieldcloud

# Check if QGIS image exists first
if ! docker images | grep -q "qfieldcloud-qgis.*latest"; then
    echo "⚠️  WARNING: QGIS image missing!"
    echo "Workers will fail without it. Fix first with:"
    echo "  cd ../qgis-image/scripts && ./restore.sh"
    echo ""
    read -p "Continue anyway? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Aborted."
        exit 1
    fi
fi

echo "Stopping workers..."
docker-compose stop worker_wrapper

echo "Starting workers..."
docker-compose up -d --scale worker_wrapper=8 worker_wrapper

echo "Waiting for workers to start (30 seconds)..."
sleep 30

# Verify workers are running
WORKER_COUNT=$(docker ps | grep -c "worker_wrapper.*Up")

if [ "$WORKER_COUNT" -eq 8 ]; then
    echo ""
    echo "✅ SUCCESS: All 8 workers restarted"
    echo ""
    echo "Worker Status:"
    docker ps --format "table {{.Names}}\t{{.Status}}" | grep worker_wrapper | sort
elif [ "$WORKER_COUNT" -gt 0 ]; then
    echo ""
    echo "⚠️  WARNING: Only $WORKER_COUNT/8 workers started"
    echo ""
    echo "Check logs with: ./logs.sh"
else
    echo ""
    echo "❌ CRITICAL: Workers failed to start!"
    echo ""
    echo "Troubleshooting:"
    echo "1. Check QGIS image: ../qgis-image/scripts/check.sh"
    echo "2. Check logs: docker-compose logs worker_wrapper"
    echo "3. Check resources: docker system df"
fi