# VF Server Operations Skill

Direct server management for Velocity Fibre server without exploration.

## Auto-Discovery

This skill is **automatically discovered** by Claude Code. Just ask naturally:
- "Check VF server status"
- "What's running on velo-server?"
- "Check disk space on the server"
- "Show Docker containers"
- "Execute command on VF server"

## Available Scripts

| Script | Purpose | Example Usage |
|--------|---------|---------------|
| `status.py` | Server health & services | "Is the VF server up?" |
| `connect.py` | Connection info | "How do I connect to VF server?" |
| `docker_status.py` | Container status | "What Docker containers are running?" |
| `disk_usage.py` | Disk & memory | "Check server disk space" |
| `execute.py` | Run commands | "Run uptime on VF server" |

## Security Configuration

### SSH Key Authentication (Recommended)

The skill now uses SSH key authentication by default. Ensure your SSH key is added to the server:

```bash
# Your key should be in: /home/louis/.ssh/authorized_keys on the server
ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAICT8ppU1021N7BA/WugL5E5Ez83Dp7BGW2+CXBi02qP1 louisdup@velocityfibre.com
```

### Environment Configuration

Add to your `.env`:
```bash
VF_SERVER_HOST=100.96.203.105
VF_SERVER_USER=louis
# VF_SERVER_PASSWORD is optional - leave unset to use SSH key authentication
# VF_SERVER_PASSWORD=<your-secure-password>  # Only if SSH keys not available
```

**Security Notes:**
- SSH key authentication is automatically used when `VF_SERVER_PASSWORD` is not set
- Password authentication is only used as a fallback
- Never commit passwords or private keys to the repository

## Services Available

| Service | URL | Port | Status (Dec 2025) |
|---------|-----|------|-------------------|
| **Grafana** | http://100.96.203.105:3000 | 3000 | ✅ Active |
| **Qdrant** | http://100.96.203.105:6333 | 6333 | ✅ Active |
| **Portainer** | http://100.96.203.105:9443 | 9443 | ❌ Down |
| **Ollama** | http://100.96.203.105:11434 | 11434 | ❌ Down |
| **FibreFlow API** | http://100.96.203.105/health | 80 | ❌ Down |

## Performance

- **Execution time**: ~100ms for status checks
- **Token usage**: ~1000 tokens per operation
- **vs Manual**: 10x faster than Claude exploring SSH commands

## Manual Usage

```bash
# Check server status
.claude/skills/vf-server/scripts/status.py

# Get connection info
.claude/skills/vf-server/scripts/connect.py

# Check Docker containers
.claude/skills/vf-server/scripts/docker_status.py

# Check disk usage
.claude/skills/vf-server/scripts/disk_usage.py

# Execute command
.claude/skills/vf-server/scripts/execute.py "ls -la /home/louis"
```

## How It Works

1. Claude detects natural language request about VF server
2. Automatically executes appropriate script
3. Returns JSON results instantly
4. No SSH command exploration needed

## Dependencies

```bash
# Only needed for password authentication (optional)
sudo apt-get install sshpass
```

**Note:** SSH key authentication requires no additional dependencies.

## Connection Methods

1. **Tailscale** (Preferred): 100.96.203.105 ✅ Verified
2. **Hostname**: velo-server ✅ Working
3. **Local Network**: 192.168.1.150 (requires LAN access)

All methods work with the skill scripts.

## Installation Paths on VF Server

### Production Data (NVMe Storage: /srv/data/)

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

### Automated Scripts (Cron Jobs: /srv/scripts/cron/)

```
/srv/scripts/cron/
├── README.md               # Complete documentation
├── backups/                # Database & data backups
│   └── example_postgres_backup.sh
├── maintenance/            # System cleanup, updates
├── monitoring/             # Health checks, alerts
└── boss/                   # BOSS-specific tasks
    └── example_knowledge_refresh.sh
```

**Note**: All production applications should be deployed under `/srv/data/apps/` on the fast NVMe storage.

## Verification Status

**Last Tested**: December 17, 2025

- ✅ SSH key authentication confirmed working
- ✅ All skill scripts tested and functional
- ✅ No password required with SSH key setup
- ⚠️ Docker commands require `louis` user in docker group

**Test Command:**
```bash
# Quick verification
.claude/skills/vf-server/scripts/execute.py "echo 'Connection verified' && uptime"
```