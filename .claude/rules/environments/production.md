# Production Environment Rules

## 🚨 Critical Safety Rules
1. **NEVER restart services during work hours** (08:00-17:00 SAST) without explicit approval
2. **ALWAYS test on staging first** before any production deployment
3. **ALWAYS use louis account** for monitoring (limited sudo)
4. **NEVER use velo account** unless explicitly approved for admin tasks

## Production URLs
- **FibreFlow**: https://app.fibreflow.app (port 3000)
- **QFieldCloud**: https://qfield.fibreflow.app (port 8082)
- **Support Portal**: https://support.fibreflow.app
- **Knowledge Base**: https://docs.fibreflow.app

## Server Access
```bash
# Monitoring (safe - use this by default)
ssh -i ~/.ssh/vf_server_key louis@100.96.203.105

# Admin (dangerous - only with approval)
ssh -i ~/.ssh/vf_server_key velo@100.96.203.105
```

## Database
- **Host**: Neon PostgreSQL (production branch)
- **Connection**: Use `$NEON_DATABASE_URL` environment variable
- **Backups**: Automatic daily at 02:00 UTC
- **Migrations**: Via Drizzle Kit (never manual SQL on production)

## Deployment Checklist
```bash
# 1. Run tests locally
./venv/bin/pytest tests/ -v

# 2. Deploy to staging first
git push origin develop

# 3. Test on staging
curl https://vf.fibreflow.app/health

# 4. Deploy to production
./sync-to-hostinger --code

# 5. Verify production
curl https://app.fibreflow.app/health

# 6. Monitor logs (10 minutes)
ssh louis@100.96.203.105 'sudo journalctl -u fibreflow -f'
```

## Rollback Procedure
```bash
# 1. Identify last stable commit
git log --oneline -10

# 2. Notify team in Slack #deployments
echo "Rolling back production due to [issue]"

# 3. Execute rollback
./sync-to-hostinger --rollback <commit-hash>

# 4. Verify services restored
curl https://app.fibreflow.app/health
```

## Monitoring Commands
```bash
# Service status (safe)
ssh louis@100.96.203.105 'sudo systemctl status fibreflow'

# View logs (safe)
ssh louis@100.96.203.105 'sudo journalctl -u fibreflow -n 100'

# Check disk space (safe)
ssh louis@100.96.203.105 'df -h'

# Check memory (safe)
ssh louis@100.96.203.105 'free -h'

# Active connections (safe)
ssh louis@100.96.203.105 'sudo netstat -tulpn | grep LISTEN'
```

## Restart Services (REQUIRES APPROVAL)
```bash
# Must be outside work hours OR emergency approved
echo "VeloBoss@2026" | sudo -S systemctl restart fibreflow
echo "VeloBoss@2026" | sudo -S systemctl restart nginx
```

## Emergency Contacts
- **Primary**: Louis (VF Server access)
- **Secondary**: Hein (Application issues)
- **Escalation**: Boris (Architecture decisions)

## Incident Response
1. Check status pages first
2. Review logs for errors
3. Check disk/memory usage
4. Notify team if service degradation
5. Create incident in `.claude/skills/fibreflow/INCIDENT_LOG.md`