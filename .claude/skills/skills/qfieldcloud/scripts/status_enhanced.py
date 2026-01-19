#!/usr/bin/env python3
"""
Enhanced QFieldCloud Status Dashboard
Includes comprehensive worker health monitoring and sync readiness checks.
"""

import subprocess
import json
import sys
from datetime import datetime, timedelta
from pathlib import Path

# Terminal colors
GREEN = '\033[92m'
YELLOW = '\033[93m'
RED = '\033[91m'
BLUE = '\033[94m'
BOLD = '\033[1m'
RESET = '\033[0m'

def run_command(cmd, capture=True):
    """Execute shell command"""
    try:
        result = subprocess.run(cmd, shell=True, capture_output=capture, text=True)
        return result.stdout.strip(), result.returncode
    except Exception as e:
        return str(e), 1

def format_status(status, text=""):
    """Format status with color"""
    if status == "ok":
        return f"{GREEN}✅ {text}{RESET}"
    elif status == "warning":
        return f"{YELLOW}⚠️  {text}{RESET}"
    elif status == "error":
        return f"{RED}❌ {text}{RESET}"
    elif status == "info":
        return f"{BLUE}ℹ️  {text}{RESET}"
    return text

def check_docker_services():
    """Check all QFieldCloud Docker services"""
    print(f"\n{BOLD}=== DOCKER SERVICES ==={RESET}")

    services = {
        'app': {'pattern': 'qfieldcloud.*app', 'critical': True},
        'database': {'pattern': 'db|postgres', 'critical': True},
        'nginx': {'pattern': 'nginx', 'critical': False},
        'redis': {'pattern': 'redis', 'critical': False},
        'memcached': {'pattern': 'memcached', 'critical': True},
        'worker': {'pattern': 'worker_wrapper|qfieldcloud-worker', 'critical': True},
    }

    all_good = True
    critical_good = True

    for name, config in services.items():
        output, _ = run_command(f"docker ps --format '{{{{.Names}}}} {{{{.Status}}}}' | grep -E '{config['pattern']}'")

        if output:
            container_info = output.split('\n')[0].split()
            container_name = container_info[0]
            uptime = ' '.join(container_info[1:])
            print(format_status("ok", f"{name:<12} {container_name:<30} {uptime}"))
        else:
            if config['critical']:
                print(format_status("error", f"{name:<12} NOT RUNNING (CRITICAL)"))
                critical_good = False
                all_good = False
            else:
                print(format_status("warning", f"{name:<12} NOT RUNNING"))
                all_good = False

    return all_good, critical_good

def check_worker_health():
    """Detailed worker health check"""
    print(f"\n{BOLD}=== WORKER HEALTH ==={RESET}")

    # Check if worker exists
    output, _ = run_command("docker ps -a --format '{{.Names}} {{.Status}}' | grep -E 'worker'")

    if not output:
        print(format_status("error", "No worker container found"))
        print(format_status("info", "Build with: docker compose build worker_wrapper"))
        return False

    container_info = output.split('\n')[0]

    if "Up" in container_info:
        print(format_status("ok", f"Worker running: {container_info}"))

        # Check resource usage
        stats, _ = run_command("docker stats qfieldcloud-worker --no-stream --format '{{json .}}'")
        if stats:
            try:
                data = json.loads(stats)
                mem_usage = data.get('MemUsage', '0MiB').split(' / ')[0]
                cpu = data.get('CPUPerc', '0%')
                print(format_status("info", f"Resources: Memory {mem_usage}, CPU {cpu}"))

                # Check if memory is high
                mem_mb = float(mem_usage.replace('MiB', '').replace('GiB', '000'))
                if mem_mb > 500:
                    print(format_status("warning", f"High memory usage: {mem_mb}MB"))
            except:
                pass

        # Check recent activity
        logs, _ = run_command("docker logs qfieldcloud-worker --tail 100 --since '5m' 2>&1 | grep 'Dequeue' | tail -1")
        if logs:
            print(format_status("ok", f"Recent activity: {logs[:80]}..."))
        else:
            print(format_status("warning", "No recent activity (might be idle)"))

        # Check for errors
        errors, _ = run_command("docker logs qfieldcloud-worker --tail 100 2>&1 | grep -E 'ERROR|CRITICAL' | tail -3")
        if errors:
            print(format_status("warning", "Recent errors detected:"))
            for line in errors.split('\n'):
                if line:
                    print(f"  {RED}{line[:100]}{RESET}")

        return True
    else:
        print(format_status("error", f"Worker stopped: {container_info}"))

        # Get last logs
        logs, _ = run_command("docker logs qfieldcloud-worker --tail 10 2>&1")
        if "Permission denied" in logs:
            print(format_status("error", "Docker socket permission issue"))
            print(format_status("info", "Fix: Run with --user root"))
        elif "could not translate host name" in logs:
            print(format_status("error", "Database connectivity issue"))
            print(format_status("info", "Fix: Check database container name"))

        return False

def check_queue_status():
    """Check job queue status"""
    print(f"\n{BOLD}=== QUEUE STATUS ==={RESET}")

    # Check if database is accessible
    db_container, _ = run_command("docker ps --format '{{.Names}}' | grep -E 'db|postgres' | head -1")

    if not db_container:
        print(format_status("error", "Database not running, cannot check queue"))
        return False

    # Get queue metrics
    queries = {
        'Pending/Queued': "SELECT COUNT(*) FROM core_job WHERE status IN ('pending', 'queued');",
        'Processing': "SELECT COUNT(*) FROM core_job WHERE status = 'started';",
        'Failed (1hr)': "SELECT COUNT(*) FROM core_job WHERE status = 'failed' AND created_at > NOW() - INTERVAL '1 hour';",
        'Stuck (>10min)': f"SELECT COUNT(*) FROM core_job WHERE status IN ('pending', 'queued') AND created_at < NOW() - INTERVAL '10 minutes';"
    }

    all_good = True
    for label, query in queries.items():
        output, rc = run_command(
            f'docker exec {db_container} psql -U qfieldcloud_db_admin -d qfieldcloud_db -t -c "{query}"'
        )

        if rc == 0:
            try:
                count = int(output.strip() or 0)
                if label == 'Pending/Queued' and count > 10:
                    print(format_status("warning", f"{label:<15} {count} (high)"))
                    all_good = False
                elif label == 'Stuck (>10min)' and count > 0:
                    print(format_status("error", f"{label:<15} {count} (needs cleanup)"))
                    all_good = False
                elif label == 'Failed (1hr)' and count > 5:
                    print(format_status("warning", f"{label:<15} {count} (investigate)"))
                    all_good = False
                else:
                    print(format_status("ok", f"{label:<15} {count}"))
            except:
                print(format_status("error", f"{label:<15} Error"))
                all_good = False
        else:
            print(format_status("error", f"{label:<15} Query failed"))
            all_good = False

    return all_good

def check_sync_readiness():
    """Overall sync readiness assessment"""
    print(f"\n{BOLD}=== SYNC READINESS ==={RESET}")

    readiness = {
        'API Server': False,
        'Database': False,
        'Cache': False,
        'Worker': False,
        'Queue': False
    }

    # Check each component
    output, _ = run_command("docker ps --format '{{.Names}}' | grep -E 'app'")
    readiness['API Server'] = bool(output)

    output, _ = run_command("docker ps --format '{{.Names}}' | grep -E 'db|postgres'")
    readiness['Database'] = bool(output)

    output, _ = run_command("docker ps --format '{{.Names}}' | grep memcached")
    readiness['Cache'] = bool(output)

    output, _ = run_command("docker ps --format '{{.Names}}' | grep -E 'worker'")
    readiness['Worker'] = bool(output)

    # Check queue health
    db_container, _ = run_command("docker ps --format '{{.Names}}' | grep -E 'db|postgres' | head -1")
    if db_container:
        stuck, rc = run_command(
            f'docker exec {db_container} psql -U qfieldcloud_db_admin -d qfieldcloud_db -t -c '
            f'"SELECT COUNT(*) FROM core_job WHERE status IN (\'pending\', \'queued\') AND created_at < NOW() - INTERVAL \'10 minutes\';"'
        )
        try:
            readiness['Queue'] = int(stuck.strip() or 0) == 0
        except:
            readiness['Queue'] = False

    # Display results
    all_ready = all(readiness.values())

    for component, ready in readiness.items():
        if ready:
            print(format_status("ok", f"{component:<15} Ready"))
        else:
            print(format_status("error", f"{component:<15} Not Ready"))

    # Overall verdict
    print(f"\n{BOLD}=== OVERALL STATUS ==={RESET}")

    if all_ready:
        print(format_status("ok", "SYNC FULLY OPERATIONAL"))

        # Get local IP for configuration
        local_ip, _ = run_command("hostname -I | awk '{print $1}'")
        print(f"\n{BOLD}QField App Configuration:{RESET}")
        print(f"  Server URL: http://{local_ip}:8011")
        print(f"  Use QFieldCloud credentials to login")
    else:
        print(format_status("error", "SYNC NOT READY"))
        print(f"\n{BOLD}Required Actions:{RESET}")

        if not readiness['Worker']:
            print("  1. Start worker: docker compose up -d worker_wrapper")
        if not readiness['Database']:
            print("  2. Start database: docker compose up -d db")
        if not readiness['API Server']:
            print("  3. Start API: docker compose up -d app")
        if not readiness['Queue']:
            print("  4. Clean stuck jobs: .claude/skills/qfieldcloud/scripts/clean_stuck_jobs.py")

    return all_ready

def check_monitoring_status():
    """Check if monitoring services are active"""
    print(f"\n{BOLD}=== MONITORING STATUS ==={RESET}")

    # Check systemd services
    services_to_check = [
        ('qfield-worker.service', 'Worker Service'),
        ('qfield-worker-monitor.service', 'Monitor Daemon'),
        ('qfield-monitor.service', 'Prevention System')
    ]

    for service, name in services_to_check:
        output, rc = run_command(f"systemctl is-active {service}")
        if output == "active":
            print(format_status("ok", f"{name:<20} Active"))
        elif output == "inactive":
            print(format_status("warning", f"{name:<20} Inactive"))
        else:
            print(format_status("info", f"{name:<20} Not installed"))

    # Check for alert logs
    alert_file = Path('/var/log/qfield_worker_alerts.log')
    if alert_file.exists():
        # Get recent alerts
        output, _ = run_command(f"tail -5 {alert_file}")
        if output:
            print(format_status("warning", "Recent Alerts:"))
            for line in output.split('\n'):
                if line:
                    print(f"  {YELLOW}{line}{RESET}")

def show_quick_fixes():
    """Show quick fix commands"""
    print(f"\n{BOLD}=== QUICK FIXES ==={RESET}")
    print(f"{BLUE}If sync isn't working:{RESET}")
    print("  .claude/skills/qfieldcloud/scripts/sync_diagnostic.py")
    print("")
    print(f"{BLUE}Restart worker:{RESET}")
    print("  .claude/skills/qfieldcloud/scripts/worker.py restart")
    print("")
    print(f"{BLUE}Install monitoring:{RESET}")
    print("  sudo cp .claude/skills/qfieldcloud/scripts/qfield-worker*.service /etc/systemd/system/")
    print("  sudo systemctl daemon-reload")
    print("  sudo systemctl enable --now qfield-worker-monitor.service")
    print("")
    print(f"{BLUE}View logs:{RESET}")
    print("  docker logs -f qfieldcloud-worker")
    print("  journalctl -u qfield-worker-monitor -f")

def main():
    """Main status check flow"""
    print(f"{BOLD}{'='*60}{RESET}")
    print(f"{BOLD}      QFIELDCLOUD STATUS DASHBOARD      {RESET}")
    print(f"{BOLD}{'='*60}{RESET}")

    # Run all checks
    services_ok, critical_ok = check_docker_services()
    worker_ok = check_worker_health()
    queue_ok = check_queue_status()
    sync_ready = check_sync_readiness()
    check_monitoring_status()

    # Show fixes if needed
    if not sync_ready:
        show_quick_fixes()

    # Exit code
    sys.exit(0 if sync_ready else 1)

if __name__ == "__main__":
    main()