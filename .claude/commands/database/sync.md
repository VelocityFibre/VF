---
description: Sync Neon PostgreSQL data to Convex backend
---

# Database Synchronization: Neon → Convex

Synchronize data from Neon PostgreSQL (source of truth) to Convex backend (operational data).

## Overview

**Purpose**: Keep Convex real-time backend in sync with production Neon database
**Direction**: Neon (source) → Convex (destination)
**Frequency**: On-demand (run this command when schema or data changes)

## Pre-Sync Checks

Before running sync:
1. ✅ Verify Neon database is accessible
2. ✅ Verify Convex deployment is up-to-date
3. ✅ Check for pending Convex function changes
4. ✅ Confirm sufficient API rate limits

## Sync Execution

Run the synchronization script:

```bash
./venv/bin/python3 sync_neon_to_convex.py
```

## Monitoring

Track sync progress in real-time:

```markdown
## Sync Progress

**Started**: [Timestamp]

### Tables to Sync
- [ ] contractors (20 records)
- [ ] projects (2 records)
- [ ] [other tables...]

### Sync Status
✅ contractors: 20/20 records synced (took 1.2s)
✅ projects: 2/2 records synced (took 0.5s)
⚠️ [table]: Partial sync - 45/50 (retrying...)
❌ [table]: Failed - [error message]

**Total Progress**: XX/XX records (YY%)
**Elapsed Time**: X.Xs
```

## Tables Synced

Primary tables synchronized:
1. **contractors** - Contractor master data
2. **projects** - Active project information
3. **tasks** - Task management data (if applicable)
4. **syncRecords** - Sync operation tracking

Additional tables can be configured in `sync_neon_to_convex.py`.

## Sync Strategy

### Full Sync vs Incremental
- **Full Sync** (default): Replace all Convex data with Neon data
- **Incremental** (if configured): Only sync changes since last run

### Conflict Resolution
- **Strategy**: Neon data always wins (source of truth)
- **Convex-only fields**: Preserved if not in Neon schema
- **Deleted records**: Optionally soft-delete in Convex

## Post-Sync Validation

After sync completes:

### Step 1: Verify Record Counts
```bash
# Check Convex record counts
npx convex run _system:listTables
npx convex run contractors:count
npx convex run projects:count
```

### Step 2: Spot Check Data
Query sample records to verify data accuracy:
```bash
# Example: Check first contractor
npx convex run contractors:get '{"id": "contractor-1"}'
```

### Step 3: Test Convex Functions
```bash
./venv/bin/python3 test_convex_deployed_functions.py
```

### Step 4: Verify syncRecords
Check sync history:
```bash
npx convex run syncRecords:list
```

## Sync Report

Generate detailed sync report:

```markdown
## Sync Report: [Timestamp]

**Status**: ✅ SUCCESS / ⚠️ PARTIAL / ❌ FAILED
**Duration**: X.Xs
**Records Synced**: XXX total

### Table Summary
| Table | Neon Count | Convex Count | Status |
|-------|------------|--------------|--------|
| contractors | 20 | 20 | ✅ Match |
| projects | 2 | 2 | ✅ Match |
| tasks | 150 | 150 | ✅ Match |

### Errors (if any)
🔴 [Critical error details]
🟡 [Warning details]

### Performance Metrics
- **Average record sync time**: Xms
- **API calls made**: XXX
- **Data transferred**: XX KB
- **Success rate**: XX%

### Recommendations
- [Action item 1]
- [Action item 2]
```

## Troubleshooting

### Common Issues

#### Issue: Connection timeout to Neon
**Cause**: Database is slow or unreachable
**Solution**:
1. Check `NEON_DATABASE_URL` in `.env`
2. Verify network connectivity
3. Check Neon dashboard for database status

#### Issue: Convex API rate limit
**Cause**: Too many requests in short time
**Solution**:
1. Add delays between batches in sync script
2. Reduce batch size
3. Wait for rate limit reset (usually 1 minute)

#### Issue: Schema mismatch
**Cause**: Convex schema doesn't match Neon schema
**Solution**:
1. Update Convex schema in `convex/schema.ts`
2. Deploy schema changes: `npx convex deploy`
3. Re-run sync

#### Issue: Partial sync (some records missing)
**Cause**: Transaction failure or network interruption
**Solution**:
1. Check sync logs for specific errors
2. Re-run sync (should be idempotent)
3. Verify data manually for affected tables

## Sync Configuration

Edit `sync_neon_to_convex.py` to customize:

```python
# Tables to sync
SYNC_TABLES = [
    'contractors',
    'projects',
    'tasks',
    # Add more tables as needed
]

# Sync options
BATCH_SIZE = 100  # Records per batch
INCREMENTAL = False  # Full sync vs incremental
SOFT_DELETE = True  # Soft delete vs hard delete
```

## When to Run Sync

Run this command when:
- ✅ Neon schema changes (new tables, columns)
- ✅ Bulk data updates in Neon
- ✅ After data migrations
- ✅ Setting up new Convex deployment
- ✅ Recovering from Convex data loss
- ⚠️ Regularly (scheduled, e.g., nightly)

Don't run sync for:
- ❌ Real-time data updates (use Convex mutations directly)
- ❌ Small single-record changes (update Convex directly)
- ❌ Testing (use test database instead)

## Automation

To schedule automatic syncs:

### Option 1: Cron Job
```bash
# Add to crontab (sync nightly at 2 AM)
0 2 * * * cd /path/to/project && ./venv/bin/python3 sync_neon_to_convex.py >> logs/sync.log 2>&1
```

### Option 2: Convex Cron
Create Convex scheduled function:
```typescript
// convex/crons.ts
import { cronJobs } from "convex/server";

const crons = cronJobs();

crons.interval(
  "sync-from-neon",
  { hours: 24 }, // Run daily
  async (ctx) => {
    // Trigger sync logic
  }
);

export default crons;
```

### Option 3: Manual (Recommended for now)
Run manually when needed until automation is proven reliable.

## Best Practices

1. **Test First**: Run sync in development before production
2. **Backup**: Backup Convex data before major syncs
3. **Monitor**: Watch sync logs for errors
4. **Validate**: Always verify record counts after sync
5. **Schedule**: Run during low-traffic periods
6. **Alert**: Set up alerts for sync failures

## Integration with Deployment

Include sync in deployment workflow:

```bash
# deployment_checklist.sh
echo "Deploying Convex functions..."
npx convex deploy

echo "Syncing Neon data to Convex..."
./venv/bin/python3 sync_neon_to_convex.py

echo "Validating sync..."
./venv/bin/python3 test_convex_deployed_functions.py
```

## Data Flow Architecture

```
┌─────────────────┐
│  Neon Database  │  ← Source of Truth (104 tables)
│  (PostgreSQL)   │
└────────┬────────┘
         │
         │ sync_neon_to_convex.py
         │
         ↓
┌─────────────────┐
│     Convex      │  ← Operational Data (Real-time)
│    Backend      │
└────────┬────────┘
         │
         ↓
┌─────────────────┐
│  FibreFlow UI   │  ← Web Interface
│   & Agents      │
└─────────────────┘
```

## Success Criteria

Sync is successful when:
- ✅ All tables synced without errors
- ✅ Record counts match between Neon and Convex
- ✅ Spot-checked data is accurate
- ✅ Convex functions work with synced data
- ✅ Sync completed in reasonable time (<5 minutes for typical data)

## Rollback

If sync causes issues:

1. **Restore Convex from backup** (if available)
2. **Clear Convex tables**:
   ```bash
   # Manual clear via Convex dashboard
   # Or write clear functions in convex/
   ```
3. **Re-run previous good sync**
4. **Investigate and fix sync script**

## Documentation

After sync:
- [ ] Update `CONVEX_SYNC_REQUIREMENTS.md` if process changed
- [ ] Document any schema changes
- [ ] Note any new tables added to sync
- [ ] Update this command if sync script evolves
