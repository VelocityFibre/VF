#!/usr/bin/env python3
"""
QFieldCloud Pre-Migration Cleanup Script
Executes cleanup tasks to prepare for server migration
"""

import os
import sys
import subprocess
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Color formatting functions
def colored(text, color, bold=False):
    """Simple colored text output"""
    colors = {
        'red': '\033[91m',
        'green': '\033[92m',
        'yellow': '\033[93m',
        'blue': '\033[94m',
        'cyan': '\033[96m',
        'white': '\033[97m',
        'reset': '\033[0m',
        'bold': '\033[1m'
    }

    color_code = colors.get(color, '')
    bold_code = colors['bold'] if bold else ''
    return f"{bold_code}{color_code}{text}{colors['reset']}"

def format_size(bytes):
    """Format bytes to human readable size"""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if bytes < 1024.0:
            return f"{bytes:.2f} {unit}"
        bytes /= 1024.0
    return f"{bytes:.2f} PB"

class QFieldCleanup:
    def __init__(self):
        self.vps_host = os.getenv('QFIELDCLOUD_VPS_HOST', '72.61.166.168')
        self.vps_user = os.getenv('QFIELDCLOUD_VPS_USER', 'root')
        self.vps_password = os.getenv('QFIELDCLOUD_VPS_PASSWORD')
        self.project_path = os.getenv('QFIELDCLOUD_PROJECT_PATH', '/opt/qfieldcloud')

    def execute_ssh_command(self, command, timeout=30):
        """Execute command on VPS via SSH"""
        ssh_cmd = ['ssh']

        ssh_options = [
            '-o', 'StrictHostKeyChecking=no',
            '-o', 'ConnectTimeout=10'
        ]

        # Use SSH key if no password provided
        if not self.vps_password:
            ssh_key_path = os.path.expanduser('~/.ssh/qfield_vps')
            if os.path.exists(ssh_key_path):
                ssh_options.extend(['-i', ssh_key_path])

        ssh_cmd.extend(ssh_options)

        if self.vps_password:
            ssh_cmd = ['sshpass', '-p', self.vps_password] + ssh_cmd
            ssh_cmd.extend(['-o', 'PubkeyAuthentication=no'])

        ssh_cmd.append(f'{self.vps_user}@{self.vps_host}')
        ssh_cmd.append(command)

        try:
            result = subprocess.run(
                ssh_cmd,
                capture_output=True,
                text=True,
                timeout=timeout
            )
            return result.stdout if result.returncode == 0 else None

        except subprocess.TimeoutExpired:
            print(colored("Command timed out", "yellow"))
            return None
        except Exception as e:
            print(colored(f"Error: {str(e)}", "red"))
            return None

    def check_disk_space(self):
        """Check current disk usage"""
        print(colored("\n📊 Current Disk Usage", "cyan", bold=True))
        print("=" * 60)

        # Check main disk
        cmd = "df -h / | awk 'NR==2 {print $2,$3,$4,$5}'"
        result = self.execute_ssh_command(cmd)
        if result:
            parts = result.strip().split()
            if len(parts) == 4:
                total, used, free, percent = parts
                print(f"Total: {total}, Used: {used}, Free: {free}, Usage: {percent}")

                usage_int = int(percent.replace('%', ''))
                if usage_int >= 85:
                    print(colored(f"❌ CRITICAL: Disk usage at {percent}", "red"))
                elif usage_int >= 70:
                    print(colored(f"⚠️  WARNING: Disk usage at {percent}", "yellow"))
                else:
                    print(colored(f"✅ OK: Disk usage at {percent}", "green"))

        # Check Docker space
        print(colored("\n🐳 Docker Disk Usage", "cyan"))
        cmd = "docker system df"
        result = self.execute_ssh_command(cmd)
        if result:
            print(result)

        return True

    def clean_docker_system(self, dry_run=False):
        """Clean Docker system artifacts"""
        print(colored("\n🧹 Docker System Cleanup", "cyan", bold=True))
        print("=" * 60)

        if dry_run:
            print(colored("DRY RUN MODE - No changes will be made", "yellow"))
            cmd = "docker system df"
        else:
            print("Removing unused Docker objects...")
            # This command removes:
            # - All stopped containers
            # - All networks not used by at least one container
            # - All dangling images
            # - All dangling build cache
            cmd = "docker system prune -af --volumes"

        result = self.execute_ssh_command(cmd, timeout=120)
        if result:
            print(result)
            if not dry_run and "Total reclaimed space" in result:
                # Extract reclaimed space
                for line in result.split('\n'):
                    if "Total reclaimed space" in line:
                        print(colored(f"✅ {line}", "green", bold=True))

        return True

    def clean_old_logs(self, dry_run=False):
        """Clean old log files"""
        print(colored("\n📄 Log File Cleanup", "cyan", bold=True))
        print("=" * 60)

        # Find large log files first
        print("Finding large log files (>100MB)...")
        cmd = "find /var/log -type f -name '*.log' -size +100M 2>/dev/null | head -10"
        large_files = self.execute_ssh_command(cmd)
        if large_files:
            print("Large log files found:")
            for file in large_files.strip().split('\n'):
                if file:
                    # Get file size
                    size_cmd = f"ls -lh {file} 2>/dev/null | awk '{{print $5}}'"
                    size = self.execute_ssh_command(size_cmd)
                    if size:
                        print(f"  {file}: {size.strip()}")

        if not dry_run:
            # Clean old logs (>30 days)
            print("\nRemoving logs older than 30 days...")
            cmd = "find /var/log -type f -name '*.log' -mtime +30 -delete 2>/dev/null"
            self.execute_ssh_command(cmd)

            # Truncate Docker container logs
            print("Truncating Docker container logs...")
            cmd = "truncate -s 0 /var/lib/docker/containers/*/*-json.log 2>/dev/null"
            self.execute_ssh_command(cmd)

            # Clean QFieldCloud specific logs
            print("Cleaning QFieldCloud logs...")
            cmd = "rm -rf /opt/qfieldcloud/logs/*.log.* 2>/dev/null"
            self.execute_ssh_command(cmd)

            print(colored("✅ Log cleanup completed", "green"))
        else:
            print(colored("DRY RUN - No logs removed", "yellow"))

        return True

    def clean_old_jobs(self, dry_run=False):
        """Clean old job records from database"""
        print(colored("\n🗄️ Database Job Cleanup", "cyan", bold=True))
        print("=" * 60)

        # Check current job statistics
        print("Checking job statistics...")
        stats_cmd = """docker exec qfieldcloud-db-1 psql -U qfieldcloud_db_admin -d qfieldcloud_db -t -c "
            SELECT
                COUNT(*) as total_jobs,
                COUNT(CASE WHEN created_at < NOW() - INTERVAL '30 days' THEN 1 END) as old_jobs,
                COUNT(CASE WHEN status IN ('pending','queued') AND created_at < NOW() - INTERVAL '1 day' THEN 1 END) as stuck_jobs
            FROM core_job;" 2>/dev/null"""

        result = self.execute_ssh_command(stats_cmd)
        if result:
            parts = result.strip().split('|')
            if len(parts) >= 3:
                total = parts[0].strip()
                old = parts[1].strip()
                stuck = parts[2].strip()
                print(f"Total jobs: {total}")
                print(f"Jobs >30 days old: {old}")
                print(f"Stuck jobs >24h: {stuck}")

                if not dry_run and int(old) > 0:
                    print(f"\nDeleting {old} old job records...")
                    delete_cmd = """docker exec qfieldcloud-db-1 psql -U qfieldcloud_db_admin -d qfieldcloud_db -c "
                        DELETE FROM core_job WHERE created_at < NOW() - INTERVAL '30 days';" 2>/dev/null"""
                    result = self.execute_ssh_command(delete_cmd)
                    if result and "DELETE" in result:
                        print(colored(f"✅ Deleted {old} old job records", "green"))
                elif dry_run:
                    print(colored(f"DRY RUN - Would delete {old} old job records", "yellow"))

        return True

    def backup_configuration(self):
        """Backup current configuration files"""
        print(colored("\n💾 Backing Up Configuration", "cyan", bold=True))
        print("=" * 60)

        backup_dir = f"/root/qfield_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        # Create backup directory
        cmd = f"mkdir -p {backup_dir}"
        self.execute_ssh_command(cmd)

        # Backup important files
        files_to_backup = [
            "/opt/qfieldcloud/.env",
            "/opt/qfieldcloud/docker-compose.yml",
            "/opt/qfieldcloud/docker-compose.override.yml"
        ]

        for file in files_to_backup:
            print(f"Backing up {file}...")
            cmd = f"cp {file} {backup_dir}/ 2>/dev/null"
            self.execute_ssh_command(cmd)

        # Save current status
        print("Saving current status...")
        status_cmd = f"""cat > {backup_dir}/status.txt << 'EOF'
Migration Preparation Date: {datetime.now()}
Server: 72.61.166.168
$(docker ps | wc -l) containers running
$(df -h / | awk 'NR==2 {{print "Disk: " $5 " used"}}')
$(docker exec qfieldcloud-db-1 psql -U qfieldcloud_db_admin -d qfieldcloud_db -t -c "SELECT 'DB Size: ' || pg_size_pretty(pg_database_size('qfieldcloud_db'));" 2>/dev/null)
EOF"""
        self.execute_ssh_command(status_cmd)

        print(colored(f"✅ Configuration backed up to {backup_dir}", "green"))
        return backup_dir

def main():
    """Main execution"""
    import argparse

    parser = argparse.ArgumentParser(description='QFieldCloud Pre-Migration Cleanup')
    parser.add_argument('--dry-run', action='store_true',
                       help='Show what would be done without making changes')
    parser.add_argument('--skip-docker', action='store_true',
                       help='Skip Docker cleanup')
    parser.add_argument('--skip-logs', action='store_true',
                       help='Skip log cleanup')
    parser.add_argument('--skip-jobs', action='store_true',
                       help='Skip database job cleanup')
    parser.add_argument('--skip-backup', action='store_true',
                       help='Skip configuration backup')

    args = parser.parse_args()

    # Initialize cleanup instance
    cleanup = QFieldCleanup()

    print(colored("🔌 Connecting to QFieldCloud server...", "cyan"))
    print(f"Server: {cleanup.vps_host}")

    try:
        # Show current status
        cleanup.check_disk_space()

        # Backup configuration first
        if not args.skip_backup and not args.dry_run:
            backup_dir = cleanup.backup_configuration()

        # Run cleanup tasks
        if not args.skip_docker:
            cleanup.clean_docker_system(args.dry_run)

        if not args.skip_logs:
            cleanup.clean_old_logs(args.dry_run)

        if not args.skip_jobs:
            cleanup.clean_old_jobs(args.dry_run)

        # Show final status
        print(colored("\n📊 Final Disk Usage", "cyan", bold=True))
        print("=" * 60)
        cleanup.check_disk_space()

        print(colored("\n✅ Pre-migration cleanup completed!", "green", bold=True))

        if args.dry_run:
            print(colored("\n⚠️  This was a DRY RUN - no changes were made", "yellow"))
            print("Run without --dry-run to actually perform cleanup")
        else:
            print(colored("\n📋 Next Steps:", "cyan"))
            print("1. Run database optimization: python3 optimize_database.py")
            print("2. Archive old project files: python3 archive_old_files.py")
            print("3. Run final readiness check: python3 migration_readiness.py")
            print("\nFull migration plan: MIGRATION_PLAN.md")

    except Exception as e:
        print(colored(f"❌ Error during cleanup: {str(e)}", "red"))
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()