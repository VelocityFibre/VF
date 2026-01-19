# QFieldCloud Fault Logging - Quick Reference

## 📝 Log a Fault

```bash
cd /home/louisdup/Agents/claude/.claude/skills/qfieldcloud/sub-skills/fault-logging/scripts

# Quick logging (recommended)
./simple_log_fault.sh "CRITICAL" "qgis-image" "Image missing" "manual" "juan"
./simple_log_fault.sh "MAJOR" "workers" "Only 4/8 running" "monitoring"
./simple_log_fault.sh "MINOR" "database" "Slow queries" "manual"
./simple_log_fault.sh "INFO" "deployment" "Maintenance complete" "manual"
```

**Note**: CRITICAL faults automatically trigger WhatsApp alerts! ✅

## 📊 View Faults

```bash
# Recent faults (quick check)
./recent_faults.sh 10

# Search by keyword
./search_faults.sh "qgis"
./search_faults.sh "CRITICAL"
./search_faults.sh "workers"

# Analyze patterns (last 30 days)
./analyze_faults.sh 30

# Generate report
./fault_report.sh 7           # Last 7 days
./fault_report.sh 30 report.txt  # Save to file
```

## 🚨 Alerting

```bash
# Manual alert check
./alert.sh

# Setup automated monitoring (one-time)
./setup_monitoring.sh
```

This configures:
- ✅ Health checks every 5 minutes
- ✅ Alert checks every 5 minutes
- ✅ Automatic WhatsApp notifications

## 🔍 Natural Language Triggers

In Claude Code, use:
- `#logFault` - Quick fault logging (450 tokens) ⚡
- `#logFaultDetail` - Detailed investigation (4,000 tokens) 📋
- `log fault` - Log an issue
- `fault history` - View recent faults
- `error pattern` - Analyze patterns
- `search faults` - Find specific issues
- `analyze faults` - Pattern analysis

**Note**: Use `#logFault` for 90% of cases. Use `#logFaultDetail` only when you need comprehensive root cause analysis and lessons learned documentation.

## 📱 Alert Configuration

- **Phone**: +27 71 155 8396
- **API**: http://100.96.203.105:8081 (VF Server)
- **Cooldown**: 30 minutes per component

## 🎯 Common Scenarios

### User reports issue
```bash
./simple_log_fault.sh "MAJOR" "web" "Users getting 403 errors" "manual" "juan"
```

### Monitoring detects problem
```bash
# Automatic via critical_check.sh integration
# Or manually:
./simple_log_fault.sh "CRITICAL" "qgis-image" "Image missing" "monitoring"
```

### Weekly review
```bash
./recent_faults.sh 20
./analyze_faults.sh 7
./fault_report.sh 7
```

### Search for recurring issues
```bash
./search_faults.sh "qgis"
./analyze_faults.sh 30  # Look for patterns
```

## 📂 File Locations

- **Fault Log**: `data/fault_log.json`
- **Alert Cooldowns**: `data/last_alert_*.txt`
- **Alert Log**: `data/alert_check.log`
- **Health Log**: `data/health_check.log`

## 🎨 Severity Colors

- 🔴 **CRITICAL** - Service down
- 🟡 **MAJOR** - Degraded service
- 🔵 **MINOR** - Non-critical issue
- ⚪ **INFO** - Informational

## ⚙️ Automated Setup

```bash
# Run once on VF Server
./setup_monitoring.sh
```

Then forget about it! System will:
1. Monitor QFieldCloud every 5 minutes
2. Auto-log any detected issues
3. Send WhatsApp alerts for CRITICAL faults
4. Build pattern history

## 🔗 Integration

Works automatically with:
- `critical_check.sh` - Auto-logs detected issues
- `health_check.sh` - Comprehensive monitoring
- WhatsApp API - Sends alerts
- Cron - Periodic execution

## 💡 Tips

1. **Use simple_log_fault.sh** for speed (vs log_fault.sh)
2. **CRITICAL faults alert immediately** - use sparingly
3. **30-min cooldown** prevents alert spam
4. **Search before logging** - check if issue already reported
5. **Weekly reviews** help spot patterns

## 📈 What You'll Learn

After 30 days of logging, you'll know:
- Which components fail most often
- Peak failure times
- Recurring patterns (e.g., "QGIS disappears every 48h")
- Resolution effectiveness
- Whether issues are getting better or worse

## 🚀 Quick Start (First Time)

```bash
cd /home/louisdup/Agents/claude/.claude/skills/qfieldcloud/sub-skills/fault-logging/scripts

# 1. Setup automated monitoring (on VF Server)
./setup_monitoring.sh

# 2. Test by logging a fault
./simple_log_fault.sh "INFO" "test" "Testing fault logging system" "manual" "$(whoami)"

# 3. View it
./recent_faults.sh 1

# 4. Done! System is now monitoring automatically
```

## 📞 Support

- **Documentation**: `README.md` (comprehensive guide)
- **Implementation**: `IMPLEMENTATION_SUMMARY.md` (technical details)
- **Skill Definition**: `skill.md` (triggers and integration)

---

**Version**: 2.0.0 (with automated alerting)
**Status**: ✅ Production ready
**Next**: Run `./setup_monitoring.sh` on VF Server
