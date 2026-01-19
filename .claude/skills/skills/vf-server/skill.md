---
name: vf-server
description: Direct VF Velocity server operations via Tailscale
version: 1.0.0
requires: ssh, sshpass, curl
async: true
context_fork: true
hooks:
  pre_tool_use: "echo '[VF-Server] Operation start: $(date) - User: $USER' >> /tmp/vf_server_ops.log"
  post_tool_use: "echo '[VF-Server] Operation end: $(date)' >> /tmp/vf_server_ops.log"
---

# VF Server Operations Skill

Provides direct access to Velocity Fibre server operations without exploration.

## Available Scripts

- `status.py` - Check server health and services
- `connect.py` - Get connection command (doesn't expose password)
- `service_check.py` - Check status of all web services
- `logs.py` - View recent logs from services
- `execute.py` - Execute commands on server
- `docker_status.py` - Check Docker containers status
- `disk_usage.py` - Check disk space
- `restart_service.py` - Restart specific services

## Services Available

- **Portainer**: Container management (port 9443)
- **Grafana**: Metrics visualization (port 3000)
- **Ollama**: Local LLM service (port 11434)
- **Qdrant**: Vector database (port 6333)
- **FibreFlow API**: Production API (port 80)
- **WhatsApp Sender**: WhatsApp messaging service (port 8081) - **REQUIRES PHONE +27 71 155 8396 PAIRED**

## WhatsApp Sender Service

**CRITICAL**: The wa-monitor module at https://app.fibreflow.app/wa-monitor depends on the WhatsApp Sender service.

### Phone Pairing Required
- **Phone Number**: +27 71 155 8396
- **Status**: Must be paired via WhatsApp "Linked Devices"
- **Session Storage**: `~/whatsapp-sender/store/whatsapp.db` on VF server
- **Service Location**: `~/whatsapp-sender/whatsapp-sender` (Go binary)
- **Logs**: `~/whatsapp-sender/whatsapp-sender.log`

### Quick Commands

```bash
# Check if service is running
VF_SERVER_PASSWORD="VeloAdmin2025!" .claude/skills/vf-server/scripts/execute.py 'ps aux | grep whatsapp-sender | grep -v grep'

# View service logs
VF_SERVER_PASSWORD="VeloAdmin2025!" .claude/skills/vf-server/scripts/execute.py 'tail -30 ~/whatsapp-sender/whatsapp-sender.log'

# Check health
VF_SERVER_PASSWORD="VeloAdmin2025!" .claude/skills/vf-server/scripts/execute.py 'curl -s http://localhost:8081/health'

# Restart service
VF_SERVER_PASSWORD="VeloAdmin2025!" .claude/skills/vf-server/scripts/execute.py 'pkill -f whatsapp-sender && cd ~/whatsapp-sender && nohup ./whatsapp-sender > whatsapp-sender.log 2>&1 &'
```

### When Phone Pairing is Lost

If logs show "Device not logged in - generating pairing code":

1. View the pairing code in logs
2. On phone +27 71 155 8396:
   - Open WhatsApp → Settings → Linked Devices
   - Tap "Link a Device" → "Link with Phone Number Instead"
   - Enter the pairing code
3. Service will automatically reconnect

**See**: `WA_MONITOR_SETUP.md` for complete setup and troubleshooting guide

## Connection Methods

1. **Tailscale** (Preferred): 100.96.203.105 or velo-server
2. **WireGuard**: Via 10.10.0.1
3. **Local Network**: 192.168.1.150

## Installation Paths on VF Server

**Production Data** (NVMe storage):
```
/srv/data/
├── boss/                    # BOSS production data
├── apps/
│   ├── fibreflow/          # FibreFlow deployment (when ready)
│   │   ├── data/           # App database, uploads
│   │   └── .env            # Production config
│   └── qfield/             # QField deployment
└── backups/                # Production backups
```

**Automated Scripts** (Cron jobs):
```
/srv/scripts/cron/
├── README.md               # Complete documentation
├── backups/                # Database & data backups
├── maintenance/            # System cleanup, updates
├── monitoring/             # Health checks, alerts
└── boss/                   # BOSS-specific tasks
```

## Security

All credentials stored in environment variables:
- VF_SERVER_HOST
- VF_SERVER_USER
- VF_SERVER_PASSWORD (encrypted in .env)