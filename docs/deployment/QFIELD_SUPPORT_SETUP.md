# QField Tech Support Setup (GitHub Issues)

**Simple KISS architecture**: GitHub Issues + GitHub MCP + qfieldcloud skill = Tech support system

## Quick Start (5 minutes)

### 1. Enable GitHub MCP

Edit `.claude/settings.local.json` and change:
```json
"github": {
  "disabled": true,  // Change to false
  ...
}
```

Restart Claude Code session to load MCP.

### 2. Set GitHub Token

Add to `.env`:
```bash
GITHUB_TOKEN=ghp_your_github_personal_access_token
```

**Get token**: https://github.com/settings/tokens/new
- Scopes needed: `repo`, `issues`

### 3. Test It Works

```bash
# In Claude Code, ask:
"Show me open issues in the current repo"
```

If that works, you're done!

## Usage

### When user reports QField issue on GitHub:

1. **Run command**:
   ```
   /qfield/support 42
   ```
   *(Replace 42 with actual issue number)*

2. **Claude will**:
   - Read the GitHub issue
   - Run qfieldcloud diagnostics
   - Post solution in issue comments
   - Add appropriate labels

3. **User gets**:
   - Status of system
   - Diagnosis of problem
   - Step-by-step solution
   - Prevention tips

### Or just ask naturally:

```
"Check GitHub issue #42 and diagnose the QField sync problem"
"What's wrong with the upload issue in GitHub issue #55?"
"Help with QField support ticket #12"
```

Claude will automatically:
- Use GitHub MCP to read issue
- Use qfieldcloud skill to gather diagnostics
- Respond with solution

## What Gets Checked Automatically

When handling support issues, Claude runs:

✅ **System Health** (status.py)
- Docker containers running?
- API responding?
- Database connected?
- SSL certificate valid?

✅ **Resources** (status.py --detailed)
- CPU usage
- Memory usage
- Disk space
- Docker resource usage

✅ **Errors** (logs.py)
- Recent application errors
- Worker failures
- Nginx errors

✅ **Prevention System** (prevention.py)
- Auto-healing status
- Stuck jobs
- Failure rates

All diagnostic data posted in GitHub comment.

## Issue Lifecycle

```
User creates issue
    ↓
You run /qfield/support <number>
    ↓
Claude gathers diagnostics (30 sec)
    ↓
Claude posts solution
    ↓
User tries fix
    ↓
User closes issue (resolved) OR comments (still broken)
    ↓
[If still broken] Claude investigates deeper
```

## Common Scenarios

### Scenario 1: "Can't sync my project"

```bash
/qfield/support 42
```

**Claude checks**:
- Worker container running?
- Sync queue stuck?
- Disk full?
- Project permissions?

**Posts solution** like:
- Restart worker: `docker-compose restart worker_wrapper`
- Check project ownership
- Clear stuck jobs

### Scenario 2: "Site is slow"

```bash
/qfield/support 55
```

**Claude checks**:
- CPU/RAM usage
- Database query performance
- Docker resource limits

**Posts solution** like:
- Increase worker memory
- Database query optimization
- Enable caching

### Scenario 3: "Getting 502 error"

```bash
/qfield/support 67
```

**Claude checks**:
- Nginx running?
- App container healthy?
- Gunicorn workers responding?

**Posts solution** like:
- Restart nginx
- Check app logs
- Increase worker timeout

## Repository Setup

For this to work, you need a GitHub repo with Issues enabled:

1. **Create repo** (if not exists): `opengisch/QFieldCloud` or your fork
2. **Enable Issues**: Settings → Features → Issues ✅
3. **Create issue template** (optional):

`.github/ISSUE_TEMPLATE/support.md`:
```markdown
---
name: Support Request
about: Get help with QField sync or server issues
title: '[SUPPORT] '
labels: 'question'
---

## Problem Description
[What's not working?]

## When Did This Start?
[Today? Yesterday? After deployment?]

## What Have You Tried?
[Steps you already took]

## Error Messages
[Copy exact error text]

---
*This issue will be handled by automated support agent*
```

Users create issues using this template, makes diagnosis easier.

## Monitoring Support Queue

Check for new issues:
```bash
# List open support issues
"Show me open QField support issues"

# Check if any are urgent
"Are there any critical QField issues?"

# Weekly summary
"Summarize QField support issues from this week"
```

## Advanced: Automated Responses

Want Claude to auto-respond to new issues? Add GitHub Action:

`.github/workflows/auto-support.yml`:
```yaml
name: Auto Support Response

on:
  issues:
    types: [opened, labeled]

jobs:
  respond:
    if: contains(github.event.issue.labels.*.name, 'question')
    runs-on: ubuntu-latest
    steps:
      - name: Auto-triage
        run: |
          # Call Claude Code API or webhook here
          # Or just add comment: "Support agent will respond within 1 hour"
          echo "Issue #${{ github.event.issue.number }} created"
```

This notifies you immediately when issues are created.

## Cost

**Total cost**: $0/month

- GitHub Issues: Free
- GitHub MCP: Free (uses your token)
- qfieldcloud skill: Free (SSH scripts)
- Claude Code: Already have it

vs. building custom system:
- Zendesk: $49+/month
- Intercom: $74+/month
- Custom build: Hours of dev time

## Troubleshooting

### GitHub MCP not working

```bash
# Check token is set
echo $GITHUB_TOKEN

# Test GitHub API directly
curl -H "Authorization: token $GITHUB_TOKEN" \
  https://api.github.com/user

# Restart Claude Code with MCP enabled
```

### Diagnostics failing

```bash
# Test qfieldcloud skill manually
cd .claude/skills/qfieldcloud/scripts
./status.py

# Check SSH access to VPS
ssh root@72.61.166.168 "echo OK"

# Verify env vars
cat .env | grep QFIELDCLOUD
```

### Issue response not posting

- Check GitHub token has `repo` scope
- Verify you're working in correct repository
- Check issue number exists and is open

## What's NOT Included

This is a **simple** system. It does NOT:

❌ Auto-respond to every issue (you run command manually)
❌ Escalate to humans (you decide when to intervene)
❌ Track SLA metrics (GitHub labels only)
❌ Send email notifications (GitHub's built-in only)
❌ Multi-language support (English only)

If you need those, add them later. Start simple!

## Next Steps After Setup

1. **Create test issue** on GitHub
2. **Run** `/qfield/support <number>`
3. **Verify** Claude posts response with diagnostics
4. **Close issue** to confirm workflow
5. **Document** for your team: "Report QField issues on GitHub"

## Example Response

Here's what users see after you run `/qfield/support 42`:

---

**Claude Bot** commented 2 minutes ago:

## Status ✅
QFieldCloud is running normally. All services healthy.

## Diagnosis 🔍
Your sync failure is caused by project quota limits. Your project "MOA_Pole_Audit" has exceeded the 500MB storage limit (currently using 523MB).

## Solution 🔧
I've increased your project quota to 1GB:

1. Accessed admin panel
2. Updated project settings: `MOA_Pole_Audit` storage = 1000MB
3. Cleared failed sync jobs from queue
4. Verified storage service is accepting uploads

Please try syncing again - it should work now.

## Prevention 🛡️
Monitor your project storage at https://qfield.fibreflow.app/projects/MOA_Pole_Audit/settings

Set up alerts when storage exceeds 80% of quota.

---
*Diagnostics gathered: 2025-12-18 10:45:33*
*Response time: 18s*

---

User reads solution, tries sync, it works, closes issue. Done!

## Tips for Better Support

1. **Label issues consistently**
   - `bug` - Something broken
   - `question` - How-to help
   - `performance` - Speed issue
   - `resolved` - Fixed, pending confirmation

2. **Use issue templates** - Gets you better info upfront

3. **Link related issues** - Build knowledge base over time

4. **Close resolved issues** - Keeps queue clean

5. **Review weekly** - Look for patterns in issues

## Documentation

- Command: `.claude/commands/qfield/support.md`
- Prompt: `.claude/commands/qfield/support.prompt.md`
- qfieldcloud skill: `.claude/skills/qfieldcloud/skill.md`

## Summary

**Before**: Users email/Slack "QField is broken" → Manual SSH → Hours to fix

**After**: Users create GitHub issue → `/qfield/support <N>` → Auto-diagnosis in 30 seconds

Simple, effective, $0 cost.
