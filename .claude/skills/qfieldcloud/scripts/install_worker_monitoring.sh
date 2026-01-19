#!/bin/bash
#
# QFieldCloud Worker Monitoring Installation Script
# Installs systemd services, sets up monitoring, and configures alerts
#

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

echo -e "${BLUE}================================${NC}"
echo -e "${BLUE}QFieldCloud Worker Monitoring Setup${NC}"
echo -e "${BLUE}================================${NC}"

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo -e "${RED}Please run as root (sudo)${NC}"
    exit 1
fi

# Step 1: Create log directories
echo -e "\n${GREEN}[1/7]${NC} Creating log directories..."
mkdir -p /var/log/qfieldcloud
chmod 755 /var/log/qfieldcloud

# Step 2: Make scripts executable
echo -e "\n${GREEN}[2/7]${NC} Setting script permissions..."
chmod +x ${SCRIPT_DIR}/worker_monitor_daemon.py
chmod +x ${SCRIPT_DIR}/worker_alerts.py
chmod +x ${SCRIPT_DIR}/sync_diagnostic.py
chmod +x ${SCRIPT_DIR}/worker.py
chmod +x ${SCRIPT_DIR}/status_enhanced.py

# Step 3: Check if worker image exists
echo -e "\n${GREEN}[3/7]${NC} Checking worker image..."
if ! docker images | grep -q worker_wrapper; then
    echo -e "${YELLOW}Worker image not found. Building (this will take 10-15 minutes)...${NC}"
    cd /home/louisdup/VF/Apps/QFieldCloud
    docker-compose build worker_wrapper
else
    echo -e "${GREEN}Worker image already exists${NC}"
fi

# Step 4: Install systemd services
echo -e "\n${GREEN}[4/7]${NC} Installing systemd services..."

# Copy service files
cp ${SCRIPT_DIR}/qfield-worker.service /etc/systemd/system/
cp ${SCRIPT_DIR}/qfield-worker-monitor.service /etc/systemd/system/

# Reload systemd
systemctl daemon-reload

# Step 5: Enable services
echo -e "\n${GREEN}[5/7]${NC} Enabling services..."

# Enable worker service
systemctl enable qfield-worker.service
echo -e "  ${GREEN}✓${NC} Worker service enabled (auto-start on boot)"

# Enable monitor service
systemctl enable qfield-worker-monitor.service
echo -e "  ${GREEN}✓${NC} Monitor service enabled (auto-restart worker)"

# Step 6: Set up cron for alerts
echo -e "\n${GREEN}[6/7]${NC} Setting up alert cron job..."

# Add cron job for periodic checks
CRON_CMD="${SCRIPT_DIR}/worker_alerts.py --check"
CRON_JOB="*/5 * * * * ${CRON_CMD}"

# Check if cron job already exists
if ! crontab -l 2>/dev/null | grep -q "${CRON_CMD}"; then
    (crontab -l 2>/dev/null; echo "${CRON_JOB}") | crontab -
    echo -e "  ${GREEN}✓${NC} Alert checks scheduled every 5 minutes"
else
    echo -e "  ${YELLOW}!${NC} Alert cron job already exists"
fi

# Step 7: Start services
echo -e "\n${GREEN}[7/7]${NC} Starting services..."

# Start worker if not running
if ! docker ps | grep -q worker; then
    echo -e "  Starting worker service..."
    systemctl start qfield-worker.service
    sleep 5
    if systemctl is-active --quiet qfield-worker.service; then
        echo -e "  ${GREEN}✓${NC} Worker service started"
    else
        echo -e "  ${YELLOW}!${NC} Worker service failed to start (check logs)"
    fi
else
    echo -e "  ${GREEN}✓${NC} Worker already running"
fi

# Start monitor
echo -e "  Starting monitor daemon..."
systemctl start qfield-worker-monitor.service
if systemctl is-active --quiet qfield-worker-monitor.service; then
    echo -e "  ${GREEN}✓${NC} Monitor daemon started"
else
    echo -e "  ${YELLOW}!${NC} Monitor daemon failed to start (check logs)"
fi

# Display status
echo -e "\n${BLUE}================================${NC}"
echo -e "${BLUE}Installation Complete!${NC}"
echo -e "${BLUE}================================${NC}"

echo -e "\n${GREEN}Status Commands:${NC}"
echo "  Check overall status:     ${SCRIPT_DIR}/status_enhanced.py"
echo "  Check worker status:      ${SCRIPT_DIR}/worker.py status"
echo "  Check sync readiness:     ${SCRIPT_DIR}/sync_diagnostic.py"
echo "  View worker logs:         docker logs -f qfieldcloud-worker"
echo "  View monitor logs:        journalctl -u qfield-worker-monitor -f"
echo "  View alerts:              tail -f /var/log/qfield_worker_alerts.log"

echo -e "\n${GREEN}Service Management:${NC}"
echo "  Restart worker:           systemctl restart qfield-worker"
echo "  Restart monitor:          systemctl restart qfield-worker-monitor"
echo "  Stop monitoring:          systemctl stop qfield-worker-monitor"
echo "  Disable auto-start:       systemctl disable qfield-worker"

echo -e "\n${GREEN}Testing:${NC}"
echo "  Send test alert:          ${SCRIPT_DIR}/worker_alerts.py --test"
echo "  Check alert config:       ${SCRIPT_DIR}/worker_alerts.py --config"
echo "  Manual alert check:       ${SCRIPT_DIR}/worker_alerts.py --check"

echo -e "\n${YELLOW}Important:${NC}"
echo "  - Worker will auto-restart if it fails"
echo "  - Monitor checks every 60 seconds"
echo "  - Alerts sent every 5 minutes (if issues detected)"
echo "  - Logs rotate automatically"
echo "  - Check /var/log/qfield_worker_alerts.log for issues"

# Run initial status check
echo -e "\n${BLUE}Running initial status check...${NC}"
${SCRIPT_DIR}/status_enhanced.py

echo -e "\n${GREEN}✅ QFieldCloud Worker Monitoring is now active!${NC}"