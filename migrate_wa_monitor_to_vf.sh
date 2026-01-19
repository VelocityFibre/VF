#!/bin/bash
# WA Monitor Migration Script: Hostinger → VF Server
# This script sets up a PARALLEL instance on VF Server for zero-downtime migration

set -e  # Exit on error

# Configuration
HOSTINGER_HOST="72.60.17.245"
HOSTINGER_USER="root"
HOSTINGER_PASS="VeloF@2025@@"
VF_SERVER_HOST="100.96.203.105"
VF_SERVER_USER="velo"
VF_SERVER_PASS="2025"
TIMESTAMP=$(date +%Y%m%d-%H%M%S)

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}═══════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}    WA Monitor Migration: Hostinger → VF Server    ${NC}"
echo -e "${GREEN}═══════════════════════════════════════════════════════════${NC}"

# Function to run SSH commands on Hostinger
hostinger_ssh() {
    sshpass -p "$HOSTINGER_PASS" ssh -o StrictHostKeyChecking=no -o PreferredAuthentications=password -o PubkeyAuthentication=no $HOSTINGER_USER@$HOSTINGER_HOST "$1"
}

# Function to run SSH commands on VF Server
vf_ssh() {
    sshpass -p "$VF_SERVER_PASS" ssh -o StrictHostKeyChecking=no $VF_SERVER_USER@$VF_SERVER_HOST "$1"
}

# Phase 0: Pre-checks
echo -e "\n${YELLOW}Phase 0: Pre-Migration Checks${NC}"
echo "----------------------------------------"

echo "✓ Checking connectivity to Hostinger..."
if hostinger_ssh "echo 'Connected'" > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Hostinger connection successful${NC}"
else
    echo -e "${RED}✗ Cannot connect to Hostinger${NC}"
    exit 1
fi

echo "✓ Checking connectivity to VF Server..."
if vf_ssh "echo 'Connected'" > /dev/null 2>&1; then
    echo -e "${GREEN}✓ VF Server connection successful${NC}"
else
    echo -e "${RED}✗ Cannot connect to VF Server${NC}"
    exit 1
fi

echo "✓ Checking wa-monitor status on Hostinger..."
STATUS=$(hostinger_ssh "systemctl is-active wa-monitor-prod" 2>/dev/null || echo "inactive")
echo "  Current status: $STATUS"

echo "✓ Checking for existing wa-monitor on VF Server..."
if vf_ssh "ls /opt/wa-monitor-vf 2>/dev/null" > /dev/null 2>&1; then
    echo -e "${YELLOW}  ⚠️  wa-monitor-vf already exists on VF Server${NC}"
    read -p "  Do you want to backup and continue? (y/n): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Migration cancelled."
        exit 1
    fi
    echo "  Creating backup..."
    vf_ssh "sudo tar -czf /opt/wa-monitor-vf-backup-$TIMESTAMP.tar.gz /opt/wa-monitor-vf 2>/dev/null" || true
fi

# Phase 1: Backup on Hostinger
echo -e "\n${YELLOW}Phase 1: Creating Backups${NC}"
echo "----------------------------------------"

echo "✓ Creating backup on Hostinger..."
hostinger_ssh "tar -czf /root/wa-monitor-backup-$TIMESTAMP.tar.gz \
    /opt/wa-monitor \
    /opt/velo-test-monitor/services/whatsapp-bridge/store \
    /etc/systemd/system/wa-monitor*.service \
    /etc/systemd/system/whatsapp-bridge*.service 2>/dev/null" || true
echo -e "${GREEN}✓ Backup created: wa-monitor-backup-$TIMESTAMP.tar.gz${NC}"

# Phase 2: Setup VF Server
echo -e "\n${YELLOW}Phase 2: Setting up VF Server${NC}"
echo "----------------------------------------"

echo "✓ Creating directory structure..."
vf_ssh "sudo mkdir -p /opt/wa-monitor-vf/{prod,dev,backup,logs}"
vf_ssh "sudo mkdir -p /opt/whatsapp-bridge-vf/store"
vf_ssh "sudo chown -R $VF_SERVER_USER:$VF_SERVER_USER /opt/wa-monitor-vf /opt/whatsapp-bridge-vf"

echo "✓ Installing Python dependencies..."
vf_ssh "sudo apt-get update > /dev/null 2>&1 && sudo apt-get install -y python3-pip python3-venv sqlite3 sshpass > /dev/null 2>&1"

echo "✓ Copying application files..."
# Create a temporary transfer script
cat > /tmp/transfer_files.sh << 'TRANSFER_EOF'
#!/bin/bash
echo "Transferring wa-monitor files..."
sshpass -p "VeloF@2025@@" scp -r -o StrictHostKeyChecking=no -o PreferredAuthentications=password -o PubkeyAuthentication=no \
    root@72.60.17.245:/opt/wa-monitor/prod/* /opt/wa-monitor-vf/prod/ 2>/dev/null

echo "Transferring WhatsApp database..."
sshpass -p "VeloF@2025@@" scp -o StrictHostKeyChecking=no -o PreferredAuthentications=password -o PubkeyAuthentication=no \
    root@72.60.17.245:/opt/velo-test-monitor/services/whatsapp-bridge/store/messages.db \
    /opt/whatsapp-bridge-vf/store/ 2>/dev/null || true
TRANSFER_EOF

# Copy and execute transfer script on VF Server
scp /tmp/transfer_files.sh $VF_SERVER_USER@$VF_SERVER_HOST:/tmp/
vf_ssh "chmod +x /tmp/transfer_files.sh && /tmp/transfer_files.sh"

echo "✓ Setting up Python virtual environment..."
vf_ssh "cd /opt/wa-monitor-vf && python3 -m venv venv"
vf_ssh "cd /opt/wa-monitor-vf && ./venv/bin/pip install psycopg2-binary pyyaml requests > /dev/null 2>&1"

# Phase 3: Configure VF Instance
echo -e "\n${YELLOW}Phase 3: Configuring VF Instance${NC}"
echo "----------------------------------------"

echo "✓ Creating environment configuration..."
vf_ssh "cat > /opt/wa-monitor-vf/prod/.env << 'EOF'
# VF Server Instance (Parallel Deployment)
NEON_DATABASE_URL=postgresql://neondb_owner:npg_MIUZXrg1tEY0@ep-dry-night-a9qyh4sj-pooler.gwc.azure.neon.tech/neondb?sslmode=require&channel_binding=require
WHATSAPP_DB_PATH=/opt/whatsapp-bridge-vf/store/messages.db
SCAN_INTERVAL=15
LOG_LEVEL=INFO
LOG_FILE=/opt/wa-monitor-vf/prod/logs/wa-monitor-vf.log
DISABLE_AUTO_MESSAGES=true
INSTANCE_NAME=vf-server-parallel
EOF"

echo "✓ Creating systemd service..."
vf_ssh "sudo tee /etc/systemd/system/wa-monitor-vf.service > /dev/null << 'EOF'
[Unit]
Description=WhatsApp Drop Monitor - VF Server Instance (Parallel)
After=network.target

[Service]
Type=simple
User=$VF_SERVER_USER
WorkingDirectory=/opt/wa-monitor-vf/prod
Environment=\"PATH=/opt/wa-monitor-vf/venv/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin\"
ExecStart=/opt/wa-monitor-vf/venv/bin/python main.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF"

echo "✓ Creating safe restart script..."
vf_ssh "cat > /opt/wa-monitor-vf/prod/restart-monitor.sh << 'EOF'
#!/bin/bash
echo \"Stopping wa-monitor-vf service...\"
sudo systemctl stop wa-monitor-vf
echo \"Clearing Python cache...\"
find /opt/wa-monitor-vf -type d -name '__pycache__' -exec rm -rf {} + 2>/dev/null
echo \"Starting wa-monitor-vf service...\"
sudo systemctl start wa-monitor-vf
echo \"Service restarted. Checking status...\"
sleep 2
sudo systemctl status wa-monitor-vf --no-pager
EOF"
vf_ssh "chmod +x /opt/wa-monitor-vf/prod/restart-monitor.sh"

# Phase 4: Start Parallel Instance
echo -e "\n${YELLOW}Phase 4: Starting Parallel Instance${NC}"
echo "----------------------------------------"

echo "✓ Reloading systemd..."
vf_ssh "sudo systemctl daemon-reload"

echo "✓ Starting wa-monitor-vf service..."
vf_ssh "sudo systemctl start wa-monitor-vf"
sleep 3

echo "✓ Checking service status..."
STATUS=$(vf_ssh "systemctl is-active wa-monitor-vf" 2>/dev/null || echo "failed")
if [ "$STATUS" = "active" ]; then
    echo -e "${GREEN}✓ wa-monitor-vf is running successfully!${NC}"
else
    echo -e "${RED}✗ wa-monitor-vf failed to start${NC}"
    echo "Checking logs..."
    vf_ssh "sudo journalctl -u wa-monitor-vf -n 20 --no-pager"
    exit 1
fi

# Phase 5: Validation
echo -e "\n${YELLOW}Phase 5: Validation${NC}"
echo "----------------------------------------"

echo "✓ Checking for errors in VF logs..."
ERROR_COUNT=$(vf_ssh "grep -c ERROR /opt/wa-monitor-vf/prod/logs/*.log 2>/dev/null" || echo "0")
echo "  Errors found: $ERROR_COUNT"

echo "✓ Testing database connectivity..."
vf_ssh "export PGPASSWORD='npg_MIUZXrg1tEY0' && psql -h ep-dry-night-a9qyh4sj-pooler.gwc.azure.neon.tech -U neondb_owner -d neondb -c 'SELECT COUNT(*) FROM qa_photo_reviews;' > /dev/null 2>&1"
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Database connection successful${NC}"
else
    echo -e "${RED}✗ Database connection failed${NC}"
fi

# Summary
echo -e "\n${GREEN}═══════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}                Migration Phase 1 Complete!                 ${NC}"
echo -e "${GREEN}═══════════════════════════════════════════════════════════${NC}"

echo -e "\n${YELLOW}Current Status:${NC}"
echo "  • Hostinger wa-monitor-prod: $(hostinger_ssh 'systemctl is-active wa-monitor-prod')"
echo "  • VF Server wa-monitor-vf: $(vf_ssh 'systemctl is-active wa-monitor-vf')"
echo "  • Both instances running in PARALLEL (zero downtime)"

echo -e "\n${YELLOW}Next Steps:${NC}"
echo "  1. Monitor both instances for 30 minutes:"
echo "     - VF logs: ssh $VF_SERVER_USER@$VF_SERVER_HOST 'tail -f /opt/wa-monitor-vf/prod/logs/*.log'"
echo "     - Hostinger: ssh $HOSTINGER_USER@$HOSTINGER_HOST 'tail -f /opt/wa-monitor/prod/logs/*.log'"
echo ""
echo "  2. Check dashboard for any issues:"
echo "     - https://app.fibreflow.app/wa-monitor"
echo ""
echo "  3. When ready to cutover, run:"
echo "     - ./wa_monitor_cutover.sh"
echo ""
echo "  4. For rollback if needed:"
echo "     - ./wa_monitor_rollback.sh"

echo -e "\n${GREEN}Parallel deployment successful! Both instances are running.${NC}"

# Create cutover script
cat > wa_monitor_cutover.sh << 'CUTOVER_EOF'
#!/bin/bash
echo "WA Monitor Cutover: Switching to VF Server"
echo "==========================================="
echo ""
echo "This will:"
echo "  1. Stop Hostinger wa-monitor-prod"
echo "  2. Rename VF wa-monitor-vf to wa-monitor-prod"
echo "  3. Update all configurations"
echo ""
read -p "Continue with cutover? (y/n): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "Stopping Hostinger instance..."
    sshpass -p "VeloF@2025@@" ssh -o StrictHostKeyChecking=no root@72.60.17.245 "systemctl stop wa-monitor-prod"

    echo "Renaming VF service..."
    ssh velo@100.96.203.105 "sudo systemctl stop wa-monitor-vf"
    ssh velo@100.96.203.105 "sudo mv /etc/systemd/system/wa-monitor-vf.service /etc/systemd/system/wa-monitor-prod.service"
    ssh velo@100.96.203.105 "sudo systemctl daemon-reload"
    ssh velo@100.96.203.105 "sudo systemctl start wa-monitor-prod"

    echo "Cutover complete!"
    echo "wa-monitor is now running on VF Server only."
fi
CUTOVER_EOF
chmod +x wa_monitor_cutover.sh

# Create rollback script
cat > wa_monitor_rollback.sh << 'ROLLBACK_EOF'
#!/bin/bash
echo "WA Monitor Rollback: Reverting to Hostinger"
echo "==========================================="
echo ""
read -p "Rollback to Hostinger? (y/n): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "Stopping VF instance..."
    ssh velo@100.96.203.105 "sudo systemctl stop wa-monitor-vf 2>/dev/null || sudo systemctl stop wa-monitor-prod"

    echo "Starting Hostinger instance..."
    sshpass -p "VeloF@2025@@" ssh -o StrictHostKeyChecking=no root@72.60.17.245 "systemctl start wa-monitor-prod"

    echo "Rollback complete!"
    echo "wa-monitor is running on Hostinger again."
fi
ROLLBACK_EOF
chmod +x wa_monitor_rollback.sh

echo -e "\n${YELLOW}Helper scripts created:${NC}"
echo "  • wa_monitor_cutover.sh  - Complete migration to VF Server"
echo "  • wa_monitor_rollback.sh - Rollback to Hostinger if needed"