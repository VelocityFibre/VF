# FibreFlow Skill

Quick tools for managing FibreFlow production app.

## Scripts

### Check Status
```bash
python3 .claude/skills/fibreflow/scripts/status.py
```
Shows if services are up or down.

### Quick Fixes
```bash
python3 .claude/skills/fibreflow/scripts/quick_fix.py
```
Common fixes:
- Restart apps
- Check logs
- Clear cache
- Restart storage

## Incident Log

Track issues in `INCIDENT_LOG.md`. When something breaks:

1. Check status: `python3 .claude/skills/fibreflow/scripts/status.py`
2. Try quick fix: `python3 .claude/skills/fibreflow/scripts/quick_fix.py`
3. Log incident: Edit `INCIDENT_LOG.md`
4. Create detailed reference if needed: `incidents/INCIDENT_REF_[date].md`

## Common Issues

### 502 Bad Gateway
- App crashed
- Fix: Restart via quick_fix.py

### Storage Upload Fails
- Storage API down
- Fix: Restart storage service

### Auth Issues
- Usually Clerk API
- Check: https://dashboard.clerk.com