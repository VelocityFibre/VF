# QFieldCloud Critical Incident - 2026-01-12
## Missing QGIS Docker Image After Migration

### Incident Timeline

**09:00 SAST** - Luke reports authentication error
- Error: `[HTTP/401] https://srv1083126.hstgr.cloud/api/v1/jobs/314d08af-bdd3-4ca8-998f/`
- User still configured for old server (srv1083126.hstgr.cloud)

**09:15 SAST** - Investigation begins
- Confirmed QFieldCloud containers running on VF Server
- All 8 workers showing as "Up 13 hours"
- MinIO storage healthy
- Database accessible

**09:30 SAST** - Authentication issues identified
- Luke's account exists: username `Lukek`, 2 projects
- Tokens were stale after migration
- Cleared authentication tokens for user ID 35

**10:00 SAST** - Static files issue discovered
- Web UI showing plain text only
- CSS returning 404 at `/static/css/qfieldcloud.css`
- Files actually served at `/staticfiles/` path

**11:00 SAST** - Juan & Luke report sync failures
- Projects failing to upload/sync
- Consistent "Failed" errors

**11:15 SAST** - ROOT CAUSE DISCOVERED
- Worker logs showing critical error:
  ```
  docker.errors.ImageNotFound: 404 Client Error
  No such image: qfieldcloud-qgis:latest
  pull access denied for qfieldcloud-qgis
  ```

**11:20-11:25 SAST** - QGIS Image rebuilt
- Built from `/opt/qfieldcloud/docker-qgis`
- Image size: 2.6GB
- Build time: ~5 minutes

**11:30 SAST** - Service restored
- All 8 workers restarted
- Sync operations functional

### Technical Details

#### Error Analysis

**Worker Error Log Sample**:
```json
{
  "error": "404 Client Error for http+docker://localhost/v1.50/images/create?tag=latest&fromImage=qfieldcloud-qgis: Not Found",
  "error_origin": "worker_wrapper",
  "message": "pull access denied for qfieldcloud-qgis, repository does not exist or may require 'docker login'"
}
```

**Affected Job**:
```sql
SELECT id, status, type, project_id, created_at
FROM core_job
WHERE id = '404c3eea-7bb7-4570-8329-7e34c9883cbe';
-- Result: failed | process_projectfile | created at 2026-01-12 09:02:05
```

#### User Impact Assessment

**Luke (ID: 35)**:
- Username: Lukek
- Projects:
  - Marketing_Overview-08-12-25
  - Project-Progress (created 2026-01-12 08:11)
- Issue: Couldn't sync, projects not visible initially

**Juan (Multiple accounts)**:
- Jaun (ID: 4)
- JaunPlanning1 (ID: 5)
- @JaunPlanning1/Jaun_1 (ID: 6)
- Issue: Permission confusion, sync failures

#### Resolution Commands

1. **Check for Docker image**:
```bash
docker images | grep qgis
# Result: No image found
```

2. **Build QGIS image**:
```bash
cd /opt/qfieldcloud/docker-qgis
docker build -t qfieldcloud-qgis:latest .
# Result: Successfully built 8c76e22e7b8b (2.6GB)
```

3. **Restart workers**:
```bash
docker-compose restart worker_wrapper
# Result: All 8 workers restarted successfully
```

4. **Fix static files**:
```bash
# Collect static files
docker-compose exec -T app python manage.py collectstatic --noinput

# Copy to host volume
mkdir -p ./volumes/staticfiles
docker cp qfieldcloud-app-1:/usr/src/app/staticfiles/. ./volumes/staticfiles/

# Update nginx config
echo "  nginx:" >> docker-compose.override.yml
echo "    volumes:" >> docker-compose.override.yml
echo "      - ./volumes/staticfiles:/staticfiles:ro" >> docker-compose.override.yml

# Restart services
docker-compose restart nginx app
```

### Root Cause Analysis

**Primary Failure**: QGIS Docker image not included in migration
- The 2.6GB processing image wasn't transferred during migration
- Workers require this image to process all project files
- Without it, no geographic data processing is possible

**Contributing Factors**:
1. Migration checklist didn't include Docker images
2. No health check for required dependencies
3. Workers don't fail gracefully when image missing
4. Error only visible in worker logs, not UI

### Lessons Learned

1. **Migration Completeness**:
   - Docker images are critical infrastructure
   - Need explicit checklist for all components
   - Test all functionality post-migration

2. **Monitoring Gaps**:
   - Worker errors not surfaced to administrators
   - No alerts for missing dependencies
   - Need proactive health checks

3. **Documentation**:
   - Missing documentation on required Docker images
   - No troubleshooting guide for common issues
   - Need runbook for incident response

### Preventive Actions

#### Immediate (This Week)
1. Document all required Docker images
2. Create backup script for Docker images
3. Add health check script to cron

#### Short Term (This Month)
1. Implement monitoring dashboard
2. Create migration validation checklist
3. Set up alerting for worker failures

#### Long Term
1. Automate Docker image management
2. Implement blue-green deployments
3. Create disaster recovery procedures

### Monitoring Script

Create `/opt/qfieldcloud/scripts/health_check.sh`:
```bash
#!/bin/bash
# QFieldCloud Health Check

echo "=== QFieldCloud Health Check ==="
echo "Time: $(date)"

# Check Docker images
echo -n "QGIS Image: "
if docker images | grep -q qfieldcloud-qgis; then
    echo "✓ Present"
else
    echo "✗ MISSING - CRITICAL!"
    exit 1
fi

# Check workers
echo -n "Workers: "
WORKER_COUNT=$(docker-compose ps | grep worker_wrapper | grep Up | wc -l)
echo "$WORKER_COUNT/8 running"

# Check recent jobs
echo -n "Recent failed jobs: "
docker-compose exec -T db psql -U qfieldcloud_db_admin -d qfieldcloud_db \
    -t -c "SELECT COUNT(*) FROM core_job WHERE status='failed'
           AND created_at > NOW() - INTERVAL '1 hour';" | xargs

# Check MinIO
echo -n "MinIO Storage: "
curl -s http://localhost:9000/minio/health/live > /dev/null 2>&1 \
    && echo "✓ Healthy" || echo "✗ Down"

echo "=== Check Complete ==="
```

### Contact Information

**Primary Support**: Louis (louis@velocityfibre.co.za)
**Server Access**: ssh velo@100.96.203.105 (password: 2025)
**QFieldCloud URL**: https://qfield.fibreflow.app
**Internal Port**: 8082

### Related Documentation

- [QFieldCloud Migration Plan](..//MIGRATION_PLAN.md)
- [Migration Complete Status](../MIGRATION_COMPLETE.md)
- [Operations Log](../../../../docs/OPERATIONS_LOG.md)
- [Infrastructure Strategy](../../../../docs/INFRASTRUCTURE_RESILIENCE_STRATEGY.md)