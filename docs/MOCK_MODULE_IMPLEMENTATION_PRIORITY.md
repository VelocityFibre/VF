# Mock Module Implementation Priority

**Based on:** DATABASE_AUDIT.md findings
**Date:** 2026-01-12

---

## Summary

FibreFlow has **10 modules using mock/hardcoded data** instead of real database queries. This document prioritizes which to implement first based on business value, data availability, and complexity.

---

## Mock Modules Ranked by Priority

### 🔴 CRITICAL (Implement First)

#### 1. **kpi-dashboard** - Hardcoded stats

**Why Critical:**
- Main dashboard that stakeholders see
- You HAVE the data (104 tables in Neon!)
- Currently showing fake numbers → credibility issue

**Data Available:**
```sql
-- All this data exists but not surfaced:
SELECT COUNT(*) FROM projects;           -- Total projects
SELECT COUNT(*) FROM contractors;        -- Active contractors
SELECT COUNT(*) FROM tickets;            -- Open tickets
SELECT COUNT(*) FROM qa_photo_reviews;   -- QA submissions today
SELECT SUM(amount) FROM purchase_orders; -- Procurement spend
```

**Complexity:** ⭐⭐ (Medium - need aggregation queries)

**Business Impact:** 🎯🎯🎯 (HIGH - executive visibility)

**Estimated Time:** 4-6 hours

---

#### 2. **daily-progress** - Hardcoded KPIs

**Why Critical:**
- Operational teams check this daily
- Data exists in `qa_photo_reviews`, `tickets`, `drops`
- Contractors expect to see real progress

**Data Available:**
```sql
-- Daily metrics that exist:
SELECT COUNT(*) FROM qa_photo_reviews
WHERE DATE(whatsapp_timestamp) = CURRENT_DATE;

SELECT COUNT(*) FROM tickets
WHERE status = 'completed'
AND DATE(completed_at) = CURRENT_DATE;

SELECT COUNT(*) FROM drops
WHERE status = 'completed'
AND DATE(updated_at) = CURRENT_DATE;
```

**Complexity:** ⭐⭐ (Medium - time-based queries)

**Business Impact:** 🎯🎯🎯 (HIGH - daily operations)

**Estimated Time:** 3-5 hours

---

### 🟡 HIGH PRIORITY (Implement Soon)

#### 3. **installations** - useHomeInstallations returns []

**Why High Priority:**
- `home_installs` table exists (per audit)
- Likely used for customer-facing features
- Empty array breaks UX

**Data Available:**
```sql
-- Table exists with data
SELECT * FROM home_installs
WHERE project_id = :project_id;
```

**Complexity:** ⭐ (Low - simple CRUD)

**Business Impact:** 🎯🎯 (MEDIUM - customer visibility)

**Estimated Time:** 2-3 hours

---

#### 4. **field-app** - Mock tasks

**Why High Priority:**
- Field technicians use this
- Data exists in `projects`, `drops`, `contractors`
- Affects field productivity

**Data Available:**
```sql
-- Can build tasks from existing data
SELECT d.*, p.name as project_name, c.name as contractor
FROM drops d
JOIN projects p ON d.project_id = p.id
JOIN contractors c ON d.contractor_id = c.id
WHERE d.status != 'completed'
AND c.id = :current_contractor_id;
```

**Complexity:** ⭐⭐⭐ (Higher - need task model)

**Business Impact:** 🎯🎯 (MEDIUM - field operations)

**Estimated Time:** 6-8 hours

---

### 🟢 MEDIUM PRIORITY (Nice to Have)

#### 5. **workflow** - Mock templates

**Why Medium:**
- `workflow_templates` table defined but empty
- Need to populate table first
- Used infrequently

**Status:** ⚠️ Schema exists, no data

**Action:** Either populate tables OR remove unused schema

**Complexity:** ⭐⭐⭐⭐ (Complex - needs workflow engine)

**Business Impact:** 🎯 (LOW-MEDIUM - process automation)

**Estimated Time:** 12-16 hours (design + implementation)

---

#### 6. **reports** - Mock data

**Why Medium:**
- Can leverage existing analytics
- Lower frequency usage
- Not blocking daily operations

**Data Available:** All project/ticket/contractor data

**Complexity:** ⭐⭐⭐ (Medium-high - need report templates)

**Business Impact:** 🎯 (LOW-MEDIUM - periodic use)

**Estimated Time:** 8-12 hours

---

### 🔵 LOW PRIORITY (Future Enhancement)

#### 7. **communications** - Empty arrays

**Status:** Unclear if actually needed
**Action:** Verify if feature is used at all

---

#### 8. **nokia-equipment** - Placeholder

**Status:** Likely future feature
**Action:** Wait for requirements

---

#### 9. **onemap** - Placeholder

**Status:** GIS integration planned
**Tables exist:** `onemap_properties`, `onemap_layers`, `onemap_features`
**Action:** Check if data is being populated

---

#### 10. **kpis** - Hardcoded metrics

**Note:** Likely overlaps with kpi-dashboard
**Action:** Consolidate with kpi-dashboard implementation

---

## Recommended Implementation Order

```
Phase 1 (This Week) - Executive Visibility
├─ 1. kpi-dashboard (4-6 hours)
└─ 2. daily-progress (3-5 hours)
   TOTAL: ~8-11 hours

Phase 2 (Next Week) - Customer & Field Operations
├─ 3. installations (2-3 hours)
└─ 4. field-app (6-8 hours)
   TOTAL: ~8-11 hours

Phase 3 (Later) - Process Improvements
├─ 5. workflow (12-16 hours) - IF tables get populated
├─ 6. reports (8-12 hours)
└─ 7-10. As needed based on usage data
```

---

## Quick Win: Start with kpi-dashboard

### Step-by-Step Implementation

**1. Identify Current Mock Data**
```typescript
// Find the hook/service returning hardcoded data
// Example: src/hooks/useKpiDashboard.ts
const stats = {
  totalProjects: 42,  // ← FAKE
  activeContractors: 15,  // ← FAKE
  // ...
};
```

**2. Create Database Service**
```typescript
// src/services/dashboardService.ts
export const dashboardService = {
  async getStats() {
    const sql = neon(process.env.NEON_DATABASE_URL);

    const [projects] = await sql`SELECT COUNT(*) as count FROM projects`;
    const [contractors] = await sql`
      SELECT COUNT(*) as count FROM contractors
      WHERE status = 'active'
    `;

    return {
      totalProjects: projects.count,
      activeContractors: contractors.count,
      // ... more real metrics
    };
  }
};
```

**3. Create API Route**
```typescript
// pages/api/dashboard/stats.ts
import { dashboardService } from '@/services/dashboardService';

export default async function handler(req, res) {
  const stats = await dashboardService.getStats();
  return res.status(200).json(stats);
}
```

**4. Update Frontend Hook**
```typescript
// src/hooks/useKpiDashboard.ts
export function useKpiDashboard() {
  return useQuery(['dashboard-stats'], async () => {
    const res = await fetch('/api/dashboard/stats');
    return res.json();
  });
}
```

**Total Time:** 4-6 hours including testing

---

## Data Validation Checklist

Before implementing, verify tables have data:

```sql
-- Check table sizes
SELECT
  schemaname,
  tablename,
  pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size,
  (SELECT COUNT(*) FROM <tablename>) as row_count
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
```

---

## Success Metrics

After Phase 1 (kpi-dashboard + daily-progress):

✅ Dashboard shows real numbers
✅ KPIs update in real-time
✅ Stakeholders see accurate project status
✅ 2 of 10 mock modules replaced (20% progress)
✅ Foundation for remaining modules

---

## Related Documentation

- `DATABASE_AUDIT.md` - Full table inventory
- `DATABASE_TABLE_CLARIFICATIONS.md` - Table usage guide
- `NEON_AGENT_GUIDE.md` - Database querying patterns

---

**Next Step:** Run `./venv/bin/python3 scripts/database-cleanup.py` to clean old data, then start implementing kpi-dashboard.
