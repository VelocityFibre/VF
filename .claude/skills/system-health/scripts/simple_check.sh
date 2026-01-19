#!/bin/bash
# Simple health check - just works, no fancy parsing

echo "{
  \"timestamp\": \"$(date -Iseconds)\",
  \"checks\": ["

# VF Server check
echo "    {
      \"service\": \"VF Server\",
      \"status\": \""
if VF_SERVER_PASSWORD='VeloAdmin2025!' .claude/skills/vf-server/scripts/execute.py 'ps aux | grep "[n]ext-server" | grep 3005' &>/dev/null; then
    echo -n "healthy"
else
    echo -n "down"
fi
echo "\",
      \"details\": \"Next.js server on port 3005\"
    },"

# QField Worker check
echo "    {
      \"service\": \"QField Worker\",
      \"status\": \""
if docker ps --filter 'name=qfieldcloud-worker' --format '{{.Status}}' 2>/dev/null | grep -q "Up"; then
    echo -n "healthy"
else
    echo -n "down"
fi
echo "\",
      \"details\": \"QFieldCloud worker container\"
    },"

# Cloudflared check
echo "    {
      \"service\": \"Cloudflared Tunnel\",
      \"status\": \""
if VF_SERVER_PASSWORD='VeloAdmin2025!' .claude/skills/vf-server/scripts/execute.py 'ps aux | grep "[c]loudflared"' &>/dev/null; then
    echo -n "healthy"
else
    echo -n "down"
fi
echo "\",
      \"details\": \"Cloudflare tunnel for public access\"
    },"

# Disk space check
echo "    {
      \"service\": \"Disk Space\",
      \"status\": \""
DISK_USAGE=$(df -h / | tail -1 | awk '{print $5}' | tr -d '%')
if [ "$DISK_USAGE" -gt 85 ]; then
    echo -n "warning"
else
    echo -n "healthy"
fi
echo "\",
      \"details\": \"Local disk at ${DISK_USAGE}%\"
    }"

echo "  ]
}"
