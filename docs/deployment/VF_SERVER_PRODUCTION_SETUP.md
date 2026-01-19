# 🚀 VF Server Production Migration Guide
**Primary Server**: 100.96.203.105 (VF Server with Battery Backup)
**Backup Server**: 72.61.197.178 (Hostinger VPS)
**Date**: 2026-01-08
**Purpose**: Move all production services to VF Server with battery backup

## 📊 Corrected Architecture

```
┌─────────────────────────────────────────────────┐
│      VF SERVER (100.96.203.105)                 │
│         PRIMARY PRODUCTION                       │
│         With Battery Backup System               │
│                                                  │
│  Current Services (keeping):                     │
│  ○ Dev instance (port 3005 - Hein)              │
│  ○ Staging (port 3006 - Louis)                  │
│                                                  │
│  New Production Services (adding):               │
│  ✅ app.fibreflow.app (port 3000)               │
│  ✅ qfield.fibreflow.app (port 8080)            │
│  ✅ WhatsApp Sender (port 8081)                 │
│  ✅ All critical production services             │
│                                                  │
│  Uptime: 99%+ with battery backup               │
│  Cost: Electricity only (~R300/month)           │
└─────────────────────────────────────────────────┘
                    ↕ Failover
┌─────────────────────────────────────────────────┐
│    HOSTINGER VPS (72.61.197.178)                │
│         BACKUP/FAILOVER                         │
│                                                  │
│  Services:                                       │
│  ○ Cold standby for production                  │
│  ○ Database backups                             │
│  ○ Disaster recovery                            │
│  ○ Manual failover if VF Server fails           │
│                                                  │
│  Uptime: 99.9% (datacenter)                     │
│  Cost: R20-30/month                             │
└─────────────────────────────────────────────────┘
```

## 🎯 Why This Architecture Makes Sense

1. **VF Server has battery backup now** - Eliminates load shedding risk
2. **Already has infrastructure** - Existing server, just add production services
3. **Cost effective** - No additional hardware needed
4. **Keeps dev/staging** - Ports 3005/3006 continue as-is
5. **Hostinger as insurance** - R20-30/month for peace of mind

## 📁 VF Server Directory Structure

```bash
# Existing (keep as-is)
/home/velo/
├── fibreflow-hein/         # Port 3005 (dev)
├── fibreflow-louis/        # Port 3006 (staging)
└── .cloudflared/           # Tunnel config

# New Production Directories
/opt/
├── fibreflow-prod/         # Production app (port 3000)
│   ├── app/                # Application code
│   ├── .env.production     # Production environment
│   └── ecosystem.config.js # PM2 config
│
├── qfieldcloud/            # QFieldCloud sync (port 8080)
│   ├── app/                # Application code
│   ├── workers/            # Background workers
│   └── config/             # Configuration
│
├── whatsapp-sender/        # WhatsApp service (port 8081)
│   ├── whatsapp-sender     # Go binary
│   ├── store/              # Session data (CRITICAL)
│   └── config.json         # Configuration
│
└── monitoring/             # Health monitoring
    ├── scripts/            # Monitoring scripts
    └── dashboards/         # Status pages

/var/
├── log/                    # Centralized logs
│   ├── fibreflow-prod/     # Production logs
│   ├── qfieldcloud/        # Sync logs
│   └── whatsapp/           # WhatsApp logs
│
└── backups/                # Local backups
    └── sync-to-hostinger/  # Replicated to backup server
```

## 🔧 Migration Steps for VF Server

### Step 1: Prepare VF Server for Production

```bash
# SSH to VF Server
ssh velo@100.96.203.105  # password: 2025

# Create production directories (as root or with sudo)
sudo mkdir -p /opt/{fibreflow-prod,qfieldcloud,whatsapp-sender,monitoring}
sudo mkdir -p /var/log/{fibreflow-prod,qfieldcloud,whatsapp}
sudo mkdir -p /var/backups/sync-to-hostinger

# Set ownership
sudo chown -R velo:velo /opt/fibreflow-prod
sudo chown -R velo:velo /opt/qfieldcloud
sudo chown -R velo:velo /opt/whatsapp-sender
sudo chown -R velo:velo /opt/monitoring

# Install PM2 globally if not present
sudo npm install -g pm2
```

### Step 2: Deploy Production FibreFlow

```bash
# Deploy production app to new location
cd /opt/fibreflow-prod
git clone https://github.com/VelocityFibre/fibreflow.git .
npm install --production

# Copy production environment from old Hostinger
scp root@72.60.17.245:/var/www/fibreflow/.env .env.production

# Create PM2 ecosystem file
cat > ecosystem.config.js << 'EOF'
module.exports = {
  apps: [{
    name: "fibreflow-production",
    script: "npm",
    args: "start",
    cwd: "/opt/fibreflow-prod",
    env: {
      NODE_ENV: "production",
      PORT: 3000
    },
    env_file: ".env.production",
    max_memory_restart: "2G",
    error_file: "/var/log/fibreflow-prod/error.log",
    out_file: "/var/log/fibreflow-prod/out.log",
    merge_logs: true,
    time: true,
    instances: 2,
    exec_mode: "cluster"
  }]
}
EOF

# Start production app
pm2 start ecosystem.config.js
pm2 save
```

### Step 3: Migrate QFieldCloud

```bash
# Transfer QFieldCloud from old Hostinger
cd /opt/qfieldcloud
scp -r root@72.60.17.245:/opt/qfieldcloud/* .

# Update configuration for new server
# Edit config files to use local paths

# Start QFieldCloud service
pm2 start app/index.js --name qfieldcloud --max-memory-restart 1G
pm2 save
```

### Step 4: Setup WhatsApp Sender

```bash
# Transfer WhatsApp sender from Hostinger
cd /opt/whatsapp-sender
scp root@72.60.17.245:/opt/whatsapp-sender/whatsapp-sender .
scp -r root@72.60.17.245:/opt/whatsapp-sender/store .

# CRITICAL: Preserve session
chmod +x whatsapp-sender

# Create systemd service (optional, or use PM2)
pm2 start whatsapp-sender --name whatsapp --max-memory-restart 500M
pm2 save
```

### Step 5: Configure Nginx

```bash
# Update nginx configuration
sudo nano /etc/nginx/sites-available/fibreflow-production

# Add production config
server {
    listen 80;
    server_name app.fibreflow.app;

    location / {
        proxy_pass http://localhost:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }
}

server {
    listen 80;
    server_name qfield.fibreflow.app;

    location / {
        proxy_pass http://localhost:8080;
        # Same proxy settings
    }
}

# Enable and reload
sudo ln -s /etc/nginx/sites-available/fibreflow-production /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

## 🔄 Port Allocation on VF Server

```
Port 3000 - FibreFlow Production (NEW)
Port 3005 - FibreFlow Dev (Hein) - EXISTING
Port 3006 - FibreFlow Staging (Louis) - EXISTING
Port 8080 - QFieldCloud (NEW)
Port 8081 - WhatsApp Sender (NEW)
Port 8100 - VLM (Qwen3-VL) - EXISTING
```

## 🔐 Hostinger Backup Server Setup

### Purpose of 72.61.197.178
- **Cold standby** - Ready to take over if VF Server fails
- **Database backups** - Daily sync from VF Server
- **Disaster recovery** - Can be activated within 30 minutes
- **Not active** - DNS points to VF Server normally

### Basic Setup for Backup Server

```bash
# SSH to Hostinger backup
ssh root@72.61.197.178

# Create backup directories
mkdir -p /opt/backups/{database,files,configs}
mkdir -p /opt/fibreflow-standby

# Install essentials
apt update && apt upgrade -y
apt install -y nodejs npm nginx postgresql-client
npm install -g pm2

# Clone production code (standby)
cd /opt/fibreflow-standby
git clone https://github.com/VelocityFibre/fibreflow.git .
npm install --production

# DO NOT START SERVICES - This is cold standby
# Services only start during failover
```

### Automated Backup Sync

Create sync script on VF Server:
```bash
# /opt/monitoring/scripts/sync-to-backup.sh
#!/bin/bash

BACKUP_SERVER="72.61.197.178"
BACKUP_USER="root"

# Sync database backups
rsync -avz /var/backups/daily/ $BACKUP_USER@$BACKUP_SERVER:/opt/backups/database/

# Sync configurations
rsync -avz /opt/fibreflow-prod/.env* $BACKUP_USER@$BACKUP_SERVER:/opt/backups/configs/

# Sync WhatsApp session (CRITICAL)
rsync -avz /opt/whatsapp-sender/store/ $BACKUP_USER@$BACKUP_SERVER:/opt/backups/whatsapp-session/

echo "Backup sync completed: $(date)" >> /var/log/backup-sync.log
```

Add to cron:
```bash
crontab -e
# Add: 0 2 * * * /opt/monitoring/scripts/sync-to-backup.sh
```

## 🔄 Failover Process

### If VF Server Fails:

1. **Detect failure** (monitoring alerts)
2. **SSH to backup server** (72.61.197.178)
3. **Restore latest backup**:
   ```bash
   cd /opt/fibreflow-standby
   cp /opt/backups/configs/.env* .
   cp -r /opt/backups/whatsapp-session/* /opt/whatsapp-sender/store/
   ```
4. **Start services**:
   ```bash
   pm2 start ecosystem.config.js
   systemctl start whatsapp-sender
   ```
5. **Update DNS** in CloudFlare:
   - app.fibreflow.app → 72.61.197.178
   - qfield.fibreflow.app → 72.61.197.178
6. **Monitor** until VF Server is restored

### Failback to VF Server:
1. Fix VF Server issue
2. Sync any changes from backup to VF
3. Switch DNS back to 100.96.203.105
4. Stop services on backup server

## 📋 Migration Checklist

### Pre-Migration
- [x] VF Server has battery backup installed
- [ ] Test battery backup during load shedding
- [ ] Backup all data from old Hostinger (72.60.17.245)
- [ ] Document all environment variables
- [ ] Test network connectivity

### Migration Day
- [ ] Create production directories on VF Server
- [ ] Deploy FibreFlow production (port 3000)
- [ ] Deploy QFieldCloud (port 8080)
- [ ] Migrate WhatsApp sender (preserve session!)
- [ ] Configure nginx
- [ ] Test all services locally
- [ ] Setup backup sync to Hostinger (72.61.197.178)
- [ ] Update CloudFlare DNS to point to VF Server
- [ ] Monitor for 24 hours

### Post-Migration
- [ ] Verify all services running
- [ ] Check backup sync working
- [ ] Document any issues
- [ ] Decommission old Hostinger (72.60.17.245)
- [ ] Update all documentation

## 🚨 Important Notes

1. **Battery Backup Critical** - Test UPS before migration
2. **WhatsApp Session** - NEVER delete store/ directory
3. **Port Conflicts** - Production uses 3000, not 3005
4. **Dev/Staging Continue** - Ports 3005/3006 unchanged
5. **DNS Propagation** - Can take 1-24 hours
6. **Backup Server** - Keep minimal, cold standby only

## 📊 Cost Analysis

| Item | Old Cost | New Cost | Savings |
|------|----------|----------|---------|
| Hostinger VPS #1 | R30/month | R0 | R30/month |
| Hostinger VPS #2 | R30/month | R20/month (backup only) | R10/month |
| VF Server | R200/month (electricity) | R300/month (electricity + UPS) | -R100/month |
| **Total** | **R260/month** | **R320/month** | **-R60/month** |

**Note**: Slight increase due to UPS power consumption, but gain full control and eliminate dependency on multiple external servers. The R20-30/month for backup Hostinger is insurance.

## 🎯 For Hein - Quick Summary

```
VF Server (100.96.203.105) becomes MAIN production:
- Already has dev (3005) and staging (3006)
- Add production on port 3000
- Add QFieldCloud on port 8080
- Battery backup makes it reliable

Hostinger (72.61.197.178) becomes BACKUP:
- Cold standby only
- Daily backups from VF Server
- Can activate if VF fails
- R20-30/month for insurance

Old Hostinger (72.60.17.245):
- Migrate everything then shut down
- Saves R30/month
```

---

**Questions?** This is the corrected plan with VF Server as primary production.
**Last Updated**: 2026-01-08