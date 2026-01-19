#!/bin/bash
# QFieldCloud Quick Status - One-line summary

cd /opt/qfieldcloud 2>/dev/null || exit 1

# Quick checks
SERVICES=$(docker ps | grep -c "qfieldcloud.*Up")
WORKERS=$(docker ps | grep -c "worker_wrapper.*Up")
QGIS=$(docker images | grep -c "qfieldcloud-qgis.*latest")
WEB=$(curl -s -o /dev/null -w "%{http_code}" https://qfield.fibreflow.app 2>/dev/null)

# Determine status
if [ "$SERVICES" -ge 4 ] && [ "$WORKERS" -eq 8 ] && [ "$QGIS" -eq 1 ] && ([ "$WEB" = "200" ] || [ "$WEB" = "302" ]); then
    echo "🟢 QFieldCloud: HEALTHY | Services: $SERVICES | Workers: $WORKERS/8 | Web: $WEB | QGIS: ✓"
    exit 0
elif [ "$WORKERS" -eq 0 ] || [ "$QGIS" -eq 0 ] || [ "$SERVICES" -lt 3 ]; then
    echo "🔴 QFieldCloud: CRITICAL | Services: $SERVICES | Workers: $WORKERS/8 | Web: $WEB | QGIS: $([ $QGIS -eq 1 ] && echo '✓' || echo '✗')"
    exit 2
else
    echo "🟡 QFieldCloud: WARNING | Services: $SERVICES | Workers: $WORKERS/8 | Web: $WEB | QGIS: $([ $QGIS -eq 1 ] && echo '✓' || echo '✗')"
    exit 1
fi