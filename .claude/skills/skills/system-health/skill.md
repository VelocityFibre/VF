---
name: system-health
version: 1.0.0
description: Autonomous health monitoring and self-healing for FibreFlow infrastructure
author: FibreFlow Team
tags: [monitoring, health-check, diagnostics, self-healing]
async: true
context_fork: true
hooks:
  pre_tool_use: "echo '[Health-Monitor] Starting health check at $(date)' >> /tmp/health_checks.log"
  post_tool_use: "echo '[Health-Monitor] Completed health check at $(date) - Status logged' >> /tmp/health_checks.log"
---

# System Health Monitor & Healer

Autonomous health monitoring and self-healing for FibreFlow infrastructure.

## What it does

Monitors VF Server, QField, services, and logs. Detects problems and suggests/applies fixes with user approval.

## When to use

- Daily health checks
- After deployments
- When something seems stuck
- Investigating issues
- Before important operations

## Capabilities

1. **Health Checks**
   - VF Server status and logs
   - QField worker status
   - Cloudflared tunnel status
   - Disk space and resource usage
   - Service availability

2. **Problem Detection**
   - Services not running
   - Error patterns in logs
   - Stuck processes
   - Disk space issues
   - Failed deployments

3. **Auto-Healing**
   - Restart stuck services (with approval)
   - Clear stuck queues
   - Free disk space
   - Fix common misconfigurations

4. **Reporting**
   - Clear status summaries
   - Problem prioritization
   - Suggested actions

## Example Usage

Just ask:
- "Check system health"
- "Is everything running okay?"
- "Why is VF server not responding?"
- "Fix the stuck QField worker"
- "Daily health report"

## Scripts

### Infrastructure Monitoring
- `quick_check.sh` - Check VF Server, QField, Cloudflared, disk

### Claude Code Behavior Monitoring
- `check_claude_behavior.sh` - Detect loops, retries, stuck patterns in my commands

### Complete Report
- `full_check.sh` - **Infrastructure + Behavior** (recommended!)

## Quick Usage

**Full health + behavior report:**
```bash
./.claude/skills/system-health/scripts/full_check.sh
```

**Or just ask me:**
- "Full health check"
- "Check everything"
- "System status report"

I'll automatically run the full check and interpret results for you!
