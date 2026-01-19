#!/bin/bash
# QFieldCloud Fault Logging

# Arguments
SEVERITY=${1:-"INFO"}  # CRITICAL, MAJOR, MINOR, INFO
COMPONENT=${2:-"unknown"}  # qgis-image, workers, csrf, database, etc.
DESCRIPTION=${3:-"No description provided"}

# Additional context
REPORTER=${4:-"manual"}  # manual, monitoring, user
USER=${5:-"$USER"}

# Data directory (relative to script location)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DATA_DIR="$SCRIPT_DIR/../data"
FAULT_LOG="$DATA_DIR/fault_log.json"
FAULT_BACKUP="$DATA_DIR/fault_log.backup.json"

# Create data directory if it doesn't exist
mkdir -p "$DATA_DIR"

# Initialize fault log if it doesn't exist
if [ ! -f "$FAULT_LOG" ]; then
    echo "[]" > "$FAULT_LOG"
fi

# Backup existing log
cp "$FAULT_LOG" "$FAULT_BACKUP" 2>/dev/null

# Generate timestamp
TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
EPOCH=$(date +%s)

# Detect environment info
HOSTNAME=$(hostname)

# Check QFieldCloud status for context
cd /opt/qfieldcloud 2>/dev/null
WORKERS=$(docker ps 2>/dev/null | grep -c "worker_wrapper.*Up" 2>/dev/null || echo "0")
QGIS_IMAGE=$(docker images 2>/dev/null | grep -c "qfieldcloud-qgis.*latest" 2>/dev/null || echo "0")

# Auto-detect resolution if it's a known issue
RESOLUTION=""
case "$DESCRIPTION" in
    *"QGIS"*|*"qgis"*|*"image missing"*)
        RESOLUTION="Run: cd ../qgis-image/scripts && ./restore.sh"
        ;;
    *"CSRF"*|*"403"*)
        RESOLUTION="Run: cd ../csrf-fix/scripts && ./apply_fix.sh"
        ;;
    *"workers"*|*"worker"*)
        RESOLUTION="Run: cd ../worker-ops/scripts && ./restart.sh"
        ;;
esac

# Create fault entry
FAULT_ENTRY=$(cat <<EOF
{
  "id": "$EPOCH",
  "timestamp": "$TIMESTAMP",
  "severity": "$SEVERITY",
  "component": "$COMPONENT",
  "description": "$DESCRIPTION",
  "resolution": "$RESOLUTION",
  "reporter": "$REPORTER",
  "user": "$USER",
  "hostname": "$HOSTNAME",
  "context": {
    "workers_running": "$WORKERS",
    "qgis_image_present": "$QGIS_IMAGE"
  },
  "resolved": false,
  "resolution_time": null
}
EOF
)

# Add to fault log using Python for proper JSON handling
python3 << PYTHON_END
import json
import sys

# Read existing log
fault_log = '$FAULT_LOG'
with open(fault_log, 'r') as f:
    faults = json.load(f)

# Add new fault
new_fault = {
    "id": "$EPOCH",
    "timestamp": "$TIMESTAMP",
    "severity": "$SEVERITY",
    "component": "$COMPONENT",
    "description": "$DESCRIPTION",
    "resolution": "$RESOLUTION",
    "reporter": "$REPORTER",
    "user": "$USER",
    "hostname": "$HOSTNAME",
    "context": {
        "workers_running": "$WORKERS",
        "qgis_image_present": "$QGIS_IMAGE"
    },
    "resolved": False,
    "resolution_time": None
}
faults.append(new_fault)

# Keep only last 1000 faults
if len(faults) > 1000:
    faults = faults[-1000:]

# Write back
with open(fault_log, 'w') as f:
    json.dump(faults, f, indent=2)

print(f'✅ Fault logged: {new_fault["severity"]} - {new_fault["component"]} - {new_fault["description"][:50]}...')
PYTHON_END

# Display fault details
echo ""
echo "================================================"
echo "Fault Logged"
echo "================================================"
echo "Time:        $TIMESTAMP"
echo "Severity:    $SEVERITY"
echo "Component:   $COMPONENT"
echo "Description: $DESCRIPTION"

if [ -n "$RESOLUTION" ]; then
    echo "Suggested:   $RESOLUTION"
fi

echo "Context:     Workers: $WORKERS/8, QGIS: $([ "$QGIS_IMAGE" = "1" ] && echo "✓" || echo "✗")"
echo "================================================"

# Check for patterns
SIMILAR_COUNT=$(python3 -c "
import json
with open('$FAULT_LOG', 'r') as f:
    faults = json.load(f)

# Count similar faults in last 7 days
from datetime import datetime, timedelta
cutoff = datetime.now() - timedelta(days=7)

similar = 0
for fault in faults:
    try:
        fault_time = datetime.strptime(fault['timestamp'], '%Y-%m-%dT%H:%M:%SZ')
        if fault_time > cutoff and fault['component'] == '$COMPONENT':
            similar += 1
    except:
        pass

print(similar)
" 2>/dev/null || echo "0")

if [ "$SIMILAR_COUNT" -gt 3 ]; then
    echo ""
    echo "⚠️  WARNING: This is occurrence #$SIMILAR_COUNT of $COMPONENT issues in the last 7 days"
    echo "Consider investigating the root cause with: ./analyze_faults.sh"
fi

# Alert if critical
if [ "$SEVERITY" = "CRITICAL" ]; then
    echo ""
    echo "🔴 CRITICAL FAULT - Immediate action required!"

    # Could add alerting here (email, Slack, etc.)
fi

exit 0