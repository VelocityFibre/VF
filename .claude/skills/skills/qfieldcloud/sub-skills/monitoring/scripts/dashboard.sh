#!/bin/bash
# QFieldCloud Live Dashboard

clear

echo "Starting QFieldCloud Live Dashboard..."
echo "Press Ctrl+C to exit"
echo ""

while true; do
    clear
    echo "╔══════════════════════════════════════════════════════════════════╗"
    echo "║               QFieldCloud Live Dashboard                         ║"
    echo "║               $(date '+%Y-%m-%d %H:%M:%S')                       ║"
    echo "╚══════════════════════════════════════════════════════════════════╝"
    echo ""

    cd /opt/qfieldcloud 2>/dev/null

    # Core Services
    echo "┌─────────────────────────────────────────────────────────────────┐"
    echo "│ CORE SERVICES                                                   │"
    echo "├─────────────────────────────────────────────────────────────────┤"

    for service in nginx app db redis minio; do
        if docker ps | grep -q "qfieldcloud-$service.*Up"; then
            UPTIME=$(docker ps --format "table {{.Names}}\t{{.Status}}" | grep "qfieldcloud-$service" | head -1 | awk '{print $3,$4,$5}')
            printf "│ %-15s │ ✅ Running  │ %-25s │\n" "$service" "$UPTIME"
        else
            printf "│ %-15s │ ❌ DOWN     │ %-25s │\n" "$service" "Not running"
        fi
    done

    echo "└─────────────────────────────────────────────────────────────────┘"
    echo ""

    # Workers
    echo "┌─────────────────────────────────────────────────────────────────┐"
    echo "│ WORKERS                                                         │"
    echo "├─────────────────────────────────────────────────────────────────┤"

    WORKER_COUNT=$(docker ps | grep -c "worker_wrapper.*Up")
    printf "│ Active Workers: %2d/8                                            │\n" "$WORKER_COUNT"

    # Worker bar graph
    printf "│ ["
    for i in $(seq 1 8); do
        if [ "$i" -le "$WORKER_COUNT" ]; then
            printf "█"
        else
            printf "░"
        fi
    done
    printf "]                                                       │\n"

    echo "└─────────────────────────────────────────────────────────────────┘"
    echo ""

    # Critical Components
    echo "┌─────────────────────────────────────────────────────────────────┐"
    echo "│ CRITICAL CHECKS                                                 │"
    echo "├─────────────────────────────────────────────────────────────────┤"

    # QGIS Image
    if docker images | grep -q "qfieldcloud-qgis.*latest"; then
        printf "│ QGIS Image      │ ✅ Present  │ 2.6GB                         │\n"
    else
        printf "│ QGIS Image      │ ❌ MISSING  │ Run restore.sh                │\n"
    fi

    # Web Interface
    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" https://qfield.fibreflow.app 2>/dev/null)
    if [ "$HTTP_CODE" = "200" ] || [ "$HTTP_CODE" = "302" ]; then
        printf "│ Web Interface   │ ✅ Online   │ HTTP %3s                      │\n" "$HTTP_CODE"
    elif [ "$HTTP_CODE" = "403" ]; then
        printf "│ Web Interface   │ ⚠️  CSRF     │ HTTP 403                      │\n"
    else
        printf "│ Web Interface   │ ❌ Offline  │ HTTP %3s                      │\n" "$HTTP_CODE"
    fi

    # Database
    if docker exec qfieldcloud-db-1 pg_isready -U qfieldcloud_db_admin 2>/dev/null | grep -q "accepting"; then
        printf "│ Database        │ ✅ Ready    │ PostgreSQL 13                 │\n"
    else
        printf "│ Database        │ ❌ Down     │ Check logs                    │\n"
    fi

    echo "└─────────────────────────────────────────────────────────────────┘"
    echo ""

    # Activity
    echo "┌─────────────────────────────────────────────────────────────────┐"
    echo "│ RECENT ACTIVITY (Last Hour)                                     │"
    echo "├─────────────────────────────────────────────────────────────────┤"

    SUCCESS=$(docker-compose logs --since=1h worker_wrapper 2>&1 | grep -c "Finished execution with code 0" 2>/dev/null)
    ERRORS=$(docker-compose logs --since=1h worker_wrapper 2>&1 | grep -c "ERROR" 2>/dev/null)

    printf "│ Successful Jobs: %-3d                                            │\n" "$SUCCESS"
    printf "│ Errors:         %-3d                                            │\n" "$ERRORS"

    # Success rate
    if [ $((SUCCESS + ERRORS)) -gt 0 ]; then
        RATE=$((SUCCESS * 100 / (SUCCESS + ERRORS)))
        printf "│ Success Rate:   %3d%%                                            │\n" "$RATE"
    else
        printf "│ Success Rate:   N/A                                             │\n"
    fi

    echo "└─────────────────────────────────────────────────────────────────┘"
    echo ""

    # System Resources
    echo "┌─────────────────────────────────────────────────────────────────┐"
    echo "│ SYSTEM RESOURCES                                                │"
    echo "├─────────────────────────────────────────────────────────────────┤"

    # Disk usage
    DISK=$(df -h /opt/qfieldcloud | tail -1 | awk '{print $5}')
    printf "│ Disk Usage:     %-4s                                            │\n" "$DISK"

    # Memory
    MEM=$(free -h | grep Mem | awk '{print $3"/"$2}')
    printf "│ Memory:         %-15s                                  │\n" "$MEM"

    # Load average
    LOAD=$(uptime | awk -F'load average:' '{print $2}')
    printf "│ Load Average:   %-20s                            │\n" "$LOAD"

    echo "└─────────────────────────────────────────────────────────────────┘"
    echo ""

    # Status Summary
    if [ "$WORKER_COUNT" -eq 8 ] && docker images | grep -q "qfieldcloud-qgis.*latest" && ([ "$HTTP_CODE" = "200" ] || [ "$HTTP_CODE" = "302" ]); then
        echo "                    🟢 SYSTEM STATUS: HEALTHY"
    elif [ "$WORKER_COUNT" -eq 0 ] || ! docker images | grep -q "qfieldcloud-qgis.*latest"; then
        echo "                    🔴 SYSTEM STATUS: CRITICAL"
    else
        echo "                    🟡 SYSTEM STATUS: WARNING"
    fi

    echo ""
    echo "Refreshing in 30 seconds... (Ctrl+C to exit)"

    sleep 30
done