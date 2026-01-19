#!/bin/bash
# Setup permanent Cloudflare tunnel for monitor.fibreflow.app

echo "Setting up permanent tunnel for monitor.fibreflow.app..."

# Step 1: Login to Cloudflare (if not already)
echo "Step 1: Logging into Cloudflare..."
cloudflared tunnel login

# Step 2: Create named tunnel
echo "Step 2: Creating tunnel 'qfield-monitor'..."
cloudflared tunnel create qfield-monitor

# Step 3: Create config file
echo "Step 3: Creating configuration..."
TUNNEL_ID=$(cloudflared tunnel list | grep qfield-monitor | awk '{print $1}')

cat > ~/.cloudflared/config-monitor.yml << EOF
tunnel: $TUNNEL_ID
credentials-file: /home/louisdup/.cloudflared/${TUNNEL_ID}.json

ingress:
  - hostname: monitor.fibreflow.app
    service: http://localhost:8888
  - service: http_status:404
EOF

echo "Step 4: Adding DNS route..."
# Step 4: Route DNS
cloudflared tunnel route dns qfield-monitor monitor.fibreflow.app

echo "Step 5: Starting tunnel..."
# Step 5: Run tunnel
cloudflared tunnel --config ~/.cloudflared/config-monitor.yml run &

echo ""
echo "✅ Setup complete!"
echo ""
echo "Your dashboard will be available at:"
echo "👉 https://monitor.fibreflow.app"
echo ""
echo "The tunnel is now running in the background."
echo "To stop: pkill -f 'cloudflared tunnel'"
echo "To restart: cloudflared tunnel --config ~/.cloudflared/config-monitor.yml run"