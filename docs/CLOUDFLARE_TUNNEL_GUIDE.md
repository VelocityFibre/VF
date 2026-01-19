# Cloudflare Tunnel Quick Reference

## Overview

FibreFlow uses Cloudflare Tunnel to expose VF Server apps to the public internet without port forwarding or exposing the server directly.

**Benefit**: Secure public access through Cloudflare's Zero Trust architecture, no router configuration needed.

## Architecture

```
Field Agent → Internet → Cloudflare → Tunnel (outbound conn) → VF Server nginx → Next.js
```

**Key Concept**: VF server creates an outbound connection to Cloudflare (allowed by router), then Cloudflare routes inbound traffic through that tunnel.

---

## Current Setup

### Tunnel Details
- **Name**: vf-downloads
- **ID**: 0bf9e4fa-f650-498c-bd23-def05abe5aaf
- **Config File**: `~/.cloudflared/config.yml` (on VF server)
- **Credentials**: `~/.cloudflared/0bf9e4fa-f650-498c-bd23-def05abe5aaf.json`
- **Log File**: `/tmp/cloudflared.log`

### Active Routes
```yaml
ingress:
  - hostname: vf.fibreflow.app
    service: http://localhost:80      # Downloads page (via nginx)

  - hostname: support.fibreflow.app
    service: http://localhost:3005    # Support portal (direct to Next.js)

  - service: http_status:404          # Catch-all
```

### DNS Records (Cloudflare)
```
vf.fibreflow.app       → CNAME → 0bf9e4fa-f650-498c-bd23-def05abe5aaf.cfargotunnel.com (Proxied)
support.fibreflow.app  → CNAME → 0bf9e4fa-f650-498c-bd23-def05abe5aaf.cfargotunnel.com (Proxied)
app.fibreflow.app      → A → 72.60.17.245 (Hostinger VPS, Proxied, Full SSL/TLS)
```

---

## Common Tasks

### Check Tunnel Status
```bash
ssh louis@100.96.203.105
ps aux | grep cloudflared
tail -f /tmp/cloudflared.log
```

### Restart Tunnel
```bash
pkill cloudflared && sleep 2
nohup ~/cloudflared tunnel run vf-downloads > /tmp/cloudflared.log 2>&1 &
```

### Add New App to Tunnel

**1. Edit config:**
```bash
nano ~/.cloudflared/config.yml
```

Add new hostname:
```yaml
ingress:
  - hostname: newapp.fibreflow.app
    service: http://localhost:PORT
  # ... existing routes ...
  - service: http_status:404
```

**2. Route DNS:**
```bash
~/cloudflared tunnel route dns vf-downloads newapp.fibreflow.app
```

**3. Restart tunnel:**
```bash
pkill cloudflared && sleep 2
nohup ~/cloudflared tunnel run vf-downloads > /tmp/cloudflared.log 2>&1 &
```

**4. Test:**
```bash
curl -I https://newapp.fibreflow.app
```

### Remove App from Tunnel

**1. Edit config** - Remove the hostname block from `~/.cloudflared/config.yml`

**2. Delete DNS record** - Go to Cloudflare DNS → Delete the CNAME for that hostname

**3. Restart tunnel**

---

## Domain Management

### Domain Setup
- **Registrar**: Xneelo
- **DNS Provider**: Cloudflare
- **Nameservers**: anton.ns.cloudflare.com, haley.ns.cloudflare.com

### SSL/TLS Configuration
- **Mode**: Full (origin has Let's Encrypt certificates)
- **Why**: Hostinger VPS has SSL certificates, so Cloudflare should use HTTPS to connect to it
- **VF Server**: No SSL needed (tunnel handles it)

### DNS Migration Date
- Migrated from Xneelo to Cloudflare nameservers: 2025-12-19
- All DNS records now managed in Cloudflare dashboard

---

## Troubleshooting

### Tunnel Not Connecting
```bash
# Check if process is running
ps aux | grep cloudflared

# Check logs for errors
tail -50 /tmp/cloudflared.log | grep -i error

# Restart tunnel
pkill cloudflared && sleep 2
nohup ~/cloudflared tunnel run vf-downloads > /tmp/cloudflared.log 2>&1 &

# Verify registration
tail -f /tmp/cloudflared.log | grep "Registered tunnel connection"
```

### app.fibreflow.app Not Working
**Symptom**: 502 Bad Gateway or connection refused

**Cause**: Wrong SSL/TLS mode in Cloudflare

**Fix**:
1. Go to Cloudflare → SSL/TLS → Overview
2. Change mode to **"Full"** (not Flexible, not Full Strict)
3. Wait 1-2 minutes for propagation
4. Test: `curl -I https://app.fibreflow.app`

### DNS Not Resolving
```bash
# Check DNS resolution
dig +short vf.fibreflow.app

# Should show Cloudflare IPs (104.x.x.x or 172.x.x.x)
# If shows old IP or nothing, DNS hasn't propagated yet (wait 5-30 min)

# Force DNS refresh (optional)
sudo systemd-resolve --flush-caches
```

### New Hostname Not Working
**Checklist**:
- [ ] Added to `~/.cloudflared/config.yml`
- [ ] Ran `~/cloudflared tunnel route dns vf-downloads HOSTNAME`
- [ ] Restarted tunnel
- [ ] DNS propagated (check with `dig +short HOSTNAME`)
- [ ] Service running on specified port (`ss -tlnp | grep PORT`)

---

## Auto-Start on Reboot

### Create Systemd Service
```bash
cat > /tmp/cloudflared.service << 'EOF'
[Unit]
Description=Cloudflare Tunnel
After=network.target

[Service]
Type=simple
User=louis
ExecStart=/home/louis/cloudflared tunnel run vf-downloads
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

sudo cp /tmp/cloudflared.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable cloudflared
sudo systemctl start cloudflared
```

### Check Status
```bash
sudo systemctl status cloudflared
journalctl -u cloudflared -f
```

---

## Security Notes

- **Tunnel Credentials**: Stored in `~/.cloudflared/*.json` - never commit to git!
- **Cloudflare Account**: louisrdup@gmail.com
- **Zero Trust**: Traffic flows through Cloudflare's secure network
- **No Port Forwarding**: Router firewall remains intact
- **DDoS Protection**: Included with Cloudflare proxy

---

## Quick Reference Commands

```bash
# Status
ps aux | grep "[c]loudflared tunnel run"

# Logs
tail -f /tmp/cloudflared.log

# Restart
pkill cloudflared && nohup ~/cloudflared tunnel run vf-downloads > /tmp/cloudflared.log 2>&1 &

# Test URLs
curl -I https://vf.fibreflow.app/downloads
curl -I https://support.fibreflow.app
curl -I https://app.fibreflow.app

# DNS check
dig +short vf.fibreflow.app
dig +short app.fibreflow.app

# Config location
cat ~/.cloudflared/config.yml
```

---

## For Future Claude Sessions

**To add a new app to the tunnel:**
> "Add `xyz.fibreflow.app` to the VF Server Cloudflare Tunnel (vf-downloads). Route it to port XXXX."

**To troubleshoot app.fibreflow.app:**
> "Check that app.fibreflow.app is working. It's hosted on Hostinger VPS (72.60.17.245) with PM2 process `fibreflow-prod`. Cloudflare SSL/TLS mode should be 'Full'."

**To troubleshoot VF server tunnel apps:**
> "Check that vf.fibreflow.app/downloads is working. It's hosted on VF Server (100.96.203.105) via Cloudflare Tunnel named 'vf-downloads'."

---

## Related Documentation

- **Setup**: docs/OPERATIONS_LOG.md (2025-12-18 entry)
- **Architecture**: CLAUDE.md (DNS & Cloudflare Setup section)
- **Changelog**: CHANGELOG.md (Infrastructure section)
- **Cloudflare Docs**: https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/
