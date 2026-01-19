---
name: qfieldcloud-qgis-image
version: 1.0.0
description: Critical QGIS Docker image management for QFieldCloud
triggers: ["qgis missing", "projects failing", "ImageNotFound", "pull access denied", "qfieldcloud-qgis"]
context_cost: 500
priority: critical
isolation: full
---

# QFieldCloud QGIS Image Management

Emergency management for the critical `qfieldcloud-qgis:latest` Docker image that mysteriously disappears.

## Quick Commands

```bash
# Check if image exists
./scripts/check.sh

# Restore from backup (30 seconds)
./scripts/restore.sh

# Rebuild from source (5 minutes)
./scripts/rebuild.sh

# Create new backup
./scripts/backup.sh
```

## Critical Information

- **Image**: qfieldcloud-qgis:latest (2.6GB)
- **Backup**: ~/qfield-backups/qfieldcloud-qgis-20260113-1034.tar.gz
- **Monitor**: /home/velo/check_qgis_image.sh (runs every 6 hours)

## Common Error

```
Error: "pull access denied for qfieldcloud-qgis, repository does not exist"
```

This means the image is missing. Run `restore.sh` immediately.