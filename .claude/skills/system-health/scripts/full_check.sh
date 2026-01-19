#!/bin/bash
# Complete health check: Infrastructure + Claude Code behavior

echo "╔════════════════════════════════════════════╗"
echo "║   FIBREFLOW HEALTH & BEHAVIOR REPORT      ║"
echo "╚════════════════════════════════════════════╝"
echo ""

# Part 1: Infrastructure
echo "━━━ INFRASTRUCTURE ━━━"
echo ""
./.claude/skills/system-health/scripts/quick_check.sh | tail -n +2 | head -n -1
echo ""

# Part 2: Claude Code Behavior
echo "━━━ CLAUDE CODE BEHAVIOR ━━━"
echo ""
./.claude/skills/system-health/scripts/check_claude_behavior.sh | tail -n +2 | head -n -1
echo ""

# Summary
echo "━━━ SUMMARY ━━━"
echo ""

# Count issues
INFRA_DOWN=$(. ./.claude/skills/system-health/scripts/quick_check.sh 2>/dev/null | grep -c "❌" || echo 0)
BEHAVIOR_LOOPS=$(. ./.claude/skills/system-health/scripts/check_claude_behavior.sh 2>/dev/null | grep -c "⚠️" || echo 0)

if [ "$INFRA_DOWN" -gt 0 ] || [ "$BEHAVIOR_LOOPS" -gt 0 ]; then
    echo "⚠️  ISSUES DETECTED:"
    [ "$INFRA_DOWN" -gt 0 ] && echo "  • $INFRA_DOWN service(s) down"
    [ "$BEHAVIOR_LOOPS" -gt 0 ] && echo "  • $BEHAVIOR_LOOPS behavioral pattern(s) detected"
else
    echo "✅ ALL SYSTEMS NORMAL"
fi

echo ""
echo "Report generated: $(date '+%Y-%m-%d %H:%M:%S')"
