# Agent Behavior Analyzer Skill

Automatically detects problematic agent behavior patterns including loops, retries, stuck operations, and inefficient command sequences.

## Quick Start

```bash
# Check for problems in last 10 minutes
.claude/skills/agent-analyzer/scripts/analyze.py --last 10m

# Real-time monitoring
.claude/skills/agent-analyzer/scripts/analyze.py --monitor

# Verbose output with details
.claude/skills/agent-analyzer/scripts/analyze.py --verbose
```

## What It Detects

### 🔄 **Loops**
- Same command repeated 3+ times within 30 seconds
- Example: Agent polling for something that isn't happening

### 🔁 **Retries**
- Failed operations being attempted repeatedly
- Example: Git push failing due to auth issues

### 📌 **Stuck Operations**
- One command category dominating (>80% of commands)
- Example: Agent searching for missing file

### ⚡ **Rapid Fire**
- More than 50 commands per minute
- Example: Tight polling loop

### 📊 **Inefficiency**
- High manual review rate (>50%)
- Example: Agent hitting unknown patterns

## Severity Levels

- **HIGH** (Red): Immediate attention needed (loops, rapid fire)
- **MEDIUM** (Yellow): Should be investigated (retries, stuck)
- **LOW** (Green): Optimization opportunity (inefficiency)

## Usage Examples

### Basic Check
```bash
# Quick check of recent activity
./venv/bin/python3 .claude/skills/agent-analyzer/scripts/analyze.py
```

Output:
```
Agent Behavior Analysis
Commands analyzed: 94
Problems found: 4

DETECTED PROBLEMS:
[HIGH] LOOP - Command repeated 5 times in 10 seconds
[MEDIUM] RETRY - Command retried 4 times with failures
```

### Real-Time Monitoring
```bash
# Monitor for problems as they happen
./venv/bin/python3 .claude/skills/agent-analyzer/scripts/analyze.py --monitor
```

The monitor will:
- Check every 10 seconds
- Alert on new problems
- Highlight HIGH severity issues
- Run until you press Ctrl+C

### Integration with Dashboard

Use together with the monitoring dashboard:

1. **Dashboard** (http://localhost:8002/monitor) - Visual overview
2. **Analyzer** - Automatic problem detection
3. **Combined** - Dashboard shows patterns, analyzer explains them

## Configuration

Edit `scripts/patterns.json` to customize:

```json
{
  "thresholds": {
    "loop_repetitions": 3,      // Commands to trigger loop detection
    "rapid_fire_rate": 50,      // Commands/minute threshold
    "stuck_dominance": 80,      // Category percentage threshold
    "high_manual_rate": 50      // Manual review percentage
  }
}
```

## Testing

```bash
# Run test suite with sample problems
./venv/bin/python3 .claude/skills/agent-analyzer/scripts/test_analyzer.py
```

This creates test data with all problem types and verifies detection.

## Files

- `skill.md` - Skill metadata for Claude Code discovery
- `scripts/analyze.py` - Main analyzer script
- `scripts/patterns.json` - Configurable thresholds and patterns
- `scripts/test_analyzer.py` - Test suite with sample problems
- `README.md` - This documentation

## How It Helps

Instead of manually watching the dashboard for problems, the analyzer:
- **Automatically detects** problematic patterns
- **Alerts immediately** when issues arise
- **Provides context** about what's wrong
- **Suggests solutions** based on pattern type

## Common Problems & Solutions

| Problem | Likely Cause | Solution |
|---------|-------------|----------|
| LOOP: Same command 5+ times | Waiting for condition | Check what agent expects |
| RETRY: Failed operations | Auth/permission issues | Fix credentials/access |
| STUCK: One category 80%+ | Missing resource | Provide missing file/service |
| RAPID_FIRE: 100+ cmd/min | Tight polling loop | Add delay or fix logic |
| INEFFICIENT: High manual rate | Unknown patterns | Update approval rules |

## Exit Codes

- `0` - No problems detected
- `1` - Problems found (check output)

Use in scripts:
```bash
if .claude/skills/agent-analyzer/scripts/analyze.py; then
    echo "All clear!"
else
    echo "Problems detected - check agent behavior"
fi
```