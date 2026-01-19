# 🔐 SERVER SECURITY REMINDER

**Created**: 2026-01-14
**Priority**: 🔴 CRITICAL
**Status**: ✅ ACTIVE

## Quick Summary

Server access now uses Hein's limited sudo model for safety:

```
DEFAULT: louis account → Limited sudo (monitoring only)
ADMIN:   velo account  → Full admin (needs approval)
```

## What Changed

1. **louis account** (your default):
   - ✅ Can monitor everything without password
   - ⚠️ Admin tasks need password: `VeloBoss@2026`
   - Safe for 95% of operations

2. **velo account** (admin):
   - Only use when explicitly needed
   - Has full sudo (password unknown)
   - Reserved for critical admin tasks

## Command Examples

```bash
# SAFE (no password needed)
ssh -i ~/.ssh/vf_server_key louis@100.96.203.105
sudo systemctl status nginx
sudo docker ps
sudo tail -f /var/log/syslog

# NEEDS PASSWORD + APPROVAL
echo "VeloBoss@2026" | sudo -S systemctl restart nginx
echo "VeloBoss@2026" | sudo -S kill -9 PID
```

## Why This Matters

- Prevents accidental service restarts
- Blocks unintended file deletion
- Maintains full monitoring capability
- Required by Hein (PM) for safety

## Documentation

- Main rules: `CLAUDE.md` (top section)
- Quick ref: `SERVER_ACCESS_RULES.md`
- Decision: `docs/DECISION_LOG.md` (ADR-006)
- Config: `/etc/sudoers.d/20-louis-readonly` on server

## If You Need to Rollback

```bash
ssh louis@100.96.203.105
echo "VeloBoss@2026" | sudo -S rm /etc/sudoers.d/20-louis-readonly
```

---

**Remember**: Always use louis by default. Only use velo when explicitly told "use admin" or "use velo".