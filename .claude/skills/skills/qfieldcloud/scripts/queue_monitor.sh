#!/bin/bash
# Queue monitoring script - runs every 5 minutes via cron
# Tracks queue depth, processing count, and failure rate
# Logs to CSV format for easy analysis

TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')
LOG_FILE="/var/log/qfieldcloud/queue_metrics.log"

# Create log directory if needed
mkdir -p /var/log/qfieldcloud

# Query database
QUEUE_DEPTH=$(docker exec qfieldcloud-db-1 psql -U qfieldcloud_db_admin -d qfieldcloud_db -t -c \
  "SELECT COUNT(*) FROM core_job WHERE status IN ('pending', 'queued');" | xargs)

PROCESSING=$(docker exec qfieldcloud-db-1 psql -U qfieldcloud_db_admin -d qfieldcloud_db -t -c \
  "SELECT COUNT(*) FROM core_job WHERE status = 'started';" | xargs)

FAILED_LAST_HOUR=$(docker exec qfieldcloud-db-1 psql -U qfieldcloud_db_admin -d qfieldcloud_db -t -c \
  "SELECT COUNT(*) FROM core_job WHERE status = 'failed' AND created_at > NOW() - INTERVAL '1 hour';" | xargs)

# Log results (CSV format for easy analysis)
echo "$TIMESTAMP,$QUEUE_DEPTH,$PROCESSING,$FAILED_LAST_HOUR" >> "$LOG_FILE"

# Alert if queue is too deep
if [ "$QUEUE_DEPTH" -gt 10 ]; then
  echo "$TIMESTAMP WARNING: Queue depth is $QUEUE_DEPTH (>10 jobs waiting)" | \
    tee -a /var/log/qfieldcloud/alerts.log
fi

# Alert if no workers processing but queue has jobs
if [ "$PROCESSING" -eq 0 ] && [ "$QUEUE_DEPTH" -gt 0 ]; then
  echo "$TIMESTAMP ERROR: No workers processing but $QUEUE_DEPTH jobs waiting!" | \
    tee -a /var/log/qfieldcloud/alerts.log
fi
