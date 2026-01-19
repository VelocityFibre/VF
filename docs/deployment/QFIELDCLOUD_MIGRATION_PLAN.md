# QFieldCloud Migration Plan - Hostinger VPS to VF Server

**Status**: 🟡 Ready for Execution
**Priority**: 🔴 CRITICAL (Disk space: 83% full, only 18GB remaining)
**Created**: 2025-12-22
**Estimated Time**: 8 hours (over 2 days)
**Estimated Downtime**: 2-4 hours

---

## Executive Summary

**Current State**: QFieldCloud running on Hostinger VPS (72.61.166.168) with critical disk space shortage
**Target State**: QFieldCloud on VF Server (100.96.203.105) with 900GB free space
**Cost Savings**: $240-360/year
**Performance Gain**: 15x RAM, 50x disk space

---

## Current Deployment Analysis

### Hostinger VPS (srv1083126.hstgr.cloud - 72.61.166.168)

**Resources**:
- **Disk**: 96GB total, 79GB used (83% full), **18GB free** 🔴
- **Docker Storage**: 84GB (almost entire disk)
- **Memory**: 8GB total, 4GB used
- **OS**: Ubuntu 24.04.3 LTS
- **Uptime**: 58 days

**Deployment**:
- **Location**: `/opt/qfieldcloud` (567MB source)
- **Production Stack**: 13 containers
- **Test Stack**: 5 containers
- **Docker Volumes**: 26 volumes (~40GB data)
- **URL**: https://qfield.fibreflow.app (⚠️ DNS not resolving)

**Production Containers**:
```
qfieldcloud-app-1              # Django API
qfieldcloud-db-1               # PostgreSQL :5433
qfieldcloud-nginx-1            # Reverse proxy
qfieldcloud-worker_wrapper-1   # GDAL worker #1
qfieldcloud-worker_wrapper-2   # GDAL worker #2
qfieldcloud-worker_wrapper-3   # GDAL worker #3
qfieldcloud-worker_wrapper-4   # GDAL worker #4
qfieldcloud-minio-1            # S3 storage :8009/:8010
qfieldcloud-memcached-1        # Caching
qfieldcloud-webdav-1           # File sync
qfieldcloud-smtp4dev-1         # Email testing
qfieldcloud-certbot-1          # SSL certificates
qfieldcloud-ofelia-1           # Cron scheduler
```

**Critical Issues**:
1. 🔴 Disk 83% full - risk of service crash
2. 🔴 Domain resolution failing (qfield.fibreflow.app)
3. ⚠️ Running production + test environments (resource competition)
4. ⚠️ Limited RAM for 23 containers

---

## Target Deployment on VF Server

### VF Server (velo-server - 100.96.203.105)

**Resources**:
- **Disk**: 984GB total, 34GB used (4%), **900GB free** ✅
- **Storage**: NVMe (/srv/data) - high performance
- **Memory**: 123GB total, 10GB used, 112GB free ✅
- **OS**: Ubuntu 24.04.3 LTS
- **Network**: Tailscale + Cloudflare Tunnel
- **Cost**: $0 (owned hardware)

**Installation Location**:
```
/srv/data/apps/qfieldcloud/
├── source/                      # QFieldCloud source code (Git clone)
│   ├── docker-compose.yml       # Production stack definition
│   ├── .env                     # Environment configuration
│   ├── conf/                    # Nginx, SSL, configs
│   ├── docker-app/              # Django app
│   └── ...
├── backups/                     # Database backups
│   ├── qfield_db_backup_20251222.sql
│   └── weekly_backups/
├── logs/                        # Application logs
└── data/                        # Persistent data (optional)
```

**Docker Volumes** (managed by Docker):
```
/var/lib/docker/volumes/
├── qfieldcloud_db_data/         # PostgreSQL database
├── qfieldcloud_minio_data1/     # MinIO S3 files
├── qfieldcloud_media_volume/    # Django media files
├── qfieldcloud_static_volume/   # Static assets
└── qfieldcloud_certbot_www/     # SSL certificates
```

**Why `/srv/data/apps/qfieldcloud/`?**

1. ✅ **Consistent with FibreFlow** - Already at `/srv/data/apps/fibreflow/`
2. ✅ **NVMe Storage** - Fast disk performance for database/file operations
3. ✅ **900GB Available** - Room for years of growth
4. ✅ **Proper Permissions** - `/srv/data` owned by velocity-team group
5. ✅ **Backup-Friendly** - Easy to rsync entire `/srv/data/apps/` directory
6. ✅ **Integration-Ready** - Same server as FibreFlow for future sync features

---

## Port Mapping

| Service | Current (Hostinger) | VF Server | Notes |
|---------|-------------------|-----------|-------|
| QField API (Django) | Internal 8000 | Internal 8000 | Via Cloudflare Tunnel |
| PostgreSQL | 5433 | 5433 | External access for backups |
| MinIO API | 8009 | 8009 | S3-compatible storage |
| MinIO Console | 8010 | 8010 | Admin UI |
| Nginx HTTP | 80 | N/A | Use Cloudflare Tunnel instead |
| Nginx HTTPS | 443 | N/A | Use Cloudflare Tunnel instead |

**Public Access**:
- **URL**: https://qfield.fibreflow.app
- **Method**: Cloudflare Tunnel (vf-downloads)
- **Backend**: http://localhost:8000 (QField Django app)
- **No exposed ports** - All traffic via tunnel (more secure)

---

## Migration Plan - Detailed Steps

### Phase 1: Preparation & Backup (30 min)

**On Hostinger VPS**:

```bash
# SSH to Hostinger
ssh -i ~/.ssh/qfield_vps root@72.61.166.168

# Create backup directory
mkdir -p /tmp/qfield_migration
cd /tmp/qfield_migration

# 1. Backup PostgreSQL database
docker exec qfieldcloud-db-1 pg_dump -U qfieldcloud qfieldcloud \
  > qfield_db_backup_$(date +%Y%m%d_%H%M%S).sql

# Check backup size
ls -lh qfield_db_backup*.sql

# 2. Archive configuration files
cd /opt/qfieldcloud
tar -czf /tmp/qfield_migration/qfield_config_$(date +%Y%m%d).tar.gz \
  docker-compose.yml \
  docker-compose.override.local.yml \
  .env \
  conf/ \
  docker-app/

# 3. Export MinIO data (if large, may skip and use volume migration)
# Check MinIO data size first:
docker exec qfieldcloud-minio-1 du -sh /data

# If < 10GB, export:
docker exec qfieldcloud-minio-1 tar -czf /tmp/minio_data.tar.gz /data

# 4. Document current state
docker-compose ps > /tmp/qfield_migration/containers_state.txt
docker volume ls > /tmp/qfield_migration/volumes_state.txt
docker images > /tmp/qfield_migration/images_state.txt

# 5. Final archive
cd /tmp/qfield_migration
tar -czf qfield_complete_backup_$(date +%Y%m%d).tar.gz ./*

# Check total backup size
du -sh qfield_complete_backup*.tar.gz
```

**Safety Check**:
- [ ] Database backup exists and is > 0 bytes
- [ ] Config archive created successfully
- [ ] Can read backup files (not corrupted)

---

### Phase 2: Transfer to VF Server (20-60 min)

**From your local machine** (or from Hostinger VPS):

```bash
# Option A: Transfer from Hostinger to VF Server directly
ssh -i ~/.ssh/qfield_vps root@72.61.166.168

# Install rsync if not present
apt install rsync -y

# Transfer to VF Server via rsync (resumable)
rsync -avz --progress -e "ssh" \
  /tmp/qfield_migration/ \
  louis@100.96.203.105:/srv/data/apps/qfield_migration/

# OR Option B: Download to local, then upload to VF Server
# (Better if connection is flaky)

# Download from Hostinger to local
scp -i ~/.ssh/qfield_vps \
  root@72.61.166.168:/tmp/qfield_migration/qfield_complete_backup*.tar.gz \
  ~/VF/vps/hostinger/qfield/backups/

# Upload to VF Server
scp ~/VF/vps/hostinger/qfield/backups/qfield_complete_backup*.tar.gz \
  louis@100.96.203.105:/srv/data/apps/
```

**Verify Transfer**:
```bash
# On VF Server
ssh louis@100.96.203.105
ls -lh /srv/data/apps/qfield_complete_backup*.tar.gz
```

---

### Phase 3: VF Server Setup (45 min)

**On VF Server**:

```bash
# SSH to VF Server
ssh louis@100.96.203.105

# 1. Create application directory
sudo mkdir -p /srv/data/apps/qfieldcloud/{source,backups,logs}
sudo chown -R louis:velocity-team /srv/data/apps/qfieldcloud
sudo chmod -R 775 /srv/data/apps/qfieldcloud

# 2. Extract backup
cd /srv/data/apps
tar -xzf qfield_complete_backup_*.tar.gz -C qfieldcloud/backups/

# 3. Clone QFieldCloud source (if needed - or use existing from Hostinger)
cd /srv/data/apps/qfieldcloud/source
git clone https://github.com/opengisch/qfieldcloud.git .

# OR extract from backup:
cd /srv/data/apps/qfieldcloud/source
tar -xzf ../backups/qfield_config_*.tar.gz

# 4. Configure environment
cd /srv/data/apps/qfieldcloud/source
cp ../backups/.env .env

# Edit .env for VF Server
nano .env

# Update these values:
# QFIELDCLOUD_HOST=qfield.fibreflow.app
# DJANGO_ALLOWED_HOSTS="qfield.fibreflow.app velo-server 100.96.203.105 app"
#
# Keep these ports (no conflicts on VF Server):
# HOST_POSTGRES_PORT=5433
# MINIO_API_PORT=8009
# MINIO_BROWSER_PORT=8010

# 5. Create Docker volumes (empty - will restore data)
docker volume create qfieldcloud_db_data
docker volume create qfieldcloud_minio_data1
docker volume create qfieldcloud_minio_data2
docker volume create qfieldcloud_minio_data3
docker volume create qfieldcloud_media_volume
docker volume create qfieldcloud_static_volume

# 6. Start database service only
docker-compose up -d db

# Wait for DB to initialize
sleep 10

# 7. Restore database
cat /srv/data/apps/qfieldcloud/backups/qfield_db_backup*.sql | \
  docker exec -i qfieldcloud-db-1 psql -U qfieldcloud qfieldcloud

# Verify database restoration
docker exec qfieldcloud-db-1 psql -U qfieldcloud -c \
  "SELECT COUNT(*) FROM django_content_type;"

# 8. Start MinIO and restore files
docker-compose up -d minio
sleep 5

# Restore MinIO data (if backed up)
# docker exec -i qfieldcloud-minio-1 tar -xzf - < /srv/data/apps/qfieldcloud/backups/minio_data.tar.gz

# 9. Start remaining services
docker-compose up -d

# 10. Check all services
docker-compose ps

# 11. View logs
docker-compose logs -f app
```

**Health Checks**:
```bash
# Database connectivity
docker exec qfieldcloud-db-1 psql -U qfieldcloud -c "SELECT version();"

# Django app
docker exec qfieldcloud-app-1 python manage.py check

# MinIO
docker exec qfieldcloud-minio-1 mc admin info local

# Worker processes
docker-compose logs worker_wrapper | grep -i "ready"
```

---

### Phase 4: Cloudflare Tunnel Configuration (30 min)

**On VF Server**:

```bash
# 1. Edit Cloudflare Tunnel config
ssh louis@100.96.203.105
nano ~/.cloudflared/config.yml

# Add QFieldCloud ingress (BEFORE the catch-all rule):
#
# ingress:
#   # QFieldCloud
#   - hostname: qfield.fibreflow.app
#     service: http://localhost:8000
#
#   # Existing FibreFlow routes
#   - hostname: vf.fibreflow.app
#     path: /downloads
#     service: http://localhost:3005
#
#   - hostname: support.fibreflow.app
#     service: http://localhost:3005
#
#   # Catch-all (must be last)
#   - service: http_status:404

# Save and exit

# 2. Restart tunnel
pkill cloudflared
sleep 2
nohup ~/cloudflared tunnel run vf-downloads > /tmp/cloudflared.log 2>&1 &

# 3. Wait for tunnel to connect
sleep 10
tail -30 /tmp/cloudflared.log | grep -E "(Registered|connection|qfield)"

# 4. Create DNS CNAME in Cloudflare
~/cloudflared tunnel route dns vf-downloads qfield.fibreflow.app
```

**On Cloudflare Dashboard** (https://dash.cloudflare.com):

1. Navigate to: fibreflow.app → DNS → Records
2. Verify CNAME exists:
   - **Type**: CNAME
   - **Name**: qfield
   - **Target**: vf-downloads.cfargotunnel.com
   - **Proxy**: ✅ Proxied (orange cloud)

---

### Phase 5: Testing & Validation (20 min)

**Functional Tests**:

```bash
# 1. Internal API test (from VF Server)
curl http://localhost:8000/api/v1/health

# 2. Database queries
docker exec qfieldcloud-db-1 psql -U qfieldcloud -c \
  "SELECT COUNT(*) FROM auth_user;"

docker exec qfieldcloud-db-1 psql -U qfieldcloud -c \
  "SELECT username, email FROM auth_user LIMIT 5;"

# 3. Public URL test (from any machine)
curl -I https://qfield.fibreflow.app

# Expected: HTTP 200 OK

# 4. Worker health
docker-compose logs worker_wrapper | tail -50 | grep -i error

# 5. MinIO accessibility
curl http://100.96.203.105:8009/minio/health/live

# 6. Full web UI test
# Open browser: https://qfield.fibreflow.app
# Login with admin credentials
# Upload test project
# Sync with QField mobile app
```

**Performance Benchmarks**:

```bash
# Database query speed
docker exec qfieldcloud-db-1 psql -U qfieldcloud -c \
  "EXPLAIN ANALYZE SELECT * FROM qfieldcloud_project LIMIT 100;"

# API response time
time curl -s https://qfield.fibreflow.app/api/v1/projects/ > /dev/null

# Disk I/O
docker exec qfieldcloud-db-1 bash -c \
  "dd if=/dev/zero of=/tmp/test bs=1M count=100 && rm /tmp/test"
```

**Validation Checklist**:
- [ ] Web UI loads at https://qfield.fibreflow.app
- [ ] Can login with existing credentials
- [ ] Projects visible in dashboard
- [ ] Can create new project
- [ ] QField mobile app can sync
- [ ] File uploads work (via web or mobile)
- [ ] Workers processing successfully
- [ ] No errors in logs (critical only)
- [ ] Database queries fast (<100ms)

---

### Phase 6: Parallel Operation Period (7 days)

**Purpose**: Ensure VF Server deployment is stable before decommissioning Hostinger

**Monitoring** (both servers):

```bash
# Daily health check - VF Server
ssh louis@100.96.203.105
cd /srv/data/apps/qfieldcloud/source
docker-compose ps
docker-compose logs --since 24h | grep -i error

# Daily health check - Hostinger (keep running)
ssh -i ~/.ssh/qfield_vps root@72.61.166.168
cd /opt/qfieldcloud
docker-compose ps

# Compare database row counts
# VF Server:
docker exec qfieldcloud-db-1 psql -U qfieldcloud -c \
  "SELECT COUNT(*) FROM qfieldcloud_project;"

# Hostinger:
docker exec qfieldcloud-db-1 psql -U qfieldcloud -c \
  "SELECT COUNT(*) FROM qfieldcloud_project;"

# Should be identical (or VF Server may have more if users are active)
```

**During this period**:
- ✅ All new activity happens on VF Server (via qfield.fibreflow.app)
- ✅ Hostinger stays online as read-only backup
- ✅ Monitor disk usage on both servers
- ✅ Check for any errors or issues
- ✅ Validate with actual users

---

### Phase 7: Decommission Hostinger VPS (30 min)

**After 7 days of successful operation**:

```bash
# 1. Final backup from Hostinger
ssh -i ~/.ssh/qfield_vps root@72.61.166.168

cd /opt/qfieldcloud

# Create final archive
docker exec qfieldcloud-db-1 pg_dump -U qfieldcloud qfieldcloud \
  > /tmp/qfield_hostinger_final_backup_$(date +%Y%m%d).sql

tar -czf /tmp/qfield_hostinger_final.tar.gz \
  /opt/qfieldcloud/ \
  /tmp/qfield_hostinger_final_backup*.sql \
  /var/lib/docker/volumes/qfieldcloud_*

# Download to local machine
exit
scp -i ~/.ssh/qfield_vps \
  root@72.61.166.168:/tmp/qfield_hostinger_final.tar.gz \
  ~/VF/vps/hostinger/qfield/backups/archive/

# 2. Stop all services on Hostinger
ssh -i ~/.ssh/qfield_vps root@72.61.166.168
cd /opt/qfieldcloud
docker-compose down

# 3. Remove test environment (cleanup before cancellation)
docker stop $(docker ps -a | grep qfieldcloud-test | awk '{print $1}')
docker rm $(docker ps -a | grep qfieldcloud-test | awk '{print $1}')
docker volume rm $(docker volume ls | grep qfieldcloud-test | awk '{print $2}')

# 4. Clean up Docker (optional - if canceling VPS)
docker system prune -a --volumes

# 5. Cancel Hostinger VPS subscription
# Visit: https://hpanel.hostinger.com/vps/1083126/settings
# Cancel subscription (saves $20-30/month)
```

---

## Rollback Plan

**If migration fails or issues found**:

```bash
# 1. Restore DNS to Hostinger (immediate)
# In Cloudflare dashboard:
# - Remove CNAME: qfield.fibreflow.app → vf-downloads.cfargotunnel.com
# - Add A record: qfield.fibreflow.app → 72.61.166.168

# 2. Restart Hostinger services
ssh -i ~/.ssh/qfield_vps root@72.61.166.168
cd /opt/qfieldcloud
docker-compose up -d

# 3. Verify Hostinger is serving
curl -I https://qfield.fibreflow.app
# Should return HTTP 200

# Total rollback time: <10 minutes
```

---

## Cost-Benefit Analysis

### Costs

| Item | Amount |
|------|--------|
| **Migration Time** | 8 hours (spread over 2 days) |
| **Downtime** | 2-4 hours (scheduled off-peak) |
| **Risk** | Medium (mitigated with backups) |

### Benefits

| Benefit | Value | Timeline |
|---------|-------|----------|
| **Monthly Savings** | $20-30 USD | Immediate |
| **Annual Savings** | $240-360 USD | 12 months |
| **Disk Space Gained** | 882GB (18GB → 900GB) | Immediate |
| **RAM Gained** | 115GB (8GB → 123GB) | Immediate |
| **Performance Improvement** | 15x faster | Immediate |
| **Integration with FibreFlow** | Better sync | Long-term |
| **Scalability** | Years of growth | Long-term |

**ROI**: Positive in first month (time saved > migration time)

---

## File Structure Reference

### Hostinger VPS (Before Migration)

```
/opt/qfieldcloud/
├── docker-compose.yml
├── docker-compose.override.local.yml
├── .env
├── conf/
│   ├── nginx/
│   │   ├── config.d/
│   │   ├── certs/
│   │   └── dhparams/
│   └── certbot/
├── docker-app/
│   └── qfieldcloud/
└── ...

/var/lib/docker/volumes/
├── qfieldcloud_db_data/
├── qfieldcloud_minio_data1/
├── qfieldcloud_media_volume/
└── ...
```

### VF Server (After Migration)

```
/srv/data/apps/qfieldcloud/
├── source/                          # Main application
│   ├── docker-compose.yml
│   ├── .env
│   ├── conf/
│   ├── docker-app/
│   └── ...
├── backups/                         # Database backups
│   ├── qfield_db_backup_20251222.sql
│   ├── weekly/
│   └── archive/
└── logs/                            # Application logs
    ├── nginx/
    ├── django/
    └── workers/

/var/lib/docker/volumes/
├── qfieldcloud_db_data/             # PostgreSQL data
├── qfieldcloud_minio_data1/         # S3 storage
├── qfieldcloud_media_volume/        # Media files
└── ...

/home/louis/.cloudflared/
└── config.yml                       # Tunnel configuration
```

---

## Environment Variables Reference

### Key .env Changes for VF Server

```bash
# OLD (Hostinger):
QFIELDCLOUD_HOST=srv1083126.hstgr.cloud
DJANGO_ALLOWED_HOSTS="srv1083126.hstgr.cloud 72.61.166.168 qfield.fibreflow.app app"

# NEW (VF Server):
QFIELDCLOUD_HOST=qfield.fibreflow.app
DJANGO_ALLOWED_HOSTS="qfield.fibreflow.app velo-server 100.96.203.105 app nginx"

# Ports (unchanged - no conflicts):
HOST_POSTGRES_PORT=5433
MINIO_API_PORT=8009
MINIO_BROWSER_PORT=8010
WEB_HTTP_PORT=80
WEB_HTTPS_PORT=443
DJANGO_DEV_PORT=8011

# Database (internal - unchanged):
POSTGRES_HOST=db
POSTGRES_PORT=5432
```

---

## Monitoring & Maintenance

### Daily Health Checks (First Week)

```bash
# Quick status script
cat > /srv/data/apps/qfieldcloud/check_health.sh << 'EOF'
#!/bin/bash
echo "=== QFieldCloud Health Check ==="
echo "Date: $(date)"
echo ""

echo "Container Status:"
cd /srv/data/apps/qfieldcloud/source
docker-compose ps

echo ""
echo "Disk Usage:"
df -h /srv/data | grep -v Filesystem

echo ""
echo "Database Connections:"
docker exec qfieldcloud-db-1 psql -U qfieldcloud -c \
  "SELECT count(*) FROM pg_stat_activity;"

echo ""
echo "Recent Errors (last hour):"
docker-compose logs --since 1h | grep -i error | wc -l

echo ""
echo "Public URL Status:"
curl -s -o /dev/null -w "HTTP %{http_code}\n" https://qfield.fibreflow.app
EOF

chmod +x /srv/data/apps/qfieldcloud/check_health.sh

# Run daily
./check_health.sh
```

### Weekly Backup Script

```bash
cat > /srv/data/apps/qfieldcloud/weekly_backup.sh << 'EOF'
#!/bin/bash
BACKUP_DIR="/srv/data/apps/qfieldcloud/backups/weekly"
DATE=$(date +%Y%m%d_%H%M%S)

mkdir -p $BACKUP_DIR

# Database backup
docker exec qfieldcloud-db-1 pg_dump -U qfieldcloud qfieldcloud \
  > $BACKUP_DIR/qfield_db_$DATE.sql

# Compress
gzip $BACKUP_DIR/qfield_db_$DATE.sql

# Keep only last 4 weeks
find $BACKUP_DIR -name "*.sql.gz" -mtime +28 -delete

echo "Backup complete: $BACKUP_DIR/qfield_db_$DATE.sql.gz"
EOF

chmod +x /srv/data/apps/qfieldcloud/weekly_backup.sh

# Add to crontab (runs every Sunday at 2 AM)
(crontab -l 2>/dev/null; echo "0 2 * * 0 /srv/data/apps/qfieldcloud/weekly_backup.sh") | crontab -
```

---

## Success Criteria

Migration is successful when:

- [ ] All containers running on VF Server (13 production containers)
- [ ] Database fully restored with all data intact
- [ ] Public URL working: https://qfield.fibreflow.app
- [ ] QField mobile app can sync successfully
- [ ] File uploads/downloads working
- [ ] Worker processes handling sync jobs
- [ ] No critical errors in logs
- [ ] Performance meets or exceeds Hostinger (response time <500ms)
- [ ] SSL certificate valid
- [ ] Existing users can login with credentials
- [ ] Projects and data accessible
- [ ] Parallel operation successful for 7 days
- [ ] Hostinger VPS decommissioned
- [ ] $20-30/month cost savings realized

---

## Support & Troubleshooting

### Common Issues

**1. DNS not resolving (qfield.fibreflow.app)**

```bash
# Check Cloudflare Tunnel status
ssh louis@100.96.203.105
tail -50 /tmp/cloudflared.log | grep qfield

# Verify DNS record
dig qfield.fibreflow.app

# Should show:
# qfield.fibreflow.app CNAME vf-downloads.cfargotunnel.com
```

**2. Database connection errors**

```bash
# Check PostgreSQL logs
docker logs qfieldcloud-db-1 | tail -50

# Test connection
docker exec qfieldcloud-db-1 psql -U qfieldcloud -c "SELECT 1;"

# Restart if needed
docker-compose restart db
```

**3. Worker not processing jobs**

```bash
# Check worker logs
docker-compose logs worker_wrapper | grep -i error

# Worker typically fails due to GDAL dependencies
# Rebuild if needed:
docker-compose up -d --build worker_wrapper
```

**4. Out of disk space (even on VF Server)**

```bash
# Clean Docker artifacts
docker system prune -a --volumes

# Check volume sizes
docker system df -v

# Monitor disk usage
df -h /srv/data
```

### Getting Help

**Documentation**:
- This migration plan: `/home/louisdup/Agents/claude/docs/deployment/QFIELDCLOUD_MIGRATION_PLAN.md`
- QField local docs: `~/VF/vps/hostinger/qfield/README.md`
- FibreFlow CLAUDE.md: `/home/louisdup/Agents/claude/CLAUDE.md`

**Contact**:
- QFieldCloud community: https://github.com/opengisch/qfieldcloud/discussions
- VF Server admin: louis@100.96.203.105 (SSH)

---

## Timeline Recommendation

| Day | Activity | Duration | Owner |
|-----|----------|----------|-------|
| **Day 1 AM** | Backup & Transfer | 2 hours | You + Claude |
| **Day 1 PM** | VF Server Setup | 2 hours | You + Claude |
| **Day 2 AM** | DNS/Tunnel Config | 1 hour | You + Claude |
| **Day 2 PM** | Testing & Validation | 2 hours | You + Team |
| **Day 3-9** | Parallel Operation | Daily checks | You |
| **Day 10** | Decommission Hostinger | 30 min | You |

**Total hands-on time**: 8 hours (spread over 2 days)
**Best timing**: Weekend or after-hours to minimize user impact

---

## Next Steps

1. ✅ Review this migration plan
2. ✅ Schedule 2-day migration window
3. ✅ Notify QFieldCloud users of upcoming migration
4. ✅ Execute Phase 1 (Backup) - can do now without downtime
5. ✅ Execute Phases 2-5 during scheduled window
6. ✅ Monitor for 7 days
7. ✅ Decommission Hostinger and celebrate savings! 🎉

---

**Document Version**: 1.0
**Last Updated**: 2025-12-22
**Author**: Claude + Louis
**Status**: Ready for Execution
