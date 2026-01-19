---
name: agent-analyzer
version: 1.0.0
description: Detect agent loops, retries, and stuck operations automatically
keywords: [monitor, debug, loops, stuck, retry, analysis, behavior]
created: 2025-12-19
author: Claude
requires_confirmation: false
---

# Agent Behavior Analyzer

Automatically detects problematic agent behavior patterns including loops, retries, stuck operations, and inefficient command sequences.

## Capabilities

- **Loop Detection**: Identifies when agents are stuck in repetitive command loops
- **Retry Pattern Analysis**: Spots failed operations being retried repeatedly
- **Stuck Operation Detection**: Finds agents that aren't making progress
- **Performance Analysis**: Measures command frequency and efficiency
- **Real-time Alerts**: Notifies when problems are detected
- **Pattern Recognition**: Learns common failure patterns

## Usage

```bash
# Analyze current agent behavior
.claude/skills/agent-analyzer/scripts/analyze.py

# Monitor in real-time
.claude/skills/agent-analyzer/scripts/analyze.py --monitor

# Check specific time window
.claude/skills/agent-analyzer/scripts/analyze.py --last 10m

# Get detailed report
.claude/skills/agent-analyzer/scripts/analyze.py --verbose
```

## Detection Patterns

### Loop Detection
- Same command repeated 3+ times within 30 seconds
- Commands with identical parameters cycling
- Rapid command execution (>50/minute)

### Retry Detection
- Failed commands followed by identical attempts
- Pattern of: attempt → error → retry → error
- Escalating retry intervals

### Stuck Detection
- No progress indicators changing
- Same operation type dominating (>80%)
- High manual review rate (>50%)

## Alerts

The analyzer will alert on:
- **Critical**: Infinite loops (>100 commands/minute)
- **Warning**: Retry patterns (3+ failures)
- **Info**: Unusual behavior patterns

## Integration

Works with the Auto-Approval Monitor dashboard to provide:
- Real-time problem detection
- Historical pattern analysis
- Automated intervention suggestions

## Files

- `scripts/analyze.py` - Main analyzer
- `scripts/patterns.json` - Problem pattern definitions
- `scripts/monitor.py` - Real-time monitoring daemon