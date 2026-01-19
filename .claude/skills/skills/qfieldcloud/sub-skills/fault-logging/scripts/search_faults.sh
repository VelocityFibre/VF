#!/bin/bash
# QFieldCloud Fault Search

KEYWORD=${1:-""}
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
FAULT_LOG="$SCRIPT_DIR/../data/fault_log.json"

if [ ! -f "$FAULT_LOG" ]; then
    echo "No fault log found. No faults have been logged yet."
    exit 1
fi

if [ -z "$KEYWORD" ]; then
    echo "Usage: $0 <keyword>"
    echo "Example: $0 qgis"
    echo ""
    echo "Available components to search:"
    echo "  qgis-image, workers, csrf, database, storage, web, resources"
    exit 1
fi

echo "================================================"
echo "Searching Faults for: $KEYWORD"
echo "================================================"
echo ""

# Search and display results
python3 -c "
import json
from datetime import datetime

with open('$FAULT_LOG', 'r') as f:
    faults = json.load(f)

keyword = '$KEYWORD'.lower()
matches = []

for fault in faults:
    if (keyword in fault.get('description', '').lower() or
        keyword in fault.get('component', '').lower() or
        keyword in fault.get('severity', '').lower()):
        matches.append(fault)

if not matches:
    print('No faults found matching \"$KEYWORD\"')
else:
    print(f'Found {len(matches)} fault(s) matching \"$KEYWORD\":')
    print('')

    # Sort by timestamp (most recent first)
    matches.sort(key=lambda x: x['timestamp'], reverse=True)

    # Display each match
    for i, fault in enumerate(matches[:20], 1):  # Show max 20 results
        severity_icon = {
            'CRITICAL': '🔴',
            'MAJOR': '🟡',
            'MINOR': '🔵',
            'INFO': '⚪'
        }.get(fault['severity'], '⚫')

        print(f'{i}. {fault[\"timestamp\"]}')
        print(f'   {severity_icon} {fault[\"severity\"]} - {fault[\"component\"]}')
        print(f'   {fault[\"description\"][:100]}')

        if fault.get('resolution'):
            print(f'   Fix: {fault[\"resolution\"][:80]}')

        if fault.get('resolved'):
            print(f'   ✅ Resolved at {fault.get(\"resolution_time\", \"unknown\")}')

        print('')

    if len(matches) > 20:
        print(f'... and {len(matches) - 20} more matches')
"

echo ""
echo "================================================"
echo "Search Tips:"
echo "================================================"
echo "• Search by component: qgis-image, workers, csrf"
echo "• Search by severity: CRITICAL, MAJOR, MINOR"
echo "• Search by keyword: error, missing, failed"
echo ""
echo "For detailed analysis: ./analyze_faults.sh"