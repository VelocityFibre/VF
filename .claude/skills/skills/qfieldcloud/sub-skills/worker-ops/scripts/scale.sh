#!/bin/bash
# QFieldCloud Worker Scaling

# Default to 8 workers if not specified
WORKERS=${1:-8}

echo "================================================"
echo "Scaling QFieldCloud Workers"
echo "================================================"

# Validate input
if ! [[ "$WORKERS" =~ ^[0-9]+$ ]]; then
    echo "❌ Error: Please provide a valid number"
    echo "Usage: ./scale.sh [number]"
    echo "Example: ./scale.sh 8"
    exit 1
fi

if [ "$WORKERS" -lt 1 ] || [ "$WORKERS" -gt 16 ]; then
    echo "❌ Error: Worker count must be between 1 and 16"
    echo "Recommended: 8 workers (current default)"
    exit 1
fi

cd /opt/qfieldcloud

echo "Current worker count: $(docker ps | grep -c 'worker_wrapper.*Up')"
echo "Scaling to: $WORKERS workers"
echo ""

# Warn about resource usage
if [ "$WORKERS" -gt 8 ]; then
    echo "⚠️  WARNING: More than 8 workers may cause high resource usage"
    read -p "Continue? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Aborted."
        exit 1
    fi
elif [ "$WORKERS" -lt 4 ]; then
    echo "⚠️  WARNING: Less than 4 workers may cause slow processing"
fi

echo "Scaling workers to $WORKERS..."
docker-compose up -d --scale worker_wrapper=$WORKERS worker_wrapper

echo "Waiting for workers to adjust (20 seconds)..."
sleep 20

# Verify scaling
NEW_COUNT=$(docker ps | grep -c "worker_wrapper.*Up")

if [ "$NEW_COUNT" -eq "$WORKERS" ]; then
    echo ""
    echo "✅ SUCCESS: Scaled to $WORKERS workers"
else
    echo ""
    echo "⚠️  WARNING: Expected $WORKERS workers, but $NEW_COUNT are running"
fi

echo ""
echo "Current workers:"
docker ps --format "table {{.Names}}\t{{.Status}}" | grep worker_wrapper | sort

echo ""
echo "Resource usage:"
docker stats --no-stream --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}" | grep worker_wrapper