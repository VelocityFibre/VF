# Server Infrastructure

## VF Server (Primary Production) - 100.96.203.105
- **Status**: ✅ Production + Dev/Staging
- **Uptime**: 99%+ with UPS battery backup (1-2 hours during load shedding)
- **Location**: Velocity Fibre office
- **Specs**: 32GB RAM, 8 CPU cores, 1TB NVMe
- **OS**: Ubuntu 22.04 LTS

### SSH Access
```bash
# Limited sudo (monitoring only) - USE THIS BY DEFAULT
ssh -i ~/.ssh/vf_server_key louis@100.96.203.105
Password (when needed): VeloBoss@2026

# Full sudo (admin tasks) - ONLY WITH APPROVAL
ssh -i ~/.ssh/vf_server_key velo@100.96.203.105
```

### Service Ports
```
3000  - FibreFlow Production (app.fibreflow.app)
3005  - Development (Hein)
3006  - Staging (Louis)
8081  - WhatsApp Sender
8082  - QFieldCloud (qfield.fibreflow.app)
8091  - Storage API (Firebase replacement)
8092  - WA Monitor Microservice
8095  - OCR Service
8100  - VLM (Vision Language Model)
5433  - PostgreSQL for QFieldCloud
8009  - MinIO Storage
8010  - MinIO Console
```

### Key Directories
```
/srv/data/apps/fibreflow/          # Production app
/srv/data/apps/fibreflow-staging/  # Staging app
/opt/qfieldcloud/                   # QFieldCloud
/opt/team-scripts/                  # Management scripts
/opt/ocr-service/                   # OCR service
/srv/data/fibreflow-storage/        # File storage
```

## Hostinger VPS (Backup) - 72.61.197.178
- **Status**: Cold standby
- **Purpose**: Disaster recovery only
- **Cost**: R20-30/month
- **Activation**: Only if VF Server fails
- **SSH**: `ssh root@72.61.197.178` (password: VeloF@2025@@)

## Decommissioned Servers
- **QFieldCloud Old** (72.61.166.168): Migrated to VF Server Jan 2026
- **Old Hostinger** (72.60.17.245): Being decommissioned

## Cloudflare Infrastructure
- **Tunnel ID**: 0bf9e4fa-f650-498c-bd23-def05abe5aaf
- **Running as**: User `velo` on VF Server
- **Routes**:
  - app.fibreflow.app → localhost:3000
  - qfield.fibreflow.app → localhost:8082
  - vf.fibreflow.app → localhost:3006
  - support.fibreflow.app → localhost:8090

## Server Monitoring
```bash
# System resources
ssh louis@100.96.203.105 'htop'

# Disk usage
ssh louis@100.96.203.105 'df -h'

# Service status
ssh louis@100.96.203.105 'sudo systemctl status'

# Docker containers (QFieldCloud)
ssh louis@100.96.203.105 'sudo docker ps'

# PM2 processes (Node.js apps)
ssh louis@100.96.203.105 'pm2 list'
```

## Backup Strategy
- **Database**: Neon handles automatic backups
- **Files**: Daily rsync to Hostinger backup VPS
- **Code**: Git repositories (GitHub)
- **WhatsApp Sessions**: Manual backup before migrations

## Security Notes
- Password authentication disabled (SSH key only)
- Firewall configured (ufw)
- Fail2ban active
- Regular security updates
- Limited sudo for louis account