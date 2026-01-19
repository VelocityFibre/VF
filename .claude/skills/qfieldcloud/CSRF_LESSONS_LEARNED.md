# QFieldCloud CSRF Configuration - Lessons Learned

## ⚠️ Critical Discovery (2026-01-13)

After multiple failed attempts to fix CSRF issues, we discovered Django in QFieldCloud does NOT automatically import `local_settings.py`. This invalidates many common Django configuration patterns.

## What DOESN'T Work ❌

1. **local_settings.py** - Django doesn't import it
2. **Environment variables as strings** - Django can't parse "origin1 origin2" format
3. **docker-compose environment section** - Variables load but aren't parsed as lists
4. **.env file entries** - Same issue as above

## What DOES Work ✅

### The ONLY Reliable Method
Append configuration directly to the main settings.py file:

```bash
docker exec qfieldcloud-app-1 bash -c "
cat >> /usr/src/app/qfieldcloud/settings.py << 'EOF'

# CSRF Fix - Direct append to settings.py
CSRF_TRUSTED_ORIGINS = [
    'https://qfield.fibreflow.app',
    'https://srv1083126.hstgr.cloud',
    'http://qfield.fibreflow.app',
    'http://srv1083126.hstgr.cloud',
    'http://100.96.203.105:8082',
    'http://localhost:8082',
]
ALLOWED_HOSTS = ['*']

# Print to logs for verification
print(f'[CSRF FIX APPLIED] CSRF_TRUSTED_ORIGINS = {CSRF_TRUSTED_ORIGINS}')
EOF
"
```

## Why This Happens

1. **Django Settings Import Chain**:
   - Django loads `settings.py`
   - `settings.py` does NOT have `from local_settings import *`
   - Environment variables are loaded but as strings
   - Django expects Python lists for CSRF_TRUSTED_ORIGINS

2. **Container Persistence**:
   - Files created at runtime may not persist
   - Docker image rebuilds lose changes
   - Only settings.py modifications survive

## Browser-Side Issues

Users experiencing CSRF errors must:
1. Clear **ALL** browser data (not just cookies)
2. **Close browser completely**
3. Reopen fresh browser session

Incognito/Private mode always works because it has no cached data.

## Verification

After applying fix, verify with:
```bash
docker-compose logs app | grep "CSRF FIX APPLIED"
```

Should show:
```
[CSRF FIX APPLIED] CSRF_TRUSTED_ORIGINS = ['https://qfield.fibreflow.app', ...]
```

## Prevention

For future Django containers:
1. Always check if local_settings.py is actually imported
2. Test environment variable parsing
3. Append critical configs directly to settings.py
4. Document the configuration method that works

## Timeline of Failed Attempts

1. **09:15** - Created local_settings.py → Failed (not imported)
2. **10:00** - Added to .env file → Failed (string not list)
3. **11:00** - Modified docker-compose.override.yml → Failed (same issue)
4. **12:09** - Appended to settings.py → **SUCCESS** ✅

## Key Takeaway

**When in doubt, append directly to settings.py** - it's the only guaranteed method for QFieldCloud Django configuration.