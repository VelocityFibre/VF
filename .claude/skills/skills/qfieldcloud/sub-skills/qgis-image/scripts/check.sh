#!/bin/bash
# QFieldCloud QGIS Image Check
# Returns 0 if image exists, 1 if missing

echo "Checking QGIS Docker image status..."

if docker images | grep -q "qfieldcloud-qgis.*latest"; then
    echo "✅ QGIS image exists:"
    docker images | grep qfieldcloud-qgis | head -1
    exit 0
else
    echo "❌ CRITICAL: QGIS image missing!"
    echo "Run restore.sh (30 sec) or rebuild.sh (5 min)"
    exit 1
fi