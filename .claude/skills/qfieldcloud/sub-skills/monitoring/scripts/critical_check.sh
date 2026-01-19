#!/bin/bash
# QFieldCloud Critical Issues Check - Fast detection of major problems

RED='\033[0;31m'
GREEN='\033[0;32m'
NC='\033[0m'

# Fault logging integration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
FAULT_LOGGER="$SCRIPT_DIR/../../fault-logging/scripts/simple_log_fault.sh"

echo "QFieldCloud Critical Check - $(date '+%H:%M:%S')"
echo "----------------------------------------"

CRITICAL=false
cd /opt/qfieldcloud 2>/dev/null || exit 1

# 1. QGIS Image (Most Common Critical Issue)
if ! docker images | grep -q "qfieldcloud-qgis.*latest"; then
    echo -e "${RED}✗ CRITICAL: QGIS image missing${NC}"
    echo "  FIX: cd ../qgis-image/scripts && ./restore.sh"
    [ -f "$FAULT_LOGGER" ] && "$FAULT_LOGGER" "CRITICAL" "qgis-image" "QGIS Docker image missing" "monitoring" "critical_check" > /dev/null 2>&1
    CRITICAL=true
else
    echo -e "${GREEN}✓${NC} QGIS image present"
fi

# 2. Workers Running
WORKERS=$(docker ps | grep -c "worker_wrapper.*Up")
if [ "$WORKERS" -eq 0 ]; then
    echo -e "${RED}✗ CRITICAL: No workers running${NC}"
    echo "  FIX: cd ../worker-ops/scripts && ./restart.sh"
    [ -f "$FAULT_LOGGER" ] && "$FAULT_LOGGER" "CRITICAL" "workers" "No workers running (0/8)" "monitoring" "critical_check" > /dev/null 2>&1
    CRITICAL=true
elif [ "$WORKERS" -lt 4 ]; then
    echo -e "${GREEN}✓${NC} Workers running ($WORKERS/8) - degraded"
    [ -f "$FAULT_LOGGER" ] && "$FAULT_LOGGER" "MAJOR" "workers" "Only $WORKERS/8 workers running" "monitoring" "critical_check" > /dev/null 2>&1
else
    echo -e "${GREEN}✓${NC} Workers running ($WORKERS/8)"
fi

# 3. Core Services
for service in app nginx db; do
    # Check if container is running (handle both naming conventions)
    if docker ps --format "{{.Names}}" | grep -qE "^qfieldcloud-${service}(-[0-9]+)?$"; then
        echo -e "${GREEN}✓${NC} $service running"
    else
        echo -e "${RED}✗ CRITICAL: $service is down${NC}"
        echo "  FIX: docker-compose restart $service"
        [ -f "$FAULT_LOGGER" ] && "$FAULT_LOGGER" "CRITICAL" "core-services" "$service container is down" "monitoring" "critical_check" > /dev/null 2>&1
        CRITICAL=true
    fi
done

# 4. Web Accessibility (403 means CSRF issue)
HTTP=$(curl -s -o /dev/null -w "%{http_code}" https://qfield.fibreflow.app 2>/dev/null)
if [ "$HTTP" = "403" ]; then
    echo -e "${RED}✗ CRITICAL: CSRF verification failing${NC}"
    echo "  FIX: cd ../csrf-fix/scripts && ./apply_fix.sh"
    [ -f "$FAULT_LOGGER" ] && "$FAULT_LOGGER" "CRITICAL" "csrf" "CSRF verification failing - HTTP 403" "monitoring" "critical_check" > /dev/null 2>&1
    CRITICAL=true
elif [ "$HTTP" != "200" ] && [ "$HTTP" != "302" ]; then
    echo -e "${RED}✗ CRITICAL: Web interface down (HTTP $HTTP)${NC}"
    [ -f "$FAULT_LOGGER" ] && "$FAULT_LOGGER" "CRITICAL" "web-interface" "Web interface down - HTTP $HTTP" "monitoring" "critical_check" > /dev/null 2>&1
    CRITICAL=true
else
    echo -e "${GREEN}✓${NC} Web interface OK (HTTP $HTTP)"
fi

# 5. Disk Space
DISK=$(df -h /opt/qfieldcloud | tail -1 | awk '{print $5}' | sed 's/%//')
if [ "$DISK" -gt 90 ]; then
    echo -e "${RED}✗ CRITICAL: Disk space at $DISK%${NC}"
    echo "  FIX: Clean up old logs/backups"
    [ -f "$FAULT_LOGGER" ] && "$FAULT_LOGGER" "CRITICAL" "disk-space" "Disk space at $DISK% - exceeds 90% threshold" "monitoring" "critical_check" > /dev/null 2>&1
    CRITICAL=true
elif [ "$DISK" -gt 80 ]; then
    echo -e "${GREEN}✓${NC} Disk space OK ($DISK%) - warning level"
    [ -f "$FAULT_LOGGER" ] && "$FAULT_LOGGER" "MAJOR" "disk-space" "Disk space at $DISK% - exceeds 80% threshold" "monitoring" "critical_check" > /dev/null 2>&1
else
    echo -e "${GREEN}✓${NC} Disk space OK ($DISK%)"
fi

echo "----------------------------------------"

if [ "$CRITICAL" = true ]; then
    echo -e "${RED}🔴 CRITICAL ISSUES DETECTED${NC}"
    exit 2
else
    echo -e "${GREEN}🟢 NO CRITICAL ISSUES${NC}"
    exit 0
fi