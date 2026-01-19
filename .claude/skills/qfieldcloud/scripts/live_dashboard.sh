#!/bin/bash
# Live dashboard - run manually to watch queue in real-time
# Updates every 5 seconds with current queue status, worker activity, and system resources

while true; do
  clear
  echo "========================================"
  echo "QFieldCloud Live Dashboard"
  echo "Time: $(date '+%Y-%m-%d %H:%M:%S')"
  echo "========================================"

  echo ""
  echo "--- Queue Status ---"
  docker exec qfieldcloud-db-1 psql -U qfieldcloud_db_admin -d qfieldcloud_db -t -c \
    "SELECT
       'Pending/Queued: ' || COUNT(*)
     FROM core_job
     WHERE status IN ('pending', 'queued');"

  docker exec qfieldcloud-db-1 psql -U qfieldcloud_db_admin -d qfieldcloud_db -t -c \
    "SELECT
       'Processing: ' || COUNT(*)
     FROM core_job
     WHERE status = 'started';"

  echo ""
  echo "--- Worker CPU/Memory ---"
  docker stats --no-stream --format \
    "{{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}" | \
    grep worker_wrapper

  echo ""
  echo "--- System Load ---"
  top -bn1 | grep "Cpu\|Mem" | head -2

  echo ""
  echo "Press Ctrl+C to exit. Refreshing in 5 seconds..."
  sleep 5
done
