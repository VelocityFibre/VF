# Foto Review Correction UI - Implementation Plan

**Date**: 2026-01-05
**Status**: Ready to Build
**Priority**: High - Enables VLM improvement over time

## Executive Summary

Build a human correction interface for the VLM foto evaluation system. When VLM makes incorrect judgments, humans can provide corrections that are saved to the database, creating a dataset for systematic improvement.

## Problem Statement

- VLM (Qwen3-VL-8B) evaluates installation photos against 10 QA steps
- VLM sometimes makes mistakes (misses details, too strict/lenient)
- Currently no way to track or learn from these mistakes
- No feedback loop to improve the system

## Solution Overview

Add correction UI to the foto-review page that allows users to:
1. Mark VLM evaluations as incorrect
2. Provide correct assessment with reasoning
3. Build a correction dataset for analysis
4. Enable systematic prompt/criteria improvements

## Architecture

### Data Flow
```
foto-review page → Correction UI → API endpoint → Database
                                         ↓
                              qa_photo_reviews table
                              - incorrect_steps: [3, 6]
                              - incorrect_comments: {"3": "..."}
                              - human_overrides: {"3": {...}}
```

### Components to Build

1. **Frontend Component**: `StepCorrectionControls.tsx`
2. **API Endpoint**: `/pages/api/foto/corrections.ts`
3. **Database Migration**: Add `human_overrides` JSONB column
4. **UI Integration**: Update `EvaluationResults.tsx`

## Database Schema

### New Column in `qa_photo_reviews`

```sql
ALTER TABLE qa_photo_reviews
ADD COLUMN IF NOT EXISTS human_overrides JSONB DEFAULT '{}'::jsonb;

-- Structure:
{
  "3": {
    "vlm_score": 2,
    "vlm_passed": false,
    "human_score": 8,
    "human_passed": true,
    "comment": "Cable entry IS visible - VLM missed the clamp",
    "corrected_by": "user@email.com",
    "corrected_at": "2026-01-05T15:30:00Z"
  }
}
```

### Existing Fields (Already There)
- `incorrect_steps`: ARRAY - List of step numbers with disagreements
- `incorrect_comments`: JSONB - Map of step → correction comment

## UI Design

### Step Display (Before Correction)
```
┌────────────────────────────────────────────┐
│ Step 3: Cable Entry Outside                │
│ ❌ FAIL - Score: 2/10                      │
│ 💬 "Cable entry not clearly visible"       │
│                                            │
│ [✅ Agree] [❌ Disagree] [💬 Add Note]     │
└────────────────────────────────────────────┘
```

### Correction Modal/Inline Form
```
┌────────────────────────────────────────────┐
│ ⚠️ Correct This Evaluation                 │
├────────────────────────────────────────────┤
│ VLM Said:                                  │
│ • Status: FAIL                             │
│ • Score: 2/10                              │
│ • Comment: "Cable entry not clearly..."    │
│                                            │
│ Your Correction:                           │
│ ┌──────────────────────────────────────┐  │
│ │ [Text input for correction comment]  │  │
│ └──────────────────────────────────────┘  │
│                                            │
│ Correct Score: [Slider] 8/10               │
│ Should Pass?: ● Yes  ○ No                  │
│                                            │
│ [Cancel] [Submit Correction]               │
└────────────────────────────────────────────┘
```

### Step Display (After Correction)
```
┌────────────────────────────────────────────┐
│ Step 3: Cable Entry Outside                │
│                                            │
│ ⚠️ HUMAN OVERRIDE                          │
│ ✅ PASS - Score: 8/10                      │
│ 💬 "Cable entry IS visible - VLM missed    │
│     the clamp on the right side"           │
│                                            │
│ 🤖 Original VLM: FAIL (2/10) [dimmed]     │
│                                            │
│ 👤 Corrected by you • 5 min ago            │
└────────────────────────────────────────────┘
```

## API Specification

### POST /api/foto/corrections

**Request Body**:
```json
{
  "dr_number": "DR1733214",
  "step_number": 3,
  "vlm_evaluation": {
    "score": 2,
    "passed": false,
    "comment": "Cable entry not clearly visible"
  },
  "human_correction": {
    "score": 8,
    "passed": true,
    "comment": "Cable entry IS visible - VLM missed the clamp on right side"
  },
  "corrected_by": "user@email.com"
}
```

**Response**:
```json
{
  "success": true,
  "data": {
    "dr_number": "DR1733214",
    "step_number": 3,
    "correction_saved": true,
    "updated_at": "2026-01-05T15:30:00Z"
  }
}
```

## Implementation Phases

### Phase 1: MVP (4-6 hours)
- [ ] Add `human_overrides` column to database
- [ ] Create basic correction modal component
- [ ] Build API endpoint for saving corrections
- [ ] Add "Disagree" button to each step
- [ ] Display human override badge on corrected steps

### Phase 2: Enhanced UI (2-3 hours)
- [ ] Add score slider
- [ ] Add pass/fail toggle
- [ ] Show correction history
- [ ] Add edit/delete correction feature

### Phase 3: Analytics (3-4 hours)
- [ ] Build correction analytics dashboard
- [ ] Show VLM accuracy by step
- [ ] Identify most-corrected steps
- [ ] Generate improvement recommendations

## Improvement Loop Process

### Weekly Cycle
```
Week 1: Collect corrections (humans mark disagreements)
   ↓
Week 2: Analyze patterns
   SQL: SELECT step_number, COUNT(*)
        FROM corrections
        GROUP BY step_number
   ↓
Week 3: Apply fixes
   - Update QA criteria (config file)
   - Enhance prompt (add specific guidance)
   ↓
Week 4: Measure improvement
   - Compare correction rate before/after
   - Track accuracy improvement
```

### Example Analysis Query
```sql
-- Find most-corrected steps
SELECT
  step_number,
  COUNT(*) as correction_count,
  AVG(CASE
    WHEN (human_overrides->step_number::text->>'human_passed')::boolean !=
         (human_overrides->step_number::text->>'vlm_passed')::boolean
    THEN 1 ELSE 0
  END) as disagreement_rate
FROM qa_photo_reviews
WHERE human_overrides != '{}'::jsonb
GROUP BY step_number
ORDER BY correction_count DESC;
```

## Files to Create/Modify

### New Files
1. `/var/www/fibreflow/src/modules/foto-review/components/StepCorrectionControls.tsx`
2. `/var/www/fibreflow/src/modules/foto-review/components/CorrectionModal.tsx`
3. `/var/www/fibreflow/pages/api/foto/corrections.ts`
4. `/var/www/fibreflow/src/modules/foto-review/hooks/useCorrectionState.ts`

### Modified Files
1. `/var/www/fibreflow/src/modules/foto-review/components/EvaluationResults.tsx` - Add correction UI
2. `/var/www/fibreflow/src/modules/foto-review/types/index.ts` - Add correction types

## Security Considerations

- **Authentication**: Require logged-in user to submit corrections
- **Authorization**: Track who made each correction (audit trail)
- **Validation**:
  - DR number must exist
  - Step number must be 1-10
  - Score must be 0-10
  - Comment required (min 10 chars)
- **Rate Limiting**: Max 10 corrections per minute per user

## Success Metrics

### Short-term (1 month)
- Correction UI implemented and deployed
- 50+ corrections collected
- Identify top 3 problem steps

### Medium-term (3 months)
- 200+ corrections collected
- Updated prompts/criteria for problem steps
- Measure 20% reduction in correction rate

### Long-term (6 months)
- 500+ corrections collected
- VLM accuracy improved by 30%
- Fine-tuning dataset ready

## Technical Stack

- **Frontend**: React, TypeScript, Tailwind CSS
- **Backend**: Next.js API routes
- **Database**: PostgreSQL (Neon)
- **Deployment**: Hostinger VPS (PM2)

## Deployment Process

1. **Development**: Test on VF Server (port 3006)
2. **Staging**: Test on Hostinger with test DRs
3. **Production**: Deploy to Hostinger production
4. **Monitoring**: Track correction submissions via logs

```bash
# Deployment commands
cd /var/www/fibreflow
git pull origin main
npm run build
pm2 restart fibreflow-prod
```

## Future Enhancements

1. **Batch Corrections**: Correct multiple steps at once
2. **Correction Templates**: Common correction patterns
3. **AI Suggestions**: Show similar past corrections
4. **Fine-tuning Pipeline**: Auto-generate training data
5. **A/B Testing**: Test prompt variations with subset
6. **Correction Voting**: Multiple users vote on disagreements

## Resources

- **VLM Service**: `/var/www/fibreflow/src/modules/foto-review/services/fotoVlmService.ts`
- **QA Config**: `/var/www/fibreflow/config/qa-evaluation-steps.json`
- **Database**: Neon PostgreSQL - `qa_photo_reviews` table
- **Frontend**: https://app.fibreflow.app/foto-review

## Contact & Support

- **System Owner**: Louis
- **VPS Access**: root@72.60.17.245 (password in CLAUDE.md)
- **Database**: NEON_DATABASE_URL in .env
- **Documentation**: This file + CLAUDE.md

---

**Status**: Ready to implement Phase 1 MVP
**Next Step**: Build StepCorrectionControls component and API endpoint
