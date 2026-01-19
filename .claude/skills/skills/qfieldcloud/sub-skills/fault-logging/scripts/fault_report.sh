#!/bin/bash
# QFieldCloud Fault Report Generator

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
FAULT_LOG="$SCRIPT_DIR/../data/fault_log.json"
DAYS=${1:-7}  # Default to 7 days
OUTPUT_FILE=${2:-""}  # Optional output file

if [ ! -f "$FAULT_LOG" ]; then
    echo "No fault log found. No faults have been logged yet."
    exit 1
fi

REPORT=$(cat <<EOF
================================================
QFieldCloud Fault Report
Generated: $(date '+%Y-%m-%d %H:%M:%S')
Period: Last $DAYS days
================================================

$(python3 -c "
import json
from datetime import datetime, timedelta
from collections import Counter

with open('$FAULT_LOG', 'r') as f:
    faults = json.load(f)

# Filter by time window
cutoff = datetime.now() - timedelta(days=$DAYS)
recent_faults = []

for fault in faults:
    try:
        fault_time = datetime.strptime(fault['timestamp'], '%Y-%m-%dT%H:%M:%SZ')
        if fault_time > cutoff:
            recent_faults.append(fault)
    except:
        pass

if not recent_faults:
    print('No faults found in the specified period.')
    exit()

# Executive Summary
print('EXECUTIVE SUMMARY')
print('-----------------')
print(f'• Total Faults: {len(recent_faults)}')
print(f'• Period: {$DAYS} days')
print(f'• Daily Average: {len(recent_faults)/$DAYS:.1f} faults/day')

severity_counts = Counter(f['severity'] for f in recent_faults)
print(f'• Critical: {severity_counts.get(\"CRITICAL\", 0)}')
print(f'• Major: {severity_counts.get(\"MAJOR\", 0)}')
print(f'• Minor: {severity_counts.get(\"MINOR\", 0)}')
print(f'• Info: {severity_counts.get(\"INFO\", 0)}')

resolved = sum(1 for f in recent_faults if f.get('resolved'))
print(f'• Resolution Rate: {resolved}/{len(recent_faults)} ({resolved/len(recent_faults)*100:.0f}%)')
print()

# Critical Issues
critical = [f for f in recent_faults if f['severity'] == 'CRITICAL']
if critical:
    print('CRITICAL ISSUES REQUIRING ATTENTION')
    print('-----------------------------------')
    for fault in critical[:5]:  # Show max 5
        print(f'• {fault[\"timestamp\"][:10]} - {fault[\"component\"]}')
        print(f'  {fault[\"description\"][:70]}')
        if not fault.get('resolved'):
            print(f'  ⚠️  UNRESOLVED')
            if fault.get('resolution'):
                print(f'  Fix: {fault[\"resolution\"][:60]}')
        print()

# Component Analysis
print('COMPONENT RELIABILITY')
print('--------------------')
component_counts = Counter(f['component'] for f in recent_faults)
total_faults = len(recent_faults)

for component, count in component_counts.most_common():
    reliability = 100 - (count / $DAYS * 10)  # Rough reliability score
    reliability = max(0, min(100, reliability))  # Clamp to 0-100

    if reliability >= 90:
        status = '🟢'
    elif reliability >= 75:
        status = '🟡'
    else:
        status = '🔴'

    print(f'{status} {component:15s} {count:2d} issues ({reliability:.0f}% reliability)')
print()

# Recurring Patterns
print('RECURRING PATTERNS')
print('-----------------')
# Find patterns in descriptions
desc_patterns = {}
for fault in recent_faults:
    key_words = ['missing', 'failed', 'down', 'error', 'timeout', 'refused']
    for word in key_words:
        if word in fault['description'].lower():
            pattern = f'{fault[\"component\"]} {word}'
            desc_patterns[pattern] = desc_patterns.get(pattern, 0) + 1

for pattern, count in sorted(desc_patterns.items(), key=lambda x: x[1], reverse=True)[:5]:
    if count > 1:
        print(f'• {pattern}: {count} occurrences')
print()

# Time Analysis
print('TEMPORAL ANALYSIS')
print('----------------')
# Group by day
day_counts = {}
for fault in recent_faults:
    try:
        fault_time = datetime.strptime(fault['timestamp'], '%Y-%m-%dT%H:%M:%SZ')
        day = fault_time.strftime('%Y-%m-%d')
        day_counts[day] = day_counts.get(day, 0) + 1
    except:
        pass

if day_counts:
    worst_day = max(day_counts, key=day_counts.get)
    print(f'• Worst Day: {worst_day} ({day_counts[worst_day]} faults)')

    # Check for trending
    recent_days = sorted(day_counts.keys())[-3:]
    if len(recent_days) >= 3:
        recent_avg = sum(day_counts.get(d, 0) for d in recent_days) / 3
        overall_avg = len(recent_faults) / $DAYS
        if recent_avg > overall_avg * 1.5:
            print(f'⚠️  TREND: Fault rate increasing (recent: {recent_avg:.1f}/day, avg: {overall_avg:.1f}/day)')
        elif recent_avg < overall_avg * 0.5:
            print(f'✅ TREND: Fault rate decreasing (recent: {recent_avg:.1f}/day, avg: {overall_avg:.1f}/day)')
print()

# Recommendations
print('RECOMMENDATIONS')
print('--------------')

# Based on most common component
if component_counts:
    top_component = component_counts.most_common(1)[0]
    if top_component[0] == 'qgis-image' and top_component[1] > 2:
        print('1. QGIS Image Persistence')
        print('   • Problem: Docker image disappearing repeatedly')
        print('   • Solution: Implement registry storage or volume mount')
        print('   • Script: ../qgis-image/scripts/README.md')
        print()
    elif top_component[0] == 'workers' and top_component[1] > 3:
        print('1. Worker Stability')
        print('   • Problem: Frequent worker failures')
        print('   • Solution: Review worker configuration and resources')
        print('   • Script: ../worker-ops/scripts/scale.sh')
        print()
    elif top_component[0] == 'csrf' and top_component[1] > 2:
        print('1. CSRF Configuration')
        print('   • Problem: Recurring CSRF verification failures')
        print('   • Solution: Permanent fix in Django settings')
        print('   • Script: ../csrf-fix/scripts/apply_fix.sh')
        print()

# Based on severity
if severity_counts.get('CRITICAL', 0) > 3:
    print('2. System Stability')
    print('   • Multiple critical failures detected')
    print('   • Consider comprehensive system review')
    print('   • Run: ../monitoring/scripts/dependencies.sh')
    print()

# Based on resolution rate
if resolved < len(recent_faults) * 0.5:
    print('3. Issue Resolution')
    print('   • Low resolution rate ({:.0f}%)'.format(resolved/len(recent_faults)*100))
    print('   • Review unresolved issues and apply fixes')
    print('   • Run: ./search_faults.sh unresolved')
    print()

# Success metrics
print('SUCCESS METRICS')
print('--------------')
days_without_critical = 0
for i in range($DAYS):
    day = (datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d')
    day_faults = [f for f in recent_faults if f['timestamp'].startswith(day) and f['severity'] == 'CRITICAL']
    if not day_faults:
        days_without_critical += 1
    else:
        break

print(f'• Days without critical issues: {days_without_critical}')
print(f'• Mean time between failures: {($DAYS * 24) / (len(recent_faults) + 1):.1f} hours')

if severity_counts.get('INFO', 0) > severity_counts.get('CRITICAL', 0):
    print('• ✅ More informational than critical issues')
")

================================================
END OF REPORT
================================================
EOF
)

if [ -n "$OUTPUT_FILE" ]; then
    echo "$REPORT" > "$OUTPUT_FILE"
    echo "Report saved to: $OUTPUT_FILE"
else
    echo "$REPORT"
fi