# Monitor Usage Guide

## 🎯 How to Make the Monitor Actually Useful

The monitor dashboard is **already running** at http://localhost:8002/monitor

Here's how to use it effectively:

---

## Option 1: Quick Manual Logging (Easiest)

Log important operations as you do them:

```bash
# Before doing something important, log it:
.claude/hooks/auto-logger.py "About to deploy to production"

# Then do the operation:
./deploy.sh

# Log the result:
.claude/hooks/auto-logger.py "Deployment complete - checking status"
```

**When to use**: One-off important operations, debugging sessions

---

## Option 2: Wrapper for Critical Commands (Recommended)

Create a bash function in your current session:

```bash
# Add to ~/.bashrc or run in current session:
track() {
    .claude/hooks/auto-logger.py "$*"
    eval "$@"
}

# Now use it:
track git push origin main
track systemctl restart nginx
track ./scripts/deploy.sh
```

**When to use**: Regular workflow, repeated operations

---

## Option 3: Watch Specific Operations (Passive)

Let the dashboard show what's happening without manual intervention:

```bash
# Just keep the dashboard open in browser
# Run your normal commands
# Check dashboard periodically to see patterns

# Example workflow:
# 1. Open http://localhost:8002/monitor in browser
# 2. Work normally for 30 minutes
# 3. Check dashboard - did you see any loops or retries?
```

**When to use**: Background awareness, pattern detection

---

## Real-World Scenarios

### Scenario 1: Deployment Debugging

**Problem**: Agent keeps restarting services

```bash
# Keep dashboard open
# Run your deployment
./deploy.sh

# Check dashboard - does it show:
# - Multiple "systemctl restart" in short time? 🚨 LOOP
# - "Build" operations >80%? 🚨 STUCK
# - Same command failing 3+ times? 🚨 RETRY
```

**Action**: Dashboard alerts tell you WHAT to investigate

---

### Scenario 2: VF Server Operations Monitoring

**Problem**: Want to see if agent is stuck on VF server commands

```bash
# Log VF operations:
track VF_SERVER_PASSWORD="..." .claude/skills/vf-server/scripts/execute.py 'ps aux'

# Check dashboard:
# - If "VF Server" category >60% = Agent might be stuck
# - Multiple failed VF commands = Connection issues
```

---

### Scenario 3: Git Operations Tracking

**Problem**: Want audit trail of git pushes

```bash
# In .git/hooks/pre-push:
#!/bin/bash
/home/louisdup/Agents/claude/.claude/hooks/auto-logger.py "git push $*"

# Now EVERY git push is logged automatically
# Check dashboard for:
# - How many pushes today?
# - Any rapid-fire pushes (possible loop)?
```

---

## Dashboard Features You Can Use Now

### 1. Loop Detection
If same command runs 3+ times in 30 seconds → 🚨 Alert

**Example**:
```
systemctl restart nginx (10:15:10)
systemctl restart nginx (10:15:25)
systemctl restart nginx (10:15:40) ← LOOP DETECTED
```

### 2. Stuck Operation Detection
If one category >80% of commands → 🚨 Alert

**Example**:
```
40 VF Server commands
2 Git commands
Total 42 commands
VF Server = 95% ← STUCK DETECTED
```

### 3. Retry Detection
Same command fails 3+ times → 🚨 Alert

**Example**:
```
rm -rf /data (BLOCKED)
rm -rf /data (BLOCKED)
rm -rf /data (BLOCKED) ← RETRY DETECTED
```

### 4. Time Saved Tracking
Shows cumulative time saved by auto-approvals

**Example**:
```
50 auto-approved commands × 3.5s each = 175s saved
= 2.9 minutes you didn't waste clicking "approve"
```

---

## Keyboard Shortcuts (In Dashboard)

- **r** - Refresh data manually
- **a** - Toggle auto-refresh (30 seconds)
- **t** - Add test data (see alerts in action)

---

## What Makes It Useful?

### ✅ Use Cases That Work Well:

1. **Post-Deployment Review**: "Did anything loop during deploy?"
2. **Pattern Detection**: "Am I pushing to git too often?"
3. **Audit Trail**: "What VF server commands ran today?"
4. **Problem Diagnosis**: "Why is the agent stuck?"

### ❌ Not Useful For:

1. Real-time blocking (permissions system is faster)
2. Preventing bad commands (permissions already does this)
3. Automatic intervention (dashboard is read-only)

---

## Quick Test

Try this NOW to see it work:

```bash
# 1. Open dashboard
xdg-open http://localhost:8002/monitor

# 2. Run these commands:
.claude/hooks/auto-logger.py "ps aux | grep python"
.claude/hooks/auto-logger.py "git status"
.claude/hooks/auto-logger.py "systemctl restart nginx"

# 3. Press 'r' in dashboard

# 4. You should see:
# - 3 new commands
# - Different categories (Monitoring, Git, System)
# - Different statuses (AUTO, MANUAL, NOTIFY)
```

---

## Bottom Line

**The monitor is useful when**:
- You want visibility into what happened
- You want to catch patterns (loops, retries, stuck operations)
- You want an audit trail of important operations

**The monitor is NOT useful when**:
- You want to block commands (use permissions for that)
- You want 100% automatic logging (requires deeper integration)

**My recommendation**:
Use Option 2 (wrapper function) for critical operations. Quick, simple, effective.

```bash
# Add to ~/.bashrc:
track() {
    /home/louisdup/Agents/claude/.claude/hooks/auto-logger.py "$*"
    eval "$@"
}

# Then just prefix important commands with 'track'
track git push origin main
track ./deploy.sh
```

That's it. Monitor becomes useful. 🎯
