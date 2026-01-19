# /deploy - Deploy to staging server

## Usage
```
/deploy                     # Deploy current branch
/deploy branch-name        # Deploy specific branch
/deploy --rollback         # Rollback to previous
/deploy --status           # Check deployment status
```

## What it does
Deploys code to staging server (vf.fibreflow.app) with automatic:
- Backup creation
- Dependency installation
- Build process
- Service restart
- Success verification
- Deployment logging

## Examples

### Simple deploy
```
/deploy
```
→ Deploys whatever branch is currently on staging

### Deploy feature branch
```
/deploy feature-auth
```
→ Switches to feature-auth branch and deploys

### Check status
```
/deploy --status
```
→ Shows last deployment info and current status

### Emergency rollback
```
/deploy --rollback
```
→ Restores last backup

## Implementation

```bash
#!/bin/bash
case "$1" in
    --status)
        ssh hein@100.96.203.105 'deployment-monitor last'
        ;;
    --rollback)
        ssh hein@100.96.203.105 'cd /home/louis/apps/fibreflow && \
            LAST_BACKUP=$(git branch -a | grep backup | tail -1 | xargs) && \
            git checkout $LAST_BACKUP && npm install && npm run build && \
            echo "VeloBoss@2026" | sudo -S systemctl restart fibreflow.service'
        ;;
    "")
        ssh hein@100.96.203.105 'deploy'
        ;;
    *)
        ssh hein@100.96.203.105 "deploy-staging $1"
        ;;
esac
```

## Response Format
```
🚀 Deployment started...
📦 Branch: {branch}
🔨 Building...
✅ Success! Site live at https://vf.fibreflow.app
⏱️ Duration: {time}s
```