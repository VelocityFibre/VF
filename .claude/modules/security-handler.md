# Security Handler Module

**Purpose:** Automatically protect sensitive information and server access
**Status:** 🟢 Partially Implemented (Server access controls active)
**Priority:** 🔴 CRITICAL
**Last Updated:** 2026-01-14

---

## Active Security Measures

### 1. SERVER ACCESS SECURITY (✅ IMPLEMENTED)

**Configuration:** Hein's model with limited sudo for personal accounts

**Access Model:**
```
DEFAULT: louis account → Limited sudo (monitoring only)
ADMIN:   velo account  → Full sudo (requires explicit approval)
```

**Implementation:**
- Server: `/etc/sudoers.d/20-louis-readonly`
- Docs: `SERVER_ACCESS_RULES.md`
- Config: `.env` (credentials)

**Protection Level:**
- ✅ Can't accidentally restart/stop services
- ✅ Can't delete files or change passwords
- ✅ Full monitoring without restrictions
- ✅ Admin tasks require password + approval

### 2. GIT PROTECTION (✅ IMPLEMENTED)

**Pre-commit Hook:** `.git/hooks/pre-commit`
- Blocks commits containing passwords
- Prevents credential leaks

**Gitignore Rules:** `.gitignore`
```
.credentials/
*vf_server_key*
*_CREDENTIALS.md
.server-audit.log
```

---

## Problem Statement

**Remaining Issues:**
1. ⚠️ No automatic detection when creating new credential files
2. ⚠️ Credentials split between .env and other files
3. ⚠️ No automated secret scanning in CI/CD

**Example Success:**
- Server access now requires approval for destructive commands
- Git pre-commit hook blocks password commits
- Audit trail logs all sudo commands

---

## Solution: Security-First Workflow

### Automatic Detection

When Claude Code handles ANY of these:
```
- Passwords
- API keys
- SSH keys (private)
- Database connection strings
- Authentication tokens
- Certificate files (.pem, .ppk)
- Sudo credentials
```

**MUST automatically:**
1. ✅ Store in `.env` (already gitignored) OR
2. ✅ Update `.gitignore` BEFORE creating file
3. ✅ Verify protection with `git check-ignore`
4. ✅ Warn user if file could be exposed

---

## Implementation Checklist

### Phase 1: Detection (Pattern Matching)
```python
SENSITIVE_PATTERNS = [
    r'password\s*[:=]',
    r'api[_-]?key\s*[:=]',
    r'-----BEGIN.*PRIVATE KEY-----',
    r'token\s*[:=]',
    r'secret\s*[:=]',
    r'sudo\s+',
    r'postgresql://',
    r'mysql://',
]

SENSITIVE_FILES = [
    '*.pem', '*.ppk', 'id_rsa*', 'id_ed25519*',
    '*_key', '*_secret', '*.env', 'credentials*',
]
```

### Phase 2: Protection Actions

**Before Writing File:**
```python
def protect_sensitive_file(filepath, content):
    """Ensure sensitive files are git-protected BEFORE writing"""

    # 1. Check if content contains secrets
    if contains_sensitive_data(content):

        # 2. Prefer .env for key-value pairs
        if is_key_value_format(content):
            return write_to_env(content)

        # 3. Otherwise add to gitignore FIRST
        update_gitignore(filepath)
        verify_gitignore(filepath)

        # 4. Only then write file
        write_file(filepath, content)

        # 5. Confirm protection
        assert git_check_ignore(filepath), f"SECURITY: {filepath} not protected!"

        return f"✅ {filepath} created and git-protected"
```

### Phase 3: Verification

**After ANY File Operation:**
```python
# Always verify sensitive files are protected
sensitive_files = find_sensitive_files()
unprotected = [f for f in sensitive_files if not is_gitignored(f)]

if unprotected:
    WARN_USER(f"🚨 SECURITY RISK: {unprotected} not git-protected!")
```

---

## Proposed Security Agent

### Agent Specification

**Name:** `security-guardian`
**Trigger:** Automatically on any file write operation
**Capabilities:**
1. Detect sensitive content in files
2. Automatically update `.gitignore`
3. Verify git protection status
4. Migrate plaintext credentials to `.env`
5. Scan repo for exposed secrets

### Agent Workflow

```
User Request → Claude Code Response
                      ↓
              [Security Guardian]
                      ↓
        ┌─────────────┴─────────────┐
        │                           │
   Contains       Does NOT contain
   Secrets?         Secrets?
        │                           │
        ↓                           ↓
  1. Store in .env        Write file normally
  2. Update .gitignore
  3. Verify protection
  4. Report to user
        ↓
     Write file
```

### Example Usage

```bash
# User asks Claude Code to save API key
User: "Save my OpenAI key: sk-abc123 to a file"

# Without Security Guardian (DANGEROUS):
Claude: "Saved to api_key.txt"  # ❌ Not gitignored!

# With Security Guardian (SAFE):
Claude: "Added to .env and verified git-protected ✅"
```

---

## Implementation Plan

### Week 1: Core Detection
- [ ] Build pattern matching for sensitive content
- [ ] Create file type detection (SSH keys, passwords, etc.)
- [ ] Test on existing codebase

### Week 2: Protection Automation
- [ ] Implement auto-gitignore updates
- [ ] Build .env integration
- [ ] Add verification checks

### Week 3: Security Agent
- [ ] Create standalone security-guardian agent
- [ ] Integrate with base_agent.py
- [ ] Add to orchestrator registry

### Week 4: Repository Scanning
- [ ] Build "security audit" command
- [ ] Scan for exposed secrets in git history
- [ ] Generate security report

---

## Success Criteria

✅ **Zero manual security reminders** - Claude Code proactively protects all secrets
✅ **All credentials in .env** - Single source of truth
✅ **Automatic gitignore updates** - No unprotected sensitive files
✅ **Pre-commit validation** - Block commits with exposed secrets
✅ **Security audit dashboard** - Real-time view of security status

---

## Related Files

- `.gitignore` - Git protection rules
- `.env` - Centralized credential storage
- `.env.example` - Template (no actual secrets)
- `.credentials/` - Legacy (migrate to .env)

---

## Notes

This module should be **ALWAYS ACTIVE** - not optional.
Security is not a feature, it's a requirement.

**Priority:** Implement ASAP to prevent future credential leaks.

---

## Quick Security Commands

### Server Access (Updated 2026-01-14)
```bash
# Safe monitoring (DEFAULT - use louis)
ssh -i ~/.ssh/vf_server_key louis@100.96.203.105
sudo systemctl status nginx          # No password needed
sudo docker ps                        # No password needed
sudo tail -f /var/log/syslog        # No password needed

# Admin tasks (requires password + approval)
echo "VeloBoss@2026" | sudo -S systemctl restart nginx
echo "VeloBoss@2026" | sudo -S kill -9 PID
```

### Verify Security
```bash
# Check sudo permissions for louis
ssh louis@server 'sudo -l'

# Check recent sudo usage
ssh louis@server 'sudo grep "sudo" /var/log/auth.log | tail -20'

# Test if monitoring works without password
ssh louis@server 'sudo systemctl status nginx && echo "✅ Works without password"'
```
