---
description: Check VPS health metrics and system status
---

# VPS Health Monitor

Check production VPS health and system status.

**Supported Servers**:
- **Hostinger VPS**: srv1092611.hstgr.cloud (72.60.17.245, Lithuania) - Public FibreFlow
- **VF Server**: velo-server (100.96.203.105 via Tailscale) - Internal operations
  - Production paths: `/srv/data/apps/`, `/srv/scripts/cron/`
  - For VF-specific operations, see `.claude/skills/vf-server/`

## Execution

Activate the VPS Monitor agent from `agents/vps-monitor/agent.py`:

```python
from agents.vps_monitor.agent import VPSMonitorAgent

agent = VPSMonitorAgent()
response = agent.chat("Check system health status")
print(response)
```

## Health Metrics to Report

### 1. CPU Usage
- **Current**: X% utilization
- **Average (5min)**: X%
- **Load Average**: 1.xx, 1.xx, 1.xx
- **Status**: ✅ Normal / ⚠️ High / 🔴 Critical

**Thresholds**:
- ✅ Normal: < 70%
- ⚠️ High: 70-90%
- 🔴 Critical: > 90%

### 2. Memory (RAM)
- **Used**: X MB / Total MB (X%)
- **Free**: X MB
- **Cached**: X MB
- **Swap Used**: X MB
- **Status**: ✅ Normal / ⚠️ High / 🔴 Critical

**Thresholds**:
- ✅ Normal: < 80%
- ⚠️ High: 80-95%
- 🔴 Critical: > 95%

### 3. Disk Space
- **Root (/)**: X GB / Total GB (X%)
- **Free**: X GB
- **Largest directories**: [List top 5]
- **Status**: ✅ Normal / ⚠️ High / 🔴 Critical

**Thresholds**:
- ✅ Normal: < 75%
- ⚠️ High: 75-90%
- 🔴 Critical: > 90%

### 4. Network Connectivity
- **External IP**: 72.60.17.245
- **Ping**: X ms
- **Connection**: ✅ Connected / ❌ Unreachable
- **Active Connections**: X

### 5. Critical Processes
Check if these are running:
- ✅ Nginx (web server)
- ✅ Python/FastAPI (agent API)
- ✅ SSH daemon
- ❌ Any crashed processes

### 6. System Uptime
- **Uptime**: X days, X hours
- **Last Reboot**: YYYY-MM-DD HH:MM
- **Status**: ✅ Stable

### 7. Recent Errors
- **System logs**: Check `/var/log/syslog` for errors
- **Application logs**: Check agent logs
- **Auth failures**: Recent SSH attempts
- **Status**: ✅ No critical errors / ⚠️ Warnings found / 🔴 Errors detected

## Health Report Format

```markdown
## VPS Health Report
**Timestamp**: [YYYY-MM-DD HH:MM:SS UTC]
**Server**: srv1092611.hstgr.cloud (72.60.17.245)

### Overall Status: ✅ HEALTHY / ⚠️ WARNING / 🔴 CRITICAL

---

### System Resources

#### CPU
- **Usage**: 25% (Normal)
- **Load Average**: 0.50, 0.45, 0.40
- **Status**: ✅ Normal

#### Memory
- **Used**: 2.1 GB / 4.0 GB (52%)
- **Free**: 1.9 GB
- **Swap**: 0 MB used
- **Status**: ✅ Normal

#### Disk
- **Root**: 15.2 GB / 50.0 GB (30%)
- **Free**: 34.8 GB
- **Status**: ✅ Normal

---

### Services

#### Web Server (Nginx)
- **Status**: ✅ Running
- **Port 80**: ✅ Listening
- **Port 443**: ✅ Listening
- **Uptime**: 15 days

#### Agent API (FastAPI)
- **Status**: ✅ Running
- **Port 8000**: ✅ Listening
- **Process ID**: 12345
- **Memory**: 250 MB

#### Database Connections
- **Neon PostgreSQL**: ✅ Connected
- **Convex Backend**: ✅ Connected

---

### Network

- **Connectivity**: ✅ Online
- **Latency**: 15ms
- **Active Connections**: 42
- **Bandwidth**: Normal

---

### Security

- **Failed SSH Attempts**: 3 (last 24h) - ✅ Normal
- **Firewall**: ✅ Active
- **Open Ports**: 22 (SSH), 80 (HTTP), 443 (HTTPS), 8000 (API)
- **Last Security Update**: YYYY-MM-DD

---

### Recent Activity

- **Last Deployment**: YYYY-MM-DD HH:MM
- **Recent Restarts**: None
- **Log Errors (24h)**: 0 critical, 2 warnings

---

### Issues Detected

[If any issues found:]
🔴 **Critical**: [Description and recommended action]
⚠️ **Warning**: [Description and monitoring advice]

[If no issues:]
✅ No issues detected. System operating normally.

---

### Recommendations

- [Action item 1, if any]
- [Action item 2, if any]

### Next Check
Recommended: [Timeframe based on current status]
- ✅ Normal: Check in 24 hours
- ⚠️ Warning: Check in 6 hours
- 🔴 Critical: Monitor continuously
```

## Alert Thresholds

Trigger alerts when:
- 🔴 **Critical**: CPU > 90%, RAM > 95%, Disk > 90%, or services down
- ⚠️ **Warning**: CPU > 70%, RAM > 80%, Disk > 75%
- 📊 **Info**: Significant changes in metrics

## Troubleshooting Actions

### High CPU
1. Check running processes: `top -n 1`
2. Identify resource-heavy processes
3. Consider restarting services
4. Check for runaway processes

### High Memory
1. Check memory usage: `free -h`
2. Identify memory-heavy processes: `ps aux --sort=-%mem | head -10`
3. Consider restarting services
4. Check for memory leaks

### High Disk
1. Find large files: `du -h / | sort -rh | head -20`
2. Clean up logs: `journalctl --vacuum-size=100M`
3. Clear temporary files
4. Archive old data

### Services Down
1. Restart service: `sudo systemctl restart [service]`
2. Check logs: `sudo journalctl -u [service] -n 50`
3. Verify configuration
4. Check port availability

## Automation

Can be run on schedule:
```bash
# Cron job for health checks (every hour)
0 * * * * /path/to/venv/bin/python3 -c "from agents.vps_monitor.agent import VPSMonitorAgent; agent = VPSMonitorAgent(); print(agent.chat('health check'))" >> /var/log/vps-health.log 2>&1
```

## Integration

This command uses:
- **VPS Monitor Agent**: `agents/vps-monitor/agent.py`
- **SSH Connection**: Requires SSH key in `~/.ssh/`
- **VPS Hostname**: From `VPS_HOSTNAME` environment variable

## Usage Scenarios

### Scenario 1: Routine Check
"Check VPS health before deployment"

### Scenario 2: Performance Investigation
"Why is the website slow? Check VPS health"

### Scenario 3: Post-Deployment Validation
"Verify VPS health after deployment"

### Scenario 4: Incident Response
"System is down! Check VPS health immediately"

## Historical Tracking

Save health reports to track trends:
```bash
# Append health check to log file
./venv/bin/python3 -c "from agents.vps_monitor.agent import VPSMonitorAgent; agent = VPSMonitorAgent(); print(agent.chat('health check'))" >> logs/vps-health-$(date +%Y-%m-%d).log
```

## Dashboard Integration

Health metrics can feed into:
- **Monitoring Dashboard**: Grafana, Datadog, etc.
- **Alert System**: PagerDuty, Slack notifications
- **Log Aggregation**: ELK stack, CloudWatch

## Success Criteria

Health check is successful when:
- ✅ All metrics collected without errors
- ✅ Critical services confirmed running
- ✅ No critical issues detected
- ✅ Clear status and recommendations provided
