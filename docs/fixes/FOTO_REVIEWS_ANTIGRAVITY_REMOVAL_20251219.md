# Foto Reviews - Antigravity API Removal Fix

**Date**: 2025-12-19  
**Issue**: https://vf.fibreflow.app/foto-reviews returning 500 errors  
**Root Cause**: API endpoints still proxying to non-existent ANTIGRAVITY_API service

## Problem

The foto-reviews page was failing with 500 errors because the API endpoints were trying to proxy requests to an "ANTIGRAVITY_API" backend service on port 8001 that was not running:

```typescript
const ANTIGRAVITY_API_URL = process.env.ANTIGRAVITY_API_URL || 'http://localhost:8001';
const url = `${ANTIGRAVITY_API_URL}/api/queue/status/${jobId}`;
const response = await fetch(url); // ❌ FAILS - service not running
```

### Affected Endpoints
- `GET /api/foto-reviews/[jobId]` - 500 error
- `GET /api/foto-reviews/[jobId]/history` - 500 error
- `GET /api/foto-reviews/pending` - ✅ Already fixed (was using Neon)

## Solution

Replaced the Antigravity API proxy endpoints with **direct Neon database queries** using the `foto_ai_reviews` table.

### Files Modified

#### 1. `/srv/data/apps/fibreflow/pages/api/foto-reviews/[jobId].ts`

**Before**: Proxied to `${ANTIGRAVITY_API_URL}/api/queue/status/${jobId}`

**After**: Direct Neon query
```typescript
import { neon } from '@neondatabase/serverless';
const sql = neon(process.env.DATABASE_URL!);

const rows = await sql`
  SELECT
    dr_number,
    overall_status,
    average_score,
    total_steps,
    passed_steps,
    step_results,
    markdown_report,
    feedback_sent,
    feedback_sent_at,
    evaluation_date,
    created_at,
    updated_at
  FROM foto_ai_reviews
  WHERE dr_number = ${jobId}
  LIMIT 1
`;
```

#### 2. `/srv/data/apps/fibreflow/pages/api/foto-reviews/[jobId]/history.ts`

**Before**: Proxied to `${ANTIGRAVITY_API_URL}/api/queue/${jobId}/history`

**After**: Returns stub data (history tracking not implemented yet)
```typescript
return res.status(200).json({
  success: true,
  data: {
    job_id: jobId,
    history: []  // TODO: Implement history table when needed
  }
});
```

## Deployment Steps

1. **Uploaded fixed files** to VF Server (100.96.203.105)
   ```bash
   scp fix_jobid_endpoint.ts louis@100.96.203.105:/srv/data/apps/fibreflow/pages/api/foto-reviews/[jobId].ts
   scp fix_history_endpoint.ts louis@100.96.203.105:/srv/data/apps/fibreflow/pages/api/foto-reviews/[jobId]/history.ts
   ```

2. **Rebuilt Next.js application**
   ```bash
   cd /srv/data/apps/fibreflow
   npm run build
   ```

3. **Restarted Next.js server**
   ```bash
   kill 424872 424827  # Old processes
   PORT=3005 NODE_ENV=production nohup npm run start > /tmp/next_vf_$(date +%s).log 2>&1 &
   ```

## Verification

### API Endpoints - All Working ✅

```bash
# Test review details
curl 'http://localhost:3005/api/foto-reviews/DR1733758' | jq '.success, .data.dr_number'
# Output: true, "DR1733758"

# Test history
curl 'http://localhost:3005/api/foto-reviews/DR1733758/history' | jq '.success, .data.history'
# Output: true, []

# Test pending reviews
curl 'http://localhost:3005/api/foto-reviews/pending?limit=2' | jq '{success, total: .data.total, count: (.data.reviews | length)}'
# Output: {"success": true, "total": 27, "count": 2}

# Test page load
curl -o /dev/null -w '%{http_code}' 'http://localhost:3005/foto-reviews'
# Output: 200
```

## Architecture

### Data Flow (After Fix)

```
┌─────────────────────────────────────────────────────────────┐
│  Frontend: https://vf.fibreflow.app/foto-reviews           │
│  (React Component: FotoReviewsDashboard.tsx)                │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│  Next.js API Routes (Port 3005)                             │
│  ├─ GET /api/foto-reviews/pending                           │
│  ├─ GET /api/foto-reviews/[jobId]                           │
│  └─ GET /api/foto-reviews/[jobId]/history                   │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│  Neon PostgreSQL Database                                   │
│  Table: foto_ai_reviews                                     │
│  - 27+ evaluations                                          │
│  - DR numbers, scores, step results                         │
│  - Markdown reports from Qwen VLM                           │
└─────────────────────────────────────────────────────────────┘
```

### VLM Integration (Unchanged)

The **Qwen VLM model** on port 8100 is still used for photo evaluations:
- Model: Qwen/Qwen3-VL-8B-Instruct
- Port: 8100
- Context: 16384 tokens
- Function: Analyzes DR photos and generates scores/feedback
- Results: Stored in `foto_ai_reviews` table

## Key Decisions

1. **Why remove Antigravity API?**
   - Service was never deployed/running
   - Adds unnecessary complexity
   - Direct database access is faster and simpler
   - Single source of truth (Neon database)

2. **Why stub the history endpoint?**
   - History tracking not implemented in current schema
   - Returns empty array to prevent errors
   - Can be implemented later with `foto_ai_reviews_history` table

3. **Why use Neon tagged templates?**
   - Required by `@neondatabase/serverless` library
   - Prevents SQL injection
   - Cleaner syntax than parameterized queries

## Future Improvements

- [ ] Implement history tracking table
- [ ] Add approval/rejection workflow
- [ ] Track reviewer information
- [ ] Add audit trail for feedback edits

## Related Documentation

- Main module docs: `/docs/deployment/WA_MONITOR_MODULE_DOCUMENTATION.md`
- VLM setup: See CLAUDE.md line 620
- Database schema: See module docs line 24-46

---

**Status**: ✅ FIXED AND DEPLOYED  
**Server**: VF Server (100.96.203.105)  
**Next.js PID**: 565392  
**Port**: 3005
