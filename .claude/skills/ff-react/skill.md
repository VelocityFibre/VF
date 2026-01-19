---
name: ff-react
version: 1.0.0
description: Complete management suite for FibreFlow React Next.js application
author: FibreFlow Team
category: application
tags: [nextjs, react, deployment, monitoring, database, vps]
created: 2024-12-17
---

# FF_React Application Management Skill

Comprehensive skill for managing the FibreFlow React Next.js application including deployment, monitoring, database operations, and service management.

## Features

- **Deployment Management**: Deploy to production and development environments
- **Process Monitoring**: Check PM2 status, view logs, restart services
- **Database Operations**: Query FF_React specific tables (drops, qa_photo_reviews, etc.)
- **VLM Service Control**: Manage Vision Language Model services
- **Git Operations**: Check status, pull updates, manage branches
- **Performance Monitoring**: Check server metrics, response times
- **WhatsApp Monitor**: Manage WA monitor services and groups

## Quick Usage

```bash
# Deploy to production
./scripts/deploy.py --env production

# Check application status
./scripts/status.py

# View recent logs
./scripts/logs.py --lines 50

# Query database
./scripts/query.py --table contractors --limit 10

# Manage VLM service
./scripts/vlm.py --action status
```

## Server Configuration

- **Production**: app.fibreflow.app (port 3005)
- **Development**: dev.fibreflow.app (port 3006)
- **Server**: 100.96.203.105 (Tailscale) / 192.168.1.150 (LAN)
- **Access**: SSH with key or password

## Application Details

- **Location**: `/home/louisdup/VF/Apps/FF_React/`
- **Framework**: Next.js 14.2.18
- **Database**: Neon PostgreSQL
- **Auth**: Clerk
- **Storage**: Firebase Storage
- **Real-time**: Socket.io + Convex

## Environment Variables

Required environment variables (stored in .env):
- `VF_SERVER_HOST`: Server IP address
- `VF_SERVER_USER`: SSH username
- `FF_REACT_DB_URL`: Neon database connection string
- `VF_SERVER_PASSWORD`: SSH password (optional if using key)

## Scripts Available

| Script | Purpose | Usage |
|--------|---------|-------|
| `deploy.py` | Deploy application | `--env [production\|development]` |
| `status.py` | Check PM2 processes | No args |
| `logs.py` | View application logs | `--lines N --env [prod\|dev]` |
| `query.py` | Database queries | `--query "SQL" or --table NAME` |
| `vlm.py` | VLM service control | `--action [status\|restart\|test]` |
| `wa-monitor.py` | WhatsApp monitor | `--action [status\|groups\|restart]` |
| `rollback.py` | Rollback deployment | `--env [prod\|dev] --commit HASH` |

## Common Operations

### Deploy to Production
```bash
./scripts/deploy.py --env production
```
This will:
1. SSH to server
2. Pull latest from master branch
3. Install dependencies
4. Build application
5. Restart PM2 process

### Check Application Health
```bash
./scripts/status.py
```
Shows:
- PM2 process status
- Memory usage
- CPU usage
- Uptime
- Recent error count

### View Logs
```bash
./scripts/logs.py --lines 100 --env production
```
Displays recent application logs with:
- Timestamps
- Log levels
- Error highlighting

### Database Query
```bash
# Query specific table
./scripts/query.py --table contractors --limit 20

# Custom SQL query
./scripts/query.py --query "SELECT * FROM qa_photo_reviews WHERE project = 'Lawley' ORDER BY upload_time DESC LIMIT 10"
```

### Manage WhatsApp Monitor
```bash
# Check status
./scripts/wa-monitor.py --action status

# List monitored groups
./scripts/wa-monitor.py --action groups

# Restart service (safe restart)
./scripts/wa-monitor.py --action restart
```

## Troubleshooting

### Common Issues

1. **Dev server Watchpack bug**: Always use production build locally
2. **Nested routes fail**: Use flattened API routes
3. **WA Monitor not sending**: Restart whatsapp-bridge-prod service

### Emergency Commands

```bash
# Force restart production
./scripts/deploy.py --env production --force-restart

# Rollback to previous commit
./scripts/rollback.py --env production --commit HEAD~1

# Check server resources
./scripts/status.py --detailed
```

## Integration with Other Skills

This skill works with:
- `vf-server`: For direct server operations
- `database-operations`: For complex database queries
- `git-operations`: For repository management

## Notes

- Always deploy to development first for testing
- Production deployments should be done during low-traffic periods
- Keep logs for debugging deployment issues
- Monitor server resources during deployments