---
name: qfieldcloud-fault-logging
version: 2.0.0
description: Quick fault logging, pattern analysis, and automated WhatsApp alerting for QFieldCloud
triggers: ["#logFault", "log fault", "quick fault", "fault history", "error pattern", "search faults", "analyze faults"]
context_cost: 450
priority: high
isolation: full
---

# QFieldCloud Fault Logging & Analytics + Automated Alerting

Persistent fault tracking, pattern analysis, and automated WhatsApp notifications for critical QFieldCloud issues.

## Quick Commands

```bash
# Log a new fault manually
./scripts/simple_log_fault.sh "severity" "component" "description"
# Example: ./scripts/simple_log_fault.sh "CRITICAL" "qgis-image" "Docker image missing again"
# Note: CRITICAL faults automatically trigger WhatsApp alerts

# Auto-log from monitoring (runs automatically)
./scripts/auto_log.sh

# Search fault history
./scripts/search_faults.sh [keyword]
# Example: ./scripts/search_faults.sh "qgis"

# Analyze patterns
./scripts/analyze_faults.sh [days]
# Example: ./scripts/analyze_faults.sh 30  # Last 30 days

# Generate report
./scripts/fault_report.sh [days]
# Example: ./scripts/fault_report.sh 7  # Last 7 days

# View recent faults
./scripts/recent_faults.sh [count]
# Example: ./scripts/recent_faults.sh 10  # Last 10 faults

# 🚨 NEW: Alerting Commands
./scripts/alert.sh  # Check and send alerts for recent CRITICAL faults
./scripts/check_and_alert.sh  # Cron-friendly alert checker
./scripts/setup_monitoring.sh  # One-time setup for automated monitoring
```

## Fault Database

Location: `data/fault_log.json`
Backup: `data/fault_log.backup.json`

## Severity Levels

- **CRITICAL** 🔴 - Service down, immediate action needed
- **MAJOR** 🟡 - Degraded service, action required
- **MINOR** 🔵 - Non-critical issue, monitor
- **INFO** ⚪ - Informational, no action needed

## Components Tracked

- **qgis-image** - Docker image issues
- **workers** - Worker processing problems
- **csrf** - Authentication/CSRF errors
- **database** - PostgreSQL issues
- **storage** - MinIO/storage problems
- **web** - Nginx/interface issues
- **network** - Connectivity problems
- **resources** - Disk/memory issues

## Auto-Logging

The monitoring scripts automatically log faults when they detect:
- Missing QGIS image
- Worker failures
- Service outages
- CSRF errors
- High error rates

## 🚨 Automated Alerting System (NEW v2.0)

**WhatsApp notifications for CRITICAL issues**

### Features
- Immediate alerts when CRITICAL faults are logged
- 30-minute cooldown per component (prevents spam)
- Integration with WhatsApp API on VF Server (port 8081)
- Alert log for debugging

### Configuration
- **Phone**: +27 71 155 8396
- **API**: http://100.96.203.105:8081
- **Cooldown**: 30 minutes per component

### Setup
```bash
./scripts/setup_monitoring.sh
```
This configures cron jobs for:
- Health checks every 5 minutes → auto-logs faults
- Alert checks every 5 minutes → sends notifications

### Alert Flow
```
Issue Detected → Monitoring → Fault Logged → CRITICAL? → WhatsApp Alert
```

## Pattern Analysis

Analyzes faults to identify:
- Most frequent issues
- Recurring patterns
- Time-based trends
- Component reliability
- Mean time between failures

## Integration

Works with other sub-skills:
- **monitoring** - Auto-logs detected issues
- **qgis-image** - Logs image disappearances
- **csrf-fix** - Tracks CSRF failures
- **worker-ops** - Records worker problems

## Usage Examples

### Manual Fault Logging
When Juan reports an issue:
```bash
./scripts/log_fault.sh "MAJOR" "web" "Users getting 403 errors on login"
```

### Searching for Patterns
```bash
./scripts/search_faults.sh "qgis"
# Shows all QGIS-related faults with timestamps
```

### Weekly Report
```bash
./scripts/fault_report.sh 7
# Generates report of last 7 days' issues
```