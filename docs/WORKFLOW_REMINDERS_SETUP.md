# Workflow Reminders - Setup Complete ✅

**Date**: 2026-01-12
**Status**: Active and enforcing best practices

---

## What's Now Active

### 1. ✅ Terminal Banner (Every Login)
Shows on every terminal startup:
```
╔════════════════════════════════════════════════════════════════╗
║             📋 FIBREFLOW DEVELOPMENT WORKFLOW                  ║
╠════════════════════════════════════════════════════════════════╣
║  ✅ BEFORE CODING: cat .claude/modules/{module-name}.md       ║
║  ✅ BEFORE DEPLOY: ./sync-to-hostinger --code                 ║
╚════════════════════════════════════════════════════════════════╝
```

**Location**: Added to `~/.bashrc`
**Frequency**: Every new terminal session

---

### 2. ✅ Git Pre-Push Hook (Automatic Enforcement)
Runs before every `git push`, checks:
- Code files changed?
- Module profile read?
- Tests run?
- **BLOCKS** push if tightly coupled module modified without E2E tests

**Location**: `.git/hooks/pre-push`
**Trigger**: Automatic on `git push`
**Can bypass**: Yes (but prompts for confirmation)

**Example**:
```bash
$ git push

🔍 Pre-Push Checklist:
  📝 Code files changed. Did you:

  [ ] Read module profile before modifying?
  [ ] Run tests?

  ⚠️  TIGHTLY COUPLED MODULE DETECTED!
  Have you run E2E tests? [y/N]:
```

---

### 3. ✅ Quick Aliases (Instant Access)
Two new commands available:

```bash
workflow    # Show deployment checklist
modules     # List all modules with isolation levels
```

**Location**: Added to `~/.bashrc`
**Usage**: Type `workflow` anytime you forget the process

---

### 4. ✅ Printed Checklists (Physical Reminders)
Two printable references created:

1. **Deployment Checklist**: `.claude/reminders/DEPLOYMENT_CHECKLIST.txt`
   - Full step-by-step workflow
   - Keep near monitor

2. **Module Quick Reference**: `.claude/reminders/MODULE_QUICK_REF.txt`
   - Color-coded by isolation level
   - Emergency contact info

**Action Required**: Print and stick near your desk

---

## How to Use Daily

### Morning (Automatic)
```bash
# Open terminal
# Banner shows automatically ✅
```

### Before Coding (30 seconds)
```bash
# Check module you're about to modify
cat .claude/modules/qfieldcloud.md
# or
cat .claude/modules/ticketing.md
# or
cat .claude/modules/workflow.md  # ⚠️ Read the warnings!
```

### Before Pushing (Automatic)
```bash
git push
# Hook runs automatically
# Answer prompts honestly
```

### If You Forget (Quick Recovery)
```bash
workflow    # Show checklist instantly
```

---

## Habit Formation Timeline

### Week 1: Awareness
- See banner daily ✅
- Git hook catches you when you forget
- Start reading module profiles

### Week 2: Resistance
- Git hook feels annoying (working as intended!)
- You start checking BEFORE git hook catches you
- `workflow` becomes muscle memory

### Week 3: Habit Forming
- Reading profiles feels natural
- You check BEFORE opening code editor
- Git hook rarely triggers

### Week 4: Automatic
- No longer need reminders
- Workflow is second nature
- You advocate for it to team

---

## Customization

### Reduce Banner Frequency (Once Per Day)
```bash
# Edit ~/.bashrc
nano ~/.bashrc

# Find the workflow-banner.sh line, replace with:
if [ ! -f /tmp/.workflow_shown_today ] || [ "$(date +%Y-%m-%d)" != "$(cat /tmp/.workflow_shown_today)" ]; then
    source ~/Agents/claude/.claude/reminders/workflow-banner.sh
    date +%Y-%m-%d > /tmp/.workflow_shown_today
fi
```

### Make Git Hook More Strict
```bash
# Edit .git/hooks/pre-push
nano .git/hooks/pre-push

# Change line 48 to require explicit yes:
read -p "Continue with push? [y/N]: " -n 1 -r  # Must type 'y'
```

### Disable Temporarily (Emergency)
```bash
# Skip git hook for urgent hotfix
git push --no-verify

# Remove banner temporarily
mv ~/.bashrc ~/.bashrc.backup
# ... do urgent work ...
mv ~/.bashrc.backup ~/.bashrc
```

---

## Troubleshooting

### "workflow: command not found"
```bash
# Reload bashrc
source ~/.bashrc

# Verify alias exists
grep "alias workflow" ~/.bashrc
```

### Git hook not running
```bash
# Check hook exists and is executable
ls -la .git/hooks/pre-push
chmod +x .git/hooks/pre-push
```

### Banner not showing
```bash
# Check bashrc has the source line
grep "workflow-banner" ~/.bashrc

# Manually trigger
source ~/.bashrc
```

---

## Files Created

| File | Purpose | Access |
|------|---------|--------|
| `.claude/reminders/workflow-banner.sh` | Terminal banner script | Auto (on login) |
| `.git/hooks/pre-push` | Git enforcement hook | Auto (on push) |
| `.claude/reminders/DEPLOYMENT_CHECKLIST.txt` | Printable checklist | `workflow` |
| `.claude/reminders/MODULE_QUICK_REF.txt` | Module reference card | Print it |
| `~/.bashrc` (modified) | Bash configuration | `source ~/.bashrc` |

---

## Success Metrics

Track effectiveness after 1 month:

**Leading Indicators** (Week 1-2):
- How often git hook triggers (should decrease)
- How often you use `workflow` command (should increase then decrease)
- Module profiles read before coding (should become automatic)

**Lagging Indicators** (Week 3-4):
- ✅ Zero breaking changes from missing dependencies
- ✅ Faster PR reviews (checklist pre-completed)
- ✅ Shorter debugging time (gotchas already documented)

---

## Next Steps

### Today
- [x] Reminders installed
- [x] Bashrc updated
- [x] Git hook active
- [ ] Print MODULE_QUICK_REF.txt and put on desk
- [ ] Try `workflow` command to familiarize

### This Week
- [ ] Read module profiles before coding (every time!)
- [ ] Let git hook guide you (don't bypass)
- [ ] Share with Hein when he's ready

### This Month
- [ ] Review habit formation (are reminders working?)
- [ ] Adjust frequency if banner feels too intrusive
- [ ] Document any new gotchas in module profiles

---

## Team Rollout (When Hein Joins)

```bash
# On Hein's machine, run setup:
cd ~/Agents/claude
./scripts/setup-workflow-reminders.sh

# Walk through one feature together:
cat .claude/modules/ticketing.md
/tdd spec example-feature
# ... etc
```

**Benefit**: Same muscle memory, same reminders, consistent workflow

---

## Related Documentation

- **Full Workflow**: `docs/NEW_DEVELOPMENT_WORKFLOW.md`
- **Test Results**: `docs/DEVELOPMENT_WORKFLOW_TEST_RESULTS.md`
- **Quick Test**: `docs/DEVELOPMENT_WORKFLOW_QUICK_TEST.md` (5-min validation)
- **Decision Record**: `docs/DECISION_LOG.md` (ADR-005)

---

## Emergency Contacts

**Workflow broken?**
- Check: `docs/NEW_DEVELOPMENT_WORKFLOW.md` troubleshooting section

**Module question?**
- Read: `.claude/modules/{module-name}.md`

**Git hook blocking urgent hotfix?**
- Bypass once: `git push --no-verify`
- Fix issue, then do proper PR later

---

**Last Updated**: 2026-01-12
**Status**: ✅ Active and enforcing
**Next Review**: 2026-02-12 (1 month - adjust as needed)
