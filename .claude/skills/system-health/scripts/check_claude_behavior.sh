#!/bin/bash
# Monitor Claude Code's own behavior for loops and problems

echo "=== CLAUDE CODE BEHAVIOR CHECK ==="
echo ""

# Check if monitoring log exists
if [ ! -f "logs/agent-commands.jsonl" ]; then
    echo "ℹ️  No command history found (monitoring not active)"
    exit 0
fi

# Count recent commands (last 5 minutes)
RECENT_COUNT=$(wc -l < logs/agent-commands.jsonl 2>/dev/null || echo 0)
echo "Recent commands logged: $RECENT_COUNT"
echo ""

# Check for repetitive patterns
echo "🔍 Checking for patterns..."

# Get last 20 commands
if [ "$RECENT_COUNT" -gt 0 ]; then
    tail -20 logs/agent-commands.jsonl 2>/dev/null | while read line; do
        CMD=$(echo "$line" | python3 -c "import sys, json; print(json.load(sys.stdin).get('command', '')[:60])" 2>/dev/null || echo "")
        STATUS=$(echo "$line" | python3 -c "import sys, json; print(json.load(sys.stdin).get('status', 'unknown'))" 2>/dev/null || echo "")

        if [ -n "$CMD" ]; then
            echo "  $STATUS | $CMD"
        fi
    done | tail -10

    echo ""

    # Detect simple loops (same command multiple times)
    LOOP_CHECK=$(tail -20 logs/agent-commands.jsonl 2>/dev/null | \
        python3 -c "
import sys, json
from collections import Counter

commands = []
for line in sys.stdin:
    try:
        entry = json.loads(line)
        cmd = entry.get('command', '')[:60]
        if cmd and 'cpuUsage' not in cmd:  # Skip IDE noise
            commands.append(cmd)
    except:
        pass

if len(commands) >= 3:
    counts = Counter(commands)
    for cmd, count in counts.most_common(3):
        if count >= 3:
            print(f'⚠️  Loop detected: \"{cmd}\" repeated {count} times')
" 2>/dev/null)

    if [ -n "$LOOP_CHECK" ]; then
        echo "$LOOP_CHECK"
    else
        echo "✅ No loops detected"
    fi

    # Check for blocked commands
    BLOCKED=$(tail -20 logs/agent-commands.jsonl 2>/dev/null | \
        grep -c '"status": "blocked"' 2>/dev/null || echo 0)

    if [ "$BLOCKED" -gt 0 ]; then
        echo "🚫 $BLOCKED blocked commands in recent activity"
    fi

else
    echo "✅ No activity to analyze"
fi

echo ""
echo "=== END OF CHECK ==="
