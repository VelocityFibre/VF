# Module: WA Monitor (WhatsApp QA Drop Monitor)

**Type**: module
**Location**: `/src/modules/wa-monitor/`
**Dashboard**: https://app.fibreflow.app/wa-monitor (Production - Shows ALL drops)
**Alternative**: https://vf.fibreflow.app/wa-monitor (Staging - Limited to 100)
**Isolation**: fully_isolated (zero-dependency, can be extracted to microservice)
**Developers**: louis
**Last Updated**: 2026-01-16
**Status**: ⚠️ Partially Working - Data displays correctly, Send Feedback button broken

---

## Overview

Real-time monitoring and validation of fiber network installation photos from WhatsApp groups. Tracks contractor work quality through photo submissions with automated data extraction from multiple WhatsApp groups.

**Critical Context**: Fully isolated module with zero dependencies on core FibreFlow modules. Can be extracted to a microservice if needed.

## 🚨 CURRENT ISSUE: Send Feedback Button Not Working

**Problem**: Send Feedback button on UI fails due to Next.js API routing/caching issue
**Workaround**: Use direct microservice call (100% working):
```bash
curl -X POST http://100.96.203.105:8092/send-feedback \
  -H "Content-Type: application/json" \
  -d '{"message": "Your message", "drNumber": "DR-NUMBER"}'
```
**Details**: See Issue #1 in Known Gotchas section below

## Dependencies

### External Dependencies
- **Backend Services**: Python services MIGRATED to **VF Server** (2026-01-14)
  - `wa-monitor`: Production monitoring service (running)
  - Location: `~/wa-monitor-vf/` on VF Server (100.96.203.105)
  - Status: ✅ Successfully migrated and operational

- **WhatsApp Bridge**: Go service for RECEIVING messages
  - Port: 8080 (VF Server)
  - Purpose: Receive messages from WhatsApp groups
  - Status: ✅ Successfully migrated
  - Phone: +27640412391

- **WhatsApp Sender**: Go service for SENDING feedback
  - Port: 8081 (VF Server)
  - Purpose: Send feedback messages to WhatsApp groups
  - Status: ✅ Operational (reconnected 2026-01-16)
  - Phone: +27 82 418 9511
  - **Note**: Accessed via microservice on port 8092

- **WhatsApp Feedback Microservice**: Express.js service (NEW 2026-01-16)
  - Port: 8092 (VF Server)
  - Purpose: Bypass Next.js API issues, direct WhatsApp communication
  - Status: ✅ Production Ready
  - Service: `wa-feedback.service`
  - **Documentation**: `docs/fixes/wa-monitor-microservice-implementation.md`
- **Neon PostgreSQL**: `qa_photo_reviews` table
  - Separate from SOW drops table
  - Source of truth for QA photo submissions
  - No Convex sync (isolated data)

### Internal Dependencies
- **None** - Fully isolated, zero-dependency module

## Database Schema

### Tables Owned
| Table | Description | Key Columns |
|-------|-------------|-------------|
| qa_photo_reviews | QA drop photo submissions | id, dr_number, contractor, project, status, created_at, gps_location, timestamp |
| whatsapp_messages | Message log (optional) | id, phone_number, message_body, direction, timestamp |

**Database Queries**:
```sql
-- Get recent QA drops
SELECT * FROM qa_photo_reviews ORDER BY created_at DESC LIMIT 20;

-- Count drops by contractor
SELECT contractor, COUNT(*)
FROM qa_photo_reviews
GROUP BY contractor;

-- Get daily drops per project
SELECT project, DATE(created_at) as date, COUNT(*) as drops
FROM qa_photo_reviews
WHERE created_at > NOW() - INTERVAL '7 days'
GROUP BY project, DATE(created_at);
```

### Tables Referenced
None - fully isolated data (separate from SOW drops table)

## API Endpoints

| Endpoint | Method | Purpose | Auth Required |
|----------|--------|---------|---------------|
| /api/wa-monitor-drops | GET | Fetch QA drops | Yes |
| /api/wa-monitor-summary | GET | Get summary statistics | Yes |
| /api/wa-monitor-daily | GET | Daily drops per project | Yes |
| /api/wa-monitor-send-feedback | POST | (DEPRECATED - use microservice) | Yes |
| http://100.96.203.105:8092/send-feedback | POST | Send feedback via microservice | No |
| /api/wa-monitor-dr-validation | POST | Validate CSV/Excel against DB | Yes |
| /api/wa-monitor-dr-validation | PUT | Add missing drops to database | Yes |
| /wa-monitor | GET | View monitoring dashboard | Yes |
| /wa-monitor/dr-validation | GET | DR reconciliation tool (Janice) | Yes |

**Monitoring Flow**:
1. WhatsApp groups receive contractor photos
2. Python backend monitors groups and extracts metadata
3. Photos stored in `qa_photo_reviews` table
4. Dashboard displays real-time drop status
5. Send feedback functionality via WhatsApp Bridge (port 8080)

## Services/Methods

### Core Services
- **Python Monitor Service** - `wa-monitor-prod` / `wa-monitor-dev`
  - Monitors multiple WhatsApp groups (Lawley, Mohadin, Velo Test, Mamelodi)
  - Extracts metadata from photos (GPS, timestamps, contractor info)
  - Stores drops in `qa_photo_reviews` table
  - Daily validation and reporting

- **WhatsApp Bridge** - `whatsapp-bridge-prod` (port 8080)
  - Sends feedback messages to WhatsApp groups
  - Go-based service for reliable message delivery
  - Restart with: `systemctl restart whatsapp-bridge-prod`

- **WA Monitor Dashboard** - `/wa-monitor`
  - Real-time view of QA drops
  - Filter by project, date range, status
  - Daily drops per project view
  - Send feedback functionality

- **DR Validation Tool** - `/wa-monitor/dr-validation` (FOR JANICE)
  - **Purpose**: CSV/Excel reconciliation, NOT photo evaluation
  - **Function**: Compares uploaded CSV files against WA monitor database
  - **Identifies**:
    - Records in both CSV and database (matched)
    - Records in CSV but missing from database (need to be added)
    - Records in database but not in CSV (extra records)
  - **Features**:
    - Auto-detects dates from uploaded files
    - Bulk add missing drops to database
    - Project-specific validation (Lawley, Mohadin, etc.)
    - Date mismatch warnings and auto-correction
  - **Used by**: Janice for ensuring all drops from CSV are captured

## File Structure

```
src/modules/wa-monitor/          # Main module directory (NOT IN THIS REPO)
├── components/
│   ├── WaMonitorDashboard.tsx  # Main dashboard component
│   ├── WaMonitorFilters.tsx    # Filter controls
│   ├── WaMonitorGrid.tsx       # Data grid display
│   ├── QaReviewCard.tsx        # Individual drop card
│   └── DropStatusBadge.tsx     # Status indicators
├── services/
│   └── waMonitorApiService.ts  # API integration
├── types/
│   └── wa-monitor.types.ts     # TypeScript definitions
├── ISOLATION_GUIDE.md          # Module isolation documentation
└── TROUBLESHOOTING.md          # Common issues and fixes

/home/velo/fibreflow/app/(main)/wa-monitor/  # ACTUAL LOCATION ON VF SERVER
├── dr-validation/
│   ├── page.tsx                # DR Validation page route
│   └── DrValidationClient.tsx  # CSV reconciliation component (Janice)

/opt/wa-monitor/                 # Backend services (VF Server)
├── prod/
│   ├── config/
│   │   └── projects.yaml      # WhatsApp groups configuration
│   └── restart-monitor.sh     # Safe production restart script
└── dev/
    └── restart-monitor.sh     # Development restart script
```

## Configuration

### Environment Variables (VF Server)
```bash
# WhatsApp Bridge
WHATSAPP_BRIDGE_URL=http://100.96.203.105:8080
WHATSAPP_BRIDGE_SERVICE=whatsapp-bridge-prod

# Database
NEON_DATABASE_URL=postgresql://...

# API Endpoints (all prefixed)
WA_MONITOR_API_PREFIX=/api/wa-monitor-
```

### Config Files
- `/opt/wa-monitor/prod/config/projects.yaml` - WhatsApp groups configuration
- `src/modules/wa-monitor/ISOLATION_GUIDE.md` - Module isolation documentation
- `src/modules/wa-monitor/TROUBLESHOOTING.md` - Common issues and fixes

## Common Operations

### Add New WhatsApp Group (5 mins)
```bash
ssh -i ~/.ssh/vf_server_key louis@100.96.203.105
nano /opt/wa-monitor/prod/config/projects.yaml
# Add new group configuration
/opt/wa-monitor/prod/restart-monitor.sh  # Safe restart (clears Python cache)
```

### Fix "Send Feedback" Issues
```bash
ssh -i ~/.ssh/vf_server_key louis@100.96.203.105
systemctl restart whatsapp-bridge-prod
# Check logs if still failing
journalctl -u whatsapp-bridge-prod -n 50
```

### Monitor Service Status
```bash
# Check Python monitor service
ssh -i ~/.ssh/vf_server_key louis@100.96.203.105
systemctl status wa-monitor-prod
tail -f /var/log/wa-monitor/prod.log

# Check WhatsApp bridge
systemctl status whatsapp-bridge-prod
```

### Production Restart
```bash
# ALWAYS use the restart script (handles cache clearing)
ssh -i ~/.ssh/vf_server_key louis@100.96.203.105
/opt/wa-monitor/prod/restart-monitor.sh

# Never use systemctl restart directly - causes Python cache issues
```

## Known Gotchas

### Issue 1: Send Feedback Button - API Routing Issue (PARTIAL FIX - 2026-01-16)
**Problem**: "Send Feedback" button fails with "Failed to communicate with WhatsApp API"
**Root Cause**: Next.js API routing/caching issue - serves old code despite rebuilds
**Current Status**: ⚠️ PARTIAL FIX - Infrastructure working, UI button broken

**What's Working**:
- ✅ WhatsApp Infrastructure: 100% operational
  - WhatsApp Bridge (8083): Receiving messages
  - WhatsApp Sender (8081): Sending messages
  - Microservice (8092): Routing correctly
- ✅ Direct sending via curl works perfectly
- ✅ Production shows ALL 3,777 drops (not limited)
- ✅ Staging shows drops (limited to 100)

**What's NOT Working**:
- ❌ Send Feedback button on both production and staging
- ❌ Next.js API route `/api/wa-monitor-send-feedback` has persistent caching issues
- ❌ Error "Missing required field: dropId" from old cached code

**Workaround (100% Working)**:
```bash
# Send feedback directly via microservice
curl -X POST http://100.96.203.105:8092/send-feedback \
  -H "Content-Type: application/json" \
  -d '{"message": "Your message here", "drNumber": "DR-NUMBER"}'
```

**Attempted Solutions**:
1. Created Express microservice on port 8092 ✅
2. Updated API routes multiple times ✅
3. Cleaned build cache and rebuilt ✅
4. Created new API endpoints (wa-feedback-v2) ✅
5. Disabled conflicting API routes ✅
6. Hard restarts and cache clearing ✅
All infrastructure fixes work, but Next.js continues serving old cached API code.

**To Fix (Future Work)**:
1. Investigate Next.js middleware interference
2. Check for global API interceptors
3. Consider moving to standalone Express API
4. Debug Next.js build cache mechanism
5. Check if Arcjet protection is interfering

**Documentation**:
- Implementation: `docs/fixes/wa-monitor-microservice-implementation.md`
- Failed attempts: `docs/fixes/wa-monitor-send-feedback-fix.md`
**Reference**: Infrastructure 100% working, Next.js API layer issue

### Issue 2: Staging Limited to 100 Drops Display (2026-01-16)
**Problem**: Staging (vf.fibreflow.app) only shows 100 drops while production shows all 3,777
**Root Cause**: Unknown - possibly a LIMIT clause or pagination issue in staging build
**Impact**: Non-critical - use production for full data view
**Workaround**: Use production (https://app.fibreflow.app/wa-monitor)

### Issue 3: Python Cache Issues After Config Change
**Problem**: Changes to projects.yaml not taking effect
**Root Cause**: Python service caching old configuration
**Solution**:
```bash
# ALWAYS use the restart script - it clears cache
/opt/wa-monitor/prod/restart-monitor.sh
# Never use: systemctl restart wa-monitor-prod (keeps cache)
```
**Reference**: `src/modules/wa-monitor/TROUBLESHOOTING.md`

### Issue 3: Missing Drops from WhatsApp Groups
**Problem**: Photos sent to groups not appearing in dashboard
**Root Cause**: Group not configured or service not monitoring
**Solution**:
```bash
# Check if group is configured
ssh -i ~/.ssh/vf_server_key louis@100.96.203.105
cat /opt/wa-monitor/prod/config/projects.yaml | grep "GroupName"

# Add group if missing
nano /opt/wa-monitor/prod/config/projects.yaml
/opt/wa-monitor/prod/restart-monitor.sh
```

### Issue 4: Database Connection Issues
**Problem**: Dashboard shows no data or errors
**Root Cause**: Neon connection string issues
**Solution**:
```bash
# Test database connection
psql $NEON_DATABASE_URL -c "SELECT COUNT(*) FROM qa_photo_reviews;"

# Check recent drops
psql $NEON_DATABASE_URL -c "SELECT * FROM qa_photo_reviews ORDER BY created_at DESC LIMIT 5;"
```

### Issue 5: WhatsApp Database Missing 'deleted' Column (Fixed 2026-01-13)
**Problem**: `ERROR - Error reading WhatsApp DB: no such column: deleted`
**Root Cause**: Database schema missing required column
**Solution**:
```bash
# Add missing column to production database
ssh root@72.60.17.245  # Hostinger VPS
sqlite3 /opt/velo-test-monitor/services/whatsapp-bridge/store/messages.db \
  "ALTER TABLE messages ADD COLUMN deleted BOOLEAN DEFAULT FALSE;"
systemctl restart wa-monitor-prod
```
**Reference**: Fixed in January 2026 session

### Issue 6: Neon Authentication Failed (Fixed 2026-01-13)
**Problem**: `ERROR: password authentication failed for user 'neondb_owner'`
**Root Cause**: Outdated password in configuration
**Solution**:
```bash
# Update password in /opt/wa-monitor/prod/.env
# Old: npg_aRNLhZc1G2CD
# New: npg_MIUZXrg1tEY0
ssh root@72.60.17.245
sed -i "s/npg_aRNLhZc1G2CD/npg_MIUZXrg1tEY0/g" /opt/wa-monitor/prod/.env
systemctl restart wa-monitor-prod
```
**Note**: Always backup .env before changes

### Issue 7: Automated Messages Spamming Groups
**Problem**: Monitor sends unwanted messages to WhatsApp groups
**Root Cause**: No control over automated messaging feature
**Solution**:
```bash
# Add to /opt/wa-monitor/prod/.env
DISABLE_AUTO_MESSAGES=true

# Code modification added to monitor.py (line 204)
# Checks DISABLE_AUTO_MESSAGES before sending
systemctl restart wa-monitor-prod
```
**Reference**: Implemented 2026-01-13 to prevent group spam

## Testing Strategy

### Unit Tests
- Location: `tests/unit/wa-monitor/`
- Coverage requirement: 80%+
- Key areas:
  - API endpoint validation
  - Data extraction from photos (metadata, GPS)
  - Database operations (insert drops, query filters)

### Integration Tests
- Location: `tests/integration/wa-monitor/`
- External dependencies: Test database, mock WhatsApp groups
- Key scenarios:
  - End-to-end monitoring flow
  - WhatsApp group message parsing
  - Send feedback functionality

### E2E Tests
- Location: Production dashboard testing
- Tool: https://app.fibreflow.app/wa-monitor
- Critical user flows:
  1. Monitor receives photos from WhatsApp groups
  2. Dashboard displays new drops in real-time
  3. Filter by project/date range works
  4. Send feedback successfully delivers to WhatsApp
  5. Daily drops per project view accurate

## Monitoring & Alerts

### Health Checks
- Python Monitor: `systemctl status wa-monitor-prod`
- WhatsApp Bridge: `systemctl status whatsapp-bridge-prod`
- Dashboard: https://app.fibreflow.app/wa-monitor
- API: `curl https://app.fibreflow.app/api/wa-monitor-summary`

### Key Metrics
- **Drops per day**: `SELECT COUNT(*) FROM qa_photo_reviews WHERE DATE(created_at) = CURRENT_DATE;`
- **Active projects**: Monitor Lawley, Mohadin, Velo Test, Mamelodi groups
- **Send feedback success rate**: >95% (check bridge logs)
- **Service uptime**: 99%+ (monitor systemd services)

### Logs
- Location: VF Server logs
  - Python monitor: `/var/log/wa-monitor/prod.log`
  - WhatsApp bridge: `journalctl -u whatsapp-bridge-prod`
- Key log patterns:
  - `New drop received from` - Photo processed
  - `Metadata extracted` - GPS/timestamp captured
  - `Feedback sent to group` - WhatsApp delivery success
  - `ERROR: Bridge timeout` - WhatsApp bridge issue
  - `ERROR: Database connection` - Neon issue

## Breaking Changes History

| Date | Change | Migration Required | Reference |
|------|--------|-------------------|-----------|
| 2025-11-XX | Initial wa-monitor implementation | Yes - Create qa_photo_reviews table | Initial deployment |
| 2025-12-XX | Added multiple WhatsApp groups | Yes - Update projects.yaml | Added Lawley, Mohadin |
| 2026-01-XX | Module isolation completed | No - Backward compatible | ISOLATION_GUIDE.md |

## Related Documentation

- [Module Isolation Guide](src/modules/wa-monitor/ISOLATION_GUIDE.md)
- [Troubleshooting Guide](src/modules/wa-monitor/TROUBLESHOOTING.md)
- [Projects Configuration](https://app.fibreflow.app/wa-monitor)

## Contact

**Primary Owner**: Louis
**Team**: FibreFlow Operations
**Server**: louis@100.96.203.105 (SSH key required)
**Dashboard**: https://app.fibreflow.app/wa-monitor
