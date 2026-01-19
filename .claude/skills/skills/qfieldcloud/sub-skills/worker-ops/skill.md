---
name: qfieldcloud-worker-ops
version: 1.0.0
description: Worker management for QFieldCloud processing tasks
triggers: ["restart workers", "workers not running", "scale workers", "worker status", "worker logs", "worker_wrapper"]
context_cost: 600
priority: high
isolation: full
---

# QFieldCloud Worker Operations

Fast management for QFieldCloud worker containers that process GIS projects.

## Quick Commands

```bash
# Check worker status (should show 8 workers)
./scripts/status.sh

# Restart all workers
./scripts/restart.sh

# Scale workers (default: 8)
./scripts/scale.sh [number]

# View recent worker logs
./scripts/logs.sh [lines]

# Check for worker errors
./scripts/check_errors.sh
```

## Important Information

- **Service Name**: worker_wrapper (NOT worker1, worker2, etc.)
- **Default Count**: 8 workers (scaled service)
- **Container Names**: qfieldcloud-worker_wrapper-1 through 8
- **Dependencies**: Requires QGIS image to be present

## Common Issues

### Workers Not Processing
1. Check QGIS image exists: `../qgis-image/scripts/check.sh`
2. Restart workers: `./scripts/restart.sh`
3. Check logs for errors: `./scripts/check_errors.sh`

### Scaling Workers
- More workers = faster processing but higher resource usage
- Default 8 workers is optimal for VF Server
- Minimum: 2 workers, Maximum: 16 workers