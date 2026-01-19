#!/bin/bash
echo "=== SYSTEM HEALTH CHECK ==="
echo ""

# VF Server
echo -n "VF Server (port 3005): "
if VF_SERVER_PASSWORD='VeloAdmin2025!' .claude/skills/vf-server/scripts/execute.py 'ps aux | grep "[n]ext-server" | grep 3005' &>/dev/null; then
    echo "✅ RUNNING"
else
    echo "❌ DOWN"
fi

# QField
echo -n "QField Worker: "
if docker ps --filter 'name=qfieldcloud-worker' --format '{{.Status}}' 2>/dev/null | grep -q "Up"; then
    echo "✅ RUNNING"
else
    echo "❌ DOWN"
fi

# Cloudflared
echo -n "Cloudflared Tunnel: "
if VF_SERVER_PASSWORD='VeloAdmin2025!' .claude/skills/vf-server/scripts/execute.py 'ps aux | grep "[c]loudflared"' &>/dev/null; then
    echo "✅ RUNNING"
else
    echo "❌ DOWN"
fi

# Disk
DISK=$(df -h / | tail -1 | awk '{print $5}')
echo "Disk Usage: $DISK"

echo ""
echo "=== END OF CHECK ==="
