#!/usr/bin/env python3
"""
QFieldCloud Worker Monitoring Daemon
Continuously monitors worker health and performs automatic recovery actions.
Integrates with the existing prevention system.
"""

import subprocess
import json
import time
import logging
import sys
from datetime import datetime, timedelta
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/var/log/qfield_worker_monitor.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Configuration
CHECK_INTERVAL = 60  # Check every minute
RESTART_THRESHOLD = 3  # Restart after 3 consecutive failures
ALERT_THRESHOLD = 5  # Alert after 5 failures in an hour
MEMORY_LIMIT_MB = 500  # Restart if worker uses >500MB
QUEUE_STUCK_MINUTES = 10  # Jobs stuck longer trigger intervention

class WorkerMonitor:
    def __init__(self):
        self.failure_count = 0
        self.last_restart = None
        self.hourly_failures = []
        self.project_path = "/home/louisdup/VF/Apps/QFieldCloud"

    def run_command(self, cmd, capture=True):
        """Execute shell command"""
        try:
            result = subprocess.run(cmd, shell=True, capture_output=capture, text=True)
            return result.stdout.strip(), result.returncode
        except Exception as e:
            logger.error(f"Command failed: {cmd}, Error: {e}")
            return str(e), 1

    def check_worker_running(self):
        """Check if worker container is running"""
        output, rc = self.run_command("docker ps --format '{{.Names}}' | grep -E 'worker_wrapper|qfieldcloud-worker'")
        return bool(output)

    def get_worker_stats(self):
        """Get worker resource usage"""
        output, rc = self.run_command(
            "docker stats qfieldcloud-worker --no-stream --format '{{json .}}'"
        )
        if rc == 0 and output:
            try:
                stats = json.loads(output)
                # Parse memory (e.g., "120MiB / 7.8GiB")
                mem_usage = stats.get('MemUsage', '0MiB').split(' / ')[0]
                mem_mb = float(mem_usage.replace('MiB', '').replace('GiB', '000'))
                return {
                    'memory_mb': mem_mb,
                    'cpu_percent': float(stats.get('CPUPerc', '0').replace('%', ''))
                }
            except Exception as e:
                logger.error(f"Failed to parse stats: {e}")
        return None

    def check_worker_health(self):
        """Comprehensive worker health check"""
        health = {
            'running': False,
            'memory_ok': True,
            'processing': False,
            'queue_healthy': True,
            'last_activity': None
        }

        # Check if running
        health['running'] = self.check_worker_running()
        if not health['running']:
            return health

        # Check resource usage
        stats = self.get_worker_stats()
        if stats:
            health['memory_ok'] = stats['memory_mb'] < MEMORY_LIMIT_MB
            if not health['memory_ok']:
                logger.warning(f"Worker memory high: {stats['memory_mb']}MB")

        # Check recent logs for activity
        logs, _ = self.run_command(
            "docker logs qfieldcloud-worker --tail 100 --since '5m' 2>&1 | grep 'Dequeue'"
        )
        health['last_activity'] = bool(logs)

        # Check for stuck jobs
        stuck_jobs, _ = self.run_command(f"""
            docker exec qfieldcloud-db-1 psql -U qfieldcloud_db_admin -d qfieldcloud_db -t -c "
                SELECT COUNT(*) FROM core_job
                WHERE status IN ('pending', 'queued')
                AND created_at < NOW() - INTERVAL '{QUEUE_STUCK_MINUTES} minutes';"
        """)
        try:
            stuck_count = int(stuck_jobs.strip() or 0)
            health['queue_healthy'] = stuck_count == 0
            if not health['queue_healthy']:
                logger.warning(f"Found {stuck_count} stuck jobs")
        except:
            pass

        return health

    def restart_worker(self, reason="Manual restart"):
        """Restart the worker container"""
        logger.info(f"Restarting worker: {reason}")

        # Stop existing worker
        self.run_command("docker stop qfieldcloud-worker", capture=False)
        self.run_command("docker rm qfieldcloud-worker", capture=False)

        # Get database container name
        db_container, _ = self.run_command(
            "docker ps --format '{{.Names}}' | grep -E 'db|postgres' | head -1"
        )

        if not db_container:
            logger.error("Database not running, cannot start worker")
            return False

        # Start worker with correct configuration
        cmd = f"""docker run -d \
            --name qfieldcloud-worker \
            --user root \
            --network qfieldcloud_default \
            -v /var/run/docker.sock:/var/run/docker.sock \
            -v {self.project_path}/mediafiles:/usr/src/app/mediafiles \
            -e DJANGO_SETTINGS_MODULE=qfieldcloud.settings \
            -e POSTGRES_HOST={db_container} \
            -e POSTGRES_DB=qfieldcloud_db \
            -e POSTGRES_USER=qfieldcloud_db_admin \
            -e POSTGRES_PASSWORD=3shJDd2r7Twwkehb \
            qfieldcloud-worker_wrapper:latest \
            python manage.py dequeue"""

        output, rc = self.run_command(cmd)
        if rc == 0:
            logger.info(f"Worker restarted successfully: {output[:12]}")
            self.last_restart = datetime.now()
            self.failure_count = 0
            return True
        else:
            logger.error(f"Failed to restart worker: {output}")
            return False

    def send_alert(self, message):
        """Send alert (can be extended to send email/Slack/etc)"""
        logger.critical(f"ALERT: {message}")

        # Write to alert file for external monitoring
        alert_file = Path('/var/log/qfield_worker_alerts.log')
        with alert_file.open('a') as f:
            f.write(f"{datetime.now().isoformat()} - {message}\n")

        # Could add email/Slack notification here
        # Example: Send to WhatsApp via wa-monitor
        try:
            self.run_command(f"""
                curl -X POST http://100.96.203.105:8081/send-message \
                    -H "Content-Type: application/json" \
                    -d '{{"to": "27711558396", "message": "QField Worker Alert: {message}"}}'
            """)
        except:
            pass  # Don't fail if WhatsApp service is down

    def clean_stuck_jobs(self):
        """Clean up jobs stuck in queue too long"""
        logger.info("Cleaning stuck jobs")

        cleanup_sql = f"""
            UPDATE core_job
            SET status = 'failed',
                finished_at = NOW(),
                output = 'Auto-cleanup: stuck >{QUEUE_STUCK_MINUTES} minutes'
            WHERE status IN ('pending', 'queued')
            AND created_at < NOW() - INTERVAL '{QUEUE_STUCK_MINUTES} minutes'
            RETURNING id;
        """

        output, rc = self.run_command(
            f'docker exec qfieldcloud-db-1 psql -U qfieldcloud_db_admin -d qfieldcloud_db -c "{cleanup_sql}"'
        )

        if rc == 0:
            lines = output.strip().split('\n')
            if len(lines) > 2:  # Has results
                count = len([l for l in lines if l.strip() and not l.startswith('id') and not l.startswith('-')])
                if count > 0:
                    logger.info(f"Cleaned up {count} stuck jobs")

    def monitor_loop(self):
        """Main monitoring loop"""
        logger.info("Starting QFieldCloud Worker Monitor Daemon")

        while True:
            try:
                health = self.check_worker_health()

                # Log current status
                logger.debug(f"Worker health: {health}")

                # Track failures for alerting
                if not health['running']:
                    self.failure_count += 1
                    self.hourly_failures.append(datetime.now())

                    # Clean old hourly failures
                    cutoff = datetime.now() - timedelta(hours=1)
                    self.hourly_failures = [f for f in self.hourly_failures if f > cutoff]

                    # Send alert if threshold exceeded
                    if len(self.hourly_failures) >= ALERT_THRESHOLD:
                        self.send_alert(f"Worker failed {len(self.hourly_failures)} times in the last hour")
                        self.hourly_failures = []  # Reset after alert

                # Perform interventions
                if not health['running']:
                    if self.failure_count >= RESTART_THRESHOLD:
                        logger.warning(f"Worker down for {self.failure_count} checks, restarting")
                        if self.restart_worker("Worker not running"):
                            time.sleep(10)  # Give it time to start
                        else:
                            self.send_alert("Failed to restart worker after multiple attempts")

                elif not health['memory_ok']:
                    logger.warning("Worker memory exceeded limit, restarting")
                    self.restart_worker("Memory limit exceeded")

                elif not health['queue_healthy']:
                    logger.warning("Stuck jobs detected, cleaning and restarting worker")
                    self.clean_stuck_jobs()
                    self.restart_worker("Stuck jobs detected")

                elif not health['last_activity'] and health['running']:
                    # Worker running but no recent activity - might be hung
                    logger.info("Worker appears idle/hung, checking queue")
                    queue_size, _ = self.run_command("""
                        docker exec qfieldcloud-db-1 psql -U qfieldcloud_db_admin -d qfieldcloud_db -t -c "
                            SELECT COUNT(*) FROM core_job WHERE status IN ('pending', 'queued');"
                    """)
                    try:
                        if int(queue_size.strip() or 0) > 0:
                            logger.warning("Worker idle with jobs in queue, restarting")
                            self.restart_worker("Worker idle with pending jobs")
                    except:
                        pass

                # Reset failure count on successful check
                if health['running']:
                    self.failure_count = 0

            except Exception as e:
                logger.error(f"Monitor loop error: {e}")

            # Sleep before next check
            time.sleep(CHECK_INTERVAL)

    def ensure_worker_built(self):
        """Ensure worker image exists before starting monitor"""
        output, _ = self.run_command("docker images | grep worker_wrapper")
        if not output:
            logger.info("Worker image not found, building (this will take 10-15 minutes)...")
            self.run_command(f"cd {self.project_path} && docker compose build worker_wrapper", capture=False)

def main():
    """Main entry point"""
    monitor = WorkerMonitor()

    # Ensure worker image exists
    monitor.ensure_worker_built()

    # Start monitoring
    try:
        monitor.monitor_loop()
    except KeyboardInterrupt:
        logger.info("Monitor daemon stopped by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Monitor daemon crashed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()