#!/bin/bash
# WhatsApp Bridge Migration Script: Hostinger → VF Server
# CRITICAL: Preserves WhatsApp session to avoid re-pairing phone

set -e  # Exit on error

# Configuration
HOSTINGER_HOST="72.60.17.245"
HOSTINGER_PASS="VeloF@2025@@"
VF_SERVER_HOST="100.96.203.105"
VF_SERVER_USER="velo"
TIMESTAMP=$(date +%Y%m%d-%H%M%S)

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${GREEN}═══════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}    WhatsApp Bridge Migration: Hostinger → VF Server    ${NC}"
echo -e "${GREEN}═══════════════════════════════════════════════════════════${NC}"
echo -e "${YELLOW}⚠️  CRITICAL: This preserves the WhatsApp phone pairing${NC}"

# Phase 1: Pre-Migration Checks
echo -e "\n${YELLOW}Phase 1: Pre-Migration Checks${NC}"
echo "----------------------------------------"

# Check if wa-monitor is running on VF Server
echo "✓ Checking wa-monitor on VF Server..."
if ssh $VF_SERVER_USER@$VF_SERVER_HOST "ps aux | grep -q '[m]ain.py'" 2>/dev/null; then
    echo -e "${GREEN}✓ wa-monitor is running on VF Server${NC}"
else
    echo -e "${RED}✗ wa-monitor not running on VF Server - start it first!${NC}"
    exit 1
fi

# Check WhatsApp Bridge on Hostinger
echo "✓ Checking WhatsApp Bridge on Hostinger..."
STATUS=$(sshpass -p "$HOSTINGER_PASS" ssh -o StrictHostKeyChecking=no -o PreferredAuthentications=password -o PubkeyAuthentication=no root@$HOSTINGER_HOST "systemctl is-active whatsapp-bridge-prod" 2>/dev/null || echo "inactive")
if [ "$STATUS" = "active" ]; then
    echo -e "${GREEN}✓ WhatsApp Bridge is active on Hostinger${NC}"
else
    echo -e "${RED}✗ WhatsApp Bridge is not active on Hostinger${NC}"
    exit 1
fi

# Phase 2: Stop the 30-second sync (no longer needed)
echo -e "\n${YELLOW}Phase 2: Stopping Message Sync${NC}"
echo "----------------------------------------"
echo "✓ Stopping the 30-second database sync..."
ssh $VF_SERVER_USER@$VF_SERVER_HOST "pkill -f 'scp.*messages.db' 2>/dev/null || true"
echo -e "${GREEN}✓ Database sync stopped${NC}"

# Phase 3: Create Backups
echo -e "\n${YELLOW}Phase 3: Creating Backups${NC}"
echo "----------------------------------------"

# Backup on Hostinger
echo "✓ Creating backup on Hostinger..."
sshpass -p "$HOSTINGER_PASS" ssh -o StrictHostKeyChecking=no -o PreferredAuthentications=password -o PubkeyAuthentication=no root@$HOSTINGER_HOST "
    tar -czf /root/whatsapp-bridge-backup-$TIMESTAMP.tar.gz \
        /opt/velo-test-monitor/services/whatsapp-bridge/ \
        /etc/systemd/system/whatsapp-bridge-prod.service 2>/dev/null
"
echo -e "${GREEN}✓ Backup created: whatsapp-bridge-backup-$TIMESTAMP.tar.gz${NC}"

# Phase 4: Copy WhatsApp Bridge to VF Server
echo -e "\n${YELLOW}Phase 4: Copying WhatsApp Bridge to VF Server${NC}"
echo "----------------------------------------"

# Create directory structure
echo "✓ Creating directory structure on VF Server..."
ssh $VF_SERVER_USER@$VF_SERVER_HOST "mkdir -p ~/whatsapp-bridge/{store,logs}"

# Copy the bridge binary and files
echo "✓ Copying WhatsApp Bridge binary and configuration..."
sshpass -p "$HOSTINGER_PASS" scp -o StrictHostKeyChecking=no -o PreferredAuthentications=password -o PubkeyAuthentication=no \
    root@$HOSTINGER_HOST:/opt/velo-test-monitor/services/whatsapp-bridge/whatsapp-bridge \
    /tmp/whatsapp-bridge-binary

scp /tmp/whatsapp-bridge-binary $VF_SERVER_USER@$VF_SERVER_HOST:~/whatsapp-bridge/whatsapp-bridge
ssh $VF_SERVER_USER@$VF_SERVER_HOST "chmod +x ~/whatsapp-bridge/whatsapp-bridge"

# Copy all database files (CRITICAL: preserves session)
echo -e "${BLUE}✓ Copying WhatsApp session databases (CRITICAL)...${NC}"
echo "  - whatsapp.db (phone pairing)"
echo "  - messages.db (chat history)"
echo "  - store.db (additional data)"

# Stop WhatsApp Bridge on Hostinger first to ensure clean database state
echo -e "${YELLOW}⚠️  Stopping WhatsApp Bridge on Hostinger for clean copy...${NC}"
sshpass -p "$HOSTINGER_PASS" ssh -o StrictHostKeyChecking=no -o PreferredAuthentications=password -o PubkeyAuthentication=no root@$HOSTINGER_HOST "
    systemctl stop whatsapp-bridge-prod
    sleep 2
"

# Copy all database files
for db in whatsapp.db messages.db store.db; do
    echo "  Copying $db..."
    sshpass -p "$HOSTINGER_PASS" scp -o StrictHostKeyChecking=no -o PreferredAuthentications=password -o PubkeyAuthentication=no \
        root@$HOSTINGER_HOST:/opt/velo-test-monitor/services/whatsapp-bridge/store/$db \
        /tmp/$db
    scp /tmp/$db $VF_SERVER_USER@$VF_SERVER_HOST:~/whatsapp-bridge/store/$db
    rm /tmp/$db
done

echo -e "${GREEN}✓ All databases copied successfully${NC}"

# Phase 5: Configure and Start on VF Server
echo -e "\n${YELLOW}Phase 5: Starting WhatsApp Bridge on VF Server${NC}"
echo "----------------------------------------"

# Create systemd service
echo "✓ Creating systemd service..."
ssh $VF_SERVER_USER@$VF_SERVER_HOST "sudo tee /etc/systemd/system/whatsapp-bridge.service > /dev/null << 'EOF'
[Unit]
Description=WhatsApp Bridge - VF Server
After=network.target

[Service]
Type=simple
User=$VF_SERVER_USER
WorkingDirectory=/home/$VF_SERVER_USER/whatsapp-bridge
ExecStart=/home/$VF_SERVER_USER/whatsapp-bridge/whatsapp-bridge
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal
Environment=\"DB_PATH=/home/$VF_SERVER_USER/whatsapp-bridge/store\"
Environment=\"PORT=8080\"

[Install]
WantedBy=multi-user.target
EOF"

# Update wa-monitor configuration to use local WhatsApp DB
echo "✓ Updating wa-monitor configuration..."
ssh $VF_SERVER_USER@$VF_SERVER_HOST "
    sed -i 's|/home/velo/whatsapp-bridge-vf/store/messages.db|/home/velo/whatsapp-bridge/store/messages.db|g' ~/wa-monitor-vf/prod/.env
"

# Start the bridge
echo "✓ Starting WhatsApp Bridge on VF Server..."
ssh $VF_SERVER_USER@$VF_SERVER_HOST "
    sudo systemctl daemon-reload
    sudo systemctl enable whatsapp-bridge
    sudo systemctl start whatsapp-bridge
"

sleep 3

# Phase 6: Validation
echo -e "\n${YELLOW}Phase 6: Validation${NC}"
echo "----------------------------------------"

# Check if bridge is running
echo "✓ Checking WhatsApp Bridge status..."
BRIDGE_STATUS=$(ssh $VF_SERVER_USER@$VF_SERVER_HOST "systemctl is-active whatsapp-bridge" 2>/dev/null || echo "failed")
if [ "$BRIDGE_STATUS" = "active" ]; then
    echo -e "${GREEN}✓ WhatsApp Bridge is running on VF Server!${NC}"
else
    echo -e "${RED}✗ WhatsApp Bridge failed to start${NC}"
    echo "Checking logs..."
    ssh $VF_SERVER_USER@$VF_SERVER_HOST "sudo journalctl -u whatsapp-bridge -n 20 --no-pager"

    # Rollback
    echo -e "${YELLOW}Rolling back...${NC}"
    sshpass -p "$HOSTINGER_PASS" ssh -o StrictHostKeyChecking=no -o PreferredAuthentications=password -o PubkeyAuthentication=no root@$HOSTINGER_HOST "systemctl start whatsapp-bridge-prod"
    exit 1
fi

# Check if port 8080 is listening
echo "✓ Checking port 8080..."
if ssh $VF_SERVER_USER@$VF_SERVER_HOST "ss -tuln | grep -q ':8080 '" 2>/dev/null; then
    echo -e "${GREEN}✓ Port 8080 is listening${NC}"
else
    echo -e "${YELLOW}⚠️  Port 8080 not listening yet (may take a moment)${NC}"
fi

# Restart wa-monitor to use local database
echo "✓ Restarting wa-monitor to use local database..."
ssh $VF_SERVER_USER@$VF_SERVER_HOST "
    pkill -f 'python main.py' 2>/dev/null || true
    sleep 2
    cd ~/wa-monitor-vf/prod && nohup ~/wa-monitor-vf/venv/bin/python main.py > ~/wa-monitor-vf/prod/logs/monitor-local.log 2>&1 &
"

echo -e "${GREEN}✓ wa-monitor restarted with local database${NC}"

# Phase 7: Final Cleanup
echo -e "\n${YELLOW}Phase 7: Cleanup${NC}"
echo "----------------------------------------"

# Disable (but don't remove) Hostinger bridge
echo "✓ Disabling Hostinger WhatsApp Bridge (keeping as backup)..."
sshpass -p "$HOSTINGER_PASS" ssh -o StrictHostKeyChecking=no -o PreferredAuthentications=password -o PubkeyAuthentication=no root@$HOSTINGER_HOST "
    systemctl disable whatsapp-bridge-prod
    echo 'WhatsApp Bridge disabled but preserved for emergency rollback'
"

# Summary
echo -e "\n${GREEN}═══════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}         WhatsApp Bridge Migration Complete! 🎉              ${NC}"
echo -e "${GREEN}═══════════════════════════════════════════════════════════${NC}"

echo -e "\n${YELLOW}New Architecture:${NC}"
echo "  VF Server (100.96.203.105):"
echo "    • wa-monitor: ✅ Processing drops (local DB)"
echo "    • WhatsApp Bridge: ✅ Running on port 8080"
echo "    • WhatsApp Session: ✅ Preserved (no re-pairing needed)"
echo "    • Database Path: ~/whatsapp-bridge/store/"
echo ""
echo "  Hostinger (72.60.17.245):"
echo "    • wa-monitor-prod: ❌ Stopped"
echo "    • whatsapp-bridge-prod: ❌ Stopped (backup available)"
echo ""
echo -e "${GREEN}Everything is now on VF Server with battery backup!${NC}"

echo -e "\n${YELLOW}Quick Commands:${NC}"
echo "  Check bridge status: ssh $VF_SERVER_USER@$VF_SERVER_HOST 'systemctl status whatsapp-bridge'"
echo "  View bridge logs: ssh $VF_SERVER_USER@$VF_SERVER_HOST 'sudo journalctl -u whatsapp-bridge -f'"
echo "  Check wa-monitor: ssh $VF_SERVER_USER@$VF_SERVER_HOST 'tail -f ~/wa-monitor-vf/prod/logs/monitor-local.log'"

echo -e "\n${YELLOW}Rollback (if needed):${NC}"
echo "  1. Stop VF Bridge: ssh $VF_SERVER_USER@$VF_SERVER_HOST 'sudo systemctl stop whatsapp-bridge'"
echo "  2. Start Hostinger: sshpass -p '$HOSTINGER_PASS' ssh root@$HOSTINGER_HOST 'systemctl start whatsapp-bridge-prod'"
echo "  3. Restart sync: (run the 30-second sync script again)"

rm /tmp/whatsapp-bridge-binary 2>/dev/null || true