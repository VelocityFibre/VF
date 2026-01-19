#!/bin/bash
# QFieldCloud Periodic Alert Checker
# Run this via cron to check for critical faults and send alerts
# Recommended: */5 * * * * (every 5 minutes)

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ALERT_SCRIPT="$SCRIPT_DIR/alert.sh"

# Log output to file for debugging
LOG_FILE="$SCRIPT_DIR/../data/alert_check.log"

{
    echo "================================================"
    echo "Alert Check Started: $(date)"
    echo "================================================"

    if [ -f "$ALERT_SCRIPT" ]; then
        "$ALERT_SCRIPT"
    else
        echo "❌ Alert script not found: $ALERT_SCRIPT"
        exit 1
    fi

    echo "================================================"
    echo "Alert Check Completed: $(date)"
    echo "================================================"
    echo ""
} >> "$LOG_FILE" 2>&1

# Keep log file size manageable (last 1000 lines)
if [ -f "$LOG_FILE" ]; then
    tail -1000 "$LOG_FILE" > "$LOG_FILE.tmp" && mv "$LOG_FILE.tmp" "$LOG_FILE"
fi
