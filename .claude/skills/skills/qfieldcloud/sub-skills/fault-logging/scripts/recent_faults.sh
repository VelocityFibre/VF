#!/bin/bash
# QFieldCloud Recent Faults Viewer

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
FAULT_LOG="$SCRIPT_DIR/../data/fault_log.json"
LIMIT=${1:-10}  # Show last 10 by default

if [ ! -f "$FAULT_LOG" ]; then
    echo "No fault log found. No faults have been logged yet."
    exit 1
fi

echo "================================================"
echo "Recent QFieldCloud Faults (Last $LIMIT)"
echo "================================================"
echo ""

python3 -c "
import json
from datetime import datetime

with open('$FAULT_LOG', 'r') as f:
    faults = json.load(f)

if not faults:
    print('No faults logged yet')
    exit()

# Get last N faults
recent = faults[-$LIMIT:] if len(faults) > $LIMIT else faults

# Display in reverse order (newest first)
for i, fault in enumerate(reversed(recent), 1):
    severity_icon = {
        'CRITICAL': '🔴',
        'MAJOR': '🟡',
        'MINOR': '🔵',
        'INFO': '⚪'
    }.get(fault['severity'], '⚫')

    print(f'{i}. {fault[\"timestamp\"]}')
    print(f'   {severity_icon} {fault[\"severity\"]:8s} | {fault[\"component\"]:12s} | {fault.get(\"reporter\", \"unknown\")}')
    print(f'   {fault[\"description\"][:80]}')

    if fault.get('resolution'):
        print(f'   💡 {fault[\"resolution\"][:70]}')

    if fault.get('resolved'):
        print(f'   ✅ Resolved')
    else:
        # Calculate age
        try:
            fault_time = datetime.strptime(fault['timestamp'], '%Y-%m-%dT%H:%M:%SZ')
            age = datetime.now() - fault_time
            if age.days > 0:
                print(f'   ⏱️  {age.days} days old')
            else:
                hours = age.seconds // 3600
                print(f'   ⏱️  {hours} hours old')
        except:
            pass

    # Show context if critical
    if fault['severity'] == 'CRITICAL' and fault.get('context'):
        ctx = fault['context']
        print(f'   Context: Workers {ctx.get(\"workers_running\", \"?\")}/8, QGIS: {ctx.get(\"qgis_image_present\", \"?\")}')

    print('')

print(f'Total faults in log: {len(faults)}')
"

echo ""
echo "Commands:"
echo "• Search faults:  ./search_faults.sh <keyword>"
echo "• Analyze trends: ./analyze_faults.sh"
echo "• Log new fault:  ./log_fault.sh <severity> <component> <description>"