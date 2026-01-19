---
name: qfield/support
description: Handle QField support issue from GitHub
tags: [support, qfield, github]
---

# QField Support Handler

Responds to QField tech support issues from GitHub Issues.

## Usage

```bash
/qfield/support <issue-number>
```

## What it does (AUTONOMOUS RESOLUTION)

This command **COMPLETELY RESOLVES** issues end-to-end, not just diagnoses:

1. **Fetches GitHub issue** - Reads the issue description and comments
2. **Gathers diagnostics** - Uses qfieldcloud skill to check system status
3. **Analyzes problem** - Identifies likely cause based on symptoms
4. **EXECUTES FIX** - Runs remediation scripts to resolve the issue (NEW!)
5. **VERIFIES FIX** - Re-runs diagnostics to confirm resolution (NEW!)
6. **Posts resolution report** - Comments on issue with before/after metrics
7. **CLOSES ISSUE** - Automatically closes if verified fixed (NEW!)

## Examples

```bash
# Handle issue #42
/qfield/support 42

# Handle issue with verbose diagnostics
/qfield/support 123 --verbose
```

## Required Setup

1. **Enable GitHub MCP** (one-time):
   ```bash
   # Edit .claude/settings.local.json
   # Set github.disabled = false
   ```

2. **Set GitHub token** in `.env`:
   ```bash
   GITHUB_TOKEN=ghp_your_github_token
   ```

3. **Verify qfieldcloud skill works**:
   ```bash
   .claude/skills/qfieldcloud/scripts/status.py
   ```

## Auto-Fix Capabilities

The command can **automatically fix** these issues:

| Issue Type | Detection | Fix | Resolution Time |
|-----------|-----------|-----|----------------|
| ✅ Worker down/crashed | status.py | Restart/rebuild container | ~1 min |
| ✅ Database down | status.py | Restart database | ~30 sec |
| ✅ Service container down | status.py | Restart service | ~30 sec |
| ✅ Queue stuck (>24h jobs) | status.py | Clean old jobs | ~10 sec |
| ✅ Disk space >90% | status.py | Docker prune | ~2 min |
| ✅ Memory limit hit | status.py | Restart service | ~30 sec |
| ⚠️ Performance issues | Depends | Varies | Varies |
| ❌ SSL expired | Manual | Admin needed | - |
| ❌ Code bugs | Manual | Developer needed | - |
| ❌ User permissions | Manual | Admin needed | - |

**Coverage**: ~80% of typical support issues can be auto-resolved

## Workflow (Autonomous Resolution)

When user reports issue on GitHub, run:
```bash
/qfield/support <issue-number>
```

The system will **autonomously resolve** the issue:

1. **Diagnose** (10-30 sec)
   - Read issue description
   - Run diagnostic scripts (status.py, prevention.py, logs.py)
   - Identify problem category

2. **Fix** (30 sec - 2 min)
   - Execute remediation script for detected issue
   - Apply appropriate fix (restart service, clean queue, etc.)
   - Wait for service stabilization

3. **Verify** (10-20 sec)
   - Re-run diagnostics
   - Compare before/after metrics
   - Confirm issue resolved

4. **Report** (5 sec)
   - Post structured resolution report with:
     - **Status**: ✅ Resolved / ⚠️ Partial / ❌ Escalated
     - **Diagnosis**: What was wrong
     - **Actions Taken**: Actual fixes executed (not suggestions)
     - **Verification**: Before/after comparison
     - **Prevention**: Future mitigation

5. **Close** (2 sec)
   - Auto-close issue if verification passed
   - OR escalate to admin if fix failed/not applicable
   - Add appropriate labels

**Total time**: 1-3 minutes for auto-fixable issues (vs hours/days with manual approach)

## Integration with QFieldCloud Skill

**Diagnostic Scripts** (gather information):
- `status.py` - Service health, container status, resource usage
- `logs.py` - Error analysis from Docker logs
- `prevention.py` - Auto-healing system status
- `sync_diagnostic.py` - Sync readiness check

**Remediation Scripts** (execute fixes):
- `remediate.py` - **NEW!** Automated fix execution
  - `--issue worker_down` - Fix worker container
  - `--issue database_down` - Fix database connection
  - `--issue stuck_queue` - Clean old queue jobs
  - `--issue disk_space` - Free disk space
  - `--issue memory_limit` - Restart service
  - `--issue service_down --service NAME` - Restart specific service
  - `--auto` - Auto-diagnose and fix all issues
  - `--dry-run` - Preview fixes without executing

All operations fully automated via skill scripts.
