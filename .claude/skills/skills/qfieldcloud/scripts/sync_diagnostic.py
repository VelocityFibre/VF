#!/usr/bin/env python3
"""
QFieldCloud Sync Diagnostic Tool
Diagnoses and fixes common sync issues, especially missing worker services.
"""

import subprocess
import sys
import json
import time

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

def check_docker_services():
    """Check status of required Docker services for sync"""
    print("🔍 Checking Docker services...")

    required_services = {
        'app': {'pattern': 'qfieldcloud.*app', 'critical': True},
        'database': {'pattern': 'qfieldcloud.*db|postgres', 'critical': True},
        'memcached': {'pattern': 'memcached', 'critical': True},
        'worker': {'pattern': 'worker_wrapper|worker', 'critical': True},  # MOST IMPORTANT FOR SYNC
    }

    status = {}
    for service, config in required_services.items():
        output, _ = run_command(f"docker ps --format '{{{{.Names}}}}' | grep -E '{config['pattern']}'")
        if output:
            status[service] = {'running': True, 'container': output.split('\n')[0]}
            print(f"  ✅ {service}: {output.split()[0] if output else 'Not found'}")
        else:
            status[service] = {'running': False}
            emoji = "❌" if config['critical'] else "⚠️"
            print(f"  {emoji} {service}: NOT RUNNING {'(CRITICAL FOR SYNC)' if config['critical'] else ''}")

    return status

def diagnose_worker_issue():
    """Diagnose why worker isn't running"""
    print("\n🔬 Diagnosing worker issues...")

    # Check if worker image exists
    output, _ = run_command("docker images | grep worker_wrapper")
    if not output:
        print("  ❌ Worker image not built")
        return "not_built"

    # Check if worker container exists but stopped
    output, _ = run_command("docker ps -a | grep worker")
    if output and "Exited" in output:
        print("  ⚠️  Worker container exists but stopped")
        # Get logs from stopped container
        container_name = output.split()[0]
        logs, _ = run_command(f"docker logs {container_name} --tail 20")
        if "Permission denied" in logs:
            print("  ❌ Docker socket permission issue")
            return "permission_issue"
        elif "could not translate host name" in logs or "could not connect" in logs:
            print("  ❌ Database connectivity issue")
            return "database_issue"
        elif "port is already allocated" in logs:
            print("  ❌ Port conflict (worker doesn't need port mapping)")
            return "port_conflict"
        else:
            print(f"  ❌ Unknown error: {logs[:200]}")
            return "unknown"

    if not output:
        print("  ⚠️  No worker container found")
        return "not_created"

    return "running"

def fix_worker(issue_type):
    """Attempt to fix worker based on issue type"""
    print(f"\n🔧 Attempting to fix: {issue_type}")

    project_path = "/home/louisdup/VF/Apps/QFieldCloud"

    if issue_type == "not_built":
        print("  📦 Building worker image (this will take 10-15 minutes)...")
        print("  ℹ️  The build installs geospatial dependencies (GDAL, GEOS, etc)")
        cmd = f"cd {project_path} && docker compose build worker_wrapper"
        print(f"  Running: {cmd}")
        run_command(cmd, capture=False)

    elif issue_type == "not_created" or issue_type == "permission_issue":
        # Get database container name
        db_container, _ = run_command("docker ps --format '{{.Names}}' | grep -E 'db|postgres' | head -1")
        if not db_container:
            print("  ❌ Cannot start worker: Database not running")
            return False

        print(f"  🚀 Starting worker container...")
        cmd = f"""cd {project_path} && docker run -d \\
            --name qfieldcloud-worker \\
            --user root \\
            --network qfieldcloud_default \\
            -v /var/run/docker.sock:/var/run/docker.sock \\
            -e DJANGO_SETTINGS_MODULE=qfieldcloud.settings \\
            -e POSTGRES_HOST={db_container} \\
            -e POSTGRES_DB=qfieldcloud_db \\
            -e POSTGRES_USER=qfieldcloud_db_admin \\
            -e POSTGRES_PASSWORD=3shJDd2r7Twwkehb \\
            qfieldcloud-worker_wrapper:latest \\
            python manage.py dequeue"""
        print(f"  Running: {cmd}")
        output, rc = run_command(cmd)
        if rc == 0:
            print(f"  ✅ Worker started: {output[:12]}...")
            return True
        else:
            print(f"  ❌ Failed to start: {output}")
            return False

    elif issue_type == "database_issue":
        print("  🔌 Fixing database connectivity...")
        # Stop existing worker
        run_command("docker stop qfieldcloud-worker && docker rm qfieldcloud-worker")
        # Retry with correct database host
        return fix_worker("not_created")

    elif issue_type == "port_conflict":
        print("  🔌 Restarting worker without port mapping...")
        run_command("docker stop qfieldcloud-worker && docker rm qfieldcloud-worker")
        return fix_worker("not_created")

    return False

def check_sync_readiness():
    """Overall sync readiness check"""
    print("\n📊 SYNC READINESS REPORT")
    print("=" * 50)

    services = check_docker_services()

    # Check worker specifically
    worker_ready = services.get('worker', {}).get('running', False)

    if not worker_ready:
        print("\n⚠️  SYNC WILL FAIL - Worker service not running")
        issue = diagnose_worker_issue()

        if issue != "running":
            response = input("\n🔧 Attempt to fix automatically? (y/n): ")
            if response.lower() == 'y':
                if fix_worker(issue):
                    print("\n✅ Worker fixed! Rechecking...")
                    time.sleep(5)
                    services = check_docker_services()
                    worker_ready = services.get('worker', {}).get('running', False)

    # Final verdict
    all_critical = all(
        services.get(svc, {}).get('running', False)
        for svc in ['app', 'database', 'memcached', 'worker']
    )

    print("\n" + "=" * 50)
    if all_critical:
        print("✅ SYNC READY - All services operational")

        # Get local IP for QField app configuration
        local_ip, _ = run_command("hostname -I | awk '{print $1}'")
        print(f"\n📱 Configure QField app:")
        print(f"   Server URL: http://{local_ip}:8011")
        print(f"   Use your QFieldCloud credentials to login")
    else:
        print("❌ SYNC NOT READY - Fix issues above")
        print("\nMissing services:")
        for svc in ['app', 'database', 'memcached', 'worker']:
            if not services.get(svc, {}).get('running', False):
                print(f"  - {svc}")

    return all_critical

def main():
    """Main diagnostic flow"""
    print("🏥 QFieldCloud Sync Diagnostic Tool")
    print("=" * 50)

    if check_sync_readiness():
        print("\n💡 Tips:")
        print("  • Worker processes sync jobs in background")
        print("  • Monitor worker: docker logs -f qfieldcloud-worker")
        print("  • Worker must have docker.sock access (root user)")
        sys.exit(0)
    else:
        print("\n📚 Manual fixes:")
        print("  • Build worker: docker compose build worker_wrapper")
        print("  • Start all: docker compose up -d")
        print("  • Check logs: docker compose logs worker_wrapper")
        sys.exit(1)

if __name__ == "__main__":
    main()