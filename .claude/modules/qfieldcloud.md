# Module: QFieldCloud

**Type**: skill (infrastructure)
**Location**: `.claude/skills/qfieldcloud/`
**Deployment**: VF Server port 8082 (https://qfield.fibreflow.app)
**Isolation**: fully_isolated
**Developers**: louis
**Last Updated**: 2026-01-12

---

## Overview

QFieldCloud is a Django-based GIS synchronization platform that enables QGIS desktop projects to sync with mobile QField apps. Runs in Docker containers with 8 background workers for processing GIS data, PostGIS database, MinIO object storage, and a 2.7GB QGIS processing image.

**Critical Context**: Fully isolated module. No dependencies on other FibreFlow modules. Can be modified/deployed independently.

## Dependencies

### External Dependencies
- **Docker Compose**: Multi-container orchestration (nginx, app, db, worker, qgis, minio)
- **PostgreSQL 13 + PostGIS**: Spatial database on port 5433
- **MinIO**: S3-compatible object storage for GIS files (ports 8009-8010)
- **QGIS 2.7GB Image**: CRITICAL for project processing - workers fail without it
- **Cloudflare Tunnel**: Public access via qfield.fibreflow.app → localhost:8082

### Internal Dependencies
- **None** - Fully isolated from other FibreFlow modules

## Database Schema

### Tables Owned
| Table | Description | Key Columns |
|-------|-------------|-------------|
| core_job | Background job queue | id, status (pending/queued/started/finished/failed), type, created_at |
| core_project | QGIS projects | id, name, owner_id, created_at |
| core_user | QField users | id, username, email, quota_mb |
| core_layer | Project GIS layers | id, project_id, name, geom_type |

**Database Credentials**:
- Host: localhost:5433 (inside Docker network: db:5432)
- User: `qfieldcloud_db_admin`
- Database: `qfieldcloud_db`

### Tables Referenced
None - standalone system

## API Endpoints

| Endpoint | Method | Purpose | Auth Required |
|----------|--------|---------|---------------|
| /api/v1/status/ | GET | Health check | No |
| /api/v1/auth/login/ | POST | User authentication | No |
| /api/v1/projects/ | GET | List user projects | Yes |
| /api/v1/projects/ | POST | Create project | Yes |
| /api/v1/projects/:id/sync/ | POST | Trigger sync | Yes |
| /swagger/ | GET | API documentation | No |

## Services/Methods

### Core Services
- **worker_wrapper** (8 replicas) - Background job processing via `python manage.py dequeue`
- **nginx** - Reverse proxy, rate limiting (10 req/min global, 5 req/min per-project)
- **app** (gunicorn) - Django application on port 8000
- **qgis** - GIS processing container (no ports, called by workers)

### Critical Operations
```bash
# Status check
.claude/skills/qfieldcloud/scripts/status.py

# Deploy updates
.claude/skills/qfieldcloud/scripts/deploy.py --branch master

# View logs
.claude/skills/qfieldcloud/scripts/logs.py --service app --lines 100

# Health check
.claude/skills/qfieldcloud/scripts/health.py --verbose
```

## File Structure

```
.claude/skills/qfieldcloud/
├── skill.md                    # Skill documentation
├── scripts/
│   ├── status.py              # Service status
│   ├── deploy.py              # Deployment
│   ├── logs.py                # Log viewer
│   ├── health.py              # Health checks
│   ├── sync_diagnostic.py     # Sync troubleshooting
│   └── worker.py              # Worker management
├── MIGRATION_COMPLETE.md      # Jan 2026 migration notes
└── dashboard/                 # Monitoring UI
```

**On VF Server** (`/opt/qfieldcloud/`):
- `.env` - Environment variables
- `docker-compose.yml` - Service definitions
- `docker-compose.override.yml` - Custom config
- `/var/lib/docker/volumes/` - MinIO data volumes

## Configuration

### Environment Variables (VF Server `/opt/qfieldcloud/.env`)
```bash
QFIELDCLOUD_HOST=qfield.fibreflow.app
QFIELDCLOUD_VPS_HOST=100.96.203.105
QFIELDCLOUD_VPS_USER=velo
QFIELDCLOUD_VPS_PASSWORD=2025

# CRITICAL: CSRF protection (space-separated)
CSRF_TRUSTED_ORIGINS=https://qfield.fibreflow.app http://100.96.203.105:8082

# Worker scaling
QFIELDCLOUD_WORKER_REPLICAS=8

# Database
POSTGRES_DB=qfieldcloud_db
POSTGRES_USER=qfieldcloud_db_admin
POSTGRES_PASSWORD=[set in .env]
```

### Config Files
- `.env` - All environment variables
- `docker-compose.yml` - Base service definitions
- `docker-compose.override.yml` - VF Server customizations

## Common Operations

### Development
```bash
# SSH to VF Server
ssh velo@100.96.203.105  # password: 2025

# Check status
cd /opt/qfieldcloud
docker compose ps

# View logs
docker compose logs app --tail=100

# Restart service
docker compose restart app
```

### Deployment
```bash
# Deploy from Claude Code
cd .claude/skills/qfieldcloud
./scripts/deploy.py --branch master --migrate

# Manual deployment on VF Server
ssh velo@100.96.203.105
cd /opt/qfieldcloud
git pull origin master
docker compose build app
docker compose up -d app
docker compose exec app python manage.py migrate
```

### Rollback
```bash
# On VF Server
cd /opt/qfieldcloud
git log --oneline -10  # Find previous commit
git checkout <commit-hash>
docker compose build app
docker compose restart app
```

## Known Gotchas

### Issue 1: CSRF 403 Forbidden Errors (MOST COMMON)
**Problem**: "CSRF verification failed. Request aborted" when uploading projects
**Root Cause**: Django CSRF protection not configured for Cloudflare Tunnel domain
**Solution**:
```bash
# On VF Server
ssh velo@100.96.203.105
cd /opt/qfieldcloud
grep CSRF_TRUSTED_ORIGINS .env
# Should contain: https://qfield.fibreflow.app http://100.96.203.105:8082

# If missing, add it and restart
echo 'CSRF_TRUSTED_ORIGINS=https://qfield.fibreflow.app http://100.96.203.105:8082' >> .env
docker compose restart app
```
**Reference**: `.claude/skills/qfieldcloud/MIGRATION_COMPLETE.md` section 5

### Issue 2: Sync Fails Silently (Workers Not Running)
**Problem**: QField connects, sync appears to start, but never completes
**Root Cause**: worker_wrapper containers not running or can't access Docker socket
**Solution**:
```bash
# Quick diagnostic
.claude/skills/qfieldcloud/scripts/sync_diagnostic.py

# Manual check
ssh velo@100.96.203.105
docker ps | grep worker_wrapper  # Should show 8 containers

# Restart workers
cd /opt/qfieldcloud
docker compose restart worker_wrapper
```
**Reference**: skill.md:172-210

### Issue 3: Project Upload Fails ("Failed" State Immediately)
**Problem**: Files upload successfully but jobs fail, projects don't appear in QField
**Root Cause**: qfieldcloud-qgis Docker image missing (2.7GB image required for GIS processing)
**Solution**:
```bash
# Verify QGIS image
ssh velo@100.96.203.105
docker images | grep qgis
# Should show: qfieldcloud-qgis:latest (2.7GB)

# Rebuild if missing
cd /opt/qfieldcloud
docker compose build qgis
docker compose restart worker_wrapper
```
**Reference**: skill.md:247-262

### Issue 4: 502 Bad Gateway on qfield.fibreflow.app
**Problem**: Public URL returns 502, but direct server access works
**Root Cause**: Cloudflare Tunnel down or nginx container not running
**Solution**:
```bash
# Test direct access (should work)
curl -I http://100.96.203.105:8082 -H "Host: qfield.fibreflow.app"

# Check Cloudflare Tunnel
ssh velo@100.96.203.105
ps aux | grep cloudflared | grep -v grep
# Expected: cloudflared tunnel run (tunnel ID: 0bf9e4fa-f650-498c-bd23-def05abe5aaf)

# Restart tunnel if needed
sudo systemctl restart cloudflared
```
**Reference**: skill.md:288-311

## Testing Strategy

### Unit Tests
- Location: QFieldCloud upstream repository (not in FibreFlow)
- Coverage requirement: N/A (third-party Django app)
- Key areas: API endpoints, job processing, sync logic

### Integration Tests
- Location: `.claude/skills/qfieldcloud/scripts/sync_diagnostic.py`
- External dependencies: Real Docker containers, PostgreSQL, MinIO
- Key scenarios:
  - Worker health check
  - Job queue processing
  - Project upload → sync → download cycle

### E2E Tests
- Location: Manual testing with QField mobile app
- Tool: QField app on Android/iOS
- Critical user flows:
  1. Login to qfield.fibreflow.app
  2. Create QGIS project in desktop
  3. Upload project to QFieldCloud
  4. Sync project to QField mobile app
  5. Collect field data
  6. Sync changes back to cloud
  7. Download changes in QGIS desktop

## Monitoring & Alerts

### Health Checks
- Endpoint: `https://qfield.fibreflow.app/api/v1/status/`
- Expected response: `{"status": "ok", "version": "..."}`
- Script: `.claude/skills/qfieldcloud/scripts/health.py --verbose`

### Key Metrics
- **Worker count**: `docker ps | grep worker_wrapper | wc -l` (should be 8)
- **Queue depth**: Jobs in pending/queued state (good: <5, warning: 5-10, critical: >10)
- **Success rate**: finished / (finished + failed) jobs (target: >90%)
- **Job duration**: Average time to process (target: <2 minutes)
- **Disk usage**: `/var/lib/docker/volumes/` (alert if >80%)

### Logs
- Location: Docker logs via `docker compose logs [service]`
- Key log patterns:
  - `ERROR` - Application errors
  - `CSRF verification failed` - CSRF misconfiguration
  - `ConnectionRefusedError` - Database or storage connectivity
  - `Job.*failed` - Background job failures

### Automated Monitoring (VF Server)
- **Cron jobs**: Every 5 minutes - worker health, queue depth
- **Self-healing**: Auto-restart workers if crashed
- **Log files**: `/var/log/qfieldcloud/queue_metrics.log` (CSV format)

## Breaking Changes History

| Date | Change | Migration Required | Reference |
|------|--------|-------------------|-----------|
| 2026-01-08 | Migrated from Hostinger to VF Server | Yes - CSRF config, worker scaling | MIGRATION_COMPLETE.md |
| 2026-01-10 | Fixed CSRF 403 errors | Yes - Add CSRF_TRUSTED_ORIGINS | MIGRATION_COMPLETE.md section 5 |
| 2026-01-10 | Scaled workers 4→8 | No - Config change only | skill.md:512-536 |

## Related Documentation

- [QFieldCloud Skill Documentation](.claude/skills/qfieldcloud/skill.md)
- [Migration Summary](.claude/skills/qfieldcloud/MIGRATION_COMPLETE.md)
- [VF Server Setup](VF_SERVER_PRODUCTION_SETUP.md)
- [Infrastructure Strategy](docs/INFRASTRUCTURE_RESILIENCE_STRATEGY.md)

## Contact

**Primary Owner**: Louis
**Team**: FibreFlow Infrastructure
**Deployment**: VF Server (100.96.203.105)
