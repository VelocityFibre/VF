# VF Server Directory Structure

**Server**: velo-server (100.96.203.105)
**OS**: Ubuntu 24.04.3 LTS
**Storage**: NVMe (984GB total, 900GB free)
**Updated**: 2025-12-22

---

## Complete Directory Layout

```
/srv/
├── data/                            # Main NVMe storage (984GB, 4% used)
│   │
│   ├── apps/                        # Production applications
│   │   │
│   │   ├── fibreflow/              # FibreFlow main app (34GB)
│   │   │   ├── pages/
│   │   │   ├── components/
│   │   │   ├── public/
│   │   │   ├── .next/
│   │   │   ├── package.json
│   │   │   ├── CLAUDE.md
│   │   │   └── ...
│   │   │   • URL: https://app.fibreflow.app
│   │   │   • Port: 3005 (Next.js)
│   │   │   • Service: PM2 on Hostinger, Direct on VF Server
│   │   │
│   │   ├── qfieldcloud/            # QFieldCloud (NEW - to be created)
│   │   │   │
│   │   │   ├── source/             # Application source code
│   │   │   │   ├── docker-compose.yml
│   │   │   │   ├── .env
│   │   │   │   ├── conf/
│   │   │   │   │   ├── nginx/
│   │   │   │   │   │   ├── config.d/
│   │   │   │   │   │   ├── certs/      # SSL certificates
│   │   │   │   │   │   └── dhparams/
│   │   │   │   │   └── certbot/
│   │   │   │   ├── docker-app/
│   │   │   │   │   └── qfieldcloud/   # Django application
│   │   │   │   ├── manage.py
│   │   │   │   └── README.md
│   │   │   │
│   │   │   ├── backups/            # Database backups
│   │   │   │   ├── qfield_db_backup_20251222.sql
│   │   │   │   ├── daily/
│   │   │   │   ├── weekly/
│   │   │   │   └── archive/
│   │   │   │
│   │   │   ├── logs/               # Application logs
│   │   │   │   ├── nginx/
│   │   │   │   ├── django/
│   │   │   │   ├── workers/
│   │   │   │   └── minio/
│   │   │   │
│   │   │   ├── scripts/            # Maintenance scripts
│   │   │   │   ├── check_health.sh
│   │   │   │   ├── weekly_backup.sh
│   │   │   │   └── restart_workers.sh
│   │   │   │
│   │   │   └── data/               # Temporary data (optional)
│   │   │       └── uploads/
│   │   │
│   │   │   • URL: https://qfield.fibreflow.app
│   │   │   • Port: 8000 (internal), 5433 (PostgreSQL)
│   │   │   • Service: Docker Compose (13 containers)
│   │   │   • Storage: ~570MB source + Docker volumes
│   │   │
│   │   └── server-dashboard/       # Server monitoring (symlink)
│   │       • URL: Internal only
│   │       • Managed by: Hein
│   │
│   └── hein/                        # Hein's projects
│       └── projects/
│           └── BOSS/
│               └── apps/
│                   └── server-dashboard/  # Real location
│
├── ml/                              # ML models storage (492GB, 16% used)
│   └── vllm/
│       ├── models/                  # VLM models
│       └── images/                  # Foto review images
│
├── scripts/                         # System scripts
│   └── cron/                        # Cron jobs
│
└── backups/                         # System-wide backups
    └── ...
```

---

## Docker Volumes (QFieldCloud)

**Location**: `/var/lib/docker/volumes/`

```
/var/lib/docker/volumes/
├── qfieldcloud_db_data/
│   └── _data/                       # PostgreSQL 13 + PostGIS database
│       ├── base/
│       ├── global/
│       ├── pg_wal/
│       └── ...
│       • Estimated size: 5-10GB
│       • Growth rate: ~1GB/year
│
├── qfieldcloud_minio_data1/
│   └── _data/                       # S3-compatible file storage (bucket 1)
│       └── qfieldcloud/
│           ├── projects/
│           ├── files/
│           └── ...
│       • Estimated size: 10-50GB
│       • Growth rate: Depends on usage
│
├── qfieldcloud_minio_data2/         # Additional MinIO shards
├── qfieldcloud_minio_data3/
│
├── qfieldcloud_media_volume/
│   └── _data/                       # Django media files
│       ├── avatars/
│       ├── project_thumbnails/
│       └── ...
│       • Estimated size: 1-5GB
│
├── qfieldcloud_static_volume/
│   └── _data/                       # Static assets (CSS, JS, images)
│       • Estimated size: ~100MB
│
└── qfieldcloud_certbot_www/
    └── _data/                       # SSL certificate challenges
        • Estimated size: <10MB
```

**Total Docker Storage Estimate**: 20-70GB (depends on project data)

---

## Port Allocation

| Service | Port | Protocol | Access | Purpose |
|---------|------|----------|--------|---------|
| **FibreFlow** | 3005 | HTTP | Cloudflare Tunnel | Main app API |
| **QFieldCloud Django** | 8000 | HTTP | Internal only | API backend |
| **QFieldCloud PostgreSQL** | 5433 | TCP | VF Server only | Database (external access for backups) |
| **MinIO API** | 8009 | HTTP | VF Server only | S3-compatible storage |
| **MinIO Console** | 8010 | HTTP | VF Server only | Admin UI |
| **QField WebDAV** | 32799 | HTTP | VF Server only | File sync protocol |
| **SMTP Test** | 32796-32798 | TCP | VF Server only | Email testing |

**Public Access**:
- All public traffic goes through **Cloudflare Tunnel** (`vf-downloads`)
- No ports exposed directly to internet (more secure)
- Internal services accessible via Tailscale (100.96.203.105)

---

## Network Architecture

```
Internet
    ↓
Cloudflare DNS (fibreflow.app)
    ↓
Cloudflare Tunnel (vf-downloads)
    ↓
VF Server (100.96.203.105)
    ↓
    ├── https://app.fibreflow.app        → localhost:3005 (FibreFlow)
    ├── https://qfield.fibreflow.app     → localhost:8000 (QFieldCloud)
    ├── https://vf.fibreflow.app/downloads → localhost:3005 (Downloads)
    └── https://support.fibreflow.app    → localhost:3005 (Support portal)

Tailscale Private Network
    ↓
VF Server (velo-server)
    ↓
    ├── ssh://louis@100.96.203.105       → SSH access
    ├── http://100.96.203.105:3005       → Direct FibreFlow access
    ├── http://100.96.203.105:8000       → Direct QFieldCloud access
    ├── http://100.96.203.105:5433       → PostgreSQL (QField)
    └── http://100.96.203.105:8009       → MinIO (QField)
```

---

## Storage Allocation Strategy

### Current Usage (Before QFieldCloud)

| Partition | Size | Used | Free | Use% | Purpose |
|-----------|------|------|------|------|---------|
| `/srv/ml` | 492GB | 72GB | 395GB | 16% | ML models + images |
| `/srv/data` | 984GB | 34GB | 900GB | 4% | Applications + data |

**Total NVMe**: 1.4TB (106GB used, 1.3TB free)

### Projected Usage (After QFieldCloud Migration)

| Application | Current | After Migration | Growth/Year |
|------------|---------|----------------|-------------|
| FibreFlow | 34GB | 34GB | +5GB |
| QFieldCloud | 0GB | 30-70GB | +10-20GB |
| Server Dashboard | <1GB | <1GB | +0.5GB |
| **Total** | 34GB | 64-104GB | +15-25GB |

**Disk Space Safety**:
- Current free: 900GB
- After migration: 830-870GB free
- 5-year projection: 750GB free (still 76% free)
- ✅ Very safe - room for massive growth

---

## Why `/srv/data/apps/qfieldcloud/`?

### Rationale

**1. Consistency with FibreFlow**
```
/srv/data/apps/
├── fibreflow/        # Already here
└── qfieldcloud/      # Same pattern - easy to remember
```

**2. NVMe Performance**
- `/srv/data` is on NVMe SSD (fast random I/O)
- Critical for PostgreSQL + MinIO file operations
- Better performance than HDD or network storage

**3. Proper Permissions**
```bash
$ ls -la /srv/data/apps/
drwxrwsr-x  3 root velocity-team  4096 Dec 22 06:26 .
```
- Group: `velocity-team` (shared access)
- Permissions: 2775 (SGID bit set - new files inherit group)
- Easy collaboration between louis, hein, and other admins

**4. Backup-Friendly**
```bash
# Single backup command for all apps
rsync -avz /srv/data/apps/ backup_server:/backups/vf_server_apps/

# Or selective backup
rsync -avz /srv/data/apps/qfieldcloud/ backup_server:/backups/qfield/
```

**5. Integration-Ready**
```python
# Future: FibreFlow can directly access QFieldCloud data
# Example: Photo sync from FibreFlow to QField projects
QFIELD_PATH = "/srv/data/apps/qfieldcloud/source"
FIBREFLOW_PATH = "/srv/data/apps/fibreflow"

# Both on same filesystem - fast file operations (no network)
import shutil
shutil.copy(
    f"{FIBREFLOW_PATH}/public/photos/project1/photo.jpg",
    f"{QFIELD_PATH}/media/projects/project1/"
)
```

**6. Docker Best Practices**
- Application code: `/srv/data/apps/qfieldcloud/source/`
- Persistent data: Docker volumes (`/var/lib/docker/volumes/`)
- Logs: `/srv/data/apps/qfieldcloud/logs/` (easy access without docker exec)
- Separation of concerns - clean architecture

---

## Comparison with Alternative Locations

| Location | Pros | Cons | Verdict |
|----------|------|------|---------|
| `/srv/data/apps/qfieldcloud/` | ✅ Consistent<br>✅ NVMe<br>✅ Group permissions<br>✅ 900GB free | None | ✅ **Recommended** |
| `/opt/qfieldcloud/` | ✅ FHS standard | ❌ Small root partition<br>❌ No group access<br>❌ Not NVMe | ❌ No |
| `/home/louis/qfieldcloud/` | ✅ Easy access | ❌ Personal ownership<br>❌ Not for services<br>❌ Not NVMe | ❌ No |
| `/var/lib/qfieldcloud/` | ✅ FHS for services | ❌ Small root partition<br>❌ Mixes with system | ❌ No |
| `/srv/ml/qfieldcloud/` | ✅ NVMe | ❌ Wrong purpose (ML storage)<br>❌ Less free space | ❌ No |

**FHS = Filesystem Hierarchy Standard** (Linux directory structure standard)

---

## File Ownership & Permissions

### Recommended Setup

```bash
# Application directory
/srv/data/apps/qfieldcloud/
Owner: louis
Group: velocity-team
Permissions: 2775 (drwxrwsr-x)

# Subdirectories
/srv/data/apps/qfieldcloud/source/       # 755 (code)
/srv/data/apps/qfieldcloud/backups/      # 770 (sensitive - DBs)
/srv/data/apps/qfieldcloud/logs/         # 775 (readable by group)
/srv/data/apps/qfieldcloud/scripts/      # 755 (executable)

# Docker volumes (managed by Docker daemon)
/var/lib/docker/volumes/qfieldcloud_*/
Owner: root
Group: root
Permissions: 755 (or container-specific)
```

### Setup Commands

```bash
# Create directories with correct ownership
sudo mkdir -p /srv/data/apps/qfieldcloud/{source,backups,logs,scripts}
sudo chown -R louis:velocity-team /srv/data/apps/qfieldcloud
sudo chmod 2775 /srv/data/apps/qfieldcloud
sudo chmod 755 /srv/data/apps/qfieldcloud/source
sudo chmod 770 /srv/data/apps/qfieldcloud/backups
sudo chmod 775 /srv/data/apps/qfieldcloud/logs
sudo chmod 755 /srv/data/apps/qfieldcloud/scripts

# Verify
ls -la /srv/data/apps/ | grep qfield
```

---

## Systemd Service (Optional)

**If you want QFieldCloud to auto-start on boot**:

```bash
# Create systemd service
sudo nano /etc/systemd/system/qfieldcloud.service
```

**Service file**:
```ini
[Unit]
Description=QFieldCloud Docker Compose Stack
Requires=docker.service
After=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=/srv/data/apps/qfieldcloud/source
ExecStart=/usr/bin/docker-compose up -d
ExecStop=/usr/bin/docker-compose down
User=louis
Group=velocity-team

[Install]
WantedBy=multi-user.target
```

**Enable and start**:
```bash
sudo systemctl daemon-reload
sudo systemctl enable qfieldcloud.service
sudo systemctl start qfieldcloud.service

# Check status
sudo systemctl status qfieldcloud.service
```

---

## Monitoring Integration

### Add to Existing VF Server Monitoring

**If you have a monitoring system**, add QFieldCloud health checks:

```bash
# Example: Add to monitoring script
cat >> /srv/scripts/vf_server_health_check.sh << 'EOF'

# QFieldCloud Health
echo "=== QFieldCloud Status ==="
docker-compose -f /srv/data/apps/qfieldcloud/source/docker-compose.yml ps

echo "QFieldCloud Database:"
docker exec qfieldcloud-db-1 psql -U qfieldcloud -c \
  "SELECT pg_database_size('qfieldcloud') AS size;" 2>/dev/null || echo "DB not responding"

echo "QFieldCloud URL:"
curl -s -o /dev/null -w "HTTP %{http_code}\n" https://qfield.fibreflow.app
EOF
```

---

## Summary

**QFieldCloud Installation Location**: `/srv/data/apps/qfieldcloud/`

**Key Benefits**:
1. ✅ Consistent with FibreFlow (`/srv/data/apps/fibreflow/`)
2. ✅ Fast NVMe storage (984GB, 900GB free)
3. ✅ Proper group permissions (velocity-team)
4. ✅ Easy backups (rsync /srv/data/apps/)
5. ✅ Integration-ready (same server, same filesystem)
6. ✅ Room for massive growth (850GB free after migration)

**Access Methods**:
- **Public**: https://qfield.fibreflow.app (via Cloudflare Tunnel)
- **Internal**: http://100.96.203.105:8000 (via Tailscale)
- **SSH**: `ssh louis@100.96.203.105` then `cd /srv/data/apps/qfieldcloud/source`

**Total Storage Impact**:
- Current: 34GB used, 900GB free
- After migration: 64-104GB used, 830-870GB free
- Still 84-88% free space - very comfortable

---

**Document Version**: 1.0
**Last Updated**: 2025-12-22
**Related Documents**:
- Migration Plan: `/home/louisdup/Agents/claude/docs/deployment/QFIELDCLOUD_MIGRATION_PLAN.md`
- FibreFlow Docs: `/home/louisdup/Agents/claude/CLAUDE.md`
