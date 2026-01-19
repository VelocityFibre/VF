---
name: qfieldcloud
version: 2.0.0
description: Orchestrator for QFieldCloud GIS synchronization platform
author: FibreFlow Team
category: application
context_cost: 200  # Minimal - just orchestration
triggers: ["qfield", "qfc", "gis", "sync"]
---

# QFieldCloud Management (Optimized)

Lightweight orchestrator for QFieldCloud operations. Uses sub-skills for specific tasks.

## 🚨 Critical Operations (Sub-Skills)

### QGIS Docker Image
**Triggers**: "projects failing", "ImageNotFound", "pull access denied"
**Sub-skill**: `sub-skills/qgis-image/`
**Context cost**: 500 tokens

### CSRF Configuration
**Triggers**: "CSRF verification failed", "403 Forbidden"
**Sub-skill**: `sub-skills/csrf-fix/`
**Context cost**: 400 tokens

### Worker Management ✅
**Triggers**: "restart workers", "scale workers", "worker status", "worker logs"
**Sub-skill**: `sub-skills/worker-ops/`
**Context cost**: 600 tokens
**Scripts**: status, restart, scale, logs, check_errors

### System Monitoring ✅
**Triggers**: "qfield status", "check qfield", "qfield health", "is qfield working"
**Sub-skill**: `sub-skills/monitoring/`
**Context cost**: 500 tokens
**Scripts**: health_check, quick_status, dashboard, critical_check, dependencies

### Fault Logging & Analytics + Alerting ✅ 🚨
**Triggers**: "#logFault", "log fault", "quick fault", "fault history", "search faults", "analyze faults"
**Sub-skill**: `sub-skills/fault-logging/`
**Context cost**: 450 tokens (90% cheaper than detailed incidents)
**Scripts**: simple_log_fault, log_fault, auto_log, search_faults, analyze_faults, fault_report, recent_faults, alert, check_and_alert, setup_monitoring
**Features**: Quick JSON logging, automatic WhatsApp alerts for CRITICAL faults (30-min cooldown), pattern analysis, searchable history
**Note**: For detailed investigations with root cause analysis, use `#logFaultDetail` (4,000 tokens, logs to INCIDENT_LOG.md)

### Database Operations
**Triggers**: "query projects", "backup database"
**Sub-skill**: `sub-skills/database/`
**Context cost**: 400 tokens (with pooling)

## Quick Status Check

```bash
# Overall health (23ms, 930 tokens total)
./scripts/status.py

# Specific checks use sub-skills
./sub-skills/qgis-image/scripts/check.sh
./sub-skills/csrf-fix/scripts/diagnose.sh
```

## Progressive Disclosure

This orchestrator only loads what's needed:
- Base cost: 200 tokens (this file)
- Operation cost: +400-600 tokens (specific sub-skill)
- **Total**: 600-800 tokens vs 4,500 (84% savings)

## Server Details

- **Host**: 100.96.203.105:8082
- **URL**: https://qfield.fibreflow.app
- **Services**: app, nginx, db, redis, minio, worker_wrapper (×8)