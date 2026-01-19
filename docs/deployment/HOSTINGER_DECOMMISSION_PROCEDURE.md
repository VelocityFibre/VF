# Hostinger QFieldCloud VPS Decommissioning Procedure

**VPS**: srv1083126.hstgr.cloud (72.61.166.168)
**Savings**: $20-30/month ($240-360/year)
**Status**: Ready for decommission after DNS validation

---

## Pre-Decommission Checklist

**✅ Complete ALL items before proceeding:**

- [ ] VF Server operational for 24-48 hours minimum
- [ ] DNS fully propagated (https://qfield.fibreflow.app points to VF Server)
- [ ] Tested with QField mobile app on VF Server
- [ ] All projects accessible on VF Server
- [ ] User accounts validated on VF Server
- [ ] No errors in VF Server logs for 24 hours
- [ ] Final backup from Hostinger completed
- [ ] Backup verified and stored in 2+ locations

**Estimated Safe Decommission Date**: 2025-12-24 (48 hours after migration)

---

## Phase 1: Final Validation (Day of Decommission)

### 1. Test VF Server Thoroughly

```bash
# SSH to VF Server
ssh louis@100.96.203.105

# Run health check
~/qfieldcloud/scripts/health_check.sh

# Expected output: "✅ ALL SYSTEMS OPERATIONAL"
```

**Required Results**:
- All 12 containers running
- Database responding
- App HTTP 302 response
- Cloudflare Tunnel active
- No critical errors

### 2. Test Public URL

```bash
# From any machine
curl -I https://qfield.fibreflow.app

# Expected: HTTP/2 302 (redirect to admin)
# NOT: Connection to Hostinger
```

### 3. Test with QField Mobile App

1. Open QField mobile app
2. Settings → QFieldCloud URL: https://qfield.fibreflow.app
3. Login with existing credentials
4. Sync a project
5. Verify files download correctly

**If ANY test fails**: STOP and investigate. Do not proceed with decommission.

---

## Phase 2: Final Backup from Hostinger

**Purpose**: Safety backup before shutdown (even though VF Server has all data)

```bash
# SSH to Hostinger
ssh -i ~/.ssh/qfield_vps root@72.61.166.168

# Create final backup directory
mkdir -p /root/qfield_final_backup
cd /root/qfield_final_backup

# 1. Backup database
docker exec qfieldcloud-db-1 pg_dump -U qfieldcloud_db_admin qfieldcloud_db \
  > qfield_db_final_$(date +%Y%m%d).sql

# 2. Backup configuration
cd /opt/qfieldcloud
tar -czf /root/qfield_final_backup/qfield_config_final.tar.gz \
  docker-compose.yml \
  docker-compose.override.local.yml \
  .env \
  conf/

# 3. Backup MinIO data (if any)
docker exec qfieldcloud-minio-1 tar -czf /tmp/minio_data_final.tar.gz /data
docker cp qfieldcloud-minio-1:/tmp/minio_data_final.tar.gz /root/qfield_final_backup/

# 4. Create final archive
cd /root/qfield_final_backup
tar -czf qfield_hostinger_final_$(date +%Y%m%d).tar.gz ./*

# Check size
ls -lh qfield_hostinger_final_*.tar.gz
```

### Download Final Backup

```bash
# From local machine
scp -i ~/.ssh/qfield_vps \
  root@72.61.166.168:/root/qfield_final_backup/qfield_hostinger_final_*.tar.gz \
  ~/VF/vps/hostinger/qfield/backups/final/

# Verify download
ls -lh ~/VF/vps/hostinger/qfield/backups/final/

# Optional: Upload to cloud storage
# aws s3 cp ~/VF/vps/hostinger/qfield/backups/final/qfield_*.tar.gz s3://backups/qfield/
```

**Backup Storage Locations** (keep 2+ copies):
1. ✅ Local machine: `~/VF/vps/hostinger/qfield/backups/final/`
2. ✅ VF Server: `/srv/data/backups/qfield_hostinger_final/` (optional)
3. ⚪ Cloud storage: S3/Backblaze/Google Drive (recommended)

---

## Phase 3: Graceful Shutdown

**ONLY proceed if all validations passed and backups complete**

```bash
# SSH to Hostinger
ssh -i ~/.ssh/qfield_vps root@72.61.166.168

# 1. Stop all QFieldCloud services
cd /opt/qfieldcloud
docker-compose down

# Verify containers stopped
docker ps | grep qfieldcloud
# Should return: (empty - no containers)

# 2. Stop test environment (if running)
docker stop $(docker ps -a | grep qfieldcloud-test | awk '{print $1}')
docker rm $(docker ps -a | grep qfieldcloud-test | awk '{print $1}')

# 3. Clean up Docker resources (optional - frees disk)
docker system prune -a --volumes

# This will ask for confirmation:
# WARNING! This will remove:
#   - all stopped containers
#   - all networks not used by at least one container
#   - all images without at least one container associated to them
#   - all build cache
# Are you sure you want to continue? [y/N]
# Answer: y

# 4. Document final state
echo "QFieldCloud shutdown at $(date)" > /root/qfield_shutdown.txt
docker ps -a > /root/docker_final_state.txt
df -h > /root/disk_final_state.txt
```

---

## Phase 4: Verification

### 1. Confirm Hostinger is Down

```bash
# From local machine
timeout 10 curl -I http://72.61.166.168:8011

# Expected: Connection timeout or refused
# NOT: HTTP response
```

### 2. Confirm VF Server Serving Traffic

```bash
# Test public URL (should work)
curl -I https://qfield.fibreflow.app

# Expected: HTTP/2 302
```

### 3. Monitor VF Server

```bash
# SSH to VF Server
ssh louis@100.96.203.105

# Watch logs for any issues
docker logs -f qfieldcloud-app-1

# Run health check every hour for first day
watch -n 3600 ~/qfieldcloud/scripts/health_check.sh
```

---

## Phase 5: VPS Cancellation

**Wait 7 days** after shutdown before canceling (safety period for rollback)

### Cancel Hostinger VPS Subscription

1. **Login** to Hostinger: https://hpanel.hostinger.com
   - Email: ai@velocityfibre.co.za
   - Password: VeloF@2025

2. **Navigate** to VPS: https://hpanel.hostinger.com/vps/1083126/settings

3. **Scroll** to "Cancel VPS" section at bottom

4. **Click** "Cancel VPS"

5. **Select** cancellation reason: "Migrated to own infrastructure"

6. **Confirm** cancellation

7. **Note** final billing date (may be prorated refund)

### Expected Outcome

- VPS will remain active until end of current billing period
- No further charges after cancellation
- Savings: $20-30/month = $240-360/year

---

## Phase 6: Post-Decommission

### 1. Update Documentation

- [ ] Update `CLAUDE.md` - Remove Hostinger VPS references
- [ ] Update `docs/OPERATIONS_LOG.md` - Record decommission date
- [ ] Archive Hostinger backups with retention date
- [ ] Update monitoring scripts to remove Hostinger checks

### 2. Clean Up Local Files

```bash
# Archive Hostinger connection info
mv ~/.ssh/qfield_vps ~/.ssh/archive/qfield_vps_decommissioned_$(date +%Y%m%d)
mv ~/VF/vps/hostinger/qfield/ ~/VF/vps/hostinger/qfield_archived_$(date +%Y%m%d)/

# Update known_hosts
ssh-keygen -R 72.61.166.168
```

### 3. Financial Tracking

- [ ] Verify Hostinger cancellation confirmation email
- [ ] Check for prorated refund (if applicable)
- [ ] Update budget spreadsheet with savings

---

## Rollback Procedure (Emergency Only)

**If critical issues found on VF Server within 7-day safety period:**

### 1. Restart Hostinger VPS

```bash
# SSH to Hostinger
ssh -i ~/.ssh/qfield_vps root@72.61.166.168

# Restart services
cd /opt/qfieldcloud
docker-compose up -d

# Wait for startup
sleep 30

# Verify
docker-compose ps
curl -I http://localhost:8011
```

### 2. Update DNS to Point Back

**Option A**: Remove VF Server tunnel route
```bash
# On VF Server
ssh louis@100.96.203.105

# Edit tunnel config - remove QField entry
nano ~/.cloudflared/config.yml
# Delete the qfield.fibreflow.app section

# Restart tunnel
pkill cloudflared
nohup ~/cloudflared tunnel run vf-downloads > /tmp/cloudflared.log 2>&1 &
```

**Option B**: Update Cloudflare DNS
1. Login: https://dash.cloudflare.com
2. Select: fibreflow.app domain
3. DNS Records: Find `qfield` CNAME
4. Delete CNAME or change target back to old configuration

### 3. Test Hostinger is Serving

```bash
# Wait 5-10 minutes for DNS
curl -I https://qfield.fibreflow.app

# Should connect to Hostinger
```

### 4. Investigate VF Server Issues

- Review logs: `docker logs qfieldcloud-app-1`
- Check health: `~/qfieldcloud/scripts/health_check.sh`
- Compare with Hostinger configuration
- Fix issues before attempting migration again

---

## Decommission Timeline

| Day | Action | Duration |
|-----|--------|----------|
| **Day 0** | Migration complete | - |
| **Day 1-2** | Monitor VF Server, test thoroughly | - |
| **Day 3** | Final validation, create backup | 1 hour |
| **Day 3** | Shutdown Hostinger services | 30 min |
| **Day 3-10** | Safety period (can rollback if needed) | - |
| **Day 10** | Cancel VPS subscription | 15 min |
| **Day 10** | Clean up documentation/files | 30 min |
| **Day 11+** | VF Server only (save $20-30/month!) | - |

---

## Success Criteria

**Decommission is successful when**:

- ✅ VF Server operational for 7+ days
- ✅ Zero critical errors in logs
- ✅ Users can access https://qfield.fibreflow.app
- ✅ QField mobile app syncing successfully
- ✅ All projects and data accessible
- ✅ Hostinger VPS canceled
- ✅ Final backups stored in 2+ locations
- ✅ $240-360/year cost savings realized

---

## Contacts & References

**Hostinger Support**:
- URL: https://www.hostinger.com/contact
- VPS ID: 1083126
- Server: srv1083126.hstgr.cloud

**VF Server**:
- Host: 100.96.203.105 (velo-server)
- User: louis
- Password: VeloAdmin2025!
- Location: ~/qfieldcloud/

**Cloudflare**:
- Domain: fibreflow.app
- Tunnel: vf-downloads (0bf9e4fa-f650-498c-bd23-def05abe5aaf)

**Migration Documentation**:
- Migration Plan: `docs/deployment/QFIELDCLOUD_MIGRATION_PLAN.md`
- VF Server Structure: `docs/deployment/VF_SERVER_DIRECTORY_STRUCTURE.md`
- Operations Log: `docs/OPERATIONS_LOG.md`

---

**Document Version**: 1.0
**Created**: 2025-12-22
**Safe Decommission Date**: 2025-12-24 (48h after migration)
**Status**: Ready for execution after validation period
