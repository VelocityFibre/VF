# QFieldCloud Application Rules

## Context
This file loads when working on QFieldCloud GIS synchronization platform.

## Technology Stack
- **Framework**: Django 4.2
- **Database**: PostgreSQL + PostGIS
- **Storage**: MinIO S3-compatible
- **Workers**: Celery (8 workers, scalable 4-12)
- **Container**: Docker Compose
- **Processing**: QGIS Server (2.7GB image)

## Infrastructure
- **Server**: VF Server (migrated from 72.61.166.168)
- **Port**: 8082 → https://qfield.fibreflow.app
- **Database Port**: 5433 (PostgreSQL/PostGIS)
- **Storage Ports**: 8009 (MinIO), 8010 (Console)
- **Location**: `/opt/qfieldcloud/` on VF Server

## Key Components
- **API**: REST API for mobile/desktop sync
- **Workers**: Process QGIS projects and field data
- **Storage**: MinIO for project files and photos
- **Database**: Spatial data with PostGIS extensions

## Deployment Process
```bash
# SSH to server
ssh louis@100.96.203.105

# Navigate to QFieldCloud
cd /opt/qfieldcloud

# Update and restart
sudo docker-compose pull
sudo docker-compose up -d

# Check status
sudo docker-compose ps
```

## Monitoring
```bash
# Health check
curl http://100.96.203.105:8082/health

# Worker status
ssh louis@100.96.203.105 'sudo docker-compose logs -f worker'

# Database connections
ssh louis@100.96.203.105 'sudo docker exec qfieldcloud_db_1 psql -U postgres -c "SELECT count(*) FROM pg_stat_activity;"'
```

## Known Issues & Solutions
1. **High memory usage**
   - Workers can scale 4-12 based on load
   - Monitor: `htop` shows 32GB RAM available

2. **CSRF token issues**
   - Fixed in production
   - See: `.claude/skills/qfieldcloud/CSRF_LESSONS_LEARNED.md`

3. **Photo compression**
   - Implemented automatic compression
   - Script: `scripts/qfield_compress_photos.py`

## Capacity
- Concurrent uploads: 50+
- Storage: 500GB NVMe available
- Processing: 8 CPU cores
- RAM: 32GB total

## Incident Response
Check incident log first:
`.claude/skills/qfieldcloud/INCIDENT_LOG.md`

Common fixes:
```bash
# Restart workers if stuck
sudo docker-compose restart worker

# Clear stuck jobs
sudo docker exec qfieldcloud_redis_1 redis-cli FLUSHDB

# Check disk space
df -h /srv/data/qfieldcloud
```

## Testing
- Unit tests: Django test suite
- Integration: Test with QGIS desktop
- Mobile: Test with QField app
- Load: Can handle 50+ concurrent users

## Skills & Scripts
- Main skill: `.claude/skills/qfieldcloud/skill.md`
- Quick fixes: `.claude/skills/qfieldcloud/scripts/quick_fix.py`
- Status check: `.claude/skills/qfieldcloud/scripts/status.py`