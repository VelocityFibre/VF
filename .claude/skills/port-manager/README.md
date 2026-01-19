# Port Manager Skill

Comprehensive port management system for VF Server (100.96.203.105).

## ✨ Features

- **Central Registry**: JSON-based port allocation tracking
- **Conflict Detection**: Automatic scanning for port conflicts
- **Dokploy Integration**: Syncs with Dokploy deployments
- **Smart Allocation**: Suggests available ports by service type
- **Real-time Scanning**: Checks actual port status vs registry
- **Process Identification**: Shows what's running on each port

## 🚀 Quick Start

The `portman` command is now installed globally:

```bash
# List all ports
portman list

# Check specific port
portman check 3000

# Scan for conflicts
portman scan

# Allocate new port
portman allocate myservice -t api

# Sync with Dokploy
portman sync --dry-run
```

## 📁 File Structure

```
.claude/skills/port-manager/
├── SKILL.md                 # Main skill documentation
├── README.md                 # This file
├── setup.sh                  # Installation script
├── config/
│   └── port_registry.json   # Port allocation database
└── scripts/
    ├── list_ports.py        # List all allocations
    ├── check_port.py        # Check specific port
    ├── scan_ports.py        # Scan and detect conflicts
    ├── allocate_port.py     # Allocate/release ports
    └── sync_dokploy.py      # Dokploy integration
```

## 🔍 Port Ranges

- **3000-3099**: Web Applications
- **5000-5999**: Database Services
- **8000-8099**: API Services
- **8100-8199**: ML/AI Services
- **9000-9099**: Monitoring & Internal
- **10000+**: Dynamic/Temporary

## 📊 Current Allocations

### Production Services
- **3000**: FibreFlow Production (app.fibreflow.app)
- **8082**: QFieldCloud (qfield.fibreflow.app)
- **8081**: WhatsApp Sender (needs re-pairing)
- **8091**: Storage API (Firebase replacement)
- **8095**: OCR Service (4-tier cascade)
- **8100**: VLM Service (Qwen3-VL-8B)

### Development/Staging
- **3005**: Hein's Development
- **3006**: Louis's Staging (vf.fibreflow.app)

## 🛠️ Common Tasks

### Check for Unregistered Ports
```bash
portman scan
```

### Allocate Port for New Service
```bash
# Allocate API port
portman allocate "my-api" -t api -o louis

# Allocate specific port
portman allocate "my-service" -p 8085
```

### Update Port Status
```bash
python3 .claude/skills/port-manager/scripts/allocate_port.py update 8081 needs_pairing -n "Session destroyed"
```

### Export as CSV
```bash
portman list -c > ports.csv
```

## 🔄 Dokploy Integration

Automatically discovers and syncs Dokploy-managed services:

```bash
# Preview changes
portman sync --dry-run

# Apply sync
portman sync

# Generate Nginx config
portman sync --nginx > dokploy-nginx.conf
```

## 🚨 Troubleshooting

### Port Shows as Unregistered
```bash
# Register existing port
portman allocate "service-name" -p PORT
```

### Port Conflict
```bash
# Check what's using the port
portman check PORT

# Scan all conflicts
portman scan -d
```

### Service Down but Port Registered
```bash
# Update status
python3 .claude/skills/port-manager/scripts/allocate_port.py update PORT inactive
```

## 📝 Registry Format

The registry is stored in `config/port_registry.json`:

```json
{
  "allocations": {
    "3000": {
      "service": "FibreFlow Production",
      "environment": "production",
      "status": "active",
      "owner": "velo",
      "url": "https://app.fibreflow.app"
    }
  }
}
```

## 🔐 Security Notes

- Registry is local-only (not synced to git)
- Port scanning requires appropriate permissions
- Some commands may need sudo for full process info
- Always verify before releasing production ports

## 📖 Additional Documentation

See `.claude/skills/port-manager/SKILL.md` for complete API documentation.