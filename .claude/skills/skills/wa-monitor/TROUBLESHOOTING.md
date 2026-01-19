# WA Monitor Troubleshooting Guide

## Quick Diagnosis Commands

```bash
# Check overall health
curl -s https://app.fibreflow.app/api/wa-monitor-health | python3 -m json.tool

# Check service status
ssh root@72.60.17.245 'systemctl status wa-monitor-prod'

# Check recent logs
ssh root@72.60.17.245 'tail -n 50 /opt/wa-monitor/prod/logs/*.log | grep -E "ERROR|WARNING"'

# Test database connection
export PGPASSWORD='npg_MIUZXrg1tEY0'
psql -h ep-dry-night-a9qyh4sj-pooler.gwc.azure.neon.tech -U neondb_owner -d neondb \
  -c "SELECT COUNT(*) FROM qa_photo_reviews WHERE DATE(created_at) = CURRENT_DATE;"
```

## Common Issues & Solutions

### 1. No Drops Appearing in Dashboard

**Symptoms:**
- Dashboard shows 0 drops for today
- API returns empty results
- Service appears to be running

**Check 1: Service Actually Running on Hostinger**
```bash
ssh root@72.60.17.245 'ps aux | grep wa-monitor'
```

**Check 2: Database Authentication**
```bash
ssh root@72.60.17.245 'grep "password authentication failed" /opt/wa-monitor/prod/logs/*.log | tail -5'
```
- If authentication errors: Update password in `/opt/wa-monitor/prod/.env`

**Check 3: WhatsApp Database Schema**
```bash
ssh root@72.60.17.245 'tail -n 30 /opt/wa-monitor/prod/logs/*.log | grep "no such column"'
```
- If "no such column: deleted" error: Run schema fix (see Issue #5 below)

### 2. Service Stops Processing Drops

**Symptom:** Service running but not finding new drops

**Solution:** Use the safe restart script (clears Python cache)
```bash
ssh root@72.60.17.245 '/opt/wa-monitor/prod/restart-monitor.sh'
# NEVER use: systemctl restart wa-monitor-prod (doesn't clear cache)
```

### 3. Automated Messages Being Sent to Groups

**Symptom:** WhatsApp groups receiving unwanted automated messages

**Immediate Fix:**
```bash
# Stop all messages NOW
ssh root@72.60.17.245 'systemctl stop wa-monitor-prod'
```

**Permanent Solution:**
```bash
# Add to /opt/wa-monitor/prod/.env
ssh root@72.60.17.245 'echo "DISABLE_AUTO_MESSAGES=true" >> /opt/wa-monitor/prod/.env'
ssh root@72.60.17.245 'systemctl restart wa-monitor-prod'
```

### 4. Send Feedback Button Not Working

**Check WhatsApp Bridge:**
```bash
ssh root@72.60.17.245 'systemctl status whatsapp-bridge-prod'
ssh root@72.60.17.245 'systemctl restart whatsapp-bridge-prod'
```

### 5. Database Schema Issues

**Error:** `ERROR - Error reading WhatsApp DB: no such column: deleted`

**Fix:**
```bash
ssh root@72.60.17.245
sqlite3 /opt/velo-test-monitor/services/whatsapp-bridge/store/messages.db \
  "ALTER TABLE messages ADD COLUMN deleted BOOLEAN DEFAULT FALSE;"
systemctl restart wa-monitor-prod
```

### 6. Neon Database Authentication Failed

**Error:** `ERROR: password authentication failed for user 'neondb_owner'`

**Fix:**
```bash
# Backup current config
ssh root@72.60.17.245 'cp /opt/wa-monitor/prod/.env /opt/wa-monitor/prod/.env.backup'

# Update password (current as of 2026-01-13)
ssh root@72.60.17.245 'sed -i "s/npg_aRNLhZc1G2CD/npg_MIUZXrg1tEY0/g" /opt/wa-monitor/prod/.env'

# Restart service
ssh root@72.60.17.245 'systemctl restart wa-monitor-prod'
```

## Critical Files & Locations

### Hostinger VPS (72.60.17.245)
- **Service Config**: `/etc/systemd/system/wa-monitor-prod.service`
- **Environment**: `/opt/wa-monitor/prod/.env`
- **Projects Config**: `/opt/wa-monitor/prod/config/projects.yaml`
- **Logs**: `/opt/wa-monitor/prod/logs/*.log`
- **WhatsApp DB**: `/opt/velo-test-monitor/services/whatsapp-bridge/store/messages.db`
- **Python Code**: `/opt/wa-monitor/prod/modules/monitor.py`

### Dashboard (Frontend)
- **URL**: https://app.fibreflow.app/wa-monitor
- **API**: https://app.fibreflow.app/api/wa-monitor-*
- **Source**: `src/modules/wa-monitor/` in FibreFlow app

## Recovery Procedures

### Complete Service Recovery
```bash
# 1. Stop service
ssh root@72.60.17.245 'systemctl stop wa-monitor-prod'

# 2. Fix any database issues
ssh root@72.60.17.245 'sqlite3 /opt/velo-test-monitor/services/whatsapp-bridge/store/messages.db "PRAGMA integrity_check;"'

# 3. Clear logs if too large
ssh root@72.60.17.245 'echo "" > /opt/wa-monitor/prod/logs/wa-monitor-prod.log'

# 4. Use safe restart (clears cache)
ssh root@72.60.17.245 '/opt/wa-monitor/prod/restart-monitor.sh'

# 5. Monitor logs
ssh root@72.60.17.245 'tail -f /opt/wa-monitor/prod/logs/*.log'
```

### Adding New WhatsApp Group
```bash
# 1. Edit config
ssh root@72.60.17.245 'nano /opt/wa-monitor/prod/config/projects.yaml'

# 2. Add group (get JID from WhatsApp Web)
# - name: NewGroup
#   enabled: true
#   group_jid: "120363XXXXXXXXXX@g.us"
#   description: "New group description"

# 3. Safe restart to apply
ssh root@72.60.17.245 '/opt/wa-monitor/prod/restart-monitor.sh'
```

## Monitoring Commands

### Check Today's Drops
```bash
export PGPASSWORD='npg_MIUZXrg1tEY0'
psql -h ep-dry-night-a9qyh4sj-pooler.gwc.azure.neon.tech -U neondb_owner -d neondb \
  -c "SELECT project, COUNT(*) FROM qa_photo_reviews WHERE DATE(created_at) = CURRENT_DATE GROUP BY project;"
```

### Check Service Performance
```bash
ssh root@72.60.17.245 'systemctl status wa-monitor-prod | grep -E "Memory|CPU"'
```

### View Recent Processing
```bash
ssh root@72.60.17.245 'grep "Found drop" /opt/wa-monitor/prod/logs/*.log | tail -20'
```

## Emergency Contacts

- **Service Owner**: Louis
- **Hostinger VPS**: root@72.60.17.245
- **Dashboard**: https://app.fibreflow.app/wa-monitor
- **Database**: Neon PostgreSQL (qa_photo_reviews table)

## Notes

- Service runs on **Hostinger VPS**, NOT VF Server
- Always use `/opt/wa-monitor/prod/restart-monitor.sh` for restarts
- Python cache issues are common - safe restart script handles this
- WhatsApp Bridge (port 8080) is separate from monitor service
- Module is fully isolated - can be debugged independently