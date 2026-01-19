# Deployment Quick Start

## 🚀 5-Minute Setup

### 1. Run Setup Script
```bash
cd /home/louisdup/Agents/claude
./deploy/setup_github.sh
```
Follow the prompts to configure GitHub integration.

### 2. Create GitHub Repository
Go to: https://github.com/new
- Name: `fibreflow-agents`
- Private: Yes (recommended)
- Don't initialize with README

### 3. Push to GitHub
```bash
git branch -M main
git push -u origin main
```

### 4. Setup VPS
```bash
ssh louisdup@72.60.17.245
cd /home/louisdup
mv agents agents_backup
git clone https://github.com/YOUR_USERNAME/fibreflow-agents.git agents
cd agents
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp ../agents_backup/.env .env
```

## 📝 Daily Workflow

### Deploy Changes
```bash
./deploy.sh "feat: Your change description"
```
This single command:
- ✅ Runs tests
- ✅ Commits changes
- ✅ Pushes to GitHub
- ✅ Deploys to VPS
- ✅ Restarts services
- ✅ Verifies deployment

### Emergency Rollback
```bash
./rollback.sh
```

## 🔍 Quick Commands

| Task | Command |
|------|---------|
| Deploy | `./deploy.sh "message"` |
| Rollback | `./rollback.sh` |
| Check VPS version | `ssh louisdup@72.60.17.245 "cd agents && git log -1 --oneline"` |
| View logs | `ssh louisdup@72.60.17.245 "journalctl -u fibreflow-api -f"` |
| Restart service | `ssh louisdup@72.60.17.245 "sudo systemctl restart fibreflow-api"` |

## ⚠️ Important Notes

1. **Never edit directly on VPS** - Always deploy through Git
2. **Always test locally first** - Deploy script runs tests automatically
3. **Keep .env out of Git** - Use .env.example as template
4. **Use meaningful commit messages** - They're your deployment history

## 📊 Why This Workflow?

| Without Git | With Git |
|-------------|----------|
| No rollback | Instant rollback |
| No history | Full audit trail |
| Risk of breaking prod | Safe deployments |
| Can't collaborate | Team-ready |
| No backup | GitHub backup |

**Time Investment**: 5 minutes setup = Months of safer deployments