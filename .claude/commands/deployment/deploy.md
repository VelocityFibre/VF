---
description: Deploy agent to production VPS with pre-deployment validation
argument-hint: [agent-name or 'all']
---

# Production Deployment

Deploy **$ARGUMENTS** to production VPS with comprehensive validation.

**Deployment Targets**:
- **Hostinger VPS**: srv1092611.hstgr.cloud (72.60.17.245) - Public FibreFlow API/UI
- **VF Server**: velo-server (100.96.203.105) - Internal operations, BOSS, QField
  - Production paths: `/srv/data/apps/`, `/srv/scripts/cron/`
  - Use `.claude/skills/vf-server/` for VF-specific operations

**Primary Target**: Hostinger VPS (this guide)
**Environment**: Production

## ⚠️ Pre-Deployment Checklist

Run all checks before deploying. **DO NOT PROCEED** if any critical checks fail.

### 1. Code Quality Checks

#### Tests
```bash
# Run full test suite
./venv/bin/pytest tests/ -v --tb=short
```

**Required**: ✅ All tests must pass
**If failed**: Fix failing tests before deploying

#### Linting (if available)
```bash
# Python linting
./venv/bin/python3 -m pylint agents/$ARGUMENTS/ || echo "Pylint not configured"
```

**Acceptable**: Warnings OK, but no critical errors

#### Code Review
```bash
# Show recent changes
git diff main...HEAD
```

**Required**: Review all changes for:
- Security issues (SQL injection, exposed secrets)
- Performance problems
- Error handling
- Breaking changes

### 2. Configuration Checks

#### Environment Variables
```bash
# Check .env.example is up to date
diff <(grep -v '^#' .env.example | grep '=' | cut -d= -f1 | sort) <(grep -v '^#' .env | grep '=' | cut -d= -f1 | sort)
```

**Required**:
- ✅ All new variables documented in `.env.example`
- ✅ Production `.env` has all required variables
- ❌ No secrets in code or git

#### Dependencies
```bash
# Check requirements.txt
./venv/bin/pip check
```

**Required**: ✅ No dependency conflicts

### 3. Database Checks

#### Migrations (if applicable)
```bash
# Check for pending migrations
# [Add project-specific migration check]
```

**Required**: All migrations applied to production

#### Convex Deployment (if applicable)
```bash
# Deploy Convex functions if changed
npx convex deploy
```

**Required**: ✅ Convex functions deployed and tested

### 4. Documentation Checks

#### README Updated
**Required**:
- [ ] Agent `README.md` exists and is current
- [ ] `CLAUDE.md` updated if architecture changed
- [ ] Deployment notes added
- [ ] Environment variables documented

#### Orchestrator Registration
**Required**:
- [ ] Agent registered in `orchestrator/registry.json`
- [ ] Triggers and capabilities defined
- [ ] Dependencies listed

### 5. Security Checks

**Critical** - Must all pass:
- [ ] No hardcoded credentials in code
- [ ] No API keys in repository
- [ ] `.gitignore` includes `.env` and sensitive files
- [ ] SSH keys not in repository
- [ ] Secrets use environment variables

### 6. Backup (Recommended)

```bash
# Backup current production state (if applicable)
# ssh vps "cd /path/to/project && git stash && tar -czf backup-$(date +%Y%m%d-%H%M%S).tar.gz ."
```

## Deployment Execution

If all checks pass, proceed with deployment:

### Step 1: Connect to VPS

```bash
ssh srv1092611.hstgr.cloud
```

### Step 2: Navigate to Project

```bash
cd /path/to/fibreflow-agents  # Adjust path as needed
```

### Step 3: Pull Latest Code

```bash
git fetch origin
git pull origin main
```

### Step 4: Update Dependencies

```bash
# Activate virtual environment
source venv/bin/activate

# Update Python packages
pip install -r requirements.txt
```

### Step 5: Deploy Specific Component

#### For Agent Deployment
```bash
# No specific deployment needed - agents are loaded dynamically
# Verify agent is accessible
./venv/bin/python3 -c "from agents.$ARGUMENTS.agent import *; print('✅ Agent loaded successfully')"
```

#### For API Deployment
```bash
# Restart FastAPI service
sudo systemctl restart fibreflow-api  # Adjust service name

# Or use deployment script
cd deploy && ./deploy_brain.sh
```

#### For Convex Deployment
```bash
# Deploy Convex functions (run from local machine, not VPS)
npx convex deploy
```

#### For Full System Deployment
```bash
# Run comprehensive deployment script (if exists)
./deploy/deploy_all.sh
```

### Step 6: Verify Services Running

```bash
# Check service status
sudo systemctl status nginx
sudo systemctl status fibreflow-api  # Adjust service name

# Check processes
ps aux | grep python
ps aux | grep nginx
```

### Step 7: Check Logs

```bash
# Recent logs
sudo journalctl -u fibreflow-api -n 50
tail -f /var/log/nginx/access.log
```

Look for:
- ✅ Successful startup messages
- ❌ Error messages
- ⚠️ Warnings

## Post-Deployment Validation

### 1. Smoke Tests

```bash
# Test health endpoint
curl http://localhost:8000/health

# Test production URL
curl http://72.60.17.245/
```

**Expected**: ✅ 200 OK responses

### 2. Agent Testing

```bash
# Test specific agent (from local machine)
./venv/bin/python3 -c "from agents.$ARGUMENTS.agent import *; agent = {AgentName}Agent(); print(agent.chat('test query'))"
```

**Expected**: ✅ Agent responds correctly

### 3. Integration Testing

Test agent through production API:
```bash
curl -X POST http://72.60.17.245:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message":"Test $ARGUMENTS agent"}'
```

**Expected**: ✅ Proper response from agent

### 4. VPS Health Check

Run `/vps-health` command to verify system resources

**Expected**:
- ✅ CPU < 70%
- ✅ Memory < 80%
- ✅ Disk < 75%
- ✅ All services running

### 5. Database Connectivity

```bash
# Test Neon connection
./venv/bin/python3 -c "import os; import psycopg2; conn = psycopg2.connect(os.getenv('NEON_DATABASE_URL')); print('✅ Neon connected')"

# Test Convex connection
curl -s "https://quixotic-crow-802.convex.cloud/api/query" \
  -H "Content-Type: application/json" \
  -d '{"path":"_system:listTables","args":{}}'
```

**Expected**: ✅ Both databases accessible

## Deployment Report

Generate deployment summary:

```markdown
## Deployment Report: $ARGUMENTS

**Date**: [YYYY-MM-DD HH:MM UTC]
**Deployed By**: [Name]
**Git Commit**: [commit hash]
**Status**: ✅ SUCCESS / ⚠️ PARTIAL / ❌ FAILED

---

### Pre-Deployment Checks
✅ All tests passed (152/152)
✅ No linting errors
✅ Configuration validated
✅ Documentation updated
✅ Security checks passed

### Deployment Steps
✅ Code pulled from main branch
✅ Dependencies updated
✅ Services restarted
✅ Logs checked - no errors

### Post-Deployment Validation
✅ Smoke tests passed
✅ Agent tested and responding
✅ Integration tests passed
✅ VPS health normal
✅ Database connections verified

---

### Performance Metrics
- **Deployment Duration**: X minutes
- **Downtime**: X seconds (if any)
- **Response Time**: Xms (before) → Yms (after)

### Issues Encountered
[List any issues and how they were resolved]
[Or: None - deployment was clean]

### Rollback Plan (if needed)
```bash
git revert [commit]
./deploy/deploy_brain.sh
```

---

### Next Steps
- [ ] Monitor logs for 1 hour
- [ ] Check error rates in dashboard
- [ ] Notify team of deployment
- [ ] Update deployment log

**Deployed Successfully**: [Yes/No]
```

## Rollback Procedure

If deployment fails or causes issues:

### 1. Immediate Rollback

```bash
# SSH to VPS
ssh srv1092611.hstgr.cloud

# Revert to previous commit
cd /path/to/project
git log --oneline -5  # Find previous good commit
git reset --hard [previous-commit-hash]

# Restart services
sudo systemctl restart fibreflow-api
```

### 2. Verify Rollback

```bash
# Check service status
sudo systemctl status fibreflow-api

# Test functionality
curl http://72.60.17.245/
```

### 3. Investigate Issue

```bash
# Check logs for errors
sudo journalctl -u fibreflow-api --since "10 minutes ago"

# Review recent changes
git diff [previous-commit]..[failed-commit]
```

### 4. Document Failure

Add to `bugs.md` or deployment log:
- What failed
- Error messages
- Root cause (if known)
- Steps to reproduce
- Resolution or next steps

## Best Practices

### 1. Deploy During Low Traffic
- Preferred: Late evening or early morning (UTC)
- Avoid: Peak business hours

### 2. Have Rollback Plan Ready
- Know previous good commit hash
- Test rollback in staging first
- Keep deployment terminal session active

### 3. Monitor Post-Deployment
- Watch logs for 30-60 minutes
- Check error rates
- Monitor VPS resources
- Verify agent functionality

### 4. Communicate
- Notify team before deployment
- Update during deployment (if issues)
- Confirm success after validation

### 5. Document Everything
- Git commit messages
- Deployment notes
- Issues encountered
- Rollback if needed

## Deployment Checklist Summary

Pre-Deployment:
- [ ] All tests passing
- [ ] Code reviewed
- [ ] Configuration validated
- [ ] Documentation updated
- [ ] Security checked

Deployment:
- [ ] Code deployed
- [ ] Dependencies updated
- [ ] Services restarted
- [ ] Logs checked

Post-Deployment:
- [ ] Smoke tests passed
- [ ] Agent functionality verified
- [ ] VPS health normal
- [ ] Monitoring active

Documentation:
- [ ] Deployment report created
- [ ] Team notified
- [ ] Deployment log updated

## Automation Potential

Future enhancement - create deployment script:

```bash
#!/bin/bash
# deploy.sh - Automated deployment with checks

# Run pre-deployment checks
./venv/bin/pytest tests/ || exit 1

# Deploy
ssh vps "cd /path && git pull && systemctl restart service"

# Validate
curl http://72.60.17.245/ || exit 1

echo "✅ Deployment successful"
```

## Success Criteria

Deployment is successful when:
- ✅ All pre-deployment checks pass
- ✅ Code deployed without errors
- ✅ All services running
- ✅ Post-deployment tests pass
- ✅ No critical errors in logs
- ✅ VPS health normal
- ✅ User-facing functionality works
