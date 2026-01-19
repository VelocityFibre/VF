#!/bin/bash
# QFieldCloud Fault Pattern Analysis

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
FAULT_LOG="$SCRIPT_DIR/../data/fault_log.json"
DAYS=${1:-30}  # Default to 30 days

if [ ! -f "$FAULT_LOG" ]; then
    echo "No fault log found. No faults have been logged yet."
    exit 1
fi

echo "================================================"
echo "QFieldCloud Fault Analysis (Last $DAYS days)"
echo "================================================"
echo ""

python3 -c "
import json
from datetime import datetime, timedelta
from collections import Counter, defaultdict

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
    print('No faults found in the last $DAYS days')
    exit()

print(f'Analyzing {len(recent_faults)} fault(s) from the last $DAYS days\\n')

# 1. Severity Distribution
print('1. SEVERITY DISTRIBUTION')
print('------------------------')
severity_counts = Counter(f['severity'] for f in recent_faults)
total = sum(severity_counts.values())

for severity in ['CRITICAL', 'MAJOR', 'MINOR', 'INFO']:
    count = severity_counts.get(severity, 0)
    percent = (count / total * 100) if total > 0 else 0
    bar = '█' * int(percent / 2)
    icon = {'CRITICAL': '🔴', 'MAJOR': '🟡', 'MINOR': '🔵', 'INFO': '⚪'}.get(severity, '')
    print(f'{icon} {severity:8s} {count:3d} ({percent:5.1f}%) {bar}')

print()

# 2. Component Breakdown
print('2. COMPONENT BREAKDOWN')
print('----------------------')
component_counts = Counter(f['component'] for f in recent_faults)
for component, count in component_counts.most_common(10):
    print(f'• {component:15s} {count:3d} faults')

print()

# 3. Most Common Issues
print('3. TOP 5 RECURRING ISSUES')
print('-------------------------')
# Group similar descriptions
descriptions = [f['description'][:50] for f in recent_faults]
desc_counts = Counter(descriptions)
for desc, count in desc_counts.most_common(5):
    if count > 1:
        print(f'• ({count}x) {desc}...')

print()

# 4. Time Pattern Analysis
print('4. TEMPORAL PATTERNS')
print('-------------------')
# Group by hour of day
hour_counts = defaultdict(int)
day_counts = defaultdict(int)

for fault in recent_faults:
    try:
        fault_time = datetime.strptime(fault['timestamp'], '%Y-%m-%dT%H:%M:%SZ')
        hour_counts[fault_time.hour] += 1
        day_counts[fault_time.strftime('%Y-%m-%d')] += 1
    except:
        pass

# Find peak hours
if hour_counts:
    peak_hour = max(hour_counts, key=hour_counts.get)
    print(f'• Peak hour: {peak_hour:02d}:00 UTC ({hour_counts[peak_hour]} faults)')

# Find worst day
if day_counts:
    worst_day = max(day_counts, key=day_counts.get)
    print(f'• Worst day: {worst_day} ({day_counts[worst_day]} faults)')

# Calculate daily average
avg_per_day = len(recent_faults) / $DAYS if $DAYS > 0 else 0
print(f'• Average: {avg_per_day:.1f} faults/day')

print()

# 5. Resolution Status
print('5. RESOLUTION STATUS')
print('-------------------')
resolved = sum(1 for f in recent_faults if f.get('resolved'))
unresolved = len(recent_faults) - resolved
print(f'• Resolved:   {resolved:3d} ({resolved/len(recent_faults)*100:.0f}%)')
print(f'• Unresolved: {unresolved:3d} ({unresolved/len(recent_faults)*100:.0f}%)')

print()

# 6. Critical Insights
print('6. CRITICAL INSIGHTS')
print('-------------------')

# Most problematic component
if component_counts:
    worst_component = component_counts.most_common(1)[0]
    print(f'• Most problematic: {worst_component[0]} ({worst_component[1]} issues)')

# Check for escalating patterns
critical_recent = sum(1 for f in recent_faults[-10:] if f['severity'] == 'CRITICAL')
if critical_recent > 3:
    print(f'⚠️  WARNING: {critical_recent} CRITICAL faults in last 10 entries!')

# QGIS image issues
qgis_issues = sum(1 for f in recent_faults if 'qgis' in f['component'].lower())
if qgis_issues > len(recent_faults) * 0.3:
    print(f'⚠️  QGIS image accounts for {qgis_issues/len(recent_faults)*100:.0f}% of issues')
    print('   Consider permanent fix for Docker image persistence')

# Worker issues
worker_issues = sum(1 for f in recent_faults if 'worker' in f['component'].lower())
if worker_issues > len(recent_faults) * 0.25:
    print(f'⚠️  Worker issues account for {worker_issues/len(recent_faults)*100:.0f}% of problems')
    print('   Consider reviewing worker configuration')

print()

# 7. Recommendations
print('7. RECOMMENDATIONS')
print('-----------------')

if component_counts.most_common(1)[0][1] > 5:
    print(f'• Focus on fixing {component_counts.most_common(1)[0][0]} issues')

if severity_counts.get('CRITICAL', 0) > 3:
    print('• Multiple critical issues detected - review system stability')

if avg_per_day > 5:
    print('• High fault rate - consider preventive maintenance')

if qgis_issues > 2:
    print('• Implement Docker image persistence solution')
    print('  See: ../qgis-image/scripts/README.md')
"

echo ""
echo "================================================"
echo "Analysis Complete"
echo "================================================"
echo ""
echo "For detailed report: ./fault_report.sh $DAYS"
echo "To search specific issues: ./search_faults.sh <keyword>"