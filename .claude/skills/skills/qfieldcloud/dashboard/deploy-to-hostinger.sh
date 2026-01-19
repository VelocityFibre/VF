#!/bin/bash
# Deploy QField Monitor Dashboard to Hostinger VPS

HOSTINGER_IP="72.60.17.245"
HOSTINGER_USER="root"
HOSTINGER_PASS="VeloF@2025@@"

echo "========================================"
echo "Deploying Monitor to Hostinger VPS"
echo "========================================"
echo ""
echo "This script will:"
echo "1. Copy dashboard files to Hostinger VPS"
echo "2. Install as systemd service"
echo "3. Configure Nginx reverse proxy"
echo "4. Set up for monitor.fibreflow.app"
echo ""

# Create deployment package
echo "Creating deployment package..."
cd /home/louisdup/Agents/claude/.claude/skills/qfieldcloud
tar -czf /tmp/qfield-monitor.tar.gz dashboard/

echo ""
echo "Run these commands:"
echo ""
echo "1. Copy files to Hostinger:"
echo "scp /tmp/qfield-monitor.tar.gz root@$HOSTINGER_IP:/opt/"
echo ""
echo "2. SSH to Hostinger:"
echo "ssh root@$HOSTINGER_IP"
echo ""
echo "3. On Hostinger, run:"
cat << 'EOF'
# Extract dashboard
cd /opt
tar -xzf qfield-monitor.tar.gz
cd dashboard

# Install Python dependencies if needed
pip3 install --upgrade pip

# Create systemd service
cat > /etc/systemd/system/qfield-monitor.service << 'SERVICE'
[Unit]
Description=QField Monitor Dashboard
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/dashboard
ExecStart=/usr/bin/python3 /opt/dashboard/monitor_server.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
SERVICE

# Enable and start service
systemctl daemon-reload
systemctl enable qfield-monitor
systemctl start qfield-monitor

# Add Nginx config for local access
cat > /etc/nginx/sites-available/qfield-monitor << 'NGINX'
server {
    listen 8888;
    server_name _;

    location / {
        proxy_pass http://127.0.0.1:8888;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }
}
NGINX

ln -s /etc/nginx/sites-available/qfield-monitor /etc/nginx/sites-enabled/
nginx -s reload

echo "Monitor dashboard deployed on Hostinger!"
echo "Local access: http://$HOSTINGER_IP:8888"
EOF

echo ""
echo "========================================"
echo "For Cloudflare Tunnel Access:"
echo "========================================"
echo ""
echo "Since you want monitor.fibreflow.app:"
echo ""
echo "Option A: Add to existing Hostinger Nginx (if app.fibreflow.app uses Nginx):"
echo "  - Edit /etc/nginx/sites-available/default"
echo "  - Add server block for monitor.fibreflow.app → localhost:8888"
echo ""
echo "Option B: Forward from VF Server tunnel:"
echo "  - On VF Server, edit ~/.cloudflared/config.yml"
echo "  - Add: hostname: monitor.fibreflow.app"
echo "  -      service: http://$HOSTINGER_IP:8888"
echo ""
echo "Option C: Run Cloudflare tunnel on Hostinger:"
echo "  - Install cloudflared on Hostinger"
echo "  - Create tunnel for monitor.fibreflow.app"
echo ""
echo "========================================"
echo "When Moving to VF Server (Future):"
echo "========================================"
echo ""
echo "1. Stop service on Hostinger:"
echo "   systemctl stop qfield-monitor"
echo ""
echo "2. Copy to VF Server and update config to:"
echo "   - Point to localhost QFieldCloud services"
echo "   - Update tunnel config"
echo "