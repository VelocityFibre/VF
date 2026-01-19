#!/bin/bash
# QFieldCloud Critical Fault Alerting
# Sends WhatsApp alerts for CRITICAL severity faults

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
FAULT_LOG="$SCRIPT_DIR/../data/fault_log.json"

# Alert configuration
ALERT_PHONE="+27711558396"  # WhatsApp number to alert
WHATSAPP_API="http://100.96.203.105:8081"  # WhatsApp sender on VF Server
COOLDOWN_MINUTES=30  # Don't spam - wait 30 min between alerts for same component

# Get last alert time for a component
get_last_alert_time() {
    local component=$1
    local alert_file="$SCRIPT_DIR/../data/last_alert_${component}.txt"

    if [ -f "$alert_file" ]; then
        cat "$alert_file"
    else
        echo "0"
    fi
}

# Record alert time
record_alert_time() {
    local component=$1
    local alert_file="$SCRIPT_DIR/../data/last_alert_${component}.txt"
    date +%s > "$alert_file"
}

# Check if cooldown period has passed
check_cooldown() {
    local component=$1
    local last_alert=$(get_last_alert_time "$component")
    local now=$(date +%s)
    local diff=$((now - last_alert))
    local cooldown_seconds=$((COOLDOWN_MINUTES * 60))

    if [ $diff -lt $cooldown_seconds ]; then
        echo "⏳ Cooldown active for $component ($(($cooldown_seconds - $diff))s remaining)"
        return 1
    fi
    return 0
}

# Send WhatsApp alert
send_alert() {
    local severity=$1
    local component=$2
    local description=$3
    local timestamp=$4

    # Format message
    local message="🚨 *QFieldCloud Alert*

*Severity:* $severity
*Component:* $component
*Time:* $timestamp

*Issue:*
$description

Check status:
https://qfield.fibreflow.app

View faults:
\`cd ~/.claude/skills/qfieldcloud/sub-skills/fault-logging/scripts && ./recent_faults.sh\`"

    echo "📤 Sending WhatsApp alert..."

    # Send via WhatsApp API
    curl -s -X POST "$WHATSAPP_API/send" \
        -H "Content-Type: application/json" \
        -d "{
            \"phone\": \"$ALERT_PHONE\",
            \"message\": $(echo "$message" | jq -Rs .)
        }" > /dev/null 2>&1

    if [ $? -eq 0 ]; then
        echo "✅ Alert sent to $ALERT_PHONE"
        record_alert_time "$component"
        return 0
    else
        echo "❌ Failed to send alert"
        return 1
    fi
}

# Main alerting logic
main() {
    if [ ! -f "$FAULT_LOG" ]; then
        echo "No fault log found. Nothing to alert."
        exit 0
    fi

    # Find recent CRITICAL faults (last 5 minutes)
    FIVE_MIN_AGO=$(date -d '5 minutes ago' -u '+%Y-%m-%dT%H:%M:%S' 2>/dev/null || date -u -v-5M '+%Y-%m-%dT%H:%M:%S')

    # Extract recent critical faults using Python
    python3 << 'PYTHON_END'
import json
import sys
from datetime import datetime, timedelta

fault_log = '$FAULT_LOG'
with open(fault_log, 'r') as f:
    faults = json.load(f)

# Find CRITICAL faults from last 5 minutes
five_min_ago = datetime.utcnow() - timedelta(minutes=5)
recent_critical = []

for fault in faults:
    if fault['severity'] == 'CRITICAL':
        fault_time = datetime.fromisoformat(fault['timestamp'].replace('Z', '+00:00'))
        if fault_time > five_min_ago:
            recent_critical.append(fault)

# Output for shell processing
for fault in recent_critical:
    print(f"{fault['component']}|{fault['description']}|{fault['timestamp']}")
PYTHON_END

    # Process each critical fault
    local alert_sent=false
    while IFS='|' read -r component description timestamp; do
        if [ -n "$component" ]; then
            echo "Found CRITICAL fault: $component"

            # Check cooldown
            if check_cooldown "$component"; then
                send_alert "CRITICAL" "$component" "$description" "$timestamp"
                alert_sent=true
            else
                echo "⏭️  Skipping (cooldown active)"
            fi
        fi
    done < <(python3 << 'PYTHON_END'
import json
from datetime import datetime, timedelta

fault_log = '$FAULT_LOG'
with open(fault_log, 'r') as f:
    faults = json.load(f)

five_min_ago = datetime.utcnow() - timedelta(minutes=5)
recent_critical = []

for fault in faults:
    if fault['severity'] == 'CRITICAL':
        fault_time = datetime.fromisoformat(fault['timestamp'].replace('Z', '+00:00'))
        if fault_time > five_min_ago:
            recent_critical.append(fault)

for fault in recent_critical:
    print(f"{fault['component']}|{fault['description']}|{fault['timestamp']}")
PYTHON_END
)

    if [ "$alert_sent" = false ]; then
        echo "✅ No new critical faults to alert"
    fi
}

# Check if called with specific fault details (for immediate alert)
if [ $# -ge 3 ]; then
    SEVERITY=$1
    COMPONENT=$2
    DESCRIPTION=$3
    TIMESTAMP=${4:-$(date -u '+%Y-%m-%dT%H:%M:%SZ')}

    if [ "$SEVERITY" = "CRITICAL" ]; then
        if check_cooldown "$COMPONENT"; then
            send_alert "$SEVERITY" "$COMPONENT" "$DESCRIPTION" "$TIMESTAMP"
        else
            echo "⏭️  Alert cooldown active for $COMPONENT"
        fi
    else
        echo "⚠️  Only CRITICAL severity triggers immediate alerts"
    fi
else
    # Scan for recent critical faults
    main
fi
