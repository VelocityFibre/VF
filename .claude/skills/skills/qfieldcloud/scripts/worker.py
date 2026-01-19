#!/usr/bin/env python3
"""
QFieldCloud Worker Management Tool
Manages the critical worker_wrapper service needed for sync operations.
"""

import subprocess
import sys
import time
import argparse

def run_command(cmd, capture=True):
    """Execute shell command and return output"""
    try:
        if capture:
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            return result.stdout.strip(), result.returncode
        else:
            subprocess.run(cmd, shell=True)
            return "", 0
    except Exception as e:
        return str(e), 1

def status():
    """Check worker status"""
    print("🔍 Worker Status:")

    # Check if running
    output, _ = run_command("docker ps --format '{{.Names}} {{.Status}}' | grep worker")
    if output:
        print(f"  ✅ Running: {output}")

        # Check logs for errors
        logs, _ = run_command("docker logs qfieldcloud-worker --tail 5 2>&1 | grep -E 'ERROR|WARNING'")
        if logs:
            print(f"  ⚠️  Recent warnings/errors detected")
    else:
        print("  ❌ Not running")

        # Check if container exists but stopped
        output, _ = run_command("docker ps -a --format '{{.Names}} {{.Status}}' | grep worker")
        if output and "Exited" in output:
            print(f"  ⚠️  Container stopped: {output}")

def build():
    """Build worker image"""
    print("🔨 Building worker image...")
    print("  ⏱️  This takes 10-15 minutes (installs GDAL, GEOS, PostGIS...)")

    project_path = "/home/louisdup/VF/Apps/QFieldCloud"
    cmd = f"cd {project_path} && docker compose build worker_wrapper"
    print(f"  Running: {cmd}")
    run_command(cmd, capture=False)

    # Verify build
    output, _ = run_command("docker images | grep worker_wrapper")
    if output:
        print("  ✅ Build successful")
    else:
        print("  ❌ Build failed")
        sys.exit(1)

def start():
    """Start worker service"""
    print("🚀 Starting worker...")

    # Check if already running
    output, _ = run_command("docker ps --format '{{.Names}}' | grep worker")
    if output:
        print("  ⚠️  Worker already running")
        return

    # Check if image exists
    output, _ = run_command("docker images | grep worker_wrapper")
    if not output:
        print("  ❌ Worker image not found. Building first...")
        build()

    # Get database container
    db_container, _ = run_command("docker ps --format '{{.Names}}' | grep -E 'db|postgres' | head -1")
    if not db_container:
        print("  ❌ Database not running. Start it first:")
        print("     docker start <database-container-name>")
        sys.exit(1)

    project_path = "/home/louisdup/VF/Apps/QFieldCloud"

    # Remove old container if exists
    run_command("docker rm -f qfieldcloud-worker 2>/dev/null")

    # Start with proper configuration
    cmd = f"""docker run -d \
        --name qfieldcloud-worker \
        --user root \
        --network qfieldcloud_default \
        -v /var/run/docker.sock:/var/run/docker.sock \
        -v {project_path}/mediafiles:/usr/src/app/mediafiles \
        -e DJANGO_SETTINGS_MODULE=qfieldcloud.settings \
        -e POSTGRES_HOST={db_container} \
        -e POSTGRES_DB=qfieldcloud_db \
        -e POSTGRES_USER=qfieldcloud_db_admin \
        -e POSTGRES_PASSWORD=3shJDd2r7Twwkehb \
        qfieldcloud-worker_wrapper:latest \
        python manage.py dequeue"""

    output, rc = run_command(cmd)
    if rc == 0:
        print(f"  ✅ Worker started: {output[:12]}...")

        # Wait and check if it's still running
        time.sleep(5)
        output, _ = run_command("docker ps | grep worker")
        if output:
            print("  ✅ Worker is running")
        else:
            print("  ❌ Worker crashed. Check logs:")
            print("     docker logs qfieldcloud-worker")
    else:
        print(f"  ❌ Failed to start: {output}")

def stop():
    """Stop worker service"""
    print("🛑 Stopping worker...")
    output, rc = run_command("docker stop qfieldcloud-worker")
    if rc == 0:
        print("  ✅ Worker stopped")
        run_command("docker rm qfieldcloud-worker")
    else:
        print("  ⚠️  Worker not running")

def restart():
    """Restart worker service"""
    print("🔄 Restarting worker...")
    stop()
    time.sleep(2)
    start()

def logs(lines=50, follow=False):
    """View worker logs"""
    print(f"📜 Worker logs (last {lines} lines):")

    cmd = f"docker logs qfieldcloud-worker --tail {lines}"
    if follow:
        cmd += " -f"

    run_command(cmd, capture=False)

def monitor():
    """Monitor worker health in real-time"""
    print("📊 Monitoring worker (Ctrl+C to stop)...")

    try:
        while True:
            # Check if running
            output, _ = run_command("docker ps --format '{{.Names}}' | grep worker")

            if output:
                # Get job count
                logs, _ = run_command("docker logs qfieldcloud-worker --tail 100 | grep 'Jobs from the DB' | tail -1")

                # Get memory usage
                stats, _ = run_command("docker stats qfieldcloud-worker --no-stream --format '{{.MemUsage}}'")

                print(f"\r✅ Worker running | Memory: {stats} | Last activity: {logs[:50]}...", end="")
            else:
                print("\r❌ Worker not running                                                  ", end="")

            time.sleep(5)
    except KeyboardInterrupt:
        print("\n👋 Monitoring stopped")

def main():
    parser = argparse.ArgumentParser(description="QFieldCloud Worker Management")
    parser.add_argument('action',
                       choices=['status', 'build', 'start', 'stop', 'restart', 'logs', 'monitor'],
                       help='Action to perform')
    parser.add_argument('--lines', type=int, default=50, help='Number of log lines to show')
    parser.add_argument('--follow', action='store_true', help='Follow log output')

    args = parser.parse_args()

    if args.action == 'status':
        status()
    elif args.action == 'build':
        build()
    elif args.action == 'start':
        start()
    elif args.action == 'stop':
        stop()
    elif args.action == 'restart':
        restart()
    elif args.action == 'logs':
        logs(args.lines, args.follow)
    elif args.action == 'monitor':
        monitor()

if __name__ == "__main__":
    main()