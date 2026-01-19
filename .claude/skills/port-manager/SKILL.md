# Port Manager Skill

Comprehensive port management system for VF Server infrastructure.

## Capabilities

1. **Port Registry Management**
   - Central database of all port allocations
   - Service descriptions and ownership tracking
   - Protocol specification (TCP/UDP)
   - Environment tagging (production/staging/dev)

2. **Conflict Detection**
   - Real-time port scanning
   - Conflict prevention before allocation
   - Orphaned port identification
   - Cross-service dependency mapping

3. **Dokploy Integration**
   - Sync with Dokploy deployments
   - Automatic port registration from Docker containers
   - Environment variable management
   - Reverse proxy configuration tracking

4. **Monitoring & Alerts**
   - Port availability monitoring
   - Service health checks via ports
   - Automatic conflict resolution suggestions
   - Usage statistics and trends

## Usage

### Check Port Status
```bash
python3 .claude/skills/port-manager/scripts/check_port.py 3000
```

### List All Allocations
```bash
python3 .claude/skills/port-manager/scripts/list_ports.py
```

### Allocate New Port
```bash
python3 .claude/skills/port-manager/scripts/allocate_port.py --service "my-service" --env production
```

### Scan for Conflicts
```bash
python3 .claude/skills/port-manager/scripts/scan_conflicts.py
```

### Sync with Dokploy
```bash
python3 .claude/skills/port-manager/scripts/sync_dokploy.py
```

## Port Ranges

- **3000-3099**: Web Applications (Production/Staging/Dev)
- **8000-8099**: API Services
- **8100-8199**: ML/AI Services (VLM, OCR, etc)
- **5000-5999**: Database Services
- **9000-9099**: Monitoring & Internal Tools
- **10000+**: Dynamic/Temporary Services

## Integration Points

- **Dokploy**: Auto-discovery of containerized services
- **Nginx**: Reverse proxy configuration sync
- **Cloudflare Tunnel**: Public exposure tracking
- **Systemd**: Service unit file parsing
- **Docker**: Container port mapping

## Quick Reference

| Range | Purpose | Examples |
|-------|---------|----------|
| 3000-3099 | Web Apps | FibreFlow (3000), Staging (3006) |
| 8000-8099 | APIs | WhatsApp (8081), Storage (8091) |
| 8100-8199 | ML/AI | VLM (8100), OCR (8095) |
| 5000-5999 | Databases | PostgreSQL (5433) |
| 9000-9099 | Internal | MinIO (9000-9001) |

## Environment Variables

```bash
PORT_REGISTRY_PATH=/opt/port-registry/ports.json
PORT_SCAN_INTERVAL=300  # seconds
PORT_CONFLICT_ACTION=alert  # alert|block|auto-reassign
DOKPLOY_API_URL=http://localhost:3000/api
```