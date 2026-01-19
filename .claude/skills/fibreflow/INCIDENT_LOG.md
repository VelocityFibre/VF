# FibreFlow Incident Log

## Purpose
Track all FibreFlow app incidents, resolutions, and fixes. Quick reference for troubleshooting.

## Format
- **Newest entries first**
- **Severity**: 🔴 Critical | 🟡 Major | 🔵 Minor
- **Status**: ⚠️ Active | ✅ Resolved

---

## 2026-01-15

### 🟡 Staging Server 502 Error (vf.fibreflow.app)

**Time**: 10:00-10:31 SAST
**Status**: ✅ Resolved
**Impact**: Staging environment inaccessible
**Operator**: Claude Code
**Reporter**: User

#### Symptoms
- 502 Bad Gateway error on https://vf.fibreflow.app
- Cloudflare error page shown
- Systemd service in constant restart loop (1900+ restarts)

#### Root Causes
1. Systemd service pointing to wrong directory (`/srv/data/apps/fibreflow` doesn't exist)
2. Port conflict: Service trying to use 3005 (occupied by Hein's dev) instead of 3006
3. Cloudflare tunnel misconfigured to route to wrong port

#### Fix
```bash
# 1. Fixed systemd service
sudo nano /etc/systemd/system/fibreflow.service
# Updated: WorkingDirectory=/home/louis/apps/fibreflow
# Updated: Environment="PORT=3006"

# 2. Fixed Cloudflare tunnel
nano ~/.cloudflared/config.yml
# Updated: vf.fibreflow.app → http://localhost:3006

# 3. Restarted services
sudo systemctl daemon-reload
sudo systemctl restart fibreflow.service
sudo systemctl restart cloudflared-tunnel.service
```

#### Quick Recovery
```bash
# If this happens again:
ssh -i ~/.ssh/vf_server_key louis@100.96.203.105
sudo systemctl status fibreflow.service
sudo journalctl -u fibreflow.service -n 50
```

#### Prevention
- Always verify port allocation before config changes
- Document port assignments: 3005 (Hein dev), 3006 (Louis staging)

---

## 2026-01-13

### 🟡 ML Services Access Issues

**Time**: 08:00-09:30 SAST
**Status**: ✅ Resolved
**Impact**: Team unable to manage VLM for foto-reviews
**Operator**: Claude Code + Louis
**Reporter**: Hein

#### Symptoms
- VLLM service (port 8100) running but team couldn't restart
- Services owned by different users (louis/hein)
- SSH password authentication failing
- Foto-reviews potentially affected

#### Root Cause
- Services running under personal accounts instead of shared
- SSH password auth disabled, only key auth working
- Team members lacking SSH keys

#### Fix
1. Created team management scripts at `/opt/team-scripts/`
2. Distributed SSH keys to team members
3. Set up proper group permissions
4. Scripts: `manage-vllm.sh`, `manage-ocr.sh`

#### Quick Commands
```bash
ssh vf-server '/opt/team-scripts/manage-vllm.sh restart'
curl http://100.96.203.105:8100/v1/models  # Test VLM
```

---

## 2026-01-12

### 🟡 Example: Authentication Issues

**Time**: XX:XX SAST
**Status**: ⚠️ Active
**Impact**: Users unable to login
**Operator**: [Name]

#### Symptoms
- Login returns 401
- Tokens not refreshing

#### Fix
- Clear browser cache
- Restart auth service

---

*Add new incidents above this line*