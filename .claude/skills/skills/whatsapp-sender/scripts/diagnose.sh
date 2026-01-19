#!/bin/bash

# WhatsApp Sender Diagnostic Script
# Comprehensive health check and troubleshooting

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Configuration
SERVER="100.96.203.105"
USER="louis"
SSH_KEY="$HOME/.ssh/vf_server_key"
WA_DIR="~/whatsapp-sender"

echo -e "${BLUE}═══════════════════════════════════════════════${NC}"
echo -e "${BLUE}    WhatsApp Sender Service Diagnostics${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════${NC}"
echo ""

# Function to execute SSH commands
exec_ssh() {
    ssh -i "$SSH_KEY" "$USER@$SERVER" "$1" 2>/dev/null || echo "SSH_ERROR"
}

# 1. Check SSH connectivity
echo -e "${YELLOW}[1/10]${NC} Checking SSH connectivity..."
if exec_ssh "echo 'OK'" | grep -q "OK"; then
    echo -e "${GREEN}  ✅ SSH connection successful${NC}"
else
    echo -e "${RED}  ❌ SSH connection failed${NC}"
    echo "  Check: SSH key at $SSH_KEY"
    echo "  Check: Server reachability at $SERVER"
    exit 1
fi

# 2. Check WhatsApp directory exists
echo -e "${YELLOW}[2/10]${NC} Checking WhatsApp directory..."
DIR_CHECK=$(exec_ssh "[ -d $WA_DIR ] && echo 'EXISTS' || echo 'MISSING'")
if [ "$DIR_CHECK" = "EXISTS" ]; then
    echo -e "${GREEN}  ✅ Directory exists at $WA_DIR${NC}"
else
    echo -e "${RED}  ❌ Directory missing at $WA_DIR${NC}"
    exit 1
fi

# 3. Check binary exists
echo -e "${YELLOW}[3/10]${NC} Checking WhatsApp binary..."
BIN_CHECK=$(exec_ssh "[ -x $WA_DIR/whatsapp-sender ] && echo 'OK' || echo 'MISSING'")
if [ "$BIN_CHECK" = "OK" ]; then
    BIN_SIZE=$(exec_ssh "ls -lh $WA_DIR/whatsapp-sender | awk '{print \$5}'")
    echo -e "${GREEN}  ✅ Binary exists and executable (${BIN_SIZE})${NC}"
else
    echo -e "${RED}  ❌ Binary missing or not executable${NC}"
fi

# 4. Check session database
echo -e "${YELLOW}[4/10]${NC} Checking session database..."
SESSION_CHECK=$(exec_ssh "[ -f $WA_DIR/store/whatsapp.db ] && echo 'EXISTS' || echo 'MISSING'")
if [ "$SESSION_CHECK" = "EXISTS" ]; then
    SESSION_SIZE=$(exec_ssh "ls -lh $WA_DIR/store/whatsapp.db 2>/dev/null | awk '{print \$5}'")
    SESSION_DATE=$(exec_ssh "stat -c %y $WA_DIR/store/whatsapp.db 2>/dev/null | cut -d' ' -f1")
    echo -e "${GREEN}  ✅ Session exists (${SESSION_SIZE}, created: ${SESSION_DATE})${NC}"
else
    echo -e "${YELLOW}  ⚠️  Session missing - pairing required${NC}"
fi

# 5. Check process status
echo -e "${YELLOW}[5/10]${NC} Checking process status..."
PID=$(exec_ssh "pgrep -f whatsapp-sender | head -1")
if [ -n "$PID" ] && [ "$PID" != "SSH_ERROR" ]; then
    echo -e "${GREEN}  ✅ Process running (PID: $PID)${NC}"
    PROCESS_RUNNING=true
else
    echo -e "${YELLOW}  ⚠️  Process not running${NC}"
    PROCESS_RUNNING=false
fi

# 6. Check port 8081
echo -e "${YELLOW}[6/10]${NC} Checking port 8081..."
PORT_CHECK=$(exec_ssh "sudo netstat -tlpn 2>/dev/null | grep :8081 | grep -o LISTEN || echo 'CLOSED'")
if [ "$PORT_CHECK" = "LISTEN" ]; then
    echo -e "${GREEN}  ✅ Port 8081 is listening${NC}"
else
    echo -e "${YELLOW}  ⚠️  Port 8081 not listening${NC}"
fi

# 7. Check API health
echo -e "${YELLOW}[7/10]${NC} Checking API health..."
HEALTH=$(exec_ssh "curl -s -m 5 http://localhost:8081/health 2>/dev/null || echo '{}'")
if echo "$HEALTH" | grep -q "healthy"; then
    echo -e "${GREEN}  ✅ API is healthy${NC}"
    if echo "$HEALTH" | grep -q '"connected":true'; then
        echo -e "${GREEN}  ✅ WhatsApp connected${NC}"
    else
        echo -e "${YELLOW}  ⚠️  WhatsApp not connected${NC}"
    fi
else
    echo -e "${YELLOW}  ⚠️  API not responding or unhealthy${NC}"
fi

# 8. Check recent logs
echo -e "${YELLOW}[8/10]${NC} Checking recent logs..."
ERROR_COUNT=$(exec_ssh "grep -c ERROR $WA_DIR/whatsapp-sender.log 2>/dev/null || echo '0'")
if [ "$ERROR_COUNT" = "0" ] || [ "$ERROR_COUNT" = "SSH_ERROR" ]; then
    echo -e "${GREEN}  ✅ No errors in logs${NC}"
else
    echo -e "${YELLOW}  ⚠️  Found $ERROR_COUNT errors in logs${NC}"
    echo "  Recent errors:"
    exec_ssh "grep ERROR $WA_DIR/whatsapp-sender.log 2>/dev/null | tail -3" | sed 's/^/    /'
fi

# 9. Check for rate limits
echo -e "${YELLOW}[9/10]${NC} Checking for rate limits..."
RATE_LIMIT=$(exec_ssh "grep -q 'rate-overlimit' $WA_DIR/whatsapp-sender.log 2>/dev/null && echo 'FOUND' || echo 'NONE'")
if [ "$RATE_LIMIT" = "FOUND" ]; then
    LAST_LIMIT=$(exec_ssh "grep 'rate-overlimit' $WA_DIR/whatsapp-sender.log | tail -1 | cut -d' ' -f1")
    echo -e "${RED}  ❌ Rate limit detected (last: $LAST_LIMIT)${NC}"
    echo "  Wait 1-24 hours before retrying"
else
    echo -e "${GREEN}  ✅ No rate limits detected${NC}"
fi

# 10. Check disk space
echo -e "${YELLOW}[10/10]${NC} Checking disk space..."
DISK_USAGE=$(exec_ssh "df -h / | awk 'NR==2 {print \$5}' | sed 's/%//'")
if [ "$DISK_USAGE" -lt 90 ]; then
    echo -e "${GREEN}  ✅ Disk usage OK (${DISK_USAGE}%)${NC}"
else
    echo -e "${YELLOW}  ⚠️  High disk usage (${DISK_USAGE}%)${NC}"
fi

# Summary and recommendations
echo ""
echo -e "${BLUE}═══════════════════════════════════════════════${NC}"
echo -e "${BLUE}                   SUMMARY${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════${NC}"

if [ "$PROCESS_RUNNING" = true ] && echo "$HEALTH" | grep -q "healthy"; then
    echo -e "${GREEN}✅ Service is OPERATIONAL${NC}"
    echo ""
    echo "Quick test command:"
    echo "  curl http://$SERVER:8081/health | jq"
elif [ "$SESSION_CHECK" = "MISSING" ]; then
    echo -e "${YELLOW}⚠️  Service needs PAIRING${NC}"
    echo ""
    echo "To pair a new phone:"
    echo "  .claude/skills/whatsapp-sender/scripts/pair_phone.sh"
elif [ "$RATE_LIMIT" = "FOUND" ]; then
    echo -e "${RED}❌ Service is RATE LIMITED${NC}"
    echo ""
    echo "You must wait 1-24 hours before attempting to pair again."
    echo "Check last rate limit time in logs."
elif [ "$PROCESS_RUNNING" = false ]; then
    echo -e "${YELLOW}⚠️  Service is STOPPED${NC}"
    echo ""
    echo "To start the service:"
    echo "  .claude/skills/whatsapp-sender/scripts/manage_service.sh start"
else
    echo -e "${YELLOW}⚠️  Service needs ATTENTION${NC}"
    echo ""
    echo "Review the issues above and:"
    echo "1. Check logs: .claude/skills/whatsapp-sender/scripts/manage_service.sh logs"
    echo "2. Restart service: .claude/skills/whatsapp-sender/scripts/manage_service.sh restart"
fi

echo ""
echo -e "${BLUE}═══════════════════════════════════════════════${NC}"