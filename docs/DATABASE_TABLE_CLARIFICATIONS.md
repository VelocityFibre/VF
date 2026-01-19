# Database Table Clarifications

**Purpose:** Clear up common confusion about similar table names in the FibreFlow database

**Last Updated:** 2026-01-12

---

## The "Two Drops" Problem

### ⚠️ MOST COMMON CONFUSION

The FibreFlow database has **TWO completely different tables** that both relate to "drops":

| Table | Purpose | Source | Key Column | Page/Module |
|-------|---------|--------|------------|-------------|
| **`drops`** | SOW planning data | Excel/CSV imports | `project_id` (UUID) | `/sow`, `/fiber-stringing` |
| **`qa_photo_reviews`** | WhatsApp QA tracking | WhatsApp messages | `project` (VARCHAR project name) | `/wa-monitor` |

### Why This Is Confusing

Both tables:
- Deal with "drops" (fiber drop cables)
- Have similar data (drop numbers, contractors, dates)
- Are used in quality assurance workflows

### Critical Differences

```
┌─────────────────────────────────────────────────────────────────┐
│ drops table (SOW Planning)                                      │
├─────────────────────────────────────────────────────────────────┤
│ Purpose:     Pre-construction planning from Excel BOQs          │
│ Source:      Manual Excel/CSV imports                           │
│ Lifecycle:   Created during project planning                    │
│ Key:         project_id (UUID foreign key to projects table)    │
│ Drop ID:     Unique per project (e.g., "001", "002")           │
│ Contractor:  May not be assigned yet                            │
│ Status:      Planning stages (not_started, in_progress, done)   │
└─────────────────────────────────────────────────────────────────┘

vs

┌─────────────────────────────────────────────────────────────────┐
│ qa_photo_reviews table (WhatsApp QA Tracking)                   │
├─────────────────────────────────────────────────────────────────┤
│ Purpose:     Track QA photo submissions via WhatsApp            │
│ Source:      WhatsApp messages (automated parsing)              │
│ Lifecycle:   Created when contractor sends QA photos            │
│ Key:         project (VARCHAR project name, e.g., "GP12")       │
│ Drop ID:     DR number (e.g., "DR001", "DR123")                 │
│ Contractor:  Always present (who sent the message)              │
│ Status:      12 boolean QA step columns (step_1 through step_12)│
└─────────────────────────────────────────────────────────────────┘
```

### Schema Comparison

**drops table:**
```sql
-- SOW Planning Data
CREATE TABLE drops (
  id UUID PRIMARY KEY,
  project_id UUID REFERENCES projects(id),  -- ⚠️ UUID foreign key
  drop_number VARCHAR,
  contractor_id UUID,
  address VARCHAR,
  latitude DECIMAL,
  longitude DECIMAL,
  status VARCHAR,  -- Planning status
  created_at TIMESTAMP
  -- NO QA STEP COLUMNS
);
```

**qa_photo_reviews table:**
```sql
-- WhatsApp QA Tracking
CREATE TABLE qa_photo_reviews (
  id UUID PRIMARY KEY,
  project VARCHAR,  -- ⚠️ VARCHAR project name, NOT UUID
  dr_number VARCHAR,  -- Drop reference number from WhatsApp
  contractor VARCHAR,

  -- 12 QA step booleans (not in drops table)
  step_1 BOOLEAN,
  step_2 BOOLEAN,
  -- ... step_3 through step_12

  photo_url VARCHAR,
  whatsapp_timestamp TIMESTAMP,
  created_at TIMESTAMP
);
```

### API Endpoints

**drops table:**
- `/api/sow/drops` - List all SOW drops
- `/api/sow/drops/search` - Search drops by project
- `/api/sow/drops/stats` - Drop statistics
- `/api/sow/import` - Import drops from Excel

**qa_photo_reviews table:**
- `/api/wa-monitor-drops` - List QA photo reviews
- `/api/wa-monitor-daily-drops` - Daily QA submissions
- `/api/wa-monitor-dr-validation` - Validate DR numbers
- `/api/wa-monitor-projects-summary` - Project QA summary

### When to Use Which Table

**Use `drops` table when:**
- ✅ Importing SOW/BOQ data from Excel
- ✅ Planning fiber stringing routes
- ✅ Assigning drops to contractors
- ✅ Tracking pre-construction planning
- ✅ Need UUID references to projects table

**Use `qa_photo_reviews` table when:**
- ✅ Processing WhatsApp QA photos
- ✅ Tracking QA step completion (12-step verification)
- ✅ Monitoring contractor submissions
- ✅ Generating QA compliance reports
- ✅ Need VARCHAR project names (e.g., "GP12")

### Common Mistakes

❌ **WRONG:** Querying `drops` table for QA step completion
```sql
-- This will FAIL - drops table has no step_1 column
SELECT * FROM drops WHERE step_1 = true;
```

✅ **RIGHT:** Use qa_photo_reviews for QA steps
```sql
SELECT * FROM qa_photo_reviews WHERE step_1 = true;
```

❌ **WRONG:** Joining qa_photo_reviews on project_id (UUID)
```sql
-- This will FAIL - qa_photo_reviews.project is VARCHAR
SELECT * FROM qa_photo_reviews
JOIN projects ON qa_photo_reviews.project_id = projects.id;
```

✅ **RIGHT:** Join on project name (VARCHAR)
```sql
SELECT * FROM qa_photo_reviews
JOIN projects ON qa_photo_reviews.project = projects.name;
```

### Migration Path (Future Consideration)

If we want to unify these tables in the future:

**Option 1: Merge into single drops table**
- Add QA step columns to drops table
- Migrate qa_photo_reviews data
- Update all WhatsApp processing to use drops table

**Option 2: Keep separate, improve linking**
- Add drop_id foreign key to qa_photo_reviews
- Link via DROP table lookup: `dr_number → drop_number`
- Maintain separation of concerns

**Option 3: Leave as-is (RECOMMENDED)**
- Different data sources → different tables
- Clear separation of concerns
- No risk of breaking existing integrations

---

## Other Common Table Confusions

### contractors vs suppliers

| Table | Purpose | Key Difference |
|-------|---------|----------------|
| `contractors` | Field workers doing fiber installation | Have teams, get assigned to drops |
| `suppliers` | Companies providing materials/equipment | Have compliance docs, quoted in RFQs |

### meetings (two contexts)

| Context | Purpose | Source |
|---------|---------|--------|
| Fireflies.ai sync | External meeting transcripts | `/api/meetings.ts` |
| LiveKit recordings | Internal video calls | `/api/livekit/recordings.ts` |

### projects vs procurement_projects

| Table | Purpose |
|-------|---------|
| `projects` | Core fiber installation projects |
| `procurement_projects` | Procurement initiatives (may map to multiple projects) |

---

## Best Practices

### 1. Always Check Table Context

Before writing a query, ask:
- What is the data source? (Excel, WhatsApp, manual entry?)
- What is the lifecycle? (Planning, execution, QA?)
- What module uses this? (SOW, wa-monitor, procurement?)

### 2. Use Type-Safe Interfaces

```typescript
// Define distinct types
interface SowDrop {
  id: string;
  project_id: string;  // UUID
  drop_number: string;
  // NO QA steps
}

interface QaPhotoReview {
  id: string;
  project: string;  // VARCHAR project name
  dr_number: string;
  step_1: boolean;  // HAS QA steps
  // ... step_2 through step_12
}
```

### 3. Document SQL Queries

```sql
-- GOOD: Clear comment about which table and why
-- Query: Get all drops from SOW planning (not QA reviews)
SELECT * FROM drops WHERE project_id = '...';

-- GOOD: Explicit about data source
-- Query: Get WhatsApp QA submissions for GP12 project
SELECT * FROM qa_photo_reviews WHERE project = 'GP12';
```

### 4. Naming Conventions

When adding new tables, avoid ambiguous names:
- ❌ Bad: `drop_photos` (which drops?)
- ✅ Good: `sow_drop_photos` (clearly SOW drops)
- ✅ Good: `qa_drop_photos` (clearly QA drops)

---

## Quick Reference Card

```
╔════════════════════════════════════════════════════════════════╗
║  QUICK REFERENCE: Which Table Should I Use?                   ║
╠════════════════════════════════════════════════════════════════╣
║                                                                ║
║  I'm importing Excel BOQ data          →  drops                ║
║  I'm processing WhatsApp messages      →  qa_photo_reviews    ║
║  I need project UUID                   →  drops (project_id)   ║
║  I need project name VARCHAR           →  qa_photo_reviews    ║
║  I need QA step booleans               →  qa_photo_reviews    ║
║  I'm planning fiber routes             →  drops                ║
║  I'm tracking contractor QA photos     →  qa_photo_reviews    ║
║                                                                ║
╚════════════════════════════════════════════════════════════════╝
```

---

## Related Documentation

- `DATABASE_AUDIT.md` (in ~/Downloads) - Full database analysis
- `NEON_DATABASE_CONSOLIDATION.md` - Database cleanup effort
- `.claude/skills/wa-monitor/` - WhatsApp monitoring implementation
- `ui-module/src/modules/sow/` - SOW module implementation (if exists)

---

**Remember:** When in doubt, check the data source. Excel = drops, WhatsApp = qa_photo_reviews.
