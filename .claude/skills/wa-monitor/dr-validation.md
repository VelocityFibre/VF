---
name: wa-monitor-dr-validation
version: 1.0.0
description: DR Validation Tool - CSV/Excel reconciliation for Janice
author: Claude
tags: [wa-monitor, dr-validation, csv, reconciliation, janice]
requires: [neon-database, vf-server]
---

# WA Monitor DR Validation Skill

CSV/Excel reconciliation tool for validating drop records against WA monitor database. Used by Janice to ensure all drops from spreadsheets are captured in the monitoring system.

## Overview

**URL**: https://app.fibreflow.app/wa-monitor/dr-validation
**Purpose**: Compare CSV/Excel files against WA monitor database
**User**: Janice (operations team)
**NOT**: This is NOT a photo evaluation tool - it's data reconciliation

## Core Functionality

### What It Does
1. **Upload & Parse**: Accepts CSV/Excel files with drop records
2. **Compare**: Matches records against `qa_photo_reviews` table
3. **Identify Gaps**:
   - ✅ In both CSV and DB (matched records)
   - ⚠️ In CSV but not in DB (missing from monitoring)
   - ℹ️ In DB but not in CSV (extra records)
4. **Bulk Add**: Add missing drops to database with one click

### Key Features
- Auto-detects dates from uploaded files
- Project-specific validation (Lawley, Mohadin, etc.)
- Date mismatch detection with auto-correction
- Shows totals: CSV records vs DB records
- Bulk operations for efficiency

## Quick Commands

### Check Page Status
```bash
# Check if page is accessible
curl -I https://app.fibreflow.app/wa-monitor/dr-validation

# View page source (requires auth)
ssh -i ~/.ssh/vf_server_key louis@100.96.203.105 \
  'cat /home/velo/fibreflow/app/\(main\)/wa-monitor/dr-validation/page.tsx'
```

### API Testing
```bash
# Test dr-validation API endpoint
curl -X GET "https://app.fibreflow.app/api/wa-monitor-daily-drops" \
  -H "Authorization: Bearer YOUR_TOKEN"

# Check database for recent drops
ssh -i ~/.ssh/vf_server_key louis@100.96.203.105 \
  'psql $NEON_DATABASE_URL -c "SELECT COUNT(*) FROM qa_photo_reviews WHERE created_at > NOW() - INTERVAL '\''7 days'\'';"'
```

### Common Operations

#### Add Missing Drops Manually
```sql
-- Connect to database
psql $NEON_DATABASE_URL

-- Insert missing drop
INSERT INTO qa_photo_reviews (
  dr_number,
  project,
  date,
  time,
  created_at
) VALUES (
  'DR1234567',
  'Lawley',
  '2024-01-14',
  '10:30:00',
  NOW()
);
```

#### Check Validation Discrepancies
```sql
-- Find drops by project and date
SELECT dr_number, project, date, time
FROM qa_photo_reviews
WHERE project = 'Lawley'
  AND date = '2024-01-14'
ORDER BY time;

-- Count drops per project per day
SELECT project, date, COUNT(*) as drop_count
FROM qa_photo_reviews
WHERE date >= CURRENT_DATE - INTERVAL '7 days'
GROUP BY project, date
ORDER BY date DESC, project;
```

## File Locations

**Frontend Code**:
```bash
/home/velo/fibreflow/app/(main)/wa-monitor/dr-validation/
├── page.tsx                 # Route definition
└── DrValidationClient.tsx   # Main component logic
```

**API Endpoints**:
- `POST /api/wa-monitor-dr-validation` - Validate CSV against database
- `PUT /api/wa-monitor-dr-validation` - Add missing drops to database
- `GET /api/wa-monitor-daily-drops` - Fetch available projects

## Troubleshooting

### Issue: "No matches found" but CSV has data
**Cause**: Date mismatch between CSV and selected date
**Solution**: Tool auto-detects and corrects date from CSV

### Issue: Upload fails
**Cause**: Wrong file format
**Solution**: Only CSV and Excel (.xlsx) files supported

### Issue: Can't add missing drops
**Cause**: API endpoint issue or permissions
**Solution**: Check user has write permissions to `qa_photo_reviews` table

## Database Schema

```sql
-- Relevant columns in qa_photo_reviews
CREATE TABLE qa_photo_reviews (
  id SERIAL PRIMARY KEY,
  dr_number VARCHAR(20) NOT NULL,
  project VARCHAR(100),
  date DATE,
  time TIME,
  created_at TIMESTAMP DEFAULT NOW(),
  -- other columns for photo evaluation (not used here)
);

-- Index for faster lookups
CREATE INDEX idx_qa_photo_reviews_dr_number ON qa_photo_reviews(dr_number);
CREATE INDEX idx_qa_photo_reviews_project_date ON qa_photo_reviews(project, date);
```

## CSV Format Expected

The tool expects CSV files with these columns (flexible parsing):
```csv
Date,Drop Number,Time
2024-01-14,DR1234567,10:30
2024-01-14,DR1234568,10:45
```

Or Excel with similar structure. The parser is flexible and auto-detects column mappings.

## Important Notes

⚠️ **This is NOT a photo evaluation tool** - It's purely for data reconciliation
📊 **Used by Janice** - Operational tool for ensuring data completeness
🔄 **One-way sync** - Only adds missing drops, doesn't remove extras
📅 **Date-aware** - Validates based on selected date, with auto-correction

## Related Documentation
- Main WA Monitor: `.claude/modules/wa-monitor.md`
- Photo Evaluation: `.claude/skills/wa-monitor/skill.md`
- API Documentation: Contact backend team