# QFieldCloud Migration to VF Server Plan
**Created**: 2026-01-08
**Source**: 72.61.166.168 (Old Hostinger)
**Target**: 100.96.203.105 (VF Server, Port 8080)
**Status**: READY TO EXECUTE

## Executive Summary

Migrate QFieldCloud from resource-constrained old Hostinger server (4 workers max, 8GB RAM) to VF Server with battery backup and better resources. This will solve upload flooding issues by enabling 8-12 workers.

## Pre-Migration Status ✅ COMPLETE

All optimization tasks completed:
- Disk usage: 78% (reduced from 86%)
- Database: 380MB (optimized from 414MB)
- Docker cleaned: 4.9GB freed
- Configuration: Fully documented
- Backups: Created and verified

## Migration Architecture

```
Current Setup (72.61.166.168):
├── QFieldCloud on port 443 (nginx)
├── 4 workers (max capacity)
├── PostgreSQL database
├── MinIO storage (4 volumes)
└── 8GB RAM, 2-4 cores

Target Setup (100.96.203.105):
├── Port 3000: FibreFlow production
├── Port 3005: Hein's dev instance
├── Port 3006: Louis's staging
├── Port 8080: QFieldCloud (NEW) ← Migration target
├── Port 8081: WhatsApp sender
└── 32+ GB RAM, 16+ cores (estimated)
```

## Phase 1: Pre-Migration Preparation (VF Server)

### 1.1 Check VF Server Resources
```bash
# SSH to VF Server
ssh velo@100.96.203.105  # password: 2025

# Check available resources
free -h
df -h /
nproc
docker ps

# Check port 8080 availability
sudo netstat -tulpn | grep 8080
```

### 1.2 Create QFieldCloud Directory Structure
```bash
# Create directories
sudo mkdir -p /opt/qfieldcloud
sudo chown velo:velo /opt/qfieldcloud

# Create data directories
mkdir -p /opt/qfieldcloud/{data,backups,logs}
```

### 1.3 Install Dependencies (if needed)
```bash
# Ensure Docker and docker-compose are latest
docker --version
docker compose version

# Install if missing
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker velo
```

## Phase 2: Data Transfer

### 2.1 Transfer Database Backup
```bash
# On VF Server, pull database backup
scp root@72.61.166.168:/root/qfield_db_backup_20260108_090406.sql /opt/qfieldcloud/backups/

# Or use rsync for resume capability
rsync -avP root@72.61.166.168:/root/qfield_db_backup_20260108_090406.sql /opt/qfieldcloud/backups/
```

### 2.2 Transfer Configuration
```bash
# Transfer configuration archive
scp root@72.61.166.168:/root/qfield_config_20260108_091458.tar.gz /opt/qfieldcloud/

# Extract configuration
cd /opt/qfieldcloud
tar -xzf qfield_config_20260108_091458.tar.gz

# Copy docker-compose files
cp qfield_config_*/docker-compose*.yml ./
```

### 2.3 Transfer MinIO Data (Large - Plan Downtime)
```bash
# Option 1: Docker volume backup (recommended)
# On OLD server:
docker run --rm -v qfieldcloud_minio_data1:/data -v $(pwd):/backup alpine tar czf /backup/minio_data1.tar.gz -C /data .
docker run --rm -v qfieldcloud_minio_data2:/data -v $(pwd):/backup alpine tar czf /backup/minio_data2.tar.gz -C /data .
docker run --rm -v qfieldcloud_minio_data3:/data -v $(pwd):/backup alpine tar czf /backup/minio_data3.tar.gz -C /data .
docker run --rm -v qfieldcloud_minio_data4:/data -v $(pwd):/backup alpine tar czf /backup/minio_data4.tar.gz -C /data .

# Transfer to VF Server
rsync -avP minio_data*.tar.gz velo@100.96.203.105:/opt/qfieldcloud/backups/

# Option 2: MinIO client sync (if possible)
# Configure mc client and sync buckets
```

## Phase 3: Configuration Updates

### 3.1 Update .env for VF Server
```bash
cd /opt/qfieldcloud
cp qfield_config_*/.env .env

# Edit .env file
nano .env
```

Key changes:
```env
# Server Configuration
QFIELDCLOUD_HOST=qfield.fibreflow.app
ENVIRONMENT=production

# Port Configuration (CRITICAL)
QFIELDCLOUD_PORT=8080
NGINX_PORT=8080

# Worker Scaling (INCREASE!)
QFIELDCLOUD_WORKER_REPLICAS=8  # From 4 to 8 initially

# Database (will be localhost after restore)
POSTGRES_HOST=db
POSTGRES_PORT=5432

# MinIO Configuration
MINIO_ENDPOINT=minio:9000
```

### 3.2 Update docker-compose.yml
```yaml
version: '3.8'

services:
  nginx:
    ports:
      - "8080:80"  # Changed from 443:443
    # Remove SSL configuration (Cloudflare will handle)

  app:
    environment:
      - PORT=8080
    # No external port mapping needed

  worker_wrapper:
    deploy:
      replicas: ${QFIELDCLOUD_WORKER_REPLICAS:-8}
```

### 3.3 Configure Nginx Reverse Proxy (Main VF Server)
```bash
# Add to main nginx configuration
sudo nano /etc/nginx/sites-available/qfieldcloud

server {
    listen 8080;
    server_name qfield.fibreflow.app;

    location / {
        proxy_pass http://localhost:8080;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # WebSocket support
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";

        # Timeouts for large file uploads
        proxy_read_timeout 600s;
        proxy_send_timeout 600s;
        client_max_body_size 500M;
    }
}

# Enable site
sudo ln -s /etc/nginx/sites-available/qfieldcloud /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

## Phase 4: Service Deployment

### 4.1 Restore Database
```bash
cd /opt/qfieldcloud

# Start only database container
docker compose up -d db

# Wait for database to be ready
sleep 10

# Restore database
docker exec -i qfieldcloud-db-1 psql -U qfieldcloud_db_admin postgres < backups/qfield_db_backup_20260108_090406.sql
```

### 4.2 Restore MinIO Volumes
```bash
# Create volumes
docker volume create qfieldcloud_minio_data1
docker volume create qfieldcloud_minio_data2
docker volume create qfieldcloud_minio_data3
docker volume create qfieldcloud_minio_data4

# Restore data
docker run --rm -v qfieldcloud_minio_data1:/data -v $(pwd)/backups:/backup alpine tar xzf /backup/minio_data1.tar.gz -C /data
docker run --rm -v qfieldcloud_minio_data2:/data -v $(pwd)/backups:/backup alpine tar xzf /backup/minio_data2.tar.gz -C /data
docker run --rm -v qfieldcloud_minio_data3:/data -v $(pwd)/backups:/backup alpine tar xzf /backup/minio_data3.tar.gz -C /data
docker run --rm -v qfieldcloud_minio_data4:/data -v $(pwd)/backups:/backup alpine tar xzf /backup/minio_data4.tar.gz -C /data
```

### 4.3 Start All Services
```bash
# Start remaining services
docker compose up -d

# Check status
docker compose ps

# Check logs
docker compose logs -f --tail 50
```

### 4.4 Verify Services
```bash
# Check worker count (should be 8)
docker ps | grep worker | wc -l

# Test API endpoint
curl -I http://localhost:8080/api/v1/status/

# Check database connection
docker exec qfieldcloud-db-1 psql -U qfieldcloud_db_admin -d qfieldcloud_db -c "SELECT COUNT(*) FROM core_job;"
```

## Phase 5: DNS and SSL Configuration

### 5.1 Update Cloudflare DNS
```
Current: qfield.fibreflow.app → 72.61.166.168
New: qfield.fibreflow.app → 100.96.203.105

Type: A record
Proxied: Yes (orange cloud)
```

### 5.2 Configure Cloudflare SSL
- SSL/TLS mode: Flexible (since internal is HTTP on 8080)
- Always Use HTTPS: On
- Automatic HTTPS Rewrites: On

## Phase 6: Testing and Validation

### 6.1 Internal Testing
```bash
# Test from VF Server
curl -H "Host: qfield.fibreflow.app" http://localhost:8080/api/v1/status/

# Should return JSON status
```

### 6.2 External Testing (After DNS)
```bash
# From any external machine
curl https://qfield.fibreflow.app/api/v1/status/

# Test with QField mobile app
# Update server URL to https://qfield.fibreflow.app
```

### 6.3 Load Testing
```bash
# Monitor worker performance
docker stats --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}"

# Watch queue depth
watch 'docker exec qfieldcloud-db-1 psql -U qfieldcloud_db_admin -d qfieldcloud_db -t -c "SELECT COUNT(*) FROM core_job WHERE status IN ('"'"'pending'"'"','"'"'queued'"'"');"'
```

## Phase 7: Post-Migration Optimization

### 7.1 Enable Rate Limiting
```bash
# Add to .env
QFIELDCLOUD_RATE_LIMIT_ENABLED=true
QFIELDCLOUD_RATE_LIMIT_PER_PROJECT=10  # 10 syncs/minute per project
QFIELDCLOUD_RATE_LIMIT_PER_USER=5      # 5 syncs/minute per user

# Restart services
docker compose restart app worker_wrapper
```

### 7.2 Scale Workers Based on Load
```bash
# Monitor for 24 hours, then adjust
# If queue stays low, keep 8 workers
# If queue builds up, increase to 10-12

# To change worker count:
sed -i 's/QFIELDCLOUD_WORKER_REPLICAS=8/QFIELDCLOUD_WORKER_REPLICAS=10/' .env
docker compose up -d --scale worker_wrapper=10
```

### 7.3 Set Up Monitoring
```bash
# Install monitoring daemon
cp /old/scripts/worker_monitor_daemon.py /opt/qfieldcloud/scripts/
python3 /opt/qfieldcloud/scripts/worker_monitor_daemon.py &

# Add to systemd for persistence
sudo nano /etc/systemd/system/qfield-monitor.service

[Unit]
Description=QFieldCloud Monitor
After=docker.service

[Service]
Type=simple
User=velo
WorkingDirectory=/opt/qfieldcloud
ExecStart=/usr/bin/python3 /opt/qfieldcloud/scripts/worker_monitor_daemon.py
Restart=always

[Install]
WantedBy=multi-user.target

# Enable service
sudo systemctl enable qfield-monitor
sudo systemctl start qfield-monitor
```

## Migration Timeline

**Total Estimated Time**: 2-4 hours

| Phase | Task | Time | Downtime |
|-------|------|------|----------|
| 1 | VF Server Preparation | 30 min | None |
| 2 | Data Transfer | 60 min | None |
| 3 | Configuration | 30 min | None |
| 4 | Service Deployment | 30 min | None |
| 5 | DNS Switch | 5 min | **START** |
| 6 | Testing | 30 min | Service available |
| 7 | Optimization | 30 min | None |

**Actual Downtime**: ~30 minutes (DNS propagation)

## Rollback Plan

If issues occur:

1. **Immediate Rollback** (< 5 minutes):
```bash
# Change DNS back to old server
qfield.fibreflow.app → 72.61.166.168

# Old server still running
```

2. **Data Rollback**:
- Database backup available: `/opt/qfieldcloud/backups/`
- Configuration backed up: `qfield_config_*/`
- MinIO data preserved in tar.gz files

## Success Metrics

After migration, expect:

| Metric | Before | After Target |
|--------|--------|--------------|
| Workers | 4 | 8-12 |
| Queue Depth | >10 (overflow) | <5 |
| Sync Success Rate | <80% | >95% |
| Concurrent Users | 10 max | 30+ |
| Sync Duration | 15-25s | 10-15s |
| Uptime | 95% | 99%+ (battery backup) |

## Important Notes

1. **Port 8080**: Ensure not conflicting with other services on VF Server
2. **Firewall**: Open port 8080 if needed (though Cloudflare proxy should handle)
3. **Backups**: Keep old server running for 48 hours minimum
4. **Monitoring**: Watch worker memory usage closely first 24 hours
5. **DNS**: Use Cloudflare proxy for DDoS protection and caching

## Contact Points

- VF Server: velo@100.96.203.105 (password: 2025)
- Old Server: root@72.61.166.168
- QFieldCloud Issues: https://github.com/opengisch/QFieldCloud
- Cloudflare DNS: [Your Cloudflare account]

---
**Status**: Ready for execution
**Risk Level**: Low (full rollback available)
**Recommended Window**: Weekend or after hours