# QFieldCloud Critical Issues & Solutions

## 🔴 CRITICAL: Missing QGIS Docker Image

### Problem
The `qfieldcloud-qgis:latest` Docker image (2.6GB) mysteriously disappears approximately every 24 hours, causing all project synchronization to fail.

### Symptoms
- All projects show "Failed" status
- Error: `pull access denied for qfieldcloud-qgis, repository does not exist`
- Workers fail with `ImageNotFound: 404 Client Error`
- Users report sync failures, authentication errors, download failures

### Root Cause
Unknown - possibly automated Docker cleanup, system prune, or container recreation. No cron jobs or cleanup scripts found during investigation.

### Impact
- **Severity**: CRITICAL - Complete service failure
- **Affected**: ALL users cannot sync, upload, or process projects
- **Frequency**: Recurred twice (Jan 12 and Jan 13, 2026)

### Quick Fix (30 seconds)
```bash
# If backup exists, restore it:
docker load < ~/qfield-backups/qfieldcloud-qgis-20260113-1034.tar.gz
cd /opt/qfieldcloud
docker-compose restart worker_wrapper
```

### Full Rebuild (5-10 minutes)
```bash
# If no backup available:
cd /opt/qfieldcloud/docker-qgis
sudo docker build -t qfieldcloud-qgis:latest .
cd ..
sudo docker-compose restart worker_wrapper
```

### Permanent Solution (Implemented Jan 13, 2026)

1. **Multiple Protective Tags**:
   - `qfieldcloud-qgis:latest`
   - `qfieldcloud-qgis:production`
   - `qfieldcloud-qgis:do-not-delete`
   - `qfieldcloud-qgis:20260113`

2. **Automated Monitoring**:
   - Script: `/home/velo/check_qgis_image.sh`
   - Runs every 6 hours via cron
   - Auto-restores from backup if missing
   - Logs to: `/home/velo/qgis_image_monitor.log`

3. **Backup Location**:
   - `~/qfield-backups/qfieldcloud-qgis-20260113-1034.tar.gz` (821MB)

### Verification Commands
```bash
# Check if image exists
docker images | grep qfieldcloud-qgis

# Check all 8 workers are running
docker ps | grep worker_wrapper | wc -l  # Should output: 8

# Test monitoring script
/home/velo/check_qgis_image.sh
```

---

## 🟡 CSRF Verification Failed

### Problem
CSRF token validation fails after configuration changes or migrations.

### Symptoms
- Web interface shows: "403 Forbidden - CSRF verification failed"
- Error: "Origin checking failed - https://qfield.fibreflow.app does not match any trusted origins"
- Works in incognito mode but not regular browser (cookie cache issue)

### Root Cause
1. Configuration overwrites when using `sed` to modify docker-compose files
2. Browser caching old CSRF tokens
3. Missing CSRF_TRUSTED_ORIGINS environment variable

### Quick Fix

#### For Users (Browser Cache):
1. **Clear ALL browser data** (not just cookies):
   - Chrome: Settings → Privacy → Clear browsing data → All time
   - Firefox: Settings → Privacy → Clear Data → Everything
   - Safari: Develop → Empty Caches + Clear History
2. **Close browser completely** (all windows)
3. Reopen and try again
4. If still fails, use Incognito/Private mode

#### For Server (Emergency Fix):
```bash
# The ONLY reliable fix - append directly to settings.py
docker exec qfieldcloud-app-1 bash -c "
cat >> /usr/src/app/qfieldcloud/settings.py << 'EOF'

# CSRF Fix
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

# Restart app
cd /opt/qfieldcloud
sudo docker-compose restart app
```

### Permanent Solution (Implemented Jan 13, 2026)
**WARNING**: local_settings.py does NOT work - Django doesn't import it!

The fix is appended directly to `/usr/src/app/qfieldcloud/settings.py`:
- CSRF_TRUSTED_ORIGINS as proper Python list
- ALLOWED_HOSTS set to ['*']
- Configuration prints to logs for verification
- Survives container restarts

**Note**: Environment variables in .env are loaded but Django doesn't parse them correctly as lists

---

## 🟡 Static Files Not Loading

### Problem
CSS/JavaScript files return 404, web interface shows plain text only.

### Symptoms
- No styling on web interface
- Browser console shows 404 for `/static/` resources
- Theme/CSS not loading at https://qfield.fibreflow.app

### Quick Fix
```bash
# Collect static files
cd /opt/qfieldcloud
sudo docker-compose exec app python manage.py collectstatic --noinput

# Set DEBUG=True in local_settings.py (already done)
# Restart nginx
sudo docker-compose restart nginx app
```

---

## Quick Reference Card

### SSH Access
```bash
# Using SSH key (preferred)
ssh -i ~/.ssh/vf_server_key velo@100.96.203.105

# Using password
ssh velo@100.96.203.105  # Password: 2025
# Sudo password: VF@2025!
```

### Service Control
```bash
cd /opt/qfieldcloud

# Check all services
sudo docker-compose ps

# Restart specific service
sudo docker-compose restart worker_wrapper  # For workers
sudo docker-compose restart app            # For Django app
sudo docker-compose restart nginx          # For web server

# View logs
sudo docker-compose logs --tail=100 worker_wrapper
sudo docker-compose logs --tail=100 app
```

### Emergency Contacts
- **Primary**: Louis (has server access)
- **Issues**: Report in WhatsApp group or GitHub
- **Logs**: Check `/home/velo/qgis_image_monitor.log` for automated fixes

### Prevention Tips
1. **Never use `sed` on docker-compose files** - Always edit manually
2. **Create backups before changes**: `cp file file.backup-$(date +%Y%m%d)`
3. **Test in staging first** if possible
4. **Document all changes** in INCIDENT_LOG.md

---

## Related Documentation
- [INCIDENT_LOG.md](./INCIDENT_LOG.md) - Complete incident history
- [MIGRATION_COMPLETE.md](./MIGRATION_COMPLETE.md) - Migration from Hostinger to VF Server
- [skill.md](./skill.md) - QFieldCloud skill documentation