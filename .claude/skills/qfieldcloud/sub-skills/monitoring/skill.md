---
name: qfieldcloud-monitoring
version: 1.0.0
description: Comprehensive health monitoring for QFieldCloud
triggers: ["qfield status", "check qfield", "qfield health", "monitor", "is qfield working", "service status"]
context_cost: 500
priority: high
isolation: full
---

# QFieldCloud System Monitoring

Complete health check and status monitoring for all QFieldCloud components.

## Quick Commands

```bash
# Full system health check
./scripts/health_check.sh

# Quick status (one-line summary)
./scripts/quick_status.sh

# Live dashboard (updates every 30s)
./scripts/dashboard.sh

# Check critical issues only
./scripts/critical_check.sh

# Service dependencies check
./scripts/dependencies.sh
```

## System Components

### Core Services
- **nginx** - Web server (port 8082)
- **app** - Django application
- **db** - PostgreSQL database (port 5433)
- **redis** - Cache/queue
- **minio** - S3 storage (ports 8009-8010)

### Processing
- **worker_wrapper** - 8 workers for job processing
- **qfieldcloud-qgis** - Docker image (2.6GB)

### Critical Checks
1. All services running
2. QGIS image present
3. Workers processing jobs
4. CSRF configuration valid
5. Database accessible
6. Storage operational

## Health Indicators

🟢 **Healthy** - All systems operational
🟡 **Warning** - Non-critical issues detected
🔴 **Critical** - Service failure, immediate action needed

## Common Issues

| Symptom | Check | Fix |
|---------|-------|-----|
| Projects failing | QGIS image | `../qgis-image/scripts/restore.sh` |
| 403 errors | CSRF config | `../csrf-fix/scripts/apply_fix.sh` |
| No workers | Worker status | `../worker-ops/scripts/restart.sh` |