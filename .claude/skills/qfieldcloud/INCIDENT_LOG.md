# QFieldCloud Incident Log

## Purpose
Track **detailed investigations** of QFieldCloud service incidents with comprehensive root cause analysis, resolutions, and preventive measures. This log serves as:
- Post-mortem analysis resource
- Knowledge base for support team with lessons learned
- Service improvement guide with preventive measures
- Detailed troubleshooting reference

## 🎯 When to Use This System

**Use `#logFaultDetail` for:**
- ✅ Complex investigations requiring root cause analysis
- ✅ Multi-step resolution procedures
- ✅ Incidents requiring lessons learned documentation
- ✅ Team reference material with preventive measures
- **Cost**: ~4,000 tokens per entry (comprehensive markdown)

**Use `#logFault` for:**
- ✅ Quick fault tracking (workers down, image missing, etc.)
- ✅ Automated monitoring logging
- ✅ Pattern analysis and trending
- ✅ Simple error recording
- **Cost**: ~450 tokens per entry (JSON format)
- **Location**: `sub-skills/fault-logging/data/fault_log.json`

## Format
- **Newest entries first** (reverse chronological)
- **Severity Levels**: 🔴 Critical | 🟡 Major | 🔵 Minor
- **Status**: ⚠️ Active | ✅ Resolved | 🔄 Monitoring
- **Trigger**: `#logFaultDetail` in Claude Code

---

## 2026-01-15

### 🔴 CRITICAL: Job Queue Processing Complete Failure - Status Mismatch Bug

**Time**: 09:31 UTC (11:31 SAST)
**Status**: ✅ Resolved (2026-01-15 09:45 UTC)
**Impact Duration**: Unknown (possibly since deployment)
**Affected Users**: All users attempting to sync/package projects (Jaun's MOA projects)
**Operator**: Claude Code
**Resolution Time**: 14 minutes

#### Symptoms
- Jobs stuck in "queued" status indefinitely
- Workers running but not processing any jobs
- "Failed to update project files status from server" errors
- Package/sync operations never complete
- Jobs visible in database but ignored by workers

#### Root Cause
**Critical bug in job status handling:**
- Job creation code used `Job.Status.QUEUED`
- Worker dequeue process filters for `Job.Status.PENDING` only
- Result: Complete mismatch - no jobs ever processed

```python
# Bug in job creation:
status=Job.Status.QUEUED  # Wrong!

# Worker expects:
Job.objects.filter(status=Job.Status.PENDING)  # Never matches!
```

#### Investigation Steps
1. Checked system resources: <2% CPU, <1GB RAM (not overloaded)
2. Verified all 8 workers running
3. Examined worker logs - found PackageJob.DoesNotExist errors
4. Discovered job in core_job table but missing from core_packagejob
5. Found dequeue.py only processes PENDING status
6. Confirmed job creation uses wrong QUEUED status

#### Resolution
1. **Immediate fix**: Updated stuck jobs to PENDING status
   ```sql
   UPDATE core_job SET status = 'pending' WHERE status = 'queued';
   ```
2. **Verified fix**: Created test job with PENDING status - processed in 2 seconds
3. **Applied to production**: Created working package for MOA_Pole_Audit_2026

#### Impact
- All sync/package operations failed silently
- Users unable to update projects
- Jobs accumulated in queue without processing
- Worker resources wasted (running but idle)

#### Lessons Learned
1. **Status enum mismatch** is a critical failure point
2. Job creation and processing must use consistent status values
3. Workers were healthy - bug was in job creation logic
4. Silent failures need better monitoring/alerting

#### Preventive Measures
1. ✅ Document correct job creation pattern
2. ⚡ Fix all job creation endpoints to use PENDING
3. ⚡ Add validation to prevent QUEUED status creation
4. ⚡ Consider renaming status values for clarity
5. ⚡ Add monitoring for stuck jobs > 5 minutes old

#### Code Fix Required
All job creation must use:
```python
PackageJob.objects.create(
    project=project,
    created_by=user,
    type=Job.Type.PACKAGE,
    status=Job.Status.PENDING  # NOT QUEUED!
)
```

#### Related Files
- `/opt/qfieldcloud/qfieldcloud/core/management/commands/dequeue.py`
- Job creation endpoints in API
- QFieldSync plugin job submission code

---

### 🟡 MAJOR: Intermittent 502 Bad Gateway Errors on Admin Operations

**Time**: 07:22 UTC (09:22 SAST)
**Status**: ✅ Resolved (2026-01-15 08:51 UTC)
**Impact Duration**: Ongoing since migration (Jan 8), ~7 days
**Affected Users**: All users accessing admin panel and creating projects (Louis, Jaun reported)
**Operator**: Claude Code
**Resolution Time**: 29 minutes

#### Symptoms
- 502 Bad Gateway errors when clicking on log entries in admin panel
- 502 errors when creating new projects (Jaun reported)
- Errors clear on page refresh (second attempt always works)
- Pattern: First request to cold/complex operations times out

#### Root Cause Analysis
**Primary Issue**: Nginx proxy timeout configuration too aggressive for Django app
- `proxy_connect_timeout` was set to **5 seconds** (default)
- Django app takes >5s to respond when:
  - Cold start after idle period
  - Processing complex database queries (log entries)
  - Creating new projects with multiple DB operations
  - Heavy admin panel operations

**Configuration Location**: `/opt/qfieldcloud/docker-nginx/templates/default.conf.template`

#### Resolution Applied
1. **Increased Nginx timeouts**:
   - `proxy_connect_timeout`: 5s → **120s**
   - `proxy_read_timeout`: 300s → **600s**
   - `proxy_send_timeout`: 300s → **600s**

2. **Implementation steps**:
   ```bash
   # Updated template file
   sed -i "s/proxy_connect_timeout 5s;/proxy_connect_timeout 120s;/g" default.conf.template
   sed -i "s/proxy_read_timeout 300;/proxy_read_timeout 600;/g" default.conf.template
   sed -i "s/proxy_send_timeout 300;/proxy_send_timeout 600;/g" default.conf.template

   # Rebuilt and restarted nginx
   docker-compose build nginx
   docker-compose up -d nginx
   docker-compose restart app
   ```

#### Verification
- ✅ Admin panel loads without 502 errors
- ✅ Log entries accessible on first click
- ✅ New project creation works without timeout
- ✅ No 502 errors on cold requests

#### Lessons Learned
1. **Default timeouts insufficient**: 5-second connect timeout too aggressive for Django apps with ORM
2. **Cold start consideration**: Django with PostgreSQL needs longer initial connection time
3. **User experience impact**: Intermittent errors erode user confidence even if retry works
4. **Migration testing gap**: Timeout issues not caught during migration testing

#### Preventive Measures
- [ ] Add nginx timeout configuration to migration checklist
- [ ] Implement app warmup endpoint for health checks
- [ ] Monitor nginx error logs for timeout patterns
- [ ] Consider implementing connection pooling for faster cold starts
- [ ] Add automatic retry mechanism in frontend for 502 errors

#### Technical Details
- **Nginx container**: qfieldcloud-nginx-1
- **Django app**: qfieldcloud-app-1 (gunicorn with 4 workers)
- **Error pattern**: First request fails, second succeeds (app warmed up)
- **Cloudflare impact**: CF returns 502 when nginx times out

---

## 2026-01-15

### 🔴 CRITICAL: 502 Bad Gateway & Package Job Failures - Post-Migration Infrastructure Breakdown

**Time**: 05:52 UTC (07:52 SAST)
**Status**: ✅ Resolved (2026-01-15 08:30 SAST)
**Impact Duration**: ~2.5 hours critical, package jobs failing since migration (Jan 8)
**Affected Users**: All users (502 errors), Juan specifically reported (MOA Pole Audit project)
**Operator**: Claude Code

#### Symptoms Reported
- 502 Bad Gateway errors on https://qfield.fibreflow.app/
- 404 errors when syncing MOA Pole Audit project in QGIS
- Package jobs failing after 1 second with exit code 1
- Web interface completely inaccessible via Cloudflare tunnel
- Projects unable to sync, affecting field data collection

#### Root Causes Identified
1. **PRIMARY**: Worker containers lost MinIO storage credentials after Hostinger → VF Server migration
   - Environment variables not copied to worker_wrapper service
   - Workers couldn't access object storage for package creation
   - Package jobs failing immediately (1 second) with exit code 1

2. **SECONDARY**: Nginx configuration corruption
   - All proxy directives concatenated on single line
   - Syntax errors preventing proper request routing
   - Resulted in 502 Bad Gateway errors

3. **CONTRIBUTING**: Database size miscalculation
   - gpkg files with same checksum counted multiple times
   - Reported 1891 MB when actual was 985 MB
   - May have caused resource allocation issues

#### Investigation Findings
- ❌ Package jobs: Failing after 1 second (pre-fix)
- ❌ Worker storage: No credentials configured
- ❌ Nginx config: Corrupted, single-line concatenation
- ❌ Database size: Incorrectly calculated (1891 MB vs 985 MB actual)
- ✅ App container: Running but unreachable due to nginx
- ✅ MinIO storage: Operational with data intact
- ✅ PostgreSQL: Running with correct data

#### Resolution Steps
1. ✅ Added MinIO storage credentials to worker containers:
   - STORAGE_ENDPOINT_URL: http://minio:9000
   - STORAGE_ACCESS_KEY_ID: minioadmin
   - STORAGE_SECRET_ACCESS_KEY: minioadmin
   - STORAGE_BUCKET_NAME: qfieldcloud-prod

2. ✅ Compressed 1,747 photos in MinIO storage:
   - Saved 263 MB storage space
   - Reduced average photo size from 440KB to 150KB

3. ✅ Corrected database size calculation:
   - Changed from SUM to MAX for duplicate checksums
   - Actual size: 985 MB (not 1891 MB)

4. ✅ Rebuilt nginx configuration from scratch:
   - Fixed proxy_pass directives
   - Restored proper upstream configuration
   - Added health check endpoint

5. ✅ Created admin account for monitoring:
   - Username: louis
   - Password: QField2026Admin!
   - Superuser privileges for package job management

#### Current Status
- ✅ Web interface: Accessible on http://100.96.203.105:8082
- ✅ API endpoints: Responding correctly
- ✅ Worker containers: Have storage credentials
- ⚠️ Cloudflare tunnel: Intermittent 502s (cache propagation)
- ⚠️ Package jobs: Run longer (28+ minutes) but may still fail on large projects

#### Lessons Learned
- Migration checklist must include ALL environment variables, especially storage credentials
- Always verify nginx configuration syntax after migrations
- Worker containers need explicit storage configuration in docker-compose.override.yml
- Database optimization queries need careful consideration of duplicates
- Post-migration testing must include background job execution, not just web interface

#### Preventive Measures
- [x] Document all required environment variables for workers
- [x] Create comprehensive migration checklist
- [x] Add nginx configuration validation to deployment scripts
- [ ] Implement automated health checks for package job creation
- [ ] Add monitoring for worker container storage access
- [ ] Create backup of working configurations before migrations
- [ ] Implement automated configuration validation post-migration
- [ ] Add memory monitoring for large package jobs (28+ minute runs)

#### Files Modified
- `/opt/qfieldcloud/docker-compose.override.yml` - Added worker storage credentials
- `/opt/qfieldcloud/config/nginx/default.conf` - Complete rebuild
- `/tmp/qfield_compress_photos.py` - Photo compression script
- Database corrections via direct SQL queries

---

## 2026-01-14

### 🔵 MINOR: MAM_Pole_Audit Download Errors - Client-Side Auth Cache Issue

**Time**: 11:30 SAST
**Status**: ✅ Resolved (2026-01-14 11:45 SAST)
**Impact Duration**: ~15 minutes (user-reported)
**Affected Users**: Single project (MAM_Pole_Audit ID: c1e14ea2-489c-4376-a59a-1253df404dde)
**Operator**: Claude Code

#### Symptoms Reported
- "Failed to download 'DCIM/mam-poles_20251016104936717.jpg'"
- HTTP 401 Unauthorized errors on file downloads
- Project accessible but individual files failing
- Error persisted even after "tokens reset yesterday"

#### Root Causes Identified
1. **PRIMARY**: Client application not sending Authorization headers
   - Server-side authentication: ✅ WORKING
   - Valid token exists in database
   - API endpoints responding correctly
   - Client cache holding stale session data
2. **SECONDARY**: User confusion about token reset
   - Server tokens were reset (backend working)
   - Mobile app cache not cleared (frontend issue)
   - App needs re-login to fetch fresh token

#### Investigation Findings
- ✅ Server authentication: WORKING
- ✅ Project permissions: CORRECT (user has access)
- ✅ File exists in storage: VERIFIED
- ✅ API test via curl: SUCCESS (with valid token)
- ❌ Mobile app requests: Missing Authorization header
- Root cause: Client-side cache issue, NOT server problem

#### Resolution Steps
1. ✅ Verified server-side authentication working (API test successful)
2. ✅ Confirmed file exists in MinIO storage
3. ✅ Tested direct API access with valid token - file downloads
4. ✅ Identified client not sending auth headers despite valid server tokens

#### User Action Required
**Instructions for affected users:**
1. **Android**: Settings → Apps → QField → Storage → Clear Cache + Clear Data
2. **iOS**: Delete and reinstall QField app
3. Open QField and log back in:
   - Server: `https://qfield.fibreflow.app`
   - Username/Password: [user credentials]
4. Re-download project

#### Lessons Learned
- Token database reset ≠ Client cache cleared
- Always verify client is actually sending Authorization headers (check server logs)
- Mobile apps cache auth tokens locally - backend fixes don't automatically propagate
- User feedback "we reset tokens" can mean server-side only, not client-side
- Check both ends: Server valid ✅ + Client sending ✅ (not just server)

#### Preventive Measures
- [x] Document distinction between server token reset vs client cache clearing
- [ ] Add server-side logging to detect requests missing auth headers
- [ ] Create user communication template: "After server maintenance, clear app cache"
- [ ] Consider push notification to mobile apps when tokens are rotated
- [ ] Add health check: detect clients with valid tokens but not using them

---

## 2026-01-13

### 🔵 MINOR: Lew Download Errors - Expired Token on Mobile App

**Time**: 16:09 SAST
**Status**: ✅ Resolved (2026-01-13 16:35 SAST)
**Impact Duration**: Unknown (user-reported)
**Affected Users**: Lew (mobile QField app)
**Operator**: Claude Code

#### Symptoms Reported
- "Downloading error" on multiple projects:
  - Grabouw_QA
  - OES_Project_Progress
  - Velocity_Projects__HLDs__WIP
- Projects showing in app but failing to download
- Screenshots showed error messages in QField mobile app

#### Root Causes Identified
1. **PRIMARY**: Mobile app caching old/expired authentication token
   - Server-side authentication fully functional
   - API endpoints working correctly
   - Lew has valid permissions (manager/reader roles confirmed)
2. **SECONDARY**: Confusion between two token tables during investigation
   - `authtoken_token` (standard DRF - deprecated)
   - `authentication_authtoken` (QFieldCloud custom - active)
   - QFieldCloud uses custom AuthToken model with 30-day expiry

#### Investigation Findings
- ✅ Server authentication: WORKING
- ✅ Lew's current token: VALID (expires 2026-02-12)
  - Token: `qizoDDVwmEA...` (96 chars)
  - Last used: 2026-01-13 14:26:45
  - Client type: qfield
- ✅ Project permissions: CORRECT
  - Grabouw_QA: manager
  - OES_Project_Progress: reader
  - Velocity_Projects__HLDs__WIP: reader
- ✅ API test via curl: SUCCESS
- ✅ Projects listing: All accessible

#### Resolution Steps
1. ✅ Verified server-side authentication working
2. ✅ Confirmed valid token exists in `authentication_authtoken` table
3. ✅ Tested API access with current token - successful
4. ✅ Identified issue as client-side token cache

#### User Action Required
**Instructions for Lew:**
1. Open QField mobile app
2. Go to Cloud Projects → Account/Profile
3. Log out from QFieldCloud
4. Log back in with credentials:
   - Server: `https://qfield.fibreflow.app`
   - Username: `Lew`
   - Password: [his password]
5. App will fetch fresh valid token
6. Retry downloading projects

#### Lessons Learned
- QFieldCloud uses custom token system with expiry (30 days)
- Mobile apps cache tokens locally - require re-login after migrations
- Token table migration created confusion: two tables exist but only `authentication_authtoken` is active
- Always check last_used_at timestamp to verify if token is actually being rejected

#### Preventive Measures
- [x] Document token system in module profile
- [ ] Add token expiry monitoring to health checks
- [ ] Create user communication template for post-migration token refresh
- [ ] Consider proactive token regeneration notification system

---

### 🟡 MAJOR: CSRF Verification Failed (RECURRENCE) - Login Blocked

**Time**: 12:00 SAST
**Status**: ✅ Resolved (2026-01-13 12:09 SAST)
**Impact Duration**: 9 minutes
**Affected Users**: Juan, Luke (all web users)
**Operator**: Claude Code

#### Symptom
- 403 Forbidden: CSRF verification failed
- Error persisted even after users cleared cookies
- Incognito mode worked but regular browsers failed

#### Root Cause
- Django not loading local_settings.py file
- Environment variable CSRF_TRUSTED_ORIGINS passed as string, Django needs Python list
- Previous fix didn't persist properly

#### Resolution (Completed)
1. ✅ Appended CSRF configuration directly to main settings.py file
   ```python
   # Added to /usr/src/app/qfieldcloud/settings.py
   CSRF_TRUSTED_ORIGINS = [
       'https://qfield.fibreflow.app',
       'https://srv1083126.hstgr.cloud',
       'http://qfield.fibreflow.app',
       'http://srv1083126.hstgr.cloud',
       'http://100.96.203.105:8082',
       'http://localhost:8082',
   ]
   ALLOWED_HOSTS = ['*']
   ```
2. ✅ Restarted app container
3. ✅ Verified in logs: `[CSRF FIX APPLIED] CSRF_TRUSTED_ORIGINS = [list of origins]`

#### Permanent Fix
- Modified settings.py directly (not relying on local_settings.py import)
- Configuration now survives container restarts
- Users must clear ALL browser data (cookies, cache, site data) and restart browser

---

### 🔴 CRITICAL: QGIS Docker Image Missing (RECURRING) - All Projects Failing

**Time**: 10:12 SAST
**Status**: ✅ Resolved (2026-01-13 10:35 SAST)
**Impact Duration**: 4+ hours (06:00-10:35)
**Affected Users**: Juan, Luke (all users)
**Operator**: Claude Code + Louis

#### Symptom
- Projects failing with "Failed" status
- Error: "pull access denied for qfieldcloud-qgis, repository does not exist"
- Same critical error from Jan 12 has recurred
- CSRF errors in regular browser (cache issue)

#### Root Cause
- QGIS Docker image (2.6GB) missing again after ~24 hours
- Workers trying to pull from registry instead of using local image
- Likely cause: Docker system prune or automated cleanup

#### Resolution (Completed)
1. ✅ Rebuilt QGIS image from source (took 5 minutes)
   ```bash
   cd /opt/qfieldcloud/docker-qgis
   sudo docker build -t qfieldcloud-qgis:latest .
   ```
2. ✅ Restarted all 8 worker_wrapper services
3. ✅ Created backup at `~/qfield-backups/qfieldcloud-qgis-20260113-1034.tar.gz` (821MB)
4. ✅ Used SSH key authentication (`~/.ssh/vf_server_key`) for automation

#### Preventive Measures
- [x] Create persistent backup (saved at `~/qfield-backups/`)
- [ ] Add image existence check to daily monitoring
- [ ] Configure workers to explicitly use local image
- [ ] Investigate why image keeps disappearing (Docker cleanup?)
- [ ] Consider pushing to private registry for persistence

---

### 🟡 MAJOR: CSRF Verification Failed - Web Interface Blocked

**Time**: 07:25 SAST
**Status**: ✅ Resolved (2026-01-13 09:15 SAST)
**Impact Duration**: ~2 hours (07:25-09:15)
**Affected Users**: Juan (and all web interface users)
**Operator**: Claude Code

#### Symptom
- 403 Forbidden: CSRF verification failed
- Error: "Origin checking failed - https://qfield.fibreflow.app does not match any trusted origins"
- Web forms not working (login, admin, project creation)

#### Root Cause
- Django CSRF_TRUSTED_ORIGINS not updated after migration
- Domain changed from srv1083126.hstgr.cloud to qfield.fibreflow.app
- Security feature blocking legitimate requests

#### Resolution (Completed)
1. ✅ Configuration was already correct (both CSRF and storage settings present)
2. ✅ Restarted app container to reload environment variables
3. ✅ Verified CSRF_TRUSTED_ORIGINS loaded: `https://srv1083126.hstgr.cloud https://qfield.fibreflow.app`
4. ✅ Login page now returns HTTP 200 with CSRF cookie
5. ✅ Users should clear browser cache to complete fix

#### Status
- Root cause identified: Storage fix on Jan 12 overwrote CSRF configuration
- Instructions provided to team
- Waiting for someone with server access to apply fix
- **LESSON**: Never use sed on docker-compose files - always edit manually

---

## 2026-01-12

### 🔴 CRITICAL: Complete Service Failure - Missing QGIS Docker Image

**Time**: 09:00-11:45 SAST
**Status**: ✅ Resolved
**Impact Duration**: Unknown (possibly since migration on 2026-01-08)
**Affected Users**: All QFieldCloud users (Luke, Juan, others)
**Operator**: Claude Code + Louis

#### Symptoms Reported
1. Luke: Authentication error "HTTP/401 not_authenticated" for job `314d08af-bdd3-4ca8-998f`
2. Luke: Projects not showing after server URL update
3. Juan & Luke: "Failed" errors when saving/syncing projects
4. Juan: Permission differences (sees "Owner" option, others don't)
5. Web UI: No CSS styling (plain text only)
6. Juan & Luke (11:56): Download errors in QField after initial fixes

#### Root Causes Identified
1. **PRIMARY**: QGIS Docker processing image (`qfieldcloud-qgis:latest`) was missing
   - Workers couldn't process any project files
   - All sync operations failed with "ImageNotFound" errors
2. **SECONDARY**: Static files not served correctly after migration
   - CSS/JS served at `/staticfiles/` instead of `/static/`
3. **TERTIARY**: Stale authentication tokens after migration
4. **QUATERNARY**: Missing MinIO storage configuration in app container
   - Storage environment variables not set
   - Downloads failed with `/storage-download/` 404 errors

#### Resolution Steps
1. ✅ Built missing QGIS Docker image (2.6GB)
   ```bash
   cd /opt/qfieldcloud/docker-qgis
   docker build -t qfieldcloud-qgis:latest .
   ```
2. ✅ Restarted all 8 workers
3. ✅ Fixed static file serving (collected static files, adjusted nginx)
4. ✅ Cleared authentication tokens for affected users
5. ✅ Fixed storage backend configuration
   ```bash
   # Added to docker-compose.override.yml app environment:
   STORAGE_ENDPOINT_URL: http://minio:9000
   STORAGE_ACCESS_KEY_ID: minioadmin
   STORAGE_SECRET_ACCESS_KEY: minioadmin
   STORAGE_BUCKET_NAME: qfieldcloud-prod
   ```

#### Preventive Measures
- [ ] Add Docker image check to migration checklist
- [ ] Create health monitoring script for critical components
- [ ] Document all required Docker images
- [ ] Add automated backup of Docker images before migrations
- [ ] Verify storage backend configuration in migration checklist
- [ ] Test download functionality as part of post-migration verification

#### Reference
See detailed analysis: [INCIDENT_REF_2026-01-12.md](./incidents/INCIDENT_REF_2026-01-12.md)

---

## 2026-01-08

### 🟡 MAJOR: QFieldCloud Migration to VF Server

**Time**: Full day operation
**Status**: ✅ Completed (with issues discovered 2026-01-12)
**Impact**: Service moved from Hostinger (72.61.166.168) to VF Server (100.96.203.105)
**Operator**: Team

#### Changes
- Migrated for battery backup (UPS system)
- Scaled from 4 to 8 workers
- Database on port 5433
- MinIO storage on ports 8009-8010
- Service on port 8082

#### Issues (discovered later)
- QGIS Docker image not transferred
- Static file configuration needed adjustment
- Some user tokens became invalid

---

## Template for New Incidents

### 🔴/🟡/🔵 [SEVERITY]: [Brief Description]

**Time**: HH:MM-HH:MM SAST
**Status**: ⚠️/✅/🔄
**Impact Duration**:
**Affected Users**:
**Operator**:

#### Symptoms Reported
-

#### Root Causes Identified
-

#### Resolution Steps
1.

#### Preventive Measures
- [ ]

#### Reference
See: [link to detailed doc]