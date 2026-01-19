# QFieldCloud Server Migration Optimization Plan
**Created**: 2026-01-08
**Status**: IN PROGRESS
**Current Server**: 72.61.166.168 (96GB disk, 8GB RAM)
**Issue**: Upload flooding due to insufficient worker capacity and large project sizes

## Executive Summary
Field workers are experiencing upload failures due to system flooding. The VF_FT_Civil&Optical_Master_cloud project contains 40+ GeoPackage files (~100MB per sync), and with only 4 workers handling 15-25 second operations, the system saturates when 10+ workers sync simultaneously.

## Current Critical Metrics
- **Disk Usage**: 86% (82GB/96GB) 🔴 CRITICAL
- **Workers**: 4 (handling ~10-16 syncs/minute) ❌ Under-provisioned
- **Project Size**: ~100MB with 40+ files
- **Sync Duration**: 15-25 seconds per operation
- **Rate Limiting**: DISABLED 🔴

## Pre-Migration Tasks (PRIORITY 1 - DO FIRST!)

### 1. Clean Disk Space ✅ CRITICAL
**Timeline**: Immediate (20 minutes)
**Impact**: Free 15-20GB, reduce migration size by 20%

```bash
# Connect to server
ssh root@72.61.166.168

# Remove Docker artifacts (10-15GB)
docker system prune -af --volumes

# Clean old logs (2-3GB)
find /var/log -type f -name "*.log" -mtime +30 -delete
rm -rf /opt/qfieldcloud/logs/*.log.*

# Remove orphaned job data
docker exec qfieldcloud-db-1 psql -U qfieldcloud_db_admin -d qfieldcloud_db -c \
  "DELETE FROM core_job WHERE created_at < NOW() - INTERVAL '30 days';"

# Clean docker logs
truncate -s 0 /var/lib/docker/containers/*/*-json.log
```

### 2. Optimize Database
**Timeline**: 30 minutes
**Impact**: Faster queries, smaller backup, improved performance

```bash
# Backup first
docker exec qfieldcloud-db-1 pg_dump -U qfieldcloud_db_admin qfieldcloud_db > /root/db_backup_$(date +%Y%m%d).sql

# Vacuum and analyze
docker exec qfieldcloud-db-1 psql -U qfieldcloud_db_admin -d qfieldcloud_db -c "VACUUM FULL ANALYZE;"

# Reindex
docker exec qfieldcloud-db-1 psql -U qfieldcloud_db_admin -d qfieldcloud_db -c "REINDEX DATABASE qfieldcloud_db;"

# Add performance indexes
docker exec qfieldcloud-db-1 psql -U qfieldcloud_db_admin -d qfieldcloud_db -c "
CREATE INDEX IF NOT EXISTS idx_job_status_created ON core_job(status, created_at);
CREATE INDEX IF NOT EXISTS idx_job_project_created ON core_job(project_id, created_at);
CREATE INDEX IF NOT EXISTS idx_job_type_status ON core_job(type, status);"
```

### 3. Archive Old Project Files
**Timeline**: 45 minutes
**Impact**: Reduce sync payload by 40-50%

```bash
# Navigate to files directory
cd /opt/qfieldcloud

# Find the main project directory
PROJECT_ID="063a1964-42fe-4fe8-9113-291fd5e00c3d"
cd /var/lib/docker/volumes/qfieldcloud_storage/_data/files/$PROJECT_ID

# List old files (November 2025 data)
ls -la | grep -E "(251125|261125|271125|201125|211125|241125)"

# Create archive directory
mkdir -p /root/qfield_archives/

# Archive November files
tar -czf /root/qfield_archives/november_2025_data.tar.gz \
  *251125*.gpkg *261125*.gpkg *271125*.gpkg \
  *201125*.gpkg *211125*.gpkg *241125*.gpkg

# Verify archive
tar -tzf /root/qfield_archives/november_2025_data.tar.gz | head -10

# Remove archived files (after verification)
# rm *251125*.gpkg *261125*.gpkg *271125*.gpkg
```

### 4. Document Current Configuration
**Timeline**: 15 minutes
**Impact**: Essential for rollback and migration reference

```bash
# Create backup directory
mkdir -p /root/qfield_migration_backup/

# Save configurations
cp /opt/qfieldcloud/.env /root/qfield_migration_backup/
cp /opt/qfieldcloud/docker-compose.yml /root/qfield_migration_backup/
cp /opt/qfieldcloud/docker-compose.override.yml /root/qfield_migration_backup/ 2>/dev/null

# Export docker images list
docker images | grep qfield > /root/qfield_migration_backup/docker_images.txt

# Save nginx configuration
docker exec qfieldcloud-nginx-1 cat /etc/nginx/nginx.conf > /root/qfield_migration_backup/nginx.conf

# Document current settings
cat > /root/qfield_migration_backup/current_status.txt << EOF
Migration Date: $(date)
Server: 72.61.166.168
Workers: 4
Database Size: $(docker exec qfieldcloud-db-1 psql -U qfieldcloud_db_admin -d qfieldcloud_db -t -c "SELECT pg_size_pretty(pg_database_size('qfieldcloud_db'));")
Disk Usage: $(df -h / | awk 'NR==2 {print $5}')
Docker Version: $(docker --version)
Containers: $(docker ps | wc -l)
EOF
```

### 5. Prepare Worker Configuration (Don't Apply Yet)
**Timeline**: 5 minutes
**Impact**: Ready for immediate scaling on new server

```bash
# Create new configuration (but don't apply)
cat > /root/qfield_migration_backup/new_server.env << 'EOF'
# Scaling configuration for new server
QFIELDCLOUD_WORKER_REPLICAS=8  # Increase from 4
QFIELDCLOUD_WORKER_MAX_JOBS=1000
QFIELDCLOUD_WORKER_TIMEOUT=120
QFIELDCLOUD_MAX_CONCURRENT_JOBS=16
POSTGRES_MAX_CONNECTIONS=200  # Increase from default 100

# Rate limiting (to enable on new server)
QFIELDCLOUD_RATE_LIMIT_ENABLED=true
QFIELDCLOUD_RATE_LIMIT_PER_PROJECT=5  # Max 5 syncs/minute per project
QFIELDCLOUD_RATE_LIMIT_PER_USER=2     # Max 2 syncs/minute per user
QFIELDCLOUD_QUEUE_MAX_DEPTH=20        # Max queue depth
EOF
```

## Migration Readiness Script

```bash
#!/bin/bash
# Save as: /root/migration_readiness.sh

echo "=========================================="
echo "QFieldCloud Migration Readiness Check"
echo "Date: $(date)"
echo "=========================================="

# 1. Disk usage check
DISK_USAGE=$(df / | awk 'NR==2 {print int($5)}')
if [ $DISK_USAGE -lt 70 ]; then
    echo "✅ Disk usage: ${DISK_USAGE}% (Ready)"
else
    echo "❌ Disk usage: ${DISK_USAGE}% (Clean up required!)"
fi

# 2. Database size
DB_SIZE=$(docker exec qfieldcloud-db-1 psql -U qfieldcloud_db_admin -d qfieldcloud_db -t -c \
  "SELECT pg_size_pretty(pg_database_size('qfieldcloud_db'));" 2>/dev/null | xargs)
echo "📊 Database size: $DB_SIZE"

# 3. Stuck jobs check
STUCK_JOBS=$(docker exec qfieldcloud-db-1 psql -U qfieldcloud_db_admin -d qfieldcloud_db -t -c \
  "SELECT COUNT(*) FROM core_job WHERE status IN ('pending','queued') AND created_at < NOW() - INTERVAL '1 day';" 2>/dev/null | xargs)
if [ "$STUCK_JOBS" = "0" ]; then
    echo "✅ No stuck jobs"
else
    echo "⚠️  Stuck jobs (>24h): $STUCK_JOBS"
fi

# 4. Container health
echo ""
echo "Container Status:"
docker ps --format "table {{.Names}}\t{{.Status}}" | grep qfield

# 5. Current queue depth
QUEUE=$(docker exec qfieldcloud-db-1 psql -U qfieldcloud_db_admin -d qfieldcloud_db -t -c \
  "SELECT COUNT(*) FROM core_job WHERE status IN ('pending','queued');" 2>/dev/null | xargs)
echo ""
echo "📈 Current queue depth: $QUEUE jobs"

# 6. Success rate (last 24h)
SUCCESS_RATE=$(docker exec qfieldcloud-db-1 psql -U qfieldcloud_db_admin -d qfieldcloud_db -t -c \
  "SELECT ROUND(100.0 * COUNT(CASE WHEN status = 'finished' THEN 1 END) / COUNT(*), 1)
   FROM core_job WHERE created_at > NOW() - INTERVAL '24 hours';" 2>/dev/null | xargs)
echo "📊 24h success rate: ${SUCCESS_RATE}%"

echo ""
echo "=========================================="
if [ $DISK_USAGE -lt 70 ] && [ "$STUCK_JOBS" = "0" ]; then
    echo "✅ READY FOR MIGRATION"
else
    echo "❌ ADDRESS ISSUES BEFORE MIGRATION"
fi
echo "=========================================="
```

## New Server Requirements

### Minimum Specifications
- **CPU**: 8 cores (2x current capacity)
- **RAM**: 16GB (2x current)
- **Storage**: 200GB SSD (2x current)
- **Network**: 1Gbps
- **OS**: Ubuntu 22.04 LTS
- **Docker**: Latest stable version

### Optimal Specifications
- **CPU**: 16 cores (for 8-12 workers)
- **RAM**: 32GB (better caching)
- **Storage**: 500GB NVMe SSD
- **Database**: Separate 100GB disk for PostgreSQL
- **Backup**: Additional storage for backups

## Post-Migration Tasks (On New Server)

### Phase 1 - Day 1 (Immediate)
1. Scale workers to 8: `QFIELDCLOUD_WORKER_REPLICAS=8`
2. Verify all services running
3. Test with limited users (5-10)
4. Monitor queue depth closely

### Phase 2 - Day 2-3 (Stabilization)
1. Enable rate limiting
2. Monitor performance metrics
3. Adjust worker count if needed
4. Full user testing

### Phase 3 - Week 1 (Optimization)
1. Consider project splitting for large projects
2. Implement monitoring alerts
3. Set up automated backups
4. Document new procedures

## Success Metrics
- Queue depth consistently <5
- Sync success rate >95%
- Average sync time <10 seconds
- Disk usage <70%
- No stuck jobs >1 hour old

## Rollback Plan
1. Keep old server running for 48 hours
2. Maintain DNS control for quick switch
3. Have database backup ready
4. Document all changes for reversal

## Contact Information
- QFieldCloud Support: support@opengis.ch
- Docker Registry: docker.io/opengisch/qfieldcloud-*
- GitHub: https://github.com/opengisch/qfieldcloud

## Notes
- VF_FT_Civil&Optical_Master_cloud project is the main bottleneck
- Consider splitting this project into regional sub-projects
- November 2025 data files can be archived (30% size reduction)
- Rate limiting essential to prevent future flooding

---
**Last Updated**: 2026-01-08
**Next Review**: Before migration
**Status**: Pre-migration optimization in progress