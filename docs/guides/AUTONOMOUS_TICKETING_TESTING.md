# Testing the Autonomous GitHub Ticketing System

Quick guide to test the end-to-end autonomous resolution workflow.

## Prerequisites

1. **GitHub MCP enabled** in `.claude/settings.local.json`
2. **GitHub token** set in `.env` with `repo` scope
3. **QFieldCloud skill working** (test `status.py`)
4. **GitHub repository** with Issues enabled

## Test Scenario 1: Worker Down (Auto-Fixable)

### Setup
```bash
# 1. Stop worker container to simulate issue
.claude/skills/vf-server/scripts/execute.py \
  'cd ~/VF/Apps/QFieldCloud && docker-compose stop worker_wrapper'

# 2. Verify worker is down
.claude/skills/qfieldcloud/scripts/status.py
# Should show: worker_wrapper = exited
```

### Create Test Issue
On GitHub (VelocityFibre/ticketing or your test repo):

**Title**: QField sync not working - stuck at 50%

**Body**:
```
I'm trying to sync my project but it gets stuck at 50% and never completes.

Started happening today around 10am.

Can you help?
```

### Run Autonomous Resolution
```bash
/qfield/support <issue-number>
```

### Expected Behavior
1. **Fetch issue** ✅ - Bot reads issue description
2. **Diagnose** ✅ - Runs `status.py`, detects worker down
3. **Execute fix** ✅ - Runs `remediate.py --issue worker_down`
4. **Verify** ✅ - Re-runs `status.py`, confirms worker running
5. **Report** ✅ - Posts resolution comment with before/after metrics
6. **Close** ✅ - Auto-closes issue

### Verify Success
Check the GitHub issue:
- [ ] Comment posted with "Status ✅ RESOLVED"
- [ ] "Actions Taken" section shows actual fix executed
- [ ] "Verification" section shows before/after comparison
- [ ] Issue is closed
- [ ] Labels added (e.g., "resolved")

**Time**: Should complete in <2 minutes

---

## Test Scenario 2: Stuck Queue (Auto-Fixable)

### Setup
```bash
# 1. Create stuck jobs in database (optional - may already exist)
# Skip if you don't want to modify database

# 2. Check current queue
.claude/skills/qfieldcloud/scripts/status.py
# Note the queue depth
```

### Create Test Issue
**Title**: Old sync jobs stuck for days

**Body**:
```
I see several sync jobs from 3 days ago still showing as "queued".

They never complete. Can these be cleaned up?
```

### Run Autonomous Resolution
```bash
/qfield/support <issue-number>
```

### Expected Behavior
1. Detects queue with old jobs (>24h)
2. Executes `remediate.py --issue stuck_queue`
3. Marks old jobs as failed (preserves history)
4. Verifies queue depth reduced
5. Posts report and closes

---

## Test Scenario 3: SSL Expired (NOT Auto-Fixable)

### Create Test Issue
**Title**: Browser certificate error on qfield.fibreflow.app

**Body**:
```
Getting "Your connection is not private" error when accessing the site.

Certificate seems to be expired?
```

### Run Autonomous Resolution
```bash
/qfield/support <issue-number>
```

### Expected Behavior (Intelligent Escalation)
1. Diagnoses SSL certificate issue
2. Recognizes NOT auto-fixable
3. Posts comment explaining why
4. @mentions admin with clear next steps
5. Adds "needs-admin" label
6. **Does NOT close issue** (keeps open for admin)

### Verify Success
Check the GitHub issue:
- [ ] Comment posted with "Status ⚠️ NEEDS ESCALATION"
- [ ] Clear explanation of why not auto-fixed
- [ ] Admin @mentioned with instructions
- [ ] Label "needs-admin" added
- [ ] Issue still open

---

## Test Scenario 4: Unknown Issue (Escalation)

### Create Test Issue
**Title**: Random 500 errors in API

**Body**:
```
Getting intermittent 500 errors when calling /api/v1/projects/

Not consistent - sometimes works, sometimes fails.

Started 2 hours ago.
```

### Run Autonomous Resolution
```bash
/qfield/support <issue-number>
```

### Expected Behavior
1. Runs diagnostics
2. All services appear healthy
3. Cannot identify root cause
4. Escalates to admin with gathered info
5. Keeps issue open

---

## Dry-Run Testing

Test remediation without affecting production:

```bash
# Test worker fix (dry-run)
.claude/skills/qfieldcloud/scripts/remediate.py \
  --issue worker_down \
  --dry-run

# Test auto-diagnose (dry-run)
.claude/skills/qfieldcloud/scripts/remediate.py \
  --auto \
  --dry-run
```

Should output:
```
[DRY RUN] Would execute: cd /opt/qfieldcloud && docker-compose up -d worker_wrapper
```

---

## Manual Remediation Testing

Test individual fix capabilities:

### Worker Down
```bash
# Stop worker
docker-compose stop worker_wrapper

# Fix it
.claude/skills/qfieldcloud/scripts/remediate.py --issue worker_down

# Verify
docker ps | grep worker
# Should show worker_wrapper running
```

### Stuck Queue
```bash
# Check queue
docker exec qfieldcloud-db-1 psql -U qfieldcloud_db_admin -d qfieldcloud_db \
  -c "SELECT status, COUNT(*) FROM core_job WHERE status IN ('pending', 'queued') GROUP BY status;"

# Clean stuck jobs
.claude/skills/qfieldcloud/scripts/remediate.py --issue stuck_queue

# Verify
# Re-run query above - should show reduced count
```

### Disk Space
```bash
# Check disk usage
df -h

# Clean up
.claude/skills/qfieldcloud/scripts/remediate.py --issue disk_space

# Verify
df -h
# Should show more free space
```

---

## Validation Checklist

After running tests, verify:

### Autonomous Resolution Works
- [ ] Bot fetches issues from GitHub
- [ ] Diagnostics run successfully
- [ ] Fixes execute (not just suggested)
- [ ] Verification compares before/after
- [ ] Reports posted to GitHub
- [ ] Issues auto-closed when fixed

### Safety Features Work
- [ ] Dry-run mode doesn't modify system
- [ ] Non-fixable issues escalated, not closed
- [ ] Admin @mentioned on escalations
- [ ] Labels added correctly
- [ ] Verification prevents false closures

### Performance Targets
- [ ] Resolution time <3 minutes (auto-fixable issues)
- [ ] Success rate >90% (fixes work when attempted)
- [ ] False closure rate <5% (no premature closes)

---

## Troubleshooting Tests

### Bot doesn't fetch issue
```bash
# Test GitHub MCP manually
# In Claude Code:
# "Can you list issues in VelocityFibre/ticketing?"

# Should return issue list. If not:
# 1. Check GitHub MCP enabled in settings
# 2. Check GITHUB_TOKEN in .env
# 3. Restart Claude Code
```

### Remediation fails
```bash
# Test SSH access to VPS
ssh root@72.61.166.168

# If fails, check:
# 1. VPS credentials in .env
# 2. SSH key permissions
# 3. VPS is running (check hosting dashboard)
```

### Verification fails but fix worked
```bash
# Check what verification is testing
# May need to adjust wait time:
sleep 60  # Instead of 30

# Or verify specific service started:
docker ps | grep worker_wrapper
```

---

## Success Criteria

✅ **Test passes if**:
1. Auto-fixable issues resolved and closed in <3 min
2. Non-fixable issues escalated with clear explanation
3. Verification prevents false closures
4. Before/after metrics shown in reports
5. No crashes or errors in execution

❌ **Test fails if**:
1. Bot only suggests fixes, doesn't execute
2. Issues closed without verification
3. Escalations don't @mention admin
4. Crashes or hangs during execution
5. False claims of resolution

---

## Next Steps After Testing

1. **Monitor first 10 real issues**:
   - Track resolution rate
   - Note any escalations
   - Gather user feedback

2. **Tune verification criteria**:
   - If false closures occur, add stricter checks
   - If too conservative, relax criteria

3. **Add more auto-fix capabilities**:
   - Identify patterns in escalated issues
   - Create new remediation methods
   - Update Auto-Fix Matrix

4. **Measure improvement**:
   ```
   Before: 2.5 days avg resolution (manual)
   After: <3 minutes avg resolution (automated)
   = 100x improvement for 80% of issues
   ```

---

## Feedback Loop

After each issue resolution:
1. Did bot correctly identify problem? (Y/N)
2. Did fix resolve the issue? (Y/N)
3. Was verification accurate? (Y/N)
4. Would user be satisfied? (Y/N)

**Target**: 4/4 "Yes" for auto-fixable issues

Track monthly:
- Auto-resolution rate (target >70%)
- Escalation rate (target <30%)
- User satisfaction (target >90%)

---

## Emergency Rollback

If system causes issues:

```bash
# 1. Disable command temporarily
# Rename command file:
mv .claude/commands/qfield/support.md \
   .claude/commands/qfield/support.md.disabled

# 2. Revert to manual process
# Create issues manually

# 3. Fix underlying problem
# Review logs, update scripts

# 4. Re-enable when fixed
mv .claude/commands/qfield/support.md.disabled \
   .claude/commands/qfield/support.md
```

---

## Key Testing Insight

`★ Insight ─────────────────────────────────────`
**Test the failure modes as much as success cases**

The value of autonomous systems isn't just fixing problems—it's **failing gracefully** when they can't.

Test these explicitly:
- What happens when fix fails?
- What happens when verification is ambiguous?
- What happens when system is completely down?
- What happens when issue is nonsensical?

A good autonomous system:
✅ Fixes 80% of issues
✅ **Escalates 20% intelligently** (with context)

A bad autonomous system:
❌ Claims to fix 100% of issues
❌ Closes issues without verification
❌ Leaves admins blind to real problems

**Trust is built through honest escalation, not false confidence.**
`─────────────────────────────────────────────────`
