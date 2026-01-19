# VPS/Server Monitoring Dashboard - Proposal

## Overview

A comprehensive real-time monitoring dashboard for VPS infrastructure, security, resources, and services - similar to the QFieldCloud monitor but focused on general server health.

**Inspired by:** QFieldCloud Monitor Dashboard (proven success)
**Target Servers:**
- Hostinger VPS (72.60.17.245) - Production FibreFlow
- VF Server (100.96.203.105) - Internal operations
- Future: Additional client servers

## Proposed Architecture

```
┌──────────────────────────────────────────────────────────┐
│  User Browser → https://monitor.fibreflow.app            │
└────────────────────────┬─────────────────────────────────┘
                         ↓
         ┌───────────────────────────────┐
         │  Monitor Server (Python)      │
         │  Port: 8889                   │
         │  - Dark theme dashboard       │
         │  - REST API                   │
         │  - Multi-server support       │
         └───────────┬───────────────────┘
                     ↓
    ┌────────────────┴────────────────────────┐
    ↓                                         ↓
┌────────────────────┐            ┌────────────────────┐
│  Hostinger VPS     │            │  VF Server         │
│  72.60.17.245      │            │  100.96.203.105    │
│  (via SSH)         │            │  (via Tailscale)   │
└────────────────────┘            └────────────────────┘
         ↓                                   ↓
    ┌─────────────────────────────────────────────────┐
    │  Metrics Collection                             │
    │  - System resources (CPU, RAM, Disk, Network)   │
    │  - Security (SSH attempts, firewall, updates)   │
    │  - Services (PM2, Nginx, PostgreSQL, Docker)    │
    │  - Ports (open ports, listening services)       │
    │  - Logs (error rates, critical events)          │
    └─────────────────────────────────────────────────┘
```

## Dashboard Panels

### 1. System Resources Panel

**Metrics:**
- **CPU Usage** (%, per core breakdown)
- **Memory** (used/total, swap usage)
- **Disk Space** (/, /srv, /var partitions)
- **Network I/O** (bytes in/out, active connections)
- **System Load** (1m, 5m, 15m averages)
- **Uptime** (days running, last boot)

**Visual Indicators:**
- 🟢 Green: <70% usage
- 🟡 Yellow: 70-85% usage
- 🔴 Red: >85% usage

**Example:**
```
┌─────────────────────────────────────────┐
│  System Resources                       │
├─────────────────────────────────────────┤
│  CPU       [████████░░] 82%   🟡        │
│  Memory    [██████░░░░] 65%   🟢        │
│  Disk /    [███░░░░░░░] 34%   🟢        │
│  Disk /srv [████████░░] 78%   🟡        │
│  Network   ↓ 2.3MB/s  ↑ 450KB/s        │
│  Uptime    12d 4h 23m                   │
└─────────────────────────────────────────┘
```

### 2. Services Status Panel

**Services to Monitor:**
- **PM2 Processes** (fibreflow-prod, etc.)
- **Nginx** (web server, reverse proxy)
- **PostgreSQL** (Neon, local DBs)
- **Docker** (containers, images)
- **Cloudflare Tunnel** (vf-downloads)
- **Redis/Memcached** (if applicable)
- **Cron Jobs** (backup scripts, etc.)

**Status:**
- Running/Active → Green
- Stopped/Failed → Red (restart button appears)
- Warning → Yellow

**Example:**
```
┌─────────────────────────────────────────┐
│  Services                               │
├─────────────────────────────────────────┤
│  PM2 (fibreflow-prod)    RUNNING  🟢    │
│  Nginx                   ACTIVE   🟢    │
│  PostgreSQL              ACTIVE   🟢    │
│  Docker Daemon           RUNNING  🟢    │
│  Cloudflare Tunnel       STOPPED  🔴 [RESTART] │
│  Backup Cron             ACTIVE   🟢    │
└─────────────────────────────────────────┘
```

### 3. Security Panel

**Metrics:**
- **SSH Login Attempts** (failed/successful last 24h)
- **Firewall Status** (UFW/iptables active)
- **Open Ports** (listening services)
- **Failed Logins** (from /var/log/auth.log)
- **Security Updates** (pending patches)
- **SSL Certificates** (expiry dates)
- **Intrusion Detection** (fail2ban status)

**Example:**
```
┌─────────────────────────────────────────┐
│  Security                               │
├─────────────────────────────────────────┤
│  Firewall (UFW)          ACTIVE   🟢    │
│  Failed SSH (24h)        23 attempts 🟡 │
│  Fail2ban Jails          3 active  🟢    │
│  Security Updates        12 pending 🟡   │
│  SSL Cert Expiry         45 days   🟢    │
│  Open Ports              5 (review) 🟡   │
└─────────────────────────────────────────┘
```

### 4. Network & Ports Panel

**Metrics:**
- **Active Connections** (established, time_wait, etc.)
- **Listening Ports** (port, service, PID)
- **Bandwidth Usage** (daily/monthly)
- **DDoS Indicators** (connection rate, unique IPs)
- **DNS Resolution** (health check)

**Example:**
```
┌─────────────────────────────────────────┐
│  Network & Ports                        │
├─────────────────────────────────────────┤
│  Port 22   (sshd)        ✓ Listening    │
│  Port 80   (nginx)       ✓ Listening    │
│  Port 443  (nginx)       ✓ Listening    │
│  Port 3005 (node)        ✓ Listening    │
│  Port 5432 (postgres)    ✓ Listening    │
│                                         │
│  Active Connections      47             │
│  Bandwidth Today         2.3 GB         │
└─────────────────────────────────────────┘
```

### 5. Application Health Panel

**Application-Specific Metrics:**
- **FibreFlow API** (response time, error rate)
- **Database Queries** (slow queries, connections)
- **Cloudflare Tunnel** (status, throughput)
- **WhatsApp Sender** (queue, messages sent)
- **VLM Service** (QField foto evaluations)

**Example:**
```
┌─────────────────────────────────────────┐
│  Application Health                     │
├─────────────────────────────────────────┤
│  FibreFlow API                          │
│    Response Time       142ms      🟢    │
│    Error Rate          0.2%       🟢    │
│    Requests/min        34               │
│                                         │
│  Database Connections  12/100     🟢    │
│  Cloudflare Tunnel     ACTIVE     🟢    │
│  WhatsApp Service      RUNNING    🟢    │
└─────────────────────────────────────────┘
```

### 6. Logs & Alerts Panel

**Real-time Activity Feed:**
- Recent errors (last 10)
- Security events (failed logins, etc.)
- Service restarts
- System warnings
- Manual interventions

**Example:**
```
┌─────────────────────────────────────────┐
│  Recent Activity                        │
├─────────────────────────────────────────┤
│  [13:42] ⚠️  High CPU usage detected    │
│  [13:35] ✓  PM2 process restarted      │
│  [13:20] ⚠️  5 failed SSH attempts      │
│  [12:58] ℹ️  Security updates available │
│  [12:30] ✓  Daily backup completed     │
└─────────────────────────────────────────┘
```

### 7. Multi-Server Overview Panel

**When monitoring multiple servers:**

```
┌─────────────────────────────────────────┐
│  Server Overview                        │
├─────────────────────────────────────────┤
│  Hostinger VPS                          │
│    Status: 🟢 Healthy                   │
│    CPU: 45% | RAM: 62% | Disk: 34%     │
│    Services: 6/6 running                │
│                                         │
│  VF Server                              │
│    Status: 🟡 Warning (high disk)       │
│    CPU: 23% | RAM: 78% | Disk: 89%     │
│    Services: 8/9 running                │
│                                         │
│  [+ Add Server]                         │
└─────────────────────────────────────────┘
```

## Features

### Core Features (Like QFieldCloud Monitor)

✅ **Real-time Updates** - Auto-refresh every 30s
✅ **Dark Theme** - Clean white-on-black UI
✅ **Manual Restart Buttons** - Only visible when services fail
✅ **Activity Log** - Color-coded event stream
✅ **REST API** - `/api/server/status` endpoint
✅ **Safe Testing** - Test dashboard that doesn't affect real systems

### Advanced Features (Beyond QFieldCloud)

🆕 **Multi-Server Support** - Monitor multiple VPS from one dashboard
🆕 **Historical Graphs** - CPU/RAM/Disk trends (Chart.js)
🆕 **Alert Rules** - Custom thresholds with notifications
🆕 **Security Insights** - SSH attack patterns, geographic analysis
🆕 **Automated Remediation** - Auto-restart failed services
🆕 **Export Metrics** - CSV/JSON download for reports
🆕 **Mobile Responsive** - Works on phones/tablets
🆕 **User Authentication** - Login required (basic auth or OAuth)
🆕 **Scheduled Reports** - Daily/weekly email summaries

## Technology Stack

### Frontend
- **HTML5** - Semantic structure
- **CSS3** - Dark theme, responsive grid
- **JavaScript (Vanilla)** - No framework overhead
- **Chart.js** - Optional graphs for historical data
- **Font:** Courier New (monospace, terminal feel)

### Backend
- **Python 3.10+** - HTTP server & API
- **http.server** - Built-in, no dependencies
- **subprocess** - Execute system commands
- **paramiko** - SSH to remote servers (better than sshpass)
- **psutil** - System metrics collection
- **Optional:** FastAPI if REST API grows complex

### Data Collection
- **Commands:**
  - `top -bn1` - CPU/memory
  - `df -h` - Disk usage
  - `ss -tuln` - Listening ports
  - `systemctl status` - Service status
  - `journalctl` - System logs
  - `fail2ban-client status` - Security events
  - `pm2 list` - PM2 processes
  - `docker ps` - Container status
  - `nginx -t` - Nginx health
  - `certbot certificates` - SSL expiry

## Implementation Plan

### Phase 1: MVP (1-2 days)
- [ ] System resources panel (CPU, RAM, Disk)
- [ ] Services status panel (PM2, Nginx, PostgreSQL)
- [ ] Basic dark theme UI
- [ ] Single server support (Hostinger VPS)
- [ ] Manual refresh button

### Phase 2: Automation (1 day)
- [ ] Auto-refresh every 30s
- [ ] Activity log with color coding
- [ ] Manual restart buttons (only on failure)
- [ ] REST API `/api/server/status`
- [ ] Safe test dashboard

### Phase 3: Security (1 day)
- [ ] Security panel (SSH attempts, firewall)
- [ ] Network & ports panel
- [ ] Failed login monitoring
- [ ] Security update tracking
- [ ] SSL certificate expiry warnings

### Phase 4: Multi-Server (1 day)
- [ ] VF Server monitoring via Tailscale
- [ ] Server overview panel
- [ ] Switch between servers
- [ ] Combined alerts view

### Phase 5: Advanced (2-3 days)
- [ ] Historical graphs (Chart.js)
- [ ] Custom alert rules
- [ ] Email/WhatsApp notifications
- [ ] Export to CSV/JSON
- [ ] Mobile responsive design
- [ ] Authentication (basic auth)

**Total Estimated Time:** 6-8 days for full implementation

## File Structure

```
.claude/skills/vps-monitor/dashboard/
├── index.html                    # Main dashboard
├── test_dashboard.html           # Safe testing environment
├── server_monitor.py             # Python backend server
├── collectors/                   # Metric collection scripts
│   ├── system_resources.py       # CPU, RAM, Disk
│   ├── security_metrics.py       # SSH, firewall, logs
│   ├── network_ports.py          # Ports, connections
│   └── service_status.py         # PM2, Docker, Nginx
├── config.yaml                   # Server list, thresholds
├── test_functionality.py         # Automated tests
├── install_monitoring.sh         # Systemd service setup
└── README.md                     # Documentation
```

## Configuration Example

`config.yaml`:
```yaml
servers:
  - name: "Hostinger VPS"
    host: "72.60.17.245"
    user: "root"
    auth_method: "password"  # or "key"
    password: "VeloF@2025@@"  # or key_file: ~/.ssh/id_rsa
    services:
      - "fibreflow-prod"
      - "nginx"
      - "postgresql"

  - name: "VF Server"
    host: "100.96.203.105"
    user: "louis"
    auth_method: "key"
    key_file: "~/.ssh/id_rsa"
    services:
      - "fibreflow"
      - "cloudflared"
      - "whatsapp-sender"

thresholds:
  cpu: 85
  memory: 90
  disk: 85
  failed_ssh_24h: 50

alerts:
  enabled: true
  channels:
    - email: "louis@velocityfibre.co.za"
    - whatsapp: "+27711558396"

refresh_interval: 30  # seconds
```

## API Endpoints

```bash
# Get all server status
GET /api/servers

# Get specific server
GET /api/server/{server_name}/status

# Get system resources
GET /api/server/{server_name}/resources

# Get security metrics
GET /api/server/{server_name}/security

# Restart service
POST /api/server/{server_name}/restart
{
  "service": "nginx"
}

# Get historical data (optional, Phase 5)
GET /api/server/{server_name}/history?metric=cpu&hours=24
```

## Deployment Options

### Option 1: Run on Local Machine (Development)
```bash
cd .claude/skills/vps-monitor/dashboard
./server_monitor.py
# Visit: http://localhost:8889
```

### Option 2: Deploy to VF Server (Recommended)
```bash
# On VF Server
cd /opt/vps-monitor
./server_monitor.py

# Add to Cloudflare tunnel
# Visit: https://monitor.fibreflow.app
```

### Option 3: Docker Container (Isolated)
```dockerfile
FROM python:3.10-slim
WORKDIR /app
COPY . .
RUN pip install paramiko psutil pyyaml
EXPOSE 8889
CMD ["python3", "server_monitor.py"]
```

```bash
docker build -t vps-monitor .
docker run -d -p 8889:8889 vps-monitor
```

## Security Considerations

1. **Authentication Required**
   - Don't expose publicly without auth
   - Use Cloudflare Access or basic auth
   - API token for programmatic access

2. **SSH Credentials**
   - Use SSH keys, not passwords
   - Store credentials in separate config file
   - Never commit credentials to git
   - Encrypt config.yaml with ansible-vault

3. **HTTPS Only**
   - Use Cloudflare Tunnel for public access
   - Don't expose HTTP port publicly

4. **Rate Limiting**
   - Limit refresh frequency
   - Prevent DoS on monitored servers

## Comparison with Existing Solutions

| Feature | Our Dashboard | Netdata | Grafana + Prometheus | Glances |
|---------|--------------|---------|----------------------|---------|
| Setup Time | Minutes | 10 mins | Hours | Minutes |
| Dependencies | None | Agent | Multiple | Python |
| Multi-Server | ✓ | Requires Cloud | ✓ | Limited |
| Dark Theme | ✓ | ✓ | ✓ | ✓ |
| Restart Services | ✓ | ✗ | ✗ | ✗ |
| Custom for FibreFlow | ✓ | ✗ | Manual | ✗ |
| Learning Curve | Low | Medium | High | Low |
| Cost | Free | Free/Paid | Free | Free |

**Why Build Custom:**
- ✅ Tailored to FibreFlow infrastructure
- ✅ Simple, no complex setup
- ✅ Integrates with existing tools (PM2, Cloudflare)
- ✅ Manual service restart capability
- ✅ Proven pattern (QFieldCloud monitor success)

## Success Metrics

**Dashboard should achieve:**
- ⏱️ <500ms page load time
- 🔄 30s refresh interval
- 📊 <5% false positive alerts
- 🚀 <1 minute to identify issues
- 🔧 <30s to restart failed service
- 📱 Mobile usable (Phase 5)
- 👥 Accessible to non-technical team members

## Next Steps

1. **Review & Approve** this proposal
2. **Phase 1 Implementation** (2 days)
   - Build MVP with system resources & services
3. **Testing** (1 day)
   - Test on Hostinger VPS and VF Server
4. **Deploy** to VF Server with Cloudflare Tunnel
5. **Iterate** based on team feedback

## Questions to Answer

1. **Which servers to monitor initially?**
   - Hostinger VPS only?
   - Both Hostinger + VF Server?
   - Client servers in future?

2. **Alert preferences?**
   - Email, WhatsApp, or both?
   - What severity levels?
   - Quiet hours?

3. **Historical data?**
   - How many days to retain?
   - Storage location?
   - Database needed?

4. **Access control?**
   - Who should access dashboard?
   - Public or team-only?
   - Authentication method?

5. **Priority features?**
   - Phase 1 MVP sufficient?
   - Need graphs immediately?
   - Multi-server support required?

---

**Status:** 📋 Proposal - Awaiting Approval
**Created:** 2025-12-19
**Estimated Effort:** 6-8 days full implementation
**Inspired By:** QFieldCloud Monitor Dashboard success
