# Setting Up monitor.fibreflow.app

## Option 1: Add to Existing VF Server Tunnel (Recommended)

Since you already have Cloudflare tunnels running, add the monitor to your existing setup:

### On VF Server (100.96.203.105):

1. SSH to VF server:
```bash
ssh louis@100.96.203.105
```

2. Edit Cloudflare config:
```bash
nano ~/.cloudflared/config.yml
```

3. Add this ingress rule:
```yaml
ingress:
  - hostname: monitor.fibreflow.app
    service: http://localhost:8888
  # ... your existing rules ...
```

4. Restart tunnel:
```bash
pkill cloudflared
nohup ~/cloudflared tunnel run vf-downloads > /tmp/cloudflared.log 2>&1 &
```

5. Add DNS record:
```bash
~/cloudflared tunnel route dns vf-downloads monitor.fibreflow.app
```

### Then on this machine, forward to VF server:

```bash
# SSH tunnel to forward port 8888 to VF server
ssh -L 8888:localhost:8888 louis@100.96.203.105 -N &
```

## Option 2: Deploy Directly to Hostinger VPS (Alternative)

Since app.fibreflow.app is already on your Hostinger VPS:

1. Copy dashboard to VPS:
```bash
scp -r /home/louisdup/Agents/claude/.claude/skills/qfieldcloud/dashboard root@72.60.17.245:/opt/qfield-monitor
```

2. SSH to VPS:
```bash
ssh root@72.60.17.245
```

3. Install and start:
```bash
cd /opt/qfield-monitor
python3 monitor_server.py &
```

4. Add Nginx config:
```nginx
server {
    server_name monitor.fibreflow.app;
    location / {
        proxy_pass http://localhost:8888;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }
}
```

5. Get SSL certificate:
```bash
certbot --nginx -d monitor.fibreflow.app
```

## Option 3: Quick Cloudflare Tunnel (New Tunnel)

For immediate access without touching existing infrastructure:

```bash
# Install cloudflared locally if not present
curl -L --output cloudflared.deb https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64.deb
sudo dpkg -i cloudflared.deb

# Login to Cloudflare
cloudflared tunnel login

# Create tunnel
cloudflared tunnel create qfield-monitor

# Create config file
cat > ~/.cloudflared/monitor-config.yml << EOF
url: http://localhost:8888
tunnel: qfield-monitor
credentials-file: /home/louisdup/.cloudflared/<tunnel-id>.json
EOF

# Route DNS
cloudflared tunnel route dns qfield-monitor monitor.fibreflow.app

# Run tunnel
cloudflared tunnel --config ~/.cloudflared/monitor-config.yml run
```

## Result

After any of these options, your dashboard will be available at:

**https://monitor.fibreflow.app**

- SSL/TLS automatically handled by Cloudflare
- Professional subdomain matching your existing setup
- Accessible worldwide
- No port forwarding needed
- DDoS protection included