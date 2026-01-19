---
name: qfieldcloud-csrf-fix
version: 1.0.0
description: CSRF configuration fix for QFieldCloud web interface
triggers: ["CSRF verification failed", "403 Forbidden", "Origin checking failed", "csrf"]
context_cost: 400
priority: high
isolation: full
---

# QFieldCloud CSRF Fix

Fast fix for "CSRF verification failed" errors on web interface.

## Quick Commands

```bash
# Check current CSRF status
./scripts/diagnose.sh

# Apply the proven fix
./scripts/apply_fix.sh
```

## User Instructions

If getting CSRF errors after fix:

1. **Clear ALL browser data**
   - Chrome: Settings → Privacy → Clear browsing data → All time
   - Firefox: Settings → Privacy → Clear Data
   - Safari: Develop → Empty Caches

2. **Close browser completely**

3. **Try again**

## Technical Details

- **Issue**: Django needs CSRF_TRUSTED_ORIGINS as Python list
- **Solution**: Append directly to settings.py (NOT local_settings.py)
- **Domains**: qfield.fibreflow.app, srv1083126.hstgr.cloud