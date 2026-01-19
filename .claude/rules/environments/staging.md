# Staging Environment Rules

## Purpose
Testing ground for new features before production deployment.

## Staging URLs
- **FibreFlow Staging**: https://vf.fibreflow.app (port 3006)
- **WA Monitor**: https://vf.fibreflow.app/wa-monitor
- **Owner**: Louis (primary staging instance)

## Key Differences from Production
- ✅ Can restart services anytime (no work hours restriction)
- ✅ Can test experimental features
- ✅ Can use test data (not production data)
- ✅ Can reset database if needed
- ✅ Aggressive caching allowed
- ⚠️ WhatsApp uses test phone: +27640412391

## Database
- **Host**: Neon PostgreSQL (staging branch)
- **Safe to**: Reset, migrate, experiment
- **Data**: Test data only (no real customer data)
- **Sync from prod**: `pg_dump` production, sanitize, restore

## Deployment Process
```bash
# Automatic deployment on push to develop
git push origin develop

# Manual deployment
./sync-to-hostinger --staging

# Direct server deployment
ssh louis@100.96.203.105
cd /srv/data/apps/fibreflow-staging
git pull
npm run build
pm2 restart fibreflow-staging
```

## Testing Checklist
Before promoting to production:
- [ ] All unit tests pass: `pytest tests/ -v`
- [ ] Manual QA on staging URL
- [ ] Test critical user flows
- [ ] Check mobile responsiveness
- [ ] Test WhatsApp integration (staging phone)
- [ ] Verify database migrations applied
- [ ] Test rollback procedure
- [ ] Load test if performance changes
- [ ] Security scan for new dependencies

## Monitoring
```bash
# Check staging health
curl https://vf.fibreflow.app/health

# View staging logs
ssh louis@100.96.203.105 'pm2 logs fibreflow-staging'

# Restart staging (safe anytime)
ssh louis@100.96.203.105 'pm2 restart fibreflow-staging'

# Check staging metrics
ssh louis@100.96.203.105 'pm2 show fibreflow-staging'
```

## Staging-Specific Features
- Debug mode enabled (verbose logging)
- Source maps available
- React DevTools enabled
- API response times logged
- Mock services available

## Reset Staging Database
```bash
# WARNING: Destroys all staging data
ssh louis@100.96.203.105
cd /srv/data/apps/fibreflow-staging

# Backup first (optional)
pg_dump $STAGING_DATABASE_URL > staging_backup.sql

# Reset database
npm run db:reset
npm run db:seed

# Verify
npm run db:status
```

## Common Staging Tasks
```bash
# Clear staging cache
redis-cli -h localhost FLUSHDB

# Reset WhatsApp session
rm -rf ~/whatsapp-staging/store/*
./whatsapp-staging/restart.sh

# Generate test data
npm run generate:test-data

# Run E2E tests against staging
npm run test:e2e:staging
```

## Staging Rules
1. **Break things freely** - It's staging
2. **Document findings** - Add to test cases
3. **Clean up after** - Reset for next tester
4. **Communicate** - Tell team if staging is broken
5. **Time-box experiments** - Don't leave staging broken overnight