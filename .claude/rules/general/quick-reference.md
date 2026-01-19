# Quick Reference Guide

## Essential Commands

### Testing
```bash
# Run all tests
./venv/bin/pytest tests/ -v

# Test specific app
./venv/bin/pytest tests/test_fibreflow.py -v
./venv/bin/pytest tests/test_qfieldcloud.py -v
```

### Deployment
```bash
# Deploy to production (with tests)
./sync-to-hostinger --code

# Deploy to staging
./sync-to-hostinger --staging

# Rollback
./sync-to-hostinger --rollback <commit-hash>
```

### Database Operations
```bash
# Sync Neon to Convex
python sync_neon_to_convex.py

# Database migrations
npm run db:migrate

# Check database status
npm run db:status
```

### Monitoring
```bash
# Check FibreFlow production
ssh louis@100.96.203.105 'sudo systemctl status fibreflow'

# Check QFieldCloud
ssh louis@100.96.203.105 'sudo docker-compose -f /opt/qfieldcloud/docker-compose.yml ps'

# View logs
ssh louis@100.96.203.105 'sudo journalctl -u fibreflow -f'
```

### WhatsApp Services
```bash
# Check WhatsApp bridge (receives)
curl http://100.96.203.105:8080/health

# Check WhatsApp sender
curl http://100.96.203.105:8081/health

# WA Monitor status
curl http://100.96.203.105:8092/health
```

### Git Workflow
```bash
# Feature branch
git checkout develop
git checkout -b feature/your-feature

# Commit with convention
git commit -m "feat: add new feature"
git commit -m "fix: resolve bug"
git commit -m "docs: update documentation"

# Create PR
gh pr create --title "Your title"
```

## Port Reference
| Port | Service | URL |
|------|---------|-----|
| 3000 | FibreFlow Production | app.fibreflow.app |
| 3006 | Staging (Louis) | vf.fibreflow.app |
| 3005 | Dev (Hein) | localhost |
| 8082 | QFieldCloud | qfield.fibreflow.app |
| 8081 | WhatsApp Sender | - |
| 8092 | WA Monitor API | - |
| 8091 | Storage API | - |
| 8095 | OCR Service | - |

## SSH Access
```bash
# Default (monitoring)
ssh -i ~/.ssh/vf_server_key louis@100.96.203.105

# Admin (only with approval)
ssh -i ~/.ssh/vf_server_key velo@100.96.203.105
```

## Environment Variables
Check `.env.example` for required variables.

## Troubleshooting
1. Check incident logs: `.claude/skills/[app]/INCIDENT_LOG.md`
2. Run quick fix: `python .claude/skills/[app]/scripts/quick_fix.py`
3. Check service health endpoints
4. Review logs on server