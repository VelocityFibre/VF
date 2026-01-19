# Staging Deployment Skill

## Purpose
Deploy to staging server (vf.fibreflow.app) with natural language commands

## Trigger Phrases
- "deploy to staging"
- "push my changes to staging"
- "update staging server"
- "deploy branch X to staging"
- "rollback staging"
- "check staging deployment"
- "who deployed to staging"

## Server Configuration
- **URL**: https://vf.fibreflow.app
- **Server**: 100.96.203.105
- **Port**: 3006
- **Path**: /home/louis/apps/fibreflow
- **Service**: fibreflow.service

## Quick Commands

### Deploy Current Branch
```bash
ssh -i ~/.ssh/vf_server_key hein@100.96.203.105 'deploy-staging'
```

### Deploy Specific Branch
```bash
ssh -i ~/.ssh/vf_server_key hein@100.96.203.105 'deploy-staging branch-name'
```

### Check Last Deployment
```bash
ssh -i ~/.ssh/vf_server_key hein@100.96.203.105 'deployment-monitor last'
```

### Rollback to Backup
```bash
ssh -i ~/.ssh/vf_server_key hein@100.96.203.105 'cd /home/louis/apps/fibreflow && git branch -a | grep backup | tail -5'
```

### Monitor Live
```bash
ssh -i ~/.ssh/vf_server_key hein@100.96.203.105 'deployment-monitor monitor'
```

## Natural Language Examples

**User**: "deploy to staging"
**Action**: Run `deploy-staging` which pulls current branch

**User**: "deploy my feature-auth branch to staging"
**Action**: Run `deploy-staging feature-auth`

**User**: "check who deployed to staging last"
**Action**: Run `deployment-monitor last`

**User**: "rollback staging to this morning"
**Action**: List backups, choose appropriate one, restore

**User**: "is staging deployment working?"
**Action**: Check service status and HTTP response

## Error Handling

### Service Won't Start
```bash
ssh -i ~/.ssh/vf_server_key hein@100.96.203.105 'sudo journalctl -u fibreflow.service -n 50'
```

### Port Conflict
```bash
ssh -i ~/.ssh/vf_server_key hein@100.96.203.105 'sudo lsof -i :3006'
```

### Build Failures
```bash
ssh -i ~/.ssh/vf_server_key hein@100.96.203.105 'cd /home/louis/apps/fibreflow && rm -rf .next && npm run build'
```

## Deployment Flow
1. Creates automatic backup branch
2. Pulls specified branch (or current)
3. Installs dependencies
4. Builds application
5. Restarts service
6. Verifies HTTP 200 response
7. Logs deployment details

## Auto-Response Templates

### Successful Deployment
```
✅ Deployed to staging successfully!
- URL: https://vf.fibreflow.app
- Branch: {branch}
- Commits: {count} new
- Duration: {time} seconds
- Backup: {backup_branch}
```

### Failed Deployment
```
❌ Deployment failed
- Error: {error}
- Rollback: git checkout {last_backup}
- Logs: sudo journalctl -u fibreflow.service
```

## Safety Features
- Automatic backup before deploy
- HTTP verification after deploy
- Rollback capability
- Deployment logging
- Team notifications (optional)

## Integration Points
- Git repository: https://github.com/VelocityFibre/FF_Next.js
- Deployment logs: /var/log/staging-deployments.log
- Service: systemd fibreflow.service
- Monitoring: deployment-monitor tool