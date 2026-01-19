---
name: qfieldcloud
version: 1.0.0
description: Complete management suite for QFieldCloud GIS synchronization platform
author: FibreFlow Team
category: application
tags: [django, docker, postgresql, gis, qfield, qgis, deployment]
created: 2024-12-17
async: true
context_fork: true
hooks:
  pre_tool_use: "echo '[QFieldCloud] Starting operation at $(date)' >> /tmp/qfield_operations.log"
  post_tool_use: "echo '[QFieldCloud] Completed operation at $(date)' >> /tmp/qfield_operations.log"
---

# QFieldCloud Management Skill

Comprehensive skill for managing QFieldCloud - a Django-based service for synchronizing QGIS projects and field data between desktop and mobile devices.

## Features

- **Docker Container Management**: Control docker-compose services (app, nginx, db, redis, worker)
- **Deployment Operations**: Deploy updates from GitHub, manage migrations
- **Service Monitoring**: Check container health, API status, database connectivity
- **Log Analysis**: View and search Docker container logs
- **Database Operations**: Backup/restore operations, migrations
- **User Management**: Create users, manage projects, check quotas
- **SSL Certificate Management**: Let's Encrypt certificate renewal

## ⚠️ Critical Issues & Quick Fixes

**IMPORTANT**: See [CRITICAL_ISSUES.md](./CRITICAL_ISSUES.md) for urgent troubleshooting.

### Most Common Issues:
1. **Projects failing with "Failed" status** → Missing QGIS Docker image
   ```bash
   # Quick fix (30 seconds):
   docker load < ~/qfield-backups/qfieldcloud-qgis-20260113-1034.tar.gz
   docker-compose restart worker_wrapper
   ```

2. **CSRF verification failed (403)** → Clear browser cookies + restart app

3. **No CSS/themes loading** → Run collectstatic + restart nginx

## Quick Usage

```bash
# Check all services status
./scripts/status.py

# Deploy latest updates
./scripts/deploy.py --branch master

# View application logs
./scripts/logs.py --service app --lines 100

# Check database status
./scripts/database.py --action status

# Monitor API health
./scripts/health.py
```

## Infrastructure Configuration

- **Production Server**: VF Server (100.96.203.105:8082)
- **Public URL**: https://qfield.fibreflow.app (via Cloudflare Tunnel)
- **Local Development**: /home/louisdup/VF/Apps/QFieldCloud/
- **GitHub**: opengisch/QFieldCloud (fork)
- **Battery Backup**: ✅ UPS system (1-2 hours load shedding protection)
- **Migration Date**: 2026-01-08 (from Hostinger srv1083126.hstgr.cloud)
- **Old Server**: 72.61.166.168 (DECOMMISSIONED - backups archived)

## Services Architecture

QFieldCloud runs multiple Docker containers:

| Service | Purpose | Port | Notes |
|---------|---------|------|-------|
| `nginx` | Reverse proxy | 8082 | Behind Cloudflare Tunnel |
| `app` | Django application (gunicorn) | 8000 | CSRF fix applied 2026-01-10 |
| `db` | PostgreSQL 13 + PostGIS | 5433 | User: qfieldcloud_db_admin |
| `minio` | Object storage (S3 compatible) | 8009-8010 | 4 data volumes |
| `worker_wrapper` (8x) | Background job processing | - | **Scaled from 4 to 8 workers** |
| `qgis` | GIS project processing | - | **CRITICAL**: 2.7GB image required |
| `memcached` | Cache | 11211 | - |
| `ofelia` | Cron job scheduler | - | - |

## Environment Variables

Required environment variables (stored in .env):
- `QFIELDCLOUD_HOST`: Server hostname (qfield.fibreflow.app)
- `QFIELDCLOUD_VPS_HOST`: VF Server IP (100.96.203.105)
- `QFIELDCLOUD_VPS_USER`: SSH username (velo)
- `QFIELDCLOUD_VPS_PASSWORD`: SSH password (2025)
- `QFIELDCLOUD_PROJECT_PATH`: Remote project path (/opt/qfieldcloud)
- `CSRF_TRUSTED_ORIGINS`: **CRITICAL** - Space-separated trusted origins for POST requests

## Scripts Available

| Script | Purpose | Usage |
|--------|---------|-------|
| `status.py` | Check Docker services | No args |
| `deploy.py` | Deploy from GitHub | `--branch [master\|develop]` |
| `logs.py` | View container logs | `--service NAME --lines N` |
| `database.py` | Database operations | `--action [status\|backup\|migrate]` |
| `health.py` | API health checks | `--verbose` |
| `users.py` | User management | `--action [list\|create\|quota]` |
| `docker.py` | Docker operations | `--action [restart\|rebuild\|prune]` |

## Common Operations

### Check Service Status
```bash
./scripts/status.py
```
Shows:
- Docker container status
- Memory and CPU usage
- Container health
- Uptime information

### Deploy Updates
```bash
# Deploy from master branch
./scripts/deploy.py --branch master

# Deploy with migrations
./scripts/deploy.py --branch master --migrate

# Deploy and collect static files
./scripts/deploy.py --branch master --collectstatic
```

### View Logs
```bash
# View app logs
./scripts/logs.py --service app --lines 100

# Follow nginx logs
./scripts/logs.py --service nginx --follow

# Search for errors
./scripts/logs.py --service all --grep "ERROR"
```

### Database Management
```bash
# Check database status
./scripts/database.py --action status

# Create backup
./scripts/database.py --action backup

# Run migrations
./scripts/database.py --action migrate

# Access database shell
./scripts/database.py --action shell
```

### Health Monitoring
```bash
# Quick health check
./scripts/health.py

# Verbose health check with response times
./scripts/health.py --verbose

# Check specific endpoint
./scripts/health.py --endpoint /api/v1/status/
```

### User Management
```bash
# List users
./scripts/users.py --action list

# Create superuser
./scripts/users.py --action create --username admin --email admin@example.com

# Check user quota
./scripts/users.py --action quota --username john
```

## Sync Troubleshooting

### Critical Requirements for Sync

The `worker_wrapper` service is **CRITICAL** for sync operations. Without it:
- App connects successfully (no error shown)
- Sync appears to start but never completes
- Jobs queue up but are never processed

```bash
# Quick sync readiness check
./scripts/sync_diagnostic.py

# Manual check for worker
docker ps | grep worker
```

### Common Sync Issues

1. **"Sync failed" - Worker not running** (MOST COMMON)
   ```bash
   # Diagnose and auto-fix
   ./scripts/sync_diagnostic.py

   # Manual fix - Build worker (15 min)
   cd /home/louisdup/VF/Apps/QFieldCloud
   docker-compose build worker_wrapper
   docker-compose up -d worker_wrapper
   ```

2. **Worker keeps crashing - Docker permission**
   ```bash
   # Worker needs root for Docker socket access
   docker run -d --name qfieldcloud-worker \
     --user root \
     --network qfieldcloud_default \
     -v /var/run/docker.sock:/var/run/docker.sock \
     qfieldcloud-worker_wrapper:latest \
     python manage.py dequeue
   ```

3. **Worker can't connect to database**
   ```bash
   # Find correct database container name
   docker ps | grep -E 'db|postgres'
   # Use that name in POSTGRES_HOST env var
   ```

4. **Port conflict errors**
   - Worker doesn't need port mapping (remove -p flag)
   - Only app service needs port 8011

## Troubleshooting

### Critical Fixes (2026-01-10) - VF Server Migration

#### ⚠️ CSRF 403 Forbidden Errors

**Symptom**: "CSRF verification failed. Request aborted. Origin checking failed"

**Quick Fix**:
```bash
# 1. Verify CSRF_TRUSTED_ORIGINS in .env
cat /opt/qfieldcloud/.env | grep CSRF

# 2. Restart app container
docker restart qfieldcloud-app-1

# 3. Verify in Django
docker exec qfieldcloud-app-1 python manage.py shell -c \
  "from django.conf import settings; print(settings.CSRF_TRUSTED_ORIGINS)"
```

**Permanent Fix**: See `MIGRATION_COMPLETE.md` for full details

#### ⚠️ Project Upload Failures ("Failed state")

**Symptom**: Files upload but jobs fail immediately, projects don't appear in QField

**Quick Fix**:
```bash
# 1. Verify QGIS image exists
docker images | grep qgis
# Should show: qfieldcloud-qgis:latest - 2.7GB

# 2. If missing, rebuild
docker-compose build qgis

# 3. Restart workers
docker ps | grep worker_wrapper | awk '{print $NF}' | xargs docker restart
```

**Root Cause**: Workers need qfieldcloud-qgis Docker image to process GIS files

### Common Issues

1. **Containers not starting**: Check docker-compose logs
   ```bash
   ./scripts/logs.py --service all --lines 200
   ```

2. **Database connection issues**: Verify PostgreSQL is running
   ```bash
   ./scripts/database.py --action status
   ```

3. **SSL certificate issues**: Now handled by Cloudflare Tunnel (no local SSL)
   ```bash
   # Check tunnel status
   ps aux | grep cloudflared
   ```

4. **Storage issues**: Check MinIO/S3 connectivity
   ```bash
   ./scripts/health.py --verbose
   ```

5. **502 Bad Gateway errors via qfield.fibreflow.app**: Tunnel or container issues
   ```bash
   # Test direct server access
   curl -I http://100.96.203.105:8082 -H "Host: qfield.fibreflow.app"
   # Expected: HTTP/1.1 302 (redirect to login)

   # Test via public URL
   curl -I https://qfield.fibreflow.app/

   # Check Cloudflare Tunnel status
   ssh velo@100.96.203.105
   ps aux | grep cloudflared | grep qfield

   # Restart tunnel if needed
   sudo systemctl restart cloudflared
   ```

   **Root Cause**: Cloudflare Tunnel down or nginx container not running

   **VF Server Configuration**:
   - QFieldCloud runs on port 8082 (internal)
   - Cloudflare Tunnel forwards qfield.fibreflow.app → localhost:8082
   - Tunnel config: /home/velo/.cloudflared/config.yml
   - Tunnel ID: 0bf9e4fa-f650-498c-bd23-def05abe5aaf

### Emergency Commands

```bash
# Restart all services
./scripts/docker.py --action restart --all

# Rebuild specific service
./scripts/docker.py --action rebuild --service app

# Clean up Docker resources
./scripts/docker.py --action prune

# Force recreate containers
./scripts/docker.py --action recreate
```

## QFieldCloud Specific Operations

### Project Management
```bash
# List all projects
./scripts/projects.py --action list

# Check project status
./scripts/projects.py --action status --project PROJECT_ID

# Export project data
./scripts/projects.py --action export --project PROJECT_ID
```

### Synchronization Monitoring
```bash
# Check sync queue
./scripts/sync.py --action queue

# View recent syncs
./scripts/sync.py --action recent --hours 24

# Check failed syncs
./scripts/sync.py --action failed
```

## Integration with Other Skills

This skill works with:
- `vf-server`: For server-level operations
- `database-operations`: For complex PostgreSQL queries
- `git-operations`: For repository management
- `ff-react`: Coordinates with main FibreFlow app

## Development Workflow

### Local Development
```bash
# SSH to VPS
ssh user@72.61.166.168

# Navigate to project
cd /path/to/qfieldcloud

# Update from git
git pull origin master

# Rebuild containers
docker-compose build

# Run migrations
docker-compose exec app python manage.py migrate

# Restart services
docker-compose restart
```

### Production Deployment
```bash
# Use deployment script
./scripts/deploy.py --branch master --migrate --collectstatic

# Monitor deployment
./scripts/logs.py --service app --follow
```

## API Endpoints

Key API endpoints to monitor:
- `/api/v1/status/` - Health check
- `/api/v1/auth/login/` - Authentication
- `/api/v1/projects/` - Project listing
- `/api/v1/users/` - User management
- `/swagger/` - API documentation

## Self-Healing Prevention System

QFieldCloud includes a comprehensive automated prevention and monitoring system to prevent upload failures and service degradation.

### Monitor Daemon

**Service**: `qfield-monitor` (systemd)
**Script**: `/home/louisdup/VF/Apps/QFieldCloud/qfield_monitor_daemon.py`
**Logs**: `/var/log/qfield_monitor.log` and `/var/log/qfield_monitor_error.log`

Continuous health monitoring (every 5 minutes) with auto-recovery:
- Detects stuck jobs (queued >10 minutes)
- Monitors worker health and auto-restarts
- Tracks failure rates (alerts if >30%)
- Self-healing with automatic interventions

```bash
# Check monitor status
sudo systemctl status qfield-monitor

# View monitor logs
tail -f /var/log/qfield_monitor.log

# Restart monitor
sudo systemctl restart qfield-monitor
```

### Rate Limiting

**Script**: `qfield_rate_limiter.sh`

Nginx rate limiting to prevent sync overload:
- Global: 10 syncs/minute
- Per-project: 5 syncs/minute
- Throttle individual projects if needed

```bash
# Apply rate limiting
./qfield_rate_limiter.sh --enable

# Throttle specific project
./qfield_rate_limiter.sh --throttle MOA_Pole_Audit
```

### Automated Maintenance

**Cron Jobs** (configured via `qfield_cron_jobs.sh`):

| Frequency | Script | Purpose |
|-----------|--------|---------|
| */5 min | `qfield_quick_check.sh` | Worker and API health |
| */30 min | `qfield_cleanup.sh` | Docker resource cleanup |
| */4 hours | `qfield_scheduled_restart.sh` | Preventive worker restart (if idle) |
| Daily 2am | `qfield_daily_maintenance.sh` | Full maintenance cycle |
| Daily 6am | `qfield_stats.sh` | Usage statistics report |

```bash
# View cron schedule
crontab -l | grep qfield

# Run maintenance manually
./qfield_daily_maintenance.sh
```

### Prevention System Setup

Complete setup in one command:
```bash
cd /home/louisdup/VF/Apps/QFieldCloud
./SETUP_PREVENTION.sh
```

This installs:
- Monitor daemon with systemd service
- Rate limiting configuration
- All automated cron jobs
- Log rotation

### Troubleshooting Prevention System

**Monitor keeps restarting workers:**
```bash
# Check what's triggering it
tail -f /var/log/qfield_monitor.log | grep "CRITICAL\|WARNING"

# Temporarily stop monitor to fix manually
sudo systemctl stop qfield-monitor
# Fix the issue...
sudo systemctl start qfield-monitor
```

**Disk full (100%):**
```bash
# Emergency cleanup
ssh root@72.61.166.168 "docker system prune -a --volumes -f"

# Check disk usage
./scripts/docker.py --action check-disk
```

**Workers missing after cleanup:**
```bash
# Rebuild workers
ssh root@72.61.166.168 "cd /opt/qfieldcloud && docker compose up -d worker_wrapper"
```

## Worker Scaling & Capacity Planning

### Scaling Workers

**Worker Configuration** (in `.env`):
```bash
QFIELDCLOUD_WORKER_REPLICAS=4  # Default: 2
```

**Important**: Don't use `deploy.replicas` in docker-compose.override.yml - it conflicts with the environment variable.

**Scaling Process**:
```bash
# 1. Backup .env
cp .env .env.backup_$(date +%Y%m%d)

# 2. Update worker count
sed -i 's/QFIELDCLOUD_WORKER_REPLICAS=2/QFIELDCLOUD_WORKER_REPLICAS=4/' .env

# 3. Restart services
docker compose down
docker compose up -d

# 4. Verify
docker ps --filter 'name=worker_wrapper' | wc -l  # Should match REPLICAS
```

**Resource Requirements per Worker**:
- CPU: <1% when idle, 20-40% when processing
- Memory: ~100-120 MB
- Disk I/O: Minimal unless processing large files

**Capacity Guidelines**:
```
2 workers  = 8-10 agents (light usage)
4 workers  = 15-20 agents (moderate usage)
6 workers  = 25-30 agents (heavy usage)
8+ workers = 30+ agents (requires multi-server architecture)
```

**Hardware Limits**:
- CPU: Each worker can use ~0.4 cores during processing
- Memory: Monitor total RAM (workers + app + db)
- 2-core VPS: Max 4-5 workers recommended
- 4-core VPS: Max 8-10 workers recommended

### Performance Monitoring

**Queue Monitoring Script** (`scripts/queue_monitor.sh`):
```bash
#!/bin/bash
# Runs every 5 minutes via cron
# Logs: /var/log/qfieldcloud/queue_metrics.log (CSV format)

TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')
QUEUE=$(docker exec qfieldcloud-db-1 psql -U qfieldcloud_db_admin -d qfieldcloud_db -t -c \
  "SELECT COUNT(*) FROM core_job WHERE status IN ('pending', 'queued');")
PROCESSING=$(docker exec qfieldcloud-db-1 psql -U qfieldcloud_db_admin -d qfieldcloud_db -t -c \
  "SELECT COUNT(*) FROM core_job WHERE status = 'started';")
FAILED=$(docker exec qfieldcloud-db-1 psql -U qfieldcloud_db_admin -d qfieldcloud_db -t -c \
  "SELECT COUNT(*) FROM core_job WHERE status = 'failed' AND created_at > NOW() - INTERVAL '1 hour';")

echo "$TIMESTAMP,$QUEUE,$PROCESSING,$FAILED" >> /var/log/qfieldcloud/queue_metrics.log
```

**Install monitoring**:
```bash
# Create monitoring directory
mkdir -p /opt/qfieldcloud/monitoring /var/log/qfieldcloud

# Install cron job
echo "*/5 * * * * /opt/qfieldcloud/monitoring/queue_monitor.sh" | crontab -
```

**Key Metrics to Track**:
- **Queue depth**: Pending + queued jobs (good: <5, warning: 5-10, bad: >10)
- **Processing count**: Active workers (should be 1-4 with 4 workers)
- **Success rate**: finished / (finished + failed) (target: >90%)
- **Job duration**: Time from created_at to finished_at (target: <2 min avg)

### Database Schema Reference

**Job Table**: `core_job` (not `qfieldcloud_job`)
**Database User**: `qfieldcloud_db_admin` (not `qfieldcloud`)
**Database Name**: `qfieldcloud_db`

**Job Statuses**:
- `pending`: Job created, waiting to be queued
- `queued`: Job in queue, waiting for worker
- `started`: Worker actively processing job
- `finished`: Job completed successfully
- `failed`: Job failed (error or timeout)

**Useful Queries**:
```sql
-- Current queue depth
SELECT status, COUNT(*) FROM core_job
WHERE status IN ('pending', 'queued')
GROUP BY status;

-- Success rate (last 24 hours)
SELECT
  status,
  COUNT(*) as count,
  ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 1) as pct
FROM core_job
WHERE created_at > NOW() - INTERVAL '24 hours'
GROUP BY status;

-- Average job duration
SELECT
  ROUND(AVG(EXTRACT(EPOCH FROM (finished_at - started_at)))) as avg_seconds
FROM core_job
WHERE status = 'finished'
  AND finished_at > NOW() - INTERVAL '24 hours';

-- Stuck jobs (>24 hours old)
SELECT id, type, status, created_at
FROM core_job
WHERE status IN ('pending', 'queued')
  AND created_at < NOW() - INTERVAL '24 hours';
```

### Queue Management

**Clean Up Stuck Jobs**:
```bash
# Mark stuck jobs as failed (preserves history)
docker exec qfieldcloud-db-1 psql -U qfieldcloud_db_admin -d qfieldcloud_db -c \
  "UPDATE core_job
   SET status = 'failed',
       finished_at = NOW(),
       output = 'Auto-cleanup: stuck >24 hours'
   WHERE status IN ('pending', 'queued')
     AND created_at < NOW() - INTERVAL '24 hours';"
```

**When to Clean Up**:
- Jobs stuck >24 hours (safe)
- Jobs stuck >48 hours (recommended)
- After system restart (check for orphaned jobs)
- After worker scaling (verify old jobs process)

**Why Jobs Get Stuck**:
1. Worker was down when job created
2. Project deleted/modified after job created
3. System restart interrupted processing
4. Database migration changed schema
5. Missing dependencies (files, permissions)

**Prevention**:
- Monitor worker health (systemd service or prevention daemon)
- Regular cleanup cron job (weekly recommended)
- Alert on queue depth >10 for >30 minutes
- Track job age in monitoring

### Capacity Planning Decision Matrix

**After 1-2 weeks of monitoring, evaluate**:

**Scenario A: Queue <5, Success >90%** ✅
```
Action: STOP - Current configuration is optimal
Capacity: Supports target agent count comfortably
Next: Continue monitoring, no changes needed
```

**Scenario B: Queue 5-10, Success >80%** ⚠️
```
Action: Consider database indexes or priority queue
Capacity: Approaching limits, optimization beneficial
Next: See /home/louisdup/VF/Apps/QFieldCloud/MODIFICATION_SAFETY_GUIDE.md
```

**Scenario C: Queue >10, Success <80%** ❌
```
Action: Investigate root cause (workers, DB, storage, code)
Capacity: Insufficient - need optimization or more workers
Next: Check worker logs, DB performance, storage I/O
```

**Scenario D: Queue always 0, Workers idle** 😴
```
Action: Over-provisioned - can scale down
Capacity: More capacity than needed (saves resources)
Next: Reduce QFIELDCLOUD_WORKER_REPLICAS by 1-2
```

### Benchmarking Methodology

**Week 1-2: Collect Baseline Data**
```bash
# Review metrics
tail -100 /var/log/qfieldcloud/queue_metrics.log

# Calculate averages
awk -F',' '{sum+=$2; count++} END {print "Avg queue:", sum/count}' \
  /var/log/qfieldcloud/queue_metrics.log

# Find peaks
awk -F',' '{if($2>max) max=$2} END {print "Peak queue:", max}' \
  /var/log/qfieldcloud/queue_metrics.log
```

**Week 3: Make Decision**
- Review collected data
- Compare against success criteria
- Decide: STOP or Phase 2 (indexes/priority queue)
- Document findings

**Key Success Indicators**:
- Queue depth avg <5 (good headroom)
- Queue depth peak <10 (no saturation)
- Success rate >90% (reliable processing)
- Job duration <2 min (fast turnaround)
- No sustained high queue (>10 for >30 min)

## Notes

- Always backup database before major updates
- Monitor disk space on VPS (Docker images can be large) - **automated via cron**
- SSL certificates now handled by Cloudflare Tunnel (no local Let's Encrypt)
- Keep docker-compose.yml in sync with upstream
- Monitor worker queue for stuck jobs - **automated via prevention system**
- Check storage quotas regularly
- Prevention system provides self-healing for common issues
- **Worker scaling**: Configuration-only change (zero risk, 2× capacity gain)
- **Queue monitoring**: Cron-based metrics collection every 5 minutes
- **Stuck jobs**: Clean up weekly, mark as failed (preserves history)

## Migration History

### 2026-01-08: Hostinger → VF Server
**Status**: ✅ COMPLETE (see `MIGRATION_COMPLETE.md`)

- **From**: srv1083126.hstgr.cloud (72.61.166.168) - 4 workers, 8GB RAM
- **To**: VF Server (100.96.203.105:8082) - 8 workers, 32GB+ RAM
- **Reason**: Resource constraints, upload flooding, no battery backup
- **Benefits**: 2x worker capacity, load shedding protection, cost savings
- **Post-Migration Fixes** (2026-01-10):
  - CSRF protection configuration
  - QGIS Docker image rebuild
  - All services validated and operational