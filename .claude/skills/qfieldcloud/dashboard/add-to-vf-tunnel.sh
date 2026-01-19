#!/bin/bash
# Add monitor.fibreflow.app to existing VF tunnel

echo "========================================"
echo "Add monitor.fibreflow.app to VF Tunnel"
echo "========================================"
echo ""
echo "Run these commands on VF Server (100.96.203.105):"
echo ""
echo "1. SSH to VF Server:"
echo "   ssh louis@100.96.203.105"
echo ""
echo "2. Edit tunnel config:"
echo "   nano ~/.cloudflared/config.yml"
echo ""
echo "3. Add this ingress rule BEFORE the last 'service: http_status:404' line:"
echo ""
cat << 'EOF'
  - hostname: monitor.fibreflow.app
    service: http://100.96.203.105:8888
    originRequest:
      noTLSVerify: true
EOF
echo ""
echo "4. Restart the tunnel:"
echo "   pkill cloudflared"
echo "   nohup ~/cloudflared tunnel run vf-downloads > /tmp/cloudflared.log 2>&1 &"
echo ""
echo "========================================"
echo "On this machine, forward port 8888 to VF:"
echo "========================================"
echo ""
echo "ssh -R 8888:localhost:8888 louis@100.96.203.105 -N &"
echo ""
echo "Your dashboard will then be available at:"
echo "https://monitor.fibreflow.app"