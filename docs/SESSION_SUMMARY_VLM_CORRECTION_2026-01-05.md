# Session Summary: VLM Foto Review System Investigation & Improvement

**Date**: 2026-01-05
**Session Duration**: ~3 hours
**Status**: ✅ Issues Resolved, Improvement Plan Created

---

## Issues Resolved

### 1. VLM Not Evaluating Photos ✅
**Problem**: User saw "eval nothing" on https://app.fibreflow.app/foto-review?dr=DR1733214

**Root Cause**:
- VLM server crashed at 10:45 AM
- Evaluation ran at 08:04 AM with VLM down → fell back to "BOSS evaluation" (basic check)
- Cached stale results in database

**Solution Applied**:
1. Restarted VLM server (Qwen3-VL-8B-Instruct on port 8100)
2. Added `VLM_API_URL=http://100.96.203.105:8100` to Hostinger production
3. Restarted production app with `pm2 restart fibreflow-prod --update-env`
4. Deleted cached evaluation from database
5. Forced fresh evaluation with `force_vlm=true` parameter

**Result**: VLM now providing detailed AI analysis:
- "Clear, well-lit photo showing the exterior of the house, including the address plaque '7006 REBONE-STR'..."
- 4/10 steps passed (40%)

---

### 2. Project Not Showing ✅
**Problem**: DR1733214 showed project as "Unknown"

**Root Cause**:
- DR1733214 not in `drops` table (where project relationships are stored)
- Only existed in `qa_photo_reviews` and BOSS API

**Solution Applied**:
1. Checked WA Monitor (`qa_photo_reviews`) → Found project: "Lawley"
2. Created drops record:
```sql
INSERT INTO drops (id, drop_number, project_id, address)
VALUES (
  '8d33fba5-71e8-4341-a185-d0463acdc89e',
  'DR1733214',
  '4eb13426-b2a1-472d-9b3c-277082ae9b55', -- Lawley
  '7006 REBONE-STR, Mamelodi East'
);
```

**Result**: Database now correctly shows DR1733214 → Lawley project linkage

---

## System Architecture Documented

### Infrastructure
```
Production App: Hostinger VPS (72.60.17.245)
  ↓ PM2: fibreflow-prod (port 3005)
  ↓ https://app.fibreflow.app

VLM Compute: VF Server (100.96.203.105)
  ↓ Qwen3-VL-8B-Instruct (port 8100)
  ↓ GPU: RTX 5090

Photo Storage: BOSS VPS (72.61.197.178:8001)
  ↓ Stores photos via WhatsApp
  ↓ 20 photos for DR1733214
```

### Data Flow for Foto Evaluations
```
User submits photos via WhatsApp
  ↓
Photos stored on BOSS VPS
  ↓
VLM service fetches photos from BOSS API
  ↓
Converts to base64, sends to VLM (port 8100)
  ↓
VLM analyzes against 10 QA steps
  ↓
Results saved to Neon: foto_ai_reviews table
  ↓
Frontend displays at app.fibreflow.app/foto-review
```

---

## VLM Evaluation Process Explained

### QA Steps (Loaded from Config)
**File**: `/var/www/fibreflow/config/qa-evaluation-steps.json`

10 steps evaluated:
1. House Photo
2. Cable Span from Pole
3. Cable Entry Outside
4. Cable Entry Inside
5. Wall for Installation
6. ONT Back & Barcode
7. Power Meter Reading
8. UPS Serial Number
9. Final Installation
10. Green Lights & DR Label

### Evaluation Prompt (Smart Batch)
**Function**: `buildSmartBatchEvaluationPrompt()` in `fotoVlmService.ts`

**Key Features**:
- Analyzes ALL photos at once (not one-by-one)
- VLM identifies what each photo shows
- Matches photos to appropriate QA steps
- One photo can match multiple steps
- Scores 0-10, Pass = 7+

**Parameters**:
- Model: Qwen3-VL-8B-Instruct
- Temperature: 0.1 (consistent results)
- Max Tokens: 2000
- Timeout: 3 minutes
- Batch Size: 5 photos at a time

---

## Key Learnings

### Port Conflict Discovered
- Hein's dev server took over port 3005 on VF Server at 15:01
- Caused confusion during testing (hitting dev server instead of production)
- Production is on Hostinger, not VF Server

### Config-Based QA Steps
- QA criteria stored in JSON file (not hardcoded)
- Can update evaluation criteria without code changes
- Just edit config file and restart app

### Architecture Philosophy
**"Customer-critical on datacenter, compute-heavy on-premises"**
- Critical services (app, data) → Hostinger (99.9% uptime)
- Heavy compute (VLM, GPU) → VF Server (85-95% uptime)

---

## Improvement Plan Created

### Problem
- No way to correct VLM mistakes
- No feedback loop to improve accuracy
- Can't track which steps VLM struggles with

### Solution: Correction UI
Build interface allowing humans to:
1. Mark VLM evaluations as incorrect
2. Provide correct assessment + reasoning
3. Save corrections to database
4. Analyze patterns → improve prompts/criteria

### Implementation
**Phase 1 (MVP)**: 4-6 hours
- Add correction modal to foto-review page
- API endpoint: POST /api/foto/corrections
- Database: Add `human_overrides` JSONB column
- Display human overrides on corrected steps

**Full Plan**: `/home/louisdup/Agents/claude/docs/FOTO_REVIEW_CORRECTION_UI_PLAN.md`

---

## Files Modified/Created This Session

### Modified
- `/var/www/fibreflow/.env.production` - Added VLM_API_URL
- Database: `drops` table - Created record for DR1733214
- Database: `foto_ai_reviews` - Deleted stale evaluation

### Created
- `/home/louisdup/Agents/claude/docs/FOTO_REVIEW_CORRECTION_UI_PLAN.md`
- `/home/louisdup/Agents/claude/docs/SESSION_SUMMARY_VLM_CORRECTION_2026-01-05.md`

---

## Action Items

### Immediate
- [x] VLM server running
- [x] Production configured with VLM_API_URL
- [x] DR1733214 linked to Lawley project
- [x] Improvement plan documented

### Next Steps
1. **Build Correction UI** (this session)
   - StepCorrectionControls component
   - API endpoint
   - Database migration

2. **Monitor VLM Performance**
   - Track evaluation accuracy
   - Collect user feedback

3. **Iterative Improvement**
   - Update QA criteria based on corrections
   - Enhance prompts for problem steps
   - Measure accuracy improvements

---

## Commands Used

```bash
# VLM Server
python3 .claude/skills/vf-server/scripts/execute.py 'curl http://localhost:8100/v1/models'

# Database Operations
.claude/skills/database-operations/scripts/execute_query.py --query "..."

# Production Deployment
HOSTINGER_PASSWORD="VeloF@2025@@" .claude/skills/hostinger-vps/scripts/execute.py 'pm2 restart fibreflow-prod'

# Delete Cached Evaluation
python3 << 'EOF'
import psycopg2
conn = psycopg2.connect(database_url)
cursor.execute("DELETE FROM foto_ai_reviews WHERE dr_number = 'DR1733214'")
conn.commit()
EOF
```

---

## Reference URLs

- **Production App**: https://app.fibreflow.app/foto-review?dr=DR1733214
- **VLM Server**: http://100.96.203.105:8100
- **BOSS API**: http://72.61.197.178:8001/api/photos
- **WA Monitor**: https://app.fibreflow.app/wa-monitor

---

**Session Complete**: All issues resolved, improvement plan documented, ready to build correction UI
