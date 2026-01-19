# QFieldCloud Troubleshooting Runbook

## 🚨 Emergency Response Flow

```mermaid
graph TD
    A[User Reports Issue] --> B{What's the symptom?}
    B -->|Projects Failing| C[Check QGIS Image]
    B -->|403 CSRF Error| D[Fix CSRF Config]
    B -->|No CSS/Styling| E[Fix Static Files]
    B -->|Can't Login| F[Check Auth]

    C --> C1[docker images | grep qgis]
    C1 -->|Missing| C2[Restore from Backup]
    C1 -->|Exists| C3[Restart Workers]

    D --> D1[Clear Browser Cache]
    D1 --> D2[Check CSRF Settings]

    E --> E1[Run collectstatic]
    E1 --> E2[Restart nginx]
```

## Step-by-Step Troubleshooting

### 1. Initial Assessment (2 minutes)

```bash
# Connect to server
ssh -i ~/.ssh/vf_server_key velo@100.96.203.105

# Check overall status
cd /opt/qfieldcloud
sudo docker-compose ps

# Quick health check
curl -I https://qfield.fibreflow.app
```

#### What to Look For:
- ✅ All containers showing "Up" status
- ✅ 8 worker_wrapper containers running
- ✅ HTTP 200 or 302 from curl (not 403, 404, 500)

### 2. Issue-Specific Procedures

#### 🔴 "Failed" Status on All Projects

**Time to Fix**: 30 seconds (with backup) or 5-10 minutes (rebuild)

1. **Check QGIS image**:
   ```bash
   docker images | grep qfieldcloud-qgis
   ```

2. **If missing, restore from backup**:
   ```bash
   docker load < ~/qfield-backups/qfieldcloud-qgis-20260113-1034.tar.gz
   cd /opt/qfieldcloud
   docker-compose restart worker_wrapper
   ```

3. **If no backup, rebuild**:
   ```bash
   cd /opt/qfieldcloud/docker-qgis
   sudo docker build -t qfieldcloud-qgis:latest .
   cd ..
   sudo docker-compose restart worker_wrapper
   ```

4. **Verify fix**:
   ```bash
   # Should show 8 workers
   docker ps | grep worker_wrapper | wc -l

   # Check recent logs for success
   sudo docker-compose logs --tail=20 worker_wrapper | grep -i "success"
   ```

#### 🟡 CSRF Verification Failed (403)

**Time to Fix**: 2 minutes

1. **For Users** - Clear ALL browser data:
   - **Chrome**: Settings → Privacy → Clear browsing data
     - Time range: **All time**
     - Check: Cookies, Cache, Site data
     - Clear → **Close Chrome completely**
   - **Firefox**: Settings → Privacy → Clear Data
     - Check both options → Clear
     - **Quit Firefox completely**
   - **Safari**: Develop → Empty Caches
     - Clear History → All history
     - **Quit Safari (Cmd+Q)**

2. **On Server** - Apply the ONLY working fix:
   ```bash
   cd /opt/qfieldcloud

   # Check if fix already applied
   docker exec qfieldcloud-app-1 grep -q "CSRF Fix" /usr/src/app/qfieldcloud/settings.py

   if [ $? -ne 0 ]; then
     # Apply fix by appending to settings.py
     docker exec qfieldcloud-app-1 bash -c "
     cat >> /usr/src/app/qfieldcloud/settings.py << 'EOF'

# CSRF Fix - Added $(date +%Y-%m-%d)
CSRF_TRUSTED_ORIGINS = [
    'https://qfield.fibreflow.app',
    'https://srv1083126.hstgr.cloud',
    'http://qfield.fibreflow.app',
    'http://srv1083126.hstgr.cloud',
    'http://100.96.203.105:8082',
    'http://localhost:8082',
]
ALLOWED_HOSTS = ['*']
print(f'[CSRF FIX APPLIED] CSRF_TRUSTED_ORIGINS = {CSRF_TRUSTED_ORIGINS}')
EOF
     "
   fi

   # Restart app
   sudo docker-compose restart app
   ```

3. **Verify**:
   ```bash
   # Check logs for confirmation
   docker-compose logs --tail=10 app | grep "CSRF FIX APPLIED"
   ```

**⚠️ WARNING**: Do NOT use local_settings.py - Django doesn't import it!

#### 🟡 Static Files Not Loading (No CSS)

**Time to Fix**: 1 minute

1. **Collect static files**:
   ```bash
   cd /opt/qfieldcloud
   sudo docker-compose exec app python manage.py collectstatic --noinput
   ```

2. **Restart services**:
   ```bash
   sudo docker-compose restart nginx app
   ```

3. **Verify**:
   ```bash
   # Should return 200 OK
   curl -I https://qfield.fibreflow.app/static/admin/css/base.css
   ```

#### 🔵 Authentication Issues

**Time to Fix**: 1 minute per user

1. **Clear user's tokens**:
   ```bash
   cd /opt/qfieldcloud
   sudo docker-compose exec app python manage.py shell
   ```
   ```python
   from django.contrib.auth import get_user_model
   from rest_framework.authtoken.models import Token
   User = get_user_model()

   # Find user
   user = User.objects.get(username='Lukek')  # or email

   # Delete old tokens
   Token.objects.filter(user=user).delete()

   # User will need to login again
   exit()
   ```

### 3. Monitoring & Prevention

#### Daily Health Check (Automated)
The monitoring script runs every 6 hours:
```bash
# Manual check
/home/velo/check_qgis_image.sh

# View monitor log
tail -f /home/velo/qgis_image_monitor.log
```

#### Weekly Maintenance
```bash
# 1. Check disk space
df -h /opt/qfieldcloud

# 2. Verify backups
ls -lah ~/qfield-backups/

# 3. Check for errors in logs
sudo docker-compose logs --since=7d 2>&1 | grep -i error | wc -l

# 4. Update backup if QGIS image changed
docker save qfieldcloud-qgis:latest | gzip > ~/qfield-backups/qfieldcloud-qgis-$(date +%Y%m%d).tar.gz
```

### 4. Escalation Path

1. **Level 1** (Self-Service):
   - Users clear browser cache
   - Check status page

2. **Level 2** (Team Member with SSH):
   - Run this runbook procedures
   - Check logs for specific errors

3. **Level 3** (Louis/Admin):
   - Server restarts
   - Database operations
   - Infrastructure changes

### 5. Communication Templates

#### For WhatsApp Group

**Issue Detected**:
```
🔴 QFieldCloud Issue Detected
Time: [TIME]
Issue: [Projects failing / CSRF error / etc]
Impact: [All users / Web only / etc]
Status: Investigating
```

**Resolution Update**:
```
✅ QFieldCloud Issue Resolved
Time: [TIME]
Issue: [What was wrong]
Fix: [What we did]
Action needed: [Clear cache / Retry sync / etc]
```

### 6. Post-Incident Actions

After resolving any incident:

1. **Update incident log**:
   ```bash
   nano .claude/skills/qfieldcloud/INCIDENT_LOG.md
   ```

2. **Document in operations log** (if significant):
   ```bash
   nano docs/OPERATIONS_LOG.md
   ```

3. **Inform users**:
   - Post in WhatsApp group
   - Update status page if exists

4. **Review prevention**:
   - Could monitoring have caught this earlier?
   - Is there a permanent fix needed?
   - Should we update the runbook?

---

## Quick Commands Cheat Sheet

```bash
# SSH to server
ssh -i ~/.ssh/vf_server_key velo@100.96.203.105

# Navigate to QFieldCloud
cd /opt/qfieldcloud

# Service management
sudo docker-compose ps                    # Check status
sudo docker-compose restart worker_wrapper # Restart workers
sudo docker-compose restart app           # Restart Django
sudo docker-compose restart nginx         # Restart web server
sudo docker-compose logs --tail=100 app   # View logs

# QGIS image management
docker images | grep qgis                 # Check if exists
docker load < ~/qfield-backups/qfieldcloud-qgis-20260113-1034.tar.gz  # Restore

# Quick fixes
sudo docker-compose exec app python manage.py collectstatic --noinput  # Fix CSS
echo $CSRF_TRUSTED_ORIGINS | sudo tee -a .env  # Fix CSRF
```

---

**Last Updated**: 2026-01-13
**Maintainer**: Claude Code + FibreFlow Team
**Related**: [CRITICAL_ISSUES.md](./CRITICAL_ISSUES.md) | [INCIDENT_LOG.md](./INCIDENT_LOG.md)