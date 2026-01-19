#!/bin/bash
# Setup QFieldCloud Automated Monitoring and Alerting
# This configures cron jobs for periodic health checks and alert notifications

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MONITORING_DIR="$SCRIPT_DIR/../../monitoring/scripts"
FAULT_DIR="$SCRIPT_DIR"

echo "================================================"
echo "QFieldCloud Monitoring Setup"
echo "================================================"
echo ""

# Check if scripts exist
if [ ! -f "$MONITORING_DIR/critical_check.sh" ]; then
    echo "❌ Critical check script not found"
    exit 1
fi

if [ ! -f "$FAULT_DIR/check_and_alert.sh" ]; then
    echo "❌ Alert check script not found"
    exit 1
fi

echo "✅ Required scripts found"
echo ""

# Create cron jobs
echo "Setting up cron jobs..."
echo ""

# Generate crontab entries
CRON_ENTRIES="
# QFieldCloud Automated Monitoring (Added by setup_monitoring.sh)
# Critical health check every 5 minutes
*/5 * * * * cd $MONITORING_DIR && ./critical_check.sh >> $SCRIPT_DIR/../data/health_check.log 2>&1

# Alert check every 5 minutes (staggered 2 minutes after health check)
2-59/5 * * * * cd $FAULT_DIR && ./check_and_alert.sh
"

echo "The following cron entries will be added:"
echo "$CRON_ENTRIES"
echo ""

read -p "Add these cron jobs? (y/n) " -n 1 -r
echo ""

if [[ $REPLY =~ ^[Yy]$ ]]; then
    # Backup existing crontab
    crontab -l > /tmp/crontab_backup_$(date +%s).txt 2>/dev/null || true

    # Remove old QFieldCloud monitoring entries if they exist
    (crontab -l 2>/dev/null | grep -v "QFieldCloud Automated Monitoring" | grep -v "critical_check.sh" | grep -v "check_and_alert.sh"; echo "$CRON_ENTRIES") | crontab -

    echo "✅ Cron jobs configured!"
    echo ""
    echo "Current crontab:"
    crontab -l | grep -A3 "QFieldCloud"
else
    echo "❌ Setup cancelled"
    exit 0
fi

echo ""
echo "================================================"
echo "Setup Complete!"
echo "================================================"
echo ""
echo "Monitoring schedule:"
echo "  • Health checks: Every 5 minutes"
echo "  • Alert checks:  Every 5 minutes (offset by 2 min)"
echo ""
echo "Log locations:"
echo "  • Health checks: $SCRIPT_DIR/../data/health_check.log"
echo "  • Alert checks:  $SCRIPT_DIR/../data/alert_check.log"
echo ""
echo "To view logs:"
echo "  tail -f $SCRIPT_DIR/../data/health_check.log"
echo "  tail -f $SCRIPT_DIR/../data/alert_check.log"
echo ""
echo "To disable monitoring:"
echo "  crontab -e  # Remove QFieldCloud entries"
echo ""
