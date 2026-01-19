# Deployment Workflow Guide

**Best Practices for FibreFlow Code Deployment to Production VPS**

## Executive Summary

**Recommended Approach**: Local Development → GitHub → VPS (Option 2)
- **Why**: Version control, rollback capability, team collaboration, zero downtime
- **Avoid**: Direct server editing (Option 1) - too risky for production
- **Consider**: Full CI/CD (Option 3) when team grows

## Deployment Options Comparison

| Approach | Risk | Speed | Rollback | Collaboration | Best For |
|----------|------|-------|----------|---------------|----------|
| 1. Direct Server Edit | ⚠️ High | Fast | ❌ None | ❌ Hard | Never for production |
| 2. **Git-Based** | ✅ Low | Good | ✅ Easy | ✅ Great | **Current recommendation** |
| 3. CI/CD Pipeline | ✅ Lowest | Auto | ✅ Auto | ✅ Best | Future scaling |

## Option 1: Direct Server Development (NOT Recommended)

### Why This is Problematic
```bash
# Editing directly on server
ssh louisdup@72.60.17.245
nano /home/louisdup/agents/agent.py  # One typo = production down
# No way to undo!
```

**Problems**:
- 🔴 **No Version Control**: Can't track what changed when
- 🔴 **No Rollback**: Break something? Too bad
- 🔴 **No Testing**: Changes go straight to production
- 🔴 **No Backup**: Server dies? Code is gone
- 🔴 **No Collaboration**: How do others contribute?
- 🔴 **Debugging Nightmare**: "It worked yesterday" - but what changed?

**Only acceptable for**: Emergency hotfixes (and immediately commit afterward)

## Option 2: GitHub-Based Workflow (RECOMMENDED)

### Initial Setup (One Time)

```bash
# 1. Create GitHub repository
# Go to github.com/new
# Create: fibreflow-agents (or your preferred name)

# 2. Initialize local repository
cd /home/louisdup/Agents/claude
git init
git add .
git commit -m "Initial commit: FibreFlow Agent Workforce"

# 3. Connect to GitHub
git remote add origin https://github.com/yourusername/fibreflow-agents.git
git branch -M main
git push -u origin main

# 4. Setup VPS for pulling
ssh louisdup@72.60.17.245
cd /home/louisdup
git clone https://github.com/yourusername/fibreflow-agents.git agents
cd agents
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# Edit .env with production values

# 5. Configure SSH key for GitHub (optional, for private repos)
ssh-keygen -t ed25519 -C "vps@fibreflow"
cat ~/.ssh/id_ed25519.pub
# Add this key to GitHub: Settings → SSH Keys
```

### Daily Development Workflow

```bash
# 1. DEVELOP LOCALLY
cd /home/louisdup/Agents/claude
# Make your changes
./venv/bin/pytest tests/  # Test locally first!

# 2. COMMIT CHANGES
git add .
git commit -m "feat: Add SharePoint integration"
git push origin main

# 3. DEPLOY TO VPS
ssh louisdup@72.60.17.245 "cd /home/louisdup/agents && git pull && source venv/bin/activate && pip install -r requirements.txt"

# 4. RESTART SERVICES
ssh louisdup@72.60.17.245 "sudo systemctl restart fibreflow-api"

# 5. VERIFY
curl http://72.60.17.245/health
```

### Quick Deployment Script

Create `deploy.sh` locally:

```bash
#!/bin/bash
# deploy.sh - One-command deployment

echo "🚀 Deploying FibreFlow to production..."

# Run tests first
echo "📋 Running tests..."
./venv/bin/pytest tests/ -q
if [ $? -ne 0 ]; then
    echo "❌ Tests failed! Aborting deployment."
    exit 1
fi

# Commit and push
echo "📤 Pushing to GitHub..."
git add .
git commit -m "$1"  # Use: ./deploy.sh "your commit message"
git push origin main

# Deploy to VPS
echo "🔄 Deploying to VPS..."
ssh louisdup@72.60.17.245 << 'ENDSSH'
cd /home/louisdup/agents
git pull origin main
source venv/bin/activate
pip install -r requirements.txt --quiet
sudo systemctl restart fibreflow-api
echo "✅ Deployment complete!"
ENDSSH

# Verify
echo "🔍 Verifying deployment..."
curl -s http://72.60.17.245/health | jq .
```

Usage:
```bash
chmod +x deploy.sh
./deploy.sh "feat: Add new agent capability"
```

### Rollback Process

If something breaks:

```bash
# Quick rollback to previous version
ssh louisdup@72.60.17.245
cd /home/louisdup/agents
git log --oneline -5  # Find last working commit
git checkout abc1234  # Rollback to that commit
sudo systemctl restart fibreflow-api

# Or rollback to specific tag
git checkout v1.0.5
```

## Option 3: Advanced CI/CD Pipeline (Future)

### GitHub Actions Setup

Create `.github/workflows/deploy.yml`:

```yaml
name: Deploy to VPS

on:
  push:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: |
          python -m venv venv
          source venv/bin/activate
          pip install -r requirements.txt
      - name: Run tests
        run: |
          source venv/bin/activate
          pytest tests/

  deploy:
    needs: test
    runs-on: ubuntu-latest
    if: success()
    steps:
      - uses: actions/checkout@v2
      - name: Deploy to VPS
        env:
          SSH_KEY: ${{ secrets.VPS_SSH_KEY }}
          HOST: ${{ secrets.VPS_HOST }}
          USER: ${{ secrets.VPS_USER }}
        run: |
          echo "$SSH_KEY" > ssh_key
          chmod 600 ssh_key
          ssh -i ssh_key -o StrictHostKeyChecking=no $USER@$HOST << 'EOF'
            cd /home/louisdup/agents
            git pull origin main
            source venv/bin/activate
            pip install -r requirements.txt
            sudo systemctl restart fibreflow-api
          EOF
```

Setup secrets in GitHub:
1. Go to Settings → Secrets → Actions
2. Add: `VPS_SSH_KEY`, `VPS_HOST`, `VPS_USER`

## Branching Strategy

### Simple (Current)
```bash
main → production (direct push)
```

### Recommended (As you grow)
```bash
main → production (protected)
develop → staging
feature/* → feature branches
```

Example:
```bash
# Create feature branch
git checkout -b feature/sharepoint-integration

# Work on feature
# ... make changes ...
git add .
git commit -m "feat: Add SharePoint upload"

# Merge to main
git checkout main
git merge feature/sharepoint-integration
git push origin main  # Auto-deploys via CI/CD
```

## Environment Management

### Separate Environments

```bash
# .env.local (git ignored)
ENVIRONMENT=development
DATABASE_URL=postgresql://localhost/fibreflow_dev
ANTHROPIC_API_KEY=sk-ant-dev-xxx

# .env.production (on VPS only, never in git)
ENVIRONMENT=production
DATABASE_URL=postgresql://neon/fibreflow_prod
ANTHROPIC_API_KEY=sk-ant-prod-xxx
```

### Configuration Management

```python
# config.py
import os
from dotenv import load_dotenv

env = os.getenv('ENVIRONMENT', 'development')
load_dotenv(f'.env.{env}')

class Config:
    DATABASE_URL = os.getenv('DATABASE_URL')
    DEBUG = env == 'development'
    API_KEY = os.getenv('ANTHROPIC_API_KEY')
```

## Monitoring Deployments

### Health Check Endpoint

```python
# ui-module/agent_api.py
@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "version": get_git_version(),
        "timestamp": datetime.now().isoformat(),
        "agents": count_active_agents()
    }
```

### Deployment Verification Script

```bash
#!/bin/bash
# verify_deployment.sh

echo "🔍 Verifying deployment..."

# Check API health
HEALTH=$(curl -s http://72.60.17.245/health)
echo "API Health: $HEALTH"

# Check specific agents
curl -s -X POST http://72.60.17.245/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "test database connection"}' | jq .

# Check logs
ssh louisdup@72.60.17.245 "tail -20 /var/log/fibreflow/api.log"
```

## Backup Strategy

### Automated Backups

```bash
# backup.sh (run via cron on VPS)
#!/bin/bash
BACKUP_DIR="/home/louisdup/backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# Backup code
tar -czf $BACKUP_DIR/code_$TIMESTAMP.tar.gz /home/louisdup/agents

# Backup database
pg_dump $DATABASE_URL > $BACKUP_DIR/db_$TIMESTAMP.sql

# Keep only last 30 days
find $BACKUP_DIR -mtime +30 -delete

# Sync to remote storage (optional)
rsync -az $BACKUP_DIR/ backup-server:/backups/fibreflow/
```

Setup cron:
```bash
crontab -e
# Add: 0 2 * * * /home/louisdup/backup.sh
```

## Security Best Practices

### Never Commit Sensitive Data
```bash
# .gitignore
.env
.env.*
*.pem
*.key
secrets/
credentials/
```

### Use Environment Variables
```python
# BAD
api_key = "sk-ant-api03-xxxx"

# GOOD
api_key = os.getenv('ANTHROPIC_API_KEY')
```

### Secure SSH Access
```bash
# On VPS
sudo nano /etc/ssh/sshd_config
# Set: PasswordAuthentication no
# Set: PermitRootLogin no
sudo systemctl restart sshd
```

## Troubleshooting Common Issues

| Issue | Solution |
|-------|----------|
| "Permission denied" on git pull | Check SSH key is added to GitHub |
| Service won't restart | Check logs: `journalctl -u fibreflow-api -n 50` |
| Database connection fails | Verify .env has correct DATABASE_URL |
| Module import errors | Run `pip install -r requirements.txt` |
| Old code still running | Restart service: `sudo systemctl restart fibreflow-api` |

## Quick Reference Commands

```bash
# Check current deployment
ssh louisdup@72.60.17.245 "cd agents && git log -1 --oneline"

# View service logs
ssh louisdup@72.60.17.245 "journalctl -u fibreflow-api -f"

# Emergency rollback
ssh louisdup@72.60.17.245 "cd agents && git reset --hard HEAD~1"

# Restart all services
ssh louisdup@72.60.17.245 "sudo systemctl restart fibreflow-api nginx"

# Check system resources
ssh louisdup@72.60.17.245 "htop"
```

## Recommended Next Steps

1. **Immediate**: Set up GitHub repository
2. **Today**: Create deploy.sh script
3. **This Week**: Implement health check endpoint
4. **This Month**: Add GitHub Actions CI/CD
5. **Future**: Set up staging environment

## Summary

**Your Current Best Path**:
1. Keep developing locally (as you are now) ✅
2. Push to GitHub for version control ⭐ (ADD THIS)
3. Pull from GitHub to VPS for deployment ⭐ (ADD THIS)

This gives you:
- ✅ Version history and rollback capability
- ✅ Backup of all code
- ✅ Ability to collaborate
- ✅ Safe production deployments
- ✅ Professional workflow

**Avoid**: Editing directly on the server (except for emergency hotfixes)
**Future**: Automate with CI/CD when ready