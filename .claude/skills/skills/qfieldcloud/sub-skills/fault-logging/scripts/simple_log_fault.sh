#!/bin/bash
# Simplified QFieldCloud Fault Logging

# Arguments
SEVERITY=${1:-"INFO"}
COMPONENT=${2:-"unknown"}
DESCRIPTION=${3:-"No description provided"}
REPORTER=${4:-"manual"}
USER=${5:-"$USER"}

# Data directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DATA_DIR="$SCRIPT_DIR/../data"
FAULT_LOG="$DATA_DIR/fault_log.json"

# Create data directory if it doesn't exist
mkdir -p "$DATA_DIR"

# Initialize fault log if it doesn't exist
if [ ! -f "$FAULT_LOG" ]; then
    echo "[]" > "$FAULT_LOG"
fi

# Generate timestamp
TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
EPOCH=$(date +%s)

# Create temp file for new fault
TEMP_FAULT="/tmp/fault_$EPOCH.json"

cat > "$TEMP_FAULT" << EOF
{
  "id": "$EPOCH",
  "timestamp": "$TIMESTAMP",
  "severity": "$SEVERITY",
  "component": "$COMPONENT",
  "description": "$DESCRIPTION",
  "reporter": "$REPORTER",
  "user": "$USER",
  "resolved": false
}
EOF

# Add to log using jq if available, otherwise use Python
if command -v jq &> /dev/null; then
    jq ". += [$(cat $TEMP_FAULT)]" "$FAULT_LOG" > "$FAULT_LOG.tmp" && mv "$FAULT_LOG.tmp" "$FAULT_LOG"
    echo "✅ Fault logged using jq"
else
    python3 -c "
import json
with open('$FAULT_LOG', 'r') as f: faults = json.load(f)
with open('$TEMP_FAULT', 'r') as f: new_fault = json.load(f)
faults.append(new_fault)
if len(faults) > 1000: faults = faults[-1000:]
with open('$FAULT_LOG', 'w') as f: json.dump(faults, f, indent=2)
"
    echo "✅ Fault logged using Python"
fi

rm -f "$TEMP_FAULT"

echo ""
echo "================================================"
echo "Fault Logged"
echo "================================================"
echo "Time:        $TIMESTAMP"
echo "Severity:    $SEVERITY"
echo "Component:   $COMPONENT"
echo "Description: $DESCRIPTION"
echo "Reporter:    $REPORTER"
echo "================================================"

# Alert if critical
if [ "$SEVERITY" = "CRITICAL" ]; then
    echo ""
    echo "🔴 CRITICAL FAULT - Immediate action required!"

    # Trigger alert
    ALERT_SCRIPT="$SCRIPT_DIR/alert.sh"
    if [ -f "$ALERT_SCRIPT" ]; then
        echo "📤 Triggering alert..."
        "$ALERT_SCRIPT" "$SEVERITY" "$COMPONENT" "$DESCRIPTION" "$TIMESTAMP" 2>&1 | grep -E "(✅|❌|⏭️)" || true
    fi
fi