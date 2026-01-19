#!/bin/bash
# QFieldCloud Comprehensive Health Check

# Color codes for output
RED='\033[0;31m'
YELLOW='\033[1;33m'
GREEN='\033[0;32m'
NC='\033[0m' # No Color

echo "================================================"
echo "QFieldCloud Health Check"
echo "Started: $(date '+%Y-%m-%d %H:%M:%S')"
echo "================================================"
echo ""

# Track overall health
HEALTH_STATUS="HEALTHY"
ISSUES=()

# Function to check service
check_service() {
    local service=$1
    local critical=$2
    local container_name=$3  # Optional specific container name

    # Use provided name or default pattern
    local search_name="${container_name:-$service}"

    if docker ps --format "{{.Names}}" | grep -qE "^${search_name}$"; then
        echo -e "${GREEN}✓${NC} $service: Running"
        return 0
    else
        echo -e "${RED}✗${NC} $service: DOWN"
        ISSUES+=("$service is down")
        if [ "$critical" = "true" ]; then
            HEALTH_STATUS="CRITICAL"
        elif [ "$HEALTH_STATUS" != "CRITICAL" ]; then
            HEALTH_STATUS="WARNING"
        fi
        return 1
    fi
}

# 1. Core Services Check
echo "1. CORE SERVICES"
echo "----------------------------------------"
cd /opt/qfieldcloud 2>/dev/null || { echo -e "${RED}ERROR: QFieldCloud directory not found${NC}"; exit 1; }

check_service "nginx" true "qfieldcloud-nginx-1"
check_service "app" true "qfieldcloud-app-1"
check_service "db" true "qfieldcloud-db-1"
check_service "redis" false "qfieldcloud-redis-1"
check_service "minio" true "qfieldcloud-minio-1"

echo ""

# 2. Worker Status
echo "2. WORKER STATUS"
echo "----------------------------------------"
WORKER_COUNT=$(docker ps | grep -c "worker_wrapper.*Up" 2>/dev/null)
echo "Workers running: $WORKER_COUNT / 8"

if [ "$WORKER_COUNT" -eq 8 ]; then
    echo -e "${GREEN}✓${NC} All workers operational"
elif [ "$WORKER_COUNT" -gt 0 ]; then
    echo -e "${YELLOW}⚠${NC}  Only $WORKER_COUNT workers running"
    ISSUES+=("Only $WORKER_COUNT/8 workers running")
    [ "$HEALTH_STATUS" != "CRITICAL" ] && HEALTH_STATUS="WARNING"
else
    echo -e "${RED}✗${NC} No workers running!"
    ISSUES+=("No workers running")
    HEALTH_STATUS="CRITICAL"
fi

echo ""

# 3. QGIS Image Check
echo "3. QGIS DOCKER IMAGE"
echo "----------------------------------------"
if docker images | grep -q "qfieldcloud-qgis.*latest"; then
    echo -e "${GREEN}✓${NC} QGIS image present"
    IMAGE_SIZE=$(docker images | grep qfieldcloud-qgis | head -1 | awk '{print $7" "$8}')
    echo "   Size: $IMAGE_SIZE"
else
    echo -e "${RED}✗${NC} QGIS image MISSING!"
    echo "   Run: ../qgis-image/scripts/restore.sh"
    ISSUES+=("QGIS Docker image missing")
    HEALTH_STATUS="CRITICAL"
fi

echo ""

# 4. Database Check
echo "4. DATABASE"
echo "----------------------------------------"
DB_CHECK=$(docker exec qfieldcloud-db-1 pg_isready -U qfieldcloud_db_admin 2>/dev/null)
if echo "$DB_CHECK" | grep -q "accepting connections"; then
    echo -e "${GREEN}✓${NC} Database accepting connections"
else
    echo -e "${RED}✗${NC} Database not responding"
    ISSUES+=("Database not accepting connections")
    HEALTH_STATUS="CRITICAL"
fi

echo ""

# 5. Web Interface Check
echo "5. WEB INTERFACE"
echo "----------------------------------------"
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" https://qfield.fibreflow.app 2>/dev/null)

if [ "$HTTP_CODE" = "200" ] || [ "$HTTP_CODE" = "302" ]; then
    echo -e "${GREEN}✓${NC} Web interface responding (HTTP $HTTP_CODE)"
elif [ "$HTTP_CODE" = "403" ]; then
    echo -e "${YELLOW}⚠${NC}  CSRF issues detected (HTTP 403)"
    echo "   Run: ../csrf-fix/scripts/apply_fix.sh"
    ISSUES+=("CSRF configuration issues")
    [ "$HEALTH_STATUS" != "CRITICAL" ] && HEALTH_STATUS="WARNING"
else
    echo -e "${RED}✗${NC} Web interface not responding (HTTP $HTTP_CODE)"
    ISSUES+=("Web interface returning HTTP $HTTP_CODE")
    HEALTH_STATUS="CRITICAL"
fi

echo ""

# 6. Storage Check
echo "6. STORAGE (MinIO)"
echo "----------------------------------------"
MINIO_HEALTH=$(curl -s http://100.96.203.105:8010/minio/health/live 2>/dev/null)
if [ "$?" -eq 0 ]; then
    echo -e "${GREEN}✓${NC} MinIO storage operational"
else
    echo -e "${YELLOW}⚠${NC}  MinIO health check failed"
    ISSUES+=("MinIO storage issues")
    [ "$HEALTH_STATUS" != "CRITICAL" ] && HEALTH_STATUS="WARNING"
fi

echo ""

# 7. Recent Job Processing
echo "7. JOB PROCESSING"
echo "----------------------------------------"
RECENT_SUCCESS=$(docker-compose logs --since=1h worker_wrapper 2>&1 | grep -c "Finished execution with code 0" 2>/dev/null)
RECENT_ERRORS=$(docker-compose logs --since=1h worker_wrapper 2>&1 | grep -c "ERROR\|ImageNotFound" 2>/dev/null)

echo "Last hour: $RECENT_SUCCESS successful, $RECENT_ERRORS errors"

if [ "$RECENT_SUCCESS" -gt 0 ]; then
    echo -e "${GREEN}✓${NC} Workers actively processing"
elif [ "$RECENT_ERRORS" -gt 10 ]; then
    echo -e "${RED}✗${NC} High error rate detected"
    ISSUES+=("High job error rate")
    HEALTH_STATUS="CRITICAL"
else
    echo -e "${YELLOW}⚠${NC}  No recent job activity"
    [ "$HEALTH_STATUS" = "HEALTHY" ] && HEALTH_STATUS="WARNING"
fi

echo ""

# 8. Disk Space
echo "8. DISK SPACE"
echo "----------------------------------------"
DISK_USAGE=$(df -h /opt/qfieldcloud | tail -1 | awk '{print $5}' | sed 's/%//')
echo "Disk usage: $DISK_USAGE%"

if [ "$DISK_USAGE" -lt 80 ]; then
    echo -e "${GREEN}✓${NC} Adequate disk space"
elif [ "$DISK_USAGE" -lt 90 ]; then
    echo -e "${YELLOW}⚠${NC}  Disk space warning"
    ISSUES+=("Disk usage at $DISK_USAGE%")
    [ "$HEALTH_STATUS" != "CRITICAL" ] && HEALTH_STATUS="WARNING"
else
    echo -e "${RED}✗${NC} Critical disk space!"
    ISSUES+=("Critical disk usage: $DISK_USAGE%")
    HEALTH_STATUS="CRITICAL"
fi

echo ""
echo "================================================"
echo "HEALTH SUMMARY"
echo "================================================"

# Display overall status
case $HEALTH_STATUS in
    "HEALTHY")
        echo -e "${GREEN}🟢 SYSTEM STATUS: HEALTHY${NC}"
        echo "All systems operational"
        ;;
    "WARNING")
        echo -e "${YELLOW}🟡 SYSTEM STATUS: WARNING${NC}"
        echo "Non-critical issues detected:"
        for issue in "${ISSUES[@]}"; do
            echo "  - $issue"
        done
        ;;
    "CRITICAL")
        echo -e "${RED}🔴 SYSTEM STATUS: CRITICAL${NC}"
        echo "Critical issues requiring immediate action:"
        for issue in "${ISSUES[@]}"; do
            echo "  - $issue"
        done
        ;;
esac

echo ""
echo "Completed: $(date '+%Y-%m-%d %H:%M:%S')"

# Exit with appropriate code
case $HEALTH_STATUS in
    "HEALTHY") exit 0 ;;
    "WARNING") exit 1 ;;
    "CRITICAL") exit 2 ;;
esac