#!/bin/bash
# QFieldCloud Migration Readiness Check Script
# Created: 2026-01-08
# Purpose: Verify system is ready for server migration

echo "=========================================="
echo "QFieldCloud Migration Readiness Check"
echo "Date: $(date)"
echo "Server: 72.61.166.168"
echo "=========================================="
echo ""

# Check if we can connect to server
if ! timeout 5 bash -c "echo > /dev/tcp/72.61.166.168/22" 2>/dev/null; then
    echo "❌ Cannot connect to server on port 22"
    exit 1
fi

# Function to run remote commands
run_remote() {
    ssh -o ConnectTimeout=5 -o StrictHostKeyChecking=no root@72.61.166.168 "$1" 2>/dev/null
}

# 1. Disk usage check
echo "📁 DISK USAGE CHECK"
echo "-------------------"
DISK_INFO=$(run_remote "df -h /")
DISK_USAGE=$(echo "$DISK_INFO" | awk 'NR==2 {print int($5)}')
DISK_USED=$(echo "$DISK_INFO" | awk 'NR==2 {print $3}')
DISK_TOTAL=$(echo "$DISK_INFO" | awk 'NR==2 {print $2}')
DISK_FREE=$(echo "$DISK_INFO" | awk 'NR==2 {print $4}')

if [ -n "$DISK_USAGE" ]; then
    if [ $DISK_USAGE -lt 70 ]; then
        echo "✅ Disk usage: ${DISK_USAGE}% (${DISK_USED}/${DISK_TOTAL}, ${DISK_FREE} free) - READY"
    elif [ $DISK_USAGE -lt 80 ]; then
        echo "⚠️  Disk usage: ${DISK_USAGE}% (${DISK_USED}/${DISK_TOTAL}, ${DISK_FREE} free) - CLEAN RECOMMENDED"
    else
        echo "❌ Disk usage: ${DISK_USAGE}% (${DISK_USED}/${DISK_TOTAL}, ${DISK_FREE} free) - CLEANUP REQUIRED!"
    fi
else
    echo "❌ Could not check disk usage"
fi
echo ""

# 2. Docker space usage
echo "🐳 DOCKER SPACE USAGE"
echo "---------------------"
DOCKER_SPACE=$(run_remote "docker system df")
if [ -n "$DOCKER_SPACE" ]; then
    echo "$DOCKER_SPACE" | head -5
    RECLAIMABLE=$(echo "$DOCKER_SPACE" | grep "RECLAIMABLE" -A 3 | tail -3 | awk '{print $4}' | paste -sd+ | bc 2>/dev/null || echo "0")
    if [ -n "$RECLAIMABLE" ] && [ "$RECLAIMABLE" != "0" ]; then
        echo "💡 Reclaimable space available - run 'docker system prune -af'"
    fi
else
    echo "❌ Could not check Docker space"
fi
echo ""

# 3. Database check
echo "🗄️  DATABASE STATUS"
echo "------------------"
DB_SIZE=$(run_remote "docker exec qfieldcloud-db-1 psql -U qfieldcloud_db_admin -d qfieldcloud_db -t -c \"SELECT pg_size_pretty(pg_database_size('qfieldcloud_db'));\" 2>/dev/null | xargs")
if [ -n "$DB_SIZE" ]; then
    echo "📊 Database size: $DB_SIZE"

    # Table sizes
    echo "📋 Largest tables:"
    run_remote "docker exec qfieldcloud-db-1 psql -U qfieldcloud_db_admin -d qfieldcloud_db -c \"
        SELECT schemaname||'.'||tablename AS table,
               pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size
        FROM pg_tables
        WHERE schemaname NOT IN ('pg_catalog', 'information_schema')
        ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC
        LIMIT 5;\" 2>/dev/null" | grep -v "+"
else
    echo "❌ Could not check database"
fi
echo ""

# 4. Job queue status
echo "📈 JOB QUEUE STATUS"
echo "-------------------"
QUEUE_STATUS=$(run_remote "docker exec qfieldcloud-db-1 psql -U qfieldcloud_db_admin -d qfieldcloud_db -t -c \"
    SELECT
        COUNT(CASE WHEN status IN ('pending','queued') THEN 1 END) as queued,
        COUNT(CASE WHEN status = 'started' THEN 1 END) as running,
        COUNT(CASE WHEN status = 'failed' AND created_at > NOW() - INTERVAL '1 hour' THEN 1 END) as recent_failed,
        COUNT(CASE WHEN status IN ('pending','queued') AND created_at < NOW() - INTERVAL '1 day' THEN 1 END) as stuck
    FROM core_job;\" 2>/dev/null")

if [ -n "$QUEUE_STATUS" ]; then
    QUEUED=$(echo "$QUEUE_STATUS" | awk -F'|' '{print $1}' | xargs)
    RUNNING=$(echo "$QUEUE_STATUS" | awk -F'|' '{print $2}' | xargs)
    FAILED=$(echo "$QUEUE_STATUS" | awk -F'|' '{print $3}' | xargs)
    STUCK=$(echo "$QUEUE_STATUS" | awk -F'|' '{print $4}' | xargs)

    echo "⏳ Queued jobs: $QUEUED"
    echo "🏃 Running jobs: $RUNNING"
    echo "❌ Failed (1hr): $FAILED"

    if [ "$STUCK" = "0" ]; then
        echo "✅ No stuck jobs"
    else
        echo "⚠️  Stuck jobs (>24h): $STUCK - Clean before migration!"
    fi
else
    echo "❌ Could not check job queue"
fi
echo ""

# 5. Container health
echo "🐋 CONTAINER STATUS"
echo "-------------------"
CONTAINERS=$(run_remote "docker ps --format 'table {{.Names}}\t{{.Status}}\t{{.State}}' | grep qfield")
if [ -n "$CONTAINERS" ]; then
    echo "$CONTAINERS" | while read line; do
        if echo "$line" | grep -q "Up"; then
            echo "✅ $line"
        else
            echo "❌ $line"
        fi
    done

    # Count workers
    WORKER_COUNT=$(echo "$CONTAINERS" | grep -c "worker_wrapper")
    echo ""
    echo "👷 Active workers: $WORKER_COUNT"
else
    echo "❌ Could not check containers"
fi
echo ""

# 6. Performance metrics (last 24h)
echo "📊 PERFORMANCE (24h)"
echo "-------------------"
PERF_STATS=$(run_remote "docker exec qfieldcloud-db-1 psql -U qfieldcloud_db_admin -d qfieldcloud_db -t -c \"
    SELECT
        COUNT(*) as total_jobs,
        ROUND(100.0 * COUNT(CASE WHEN status = 'finished' THEN 1 END) / NULLIF(COUNT(*), 0), 1) as success_rate,
        ROUND(AVG(CASE WHEN status = 'finished' THEN EXTRACT(EPOCH FROM (finished_at - started_at)) END)) as avg_duration_sec
    FROM core_job
    WHERE created_at > NOW() - INTERVAL '24 hours';\" 2>/dev/null")

if [ -n "$PERF_STATS" ]; then
    TOTAL=$(echo "$PERF_STATS" | awk -F'|' '{print $1}' | xargs)
    SUCCESS=$(echo "$PERF_STATS" | awk -F'|' '{print $2}' | xargs)
    DURATION=$(echo "$PERF_STATS" | awk -F'|' '{print $3}' | xargs)

    echo "📝 Total jobs: $TOTAL"
    echo "✅ Success rate: ${SUCCESS}%"
    echo "⏱️  Avg duration: ${DURATION}s"
else
    echo "❌ Could not check performance"
fi
echo ""

# 7. Log file sizes
echo "📄 LOG FILES"
echo "------------"
LOG_SIZES=$(run_remote "find /var/log -type f -name '*.log' -size +100M 2>/dev/null | head -5")
if [ -n "$LOG_SIZES" ]; then
    echo "Large log files (>100MB):"
    run_remote "find /var/log -type f -name '*.log' -size +100M -exec ls -lh {} \; 2>/dev/null | head -5" | awk '{print "  " $9 ": " $5}'
else
    echo "✅ No large log files"
fi
echo ""

# Final recommendation
echo "=========================================="
echo "MIGRATION READINESS ASSESSMENT"
echo "=========================================="

READY=true
WARNINGS=""
CRITICALS=""

# Check critical conditions
if [ -n "$DISK_USAGE" ] && [ $DISK_USAGE -gt 85 ]; then
    READY=false
    CRITICALS="${CRITICALS}❌ Disk usage too high ($DISK_USAGE%)\n"
fi

if [ -n "$STUCK" ] && [ "$STUCK" != "0" ]; then
    READY=false
    CRITICALS="${CRITICALS}❌ Stuck jobs need clearing ($STUCK jobs)\n"
fi

# Check warning conditions
if [ -n "$DISK_USAGE" ] && [ $DISK_USAGE -gt 70 ] && [ $DISK_USAGE -le 85 ]; then
    WARNINGS="${WARNINGS}⚠️  Disk cleanup recommended ($DISK_USAGE%)\n"
fi

if [ -n "$SUCCESS" ] && [ "${SUCCESS%.*}" -lt 90 ]; then
    WARNINGS="${WARNINGS}⚠️  Low success rate (${SUCCESS}%)\n"
fi

# Print results
if [ "$READY" = true ] && [ -z "$WARNINGS" ]; then
    echo "✅ SYSTEM IS READY FOR MIGRATION"
    echo ""
    echo "All checks passed. Safe to proceed with migration."
elif [ "$READY" = true ] && [ -n "$WARNINGS" ]; then
    echo "⚠️  READY WITH WARNINGS"
    echo ""
    echo "Warnings:"
    echo -e "$WARNINGS"
    echo "Consider addressing these before migration."
else
    echo "❌ NOT READY FOR MIGRATION"
    echo ""
    echo "Critical issues:"
    echo -e "$CRITICALS"
    if [ -n "$WARNINGS" ]; then
        echo "Warnings:"
        echo -e "$WARNINGS"
    fi
    echo "Address critical issues before proceeding."
fi

echo "=========================================="
echo ""
echo "📋 Next steps:"
if [ -n "$DISK_USAGE" ] && [ $DISK_USAGE -gt 70 ]; then
    echo "1. Run disk cleanup: docker system prune -af --volumes"
fi
if [ -n "$STUCK" ] && [ "$STUCK" != "0" ]; then
    echo "2. Clear stuck jobs from database"
fi
echo "3. Run database optimization (VACUUM FULL)"
echo "4. Archive old project files"
echo "5. Document configuration and take backups"
echo ""
echo "Full plan: /home/louisdup/Agents/claude/.claude/skills/qfieldcloud/MIGRATION_PLAN.md"