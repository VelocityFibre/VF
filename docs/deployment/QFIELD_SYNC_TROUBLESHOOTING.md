# QFieldCloud Sync Troubleshooting Guide

**Created**: 2025-12-19
**Status**: Production Ready
**Critical Learning**: Worker service is MANDATORY for sync operations

## Executive Summary

QFieldCloud sync failures are almost always caused by a missing or misconfigured `worker_wrapper` Docker service. This service processes background sync jobs and without it, the QField mobile app can connect but cannot sync data.

## Quick Fix

```bash
# Run diagnostic and auto-fix
.claude/skills/qfieldcloud/scripts/sync_diagnostic.py

# Or manually start worker
cd /home/louisdup/VF/Apps/QFieldCloud
docker-compose up -d worker_wrapper
```

## Architecture Understanding

### Required Services for Sync

| Service | Purpose | Port | Critical for Sync |
|---------|---------|------|-------------------|
| `app` | Django API server | 8011 | ✅ Yes |
| `db` | PostgreSQL database | 5432 | ✅ Yes |
| `memcached` | Cache layer | 11211 | ✅ Yes |
| **`worker_wrapper`** | **Sync job processor** | - | **✅ CRITICAL** |
| `nginx` | Reverse proxy | 80/443 | ❌ No (for local) |
| `ofelia` | Cron scheduler | - | ❌ No |

### Why Worker is Critical

The sync process works as follows:
1. QField app sends sync request to API (`app` service)
2. API queues the sync job in database
3. **Worker service picks up job and processes it** ← Without this, sync hangs forever
4. Worker updates database with results
5. API returns results to QField app

**Without the worker**, steps 3-5 never happen, causing "silent" sync failures.

## Common Issues and Solutions

### Issue 1: Worker Not Running (90% of cases)

**Symptoms**:
- QField connects successfully
- Sync starts but never completes
- No error messages shown

**Diagnosis**:
```bash
docker ps | grep worker
# If nothing shows, worker is not running
```

**Solution**:
```bash
# Option A: Use diagnostic tool
.claude/skills/qfieldcloud/scripts/sync_diagnostic.py

# Option B: Manual fix
cd /home/louisdup/VF/Apps/QFieldCloud
docker-compose build worker_wrapper  # Takes 10-15 minutes
docker-compose up -d worker_wrapper
```

### Issue 2: Worker Image Not Built

**Symptoms**:
- `docker-compose up worker_wrapper` fails
- Error: "Service 'worker_wrapper' failed to build"

**Diagnosis**:
```bash
docker images | grep worker_wrapper
# If nothing shows, image needs building
```

**Solution**:
```bash
cd /home/louisdup/VF/Apps/QFieldCloud
docker-compose build worker_wrapper
# ⏱️ Takes 10-15 minutes (installs GDAL, GEOS, PostGIS, etc.)
```

### Issue 3: Docker Permission Denied

**Symptoms**:
- Worker starts then crashes immediately
- Logs show: "Permission denied" on docker.sock

**Diagnosis**:
```bash
docker logs qfieldcloud-worker | grep "Permission denied"
```

**Solution**:
```bash
# Worker needs root access to Docker socket
docker run -d --name qfieldcloud-worker \
  --user root \  # ← Critical!
  --network qfieldcloud_default \
  -v /var/run/docker.sock:/var/run/docker.sock \
  qfieldcloud-worker_wrapper:latest \
  python manage.py dequeue
```

### Issue 4: Database Connection Failed

**Symptoms**:
- Worker logs: "could not translate host name"
- Worker logs: "could not connect to server"

**Diagnosis**:
```bash
# Find actual database container name
docker ps | grep -E 'db|postgres'
```

**Solution**:
```bash
# Use correct database hostname
docker run -d --name qfieldcloud-worker \
  --network qfieldcloud_default \
  -e POSTGRES_HOST=<actual-db-container-name> \
  -e POSTGRES_DB=qfieldcloud_db \
  -e POSTGRES_USER=qfieldcloud_db_admin \
  -e POSTGRES_PASSWORD=3shJDd2r7Twwkehb \
  qfieldcloud-worker_wrapper:latest \
  python manage.py dequeue
```

### Issue 5: Port Conflict

**Symptoms**:
- Error: "Bind for 0.0.0.0:8011 failed: port is already allocated"

**Diagnosis**:
Worker service doesn't need port mapping!

**Solution**:
```bash
# Remove any -p flags when starting worker
# Only the app service needs port 8011
docker run -d --name qfieldcloud-worker \
  --network qfieldcloud_default \
  # NO -p flag here!
  qfieldcloud-worker_wrapper:latest \
  python manage.py dequeue
```

## Build Time Expectations

Building the worker image takes **10-15 minutes** because it installs:
- Python 3.10 base image
- PostgreSQL development libraries
- GDAL (Geospatial Data Abstraction Library)
- GEOS (Geometry Engine)
- PostGIS extensions
- Django and dependencies
- Docker client libraries

This is normal and expected. The build is cached after first completion.

## Monitoring Worker Health

### Check Status
```bash
# Quick status
.claude/skills/qfieldcloud/scripts/worker.py status

# Detailed logs
docker logs qfieldcloud-worker --tail 50

# Follow logs in real-time
docker logs -f qfieldcloud-worker
```

### Healthy Worker Logs
```
Postgres is ready! ✨ 💅
{"level":"INFO","message":"Dequeue QFieldCloud Jobs from the DB"}
```

### Unhealthy Worker Signs
- Repeated "Postgres isn't ready"
- "Permission denied" errors
- Container constantly restarting
- No new log entries for >5 minutes

## Automation Tools

### New Scripts Added

1. **`sync_diagnostic.py`** - Complete sync readiness check
   - Auto-detects missing services
   - Diagnoses worker issues
   - Offers automatic fixes
   - Shows QField app configuration

2. **`worker.py`** - Worker management
   - `status` - Check if running
   - `build` - Build image
   - `start` - Start with correct config
   - `restart` - Restart cleanly
   - `logs` - View recent activity
   - `monitor` - Real-time health

### Usage Examples
```bash
# Full diagnostic
.claude/skills/qfieldcloud/scripts/sync_diagnostic.py

# Worker operations
.claude/skills/qfieldcloud/scripts/worker.py status
.claude/skills/qfieldcloud/scripts/worker.py restart
.claude/skills/qfieldcloud/scripts/worker.py logs --follow
```

## Best Practices

### Startup Sequence
Always start services in this order:
```bash
cd /home/louisdup/VF/Apps/QFieldCloud
docker-compose up -d db          # 1. Database first
sleep 10                         # 2. Wait for DB
docker-compose up -d app memcached  # 3. Core services
docker-compose up -d worker_wrapper # 4. Worker last
```

### Permanent Solution
Add to system startup:
```bash
# /etc/rc.local or systemd service
cd /home/louisdup/VF/Apps/QFieldCloud
docker-compose up -d
```

### Regular Maintenance
```bash
# Weekly: Clean old containers
docker system prune -f

# Monthly: Rebuild worker for updates
docker-compose build --no-cache worker_wrapper
```

## Testing Sync After Fix

1. **Get local IP**:
   ```bash
   hostname -I | awk '{print $1}'
   # Example: 172.20.10.3
   ```

2. **Configure QField App**:
   - Settings → QFieldCloud
   - Server: `http://[YOUR-IP]:8011`
   - Login with credentials

3. **Test Sync**:
   - Create/open a project
   - Add a test feature
   - Press sync button
   - Watch for completion

4. **Verify in Logs**:
   ```bash
   docker logs -f qfieldcloud-worker
   # Should see job processing
   ```

## Key Learnings

1. **Worker is not optional** - It's mandatory for sync
2. **Build time is long** - Plan for 15 minutes
3. **Docker permissions matter** - Worker needs root
4. **Network names are important** - Use correct container names
5. **No port mapping for worker** - Common mistake
6. **Database must be running first** - Dependency order matters

## Related Documentation

- `.claude/skills/qfieldcloud/skill.md` - Complete QFieldCloud skill docs
- `.claude/commands/qfield/support.md` - GitHub issue handler
- `QFIELD_SUPPORT_SETUP.md` - Initial QField setup
- `CLAUDE.md` - QFieldCloud local development section

## Support Contacts

- **QFieldCloud Issues**: https://github.com/opengisch/QFieldCloud/issues
- **FibreFlow Support**: support@fibreflow.app
- **Internal**: Check worker first, always!