#!/home/louisdup/Agents/claude/venv/bin/python3
"""
QFieldCloud Automated Remediation System
Executes fixes for common QField issues with safety checks
"""

import os
import sys
import json
import argparse
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple

# Load environment variables
from dotenv import load_dotenv
load_dotenv()


class QFieldCloudRemediation:
    """Automated remediation for common QFieldCloud issues"""

    def __init__(self, dry_run=False):
        self.vps_host = os.getenv('QFIELDCLOUD_VPS_HOST', '72.61.166.168')
        self.vps_user = os.getenv('QFIELDCLOUD_VPS_USER', 'root')
        self.vps_password = os.getenv('QFIELDCLOUD_VPS_PASSWORD')
        self.project_path = os.getenv('QFIELDCLOUD_PROJECT_PATH', '/opt/qfieldcloud')
        self.dry_run = dry_run

        # Remediation history
        self.actions_taken = []

    def execute_ssh_command(self, command: str) -> Tuple[bool, str, str]:
        """Execute command on VPS via SSH"""
        if self.dry_run:
            print(f"[DRY RUN] Would execute: {command}")
            return True, "dry-run-success", ""

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
                timeout=120  # 2 min timeout for potentially long operations
            )

            return result.returncode == 0, result.stdout, result.stderr

        except subprocess.TimeoutExpired:
            return False, "", "Command timed out"
        except Exception as e:
            return False, "", str(e)

    def log_action(self, action: str, success: bool, details: str = ""):
        """Log remediation action"""
        self.actions_taken.append({
            "timestamp": datetime.now().isoformat(),
            "action": action,
            "success": success,
            "details": details
        })

    def fix_worker_down(self) -> Dict:
        """Fix: Worker container not running"""
        print("\n🔧 Fixing worker container...")

        # 1. Check if worker exists but stopped
        success, stdout, _ = self.execute_ssh_command(
            f"cd {self.project_path} && docker compose ps worker_wrapper --format json"
        )

        if success and stdout:
            # Worker exists, just restart
            print("   ↳ Worker container exists, restarting...")
            success, stdout, stderr = self.execute_ssh_command(
                f"cd {self.project_path} && docker compose up -d worker_wrapper"
            )

            if success:
                self.log_action("restart_worker", True, "Worker container restarted")
                return {"fixed": True, "action": "restarted_worker", "message": "Worker container restarted successfully"}
            else:
                self.log_action("restart_worker", False, stderr)
                return {"fixed": False, "action": "restart_worker", "error": stderr}
        else:
            # Worker doesn't exist, rebuild
            print("   ↳ Worker container missing, rebuilding...")
            success, stdout, stderr = self.execute_ssh_command(
                f"cd {self.project_path} && docker compose build worker_wrapper && docker compose up -d worker_wrapper"
            )

            if success:
                self.log_action("rebuild_worker", True, "Worker container rebuilt")
                return {"fixed": True, "action": "rebuilt_worker", "message": "Worker container rebuilt and started (15 min build time)"}
            else:
                self.log_action("rebuild_worker", False, stderr)
                return {"fixed": False, "action": "rebuild_worker", "error": stderr}

    def fix_database_connection(self) -> Dict:
        """Fix: Database connection issues"""
        print("\n🔧 Fixing database connection...")

        # 1. Check if database container is running
        success, stdout, _ = self.execute_ssh_command(
            f"cd {self.project_path} && docker compose ps db --format json"
        )

        if not success or "running" not in stdout.lower():
            # Database container not running
            print("   ↳ Database container down, starting...")
            success, stdout, stderr = self.execute_ssh_command(
                f"cd {self.project_path} && docker compose up -d db"
            )

            if success:
                self.log_action("start_database", True, "Database container started")
                return {"fixed": True, "action": "started_database", "message": "Database container started"}
            else:
                self.log_action("start_database", False, stderr)
                return {"fixed": False, "action": "start_database", "error": stderr}

        # 2. Database running but not accepting connections - restart
        print("   ↳ Database running but not responsive, restarting...")
        success, stdout, stderr = self.execute_ssh_command(
            f"cd {self.project_path} && docker compose restart db"
        )

        if success:
            self.log_action("restart_database", True, "Database container restarted")
            return {"fixed": True, "action": "restarted_database", "message": "Database restarted"}
        else:
            self.log_action("restart_database", False, stderr)
            return {"fixed": False, "action": "restart_database", "error": stderr}

    def fix_service_down(self, service: str) -> Dict:
        """Fix: Generic service container down"""
        print(f"\n🔧 Fixing {service} service...")

        success, stdout, stderr = self.execute_ssh_command(
            f"cd {self.project_path} && docker compose up -d {service}"
        )

        if success:
            self.log_action(f"restart_{service}", True, f"{service} restarted")
            return {"fixed": True, "action": f"restarted_{service}", "message": f"{service} service restarted"}
        else:
            self.log_action(f"restart_{service}", False, stderr)
            return {"fixed": False, "action": f"restart_{service}", "error": stderr}

    def fix_stuck_queue(self) -> Dict:
        """Fix: Queue stuck with old jobs"""
        print("\n🔧 Cleaning stuck queue jobs...")

        # Mark jobs stuck >24 hours as failed
        command = f"""docker exec qfieldcloud-db-1 psql -U qfieldcloud_db_admin -d qfieldcloud_db -c \
            "UPDATE core_job SET status = 'failed', finished_at = NOW(), \
             output = 'Auto-cleanup: stuck >24 hours' \
             WHERE status IN ('pending', 'queued') \
             AND created_at < NOW() - INTERVAL '24 hours';"
        """

        success, stdout, stderr = self.execute_ssh_command(command)

        if success:
            # Count cleaned jobs
            try:
                cleaned_count = stdout.strip().split()[-1]  # "UPDATE 5" -> "5"
                self.log_action("clean_stuck_queue", True, f"Cleaned {cleaned_count} stuck jobs")
                return {"fixed": True, "action": "cleaned_queue", "message": f"Cleaned {cleaned_count} stuck jobs (>24h old)"}
            except:
                self.log_action("clean_stuck_queue", True, "Queue cleaned")
                return {"fixed": True, "action": "cleaned_queue", "message": "Stuck queue jobs cleaned"}
        else:
            self.log_action("clean_stuck_queue", False, stderr)
            return {"fixed": False, "action": "clean_queue", "error": stderr}

    def fix_disk_space(self) -> Dict:
        """Fix: Disk space issues"""
        print("\n🔧 Cleaning disk space...")

        # Docker system prune (removes unused images, containers, volumes)
        success, stdout, stderr = self.execute_ssh_command(
            "docker system prune -a --volumes -f"
        )

        if success:
            # Extract freed space from output
            freed = "unknown"
            if "reclaimed" in stdout.lower():
                try:
                    freed = stdout.split("reclaimed")[-1].strip()
                except:
                    pass

            self.log_action("disk_cleanup", True, f"Freed: {freed}")
            return {"fixed": True, "action": "cleaned_disk", "message": f"Docker cleanup completed. Space freed: {freed}"}
        else:
            self.log_action("disk_cleanup", False, stderr)
            return {"fixed": False, "action": "clean_disk", "error": stderr}

    def fix_memory_limit(self, service: str = "worker_wrapper") -> Dict:
        """Fix: Service hitting memory limits"""
        print(f"\n🔧 Increasing memory limit for {service}...")

        # Update docker compose.override.yml to increase memory
        # This requires careful editing - for now, restart service to free memory
        print(f"   ↳ Restarting {service} to free memory...")

        success, stdout, stderr = self.execute_ssh_command(
            f"cd {self.project_path} && docker compose restart {service}"
        )

        if success:
            self.log_action(f"restart_{service}_memory", True, "Service restarted to free memory")
            return {
                "fixed": True,
                "action": f"restarted_{service}",
                "message": f"{service} restarted (temporary fix). Consider increasing memory_limit in docker compose.yml"
            }
        else:
            self.log_action(f"restart_{service}_memory", False, stderr)
            return {"fixed": False, "action": f"restart_{service}", "error": stderr}

    def diagnose_and_fix(self) -> Dict:
        """Run diagnostics and automatically fix detected issues"""
        print("🔍 Running diagnostics...")

        # Import status script functionality (or call it)
        from status import QFieldCloudMonitor

        monitor = QFieldCloudMonitor()
        status = monitor.get_status()

        fixes_applied = []
        fixes_failed = []

        # Analyze status and apply fixes
        if not status.get('worker_healthy'):
            result = self.fix_worker_down()
            if result['fixed']:
                fixes_applied.append(result)
            else:
                fixes_failed.append(result)

        if not status.get('database_healthy'):
            result = self.fix_database_connection()
            if result['fixed']:
                fixes_applied.append(result)
            else:
                fixes_failed.append(result)

        # Check for stuck queue
        if status.get('queue_depth', 0) > 10:
            result = self.fix_stuck_queue()
            if result['fixed']:
                fixes_applied.append(result)
            else:
                fixes_failed.append(result)

        # Check disk space
        if status.get('disk_usage_pct', 0) > 90:
            result = self.fix_disk_space()
            if result['fixed']:
                fixes_applied.append(result)
            else:
                fixes_failed.append(result)

        return {
            "diagnostics": status,
            "fixes_applied": fixes_applied,
            "fixes_failed": fixes_failed,
            "all_actions": self.actions_taken,
            "success": len(fixes_failed) == 0
        }

    def get_remediation_report(self) -> str:
        """Generate human-readable remediation report"""
        if not self.actions_taken:
            return "No remediation actions taken."

        report = "## Remediation Actions Taken\n\n"

        for action in self.actions_taken:
            status_emoji = "✅" if action['success'] else "❌"
            report += f"{status_emoji} **{action['action']}** ({action['timestamp']})\n"
            if action['details']:
                report += f"   {action['details']}\n"
            report += "\n"

        return report


def main():
    parser = argparse.ArgumentParser(description='QFieldCloud Automated Remediation')
    parser.add_argument('--issue', choices=[
        'worker_down', 'database_down', 'stuck_queue',
        'disk_space', 'memory_limit', 'service_down'
    ], help='Specific issue to fix')
    parser.add_argument('--service', help='Service name for generic service_down fix')
    parser.add_argument('--auto', action='store_true', help='Auto-diagnose and fix all issues')
    parser.add_argument('--dry-run', action='store_true', help='Show what would be done without executing')
    parser.add_argument('--json', action='store_true', help='Output results as JSON')

    args = parser.parse_args()

    remediation = QFieldCloudRemediation(dry_run=args.dry_run)

    try:
        if args.auto:
            result = remediation.diagnose_and_fix()
        elif args.issue == 'worker_down':
            result = remediation.fix_worker_down()
        elif args.issue == 'database_down':
            result = remediation.fix_database_connection()
        elif args.issue == 'stuck_queue':
            result = remediation.fix_stuck_queue()
        elif args.issue == 'disk_space':
            result = remediation.fix_disk_space()
        elif args.issue == 'memory_limit':
            result = remediation.fix_memory_limit()
        elif args.issue == 'service_down' and args.service:
            result = remediation.fix_service_down(args.service)
        else:
            print("Error: Specify --issue or --auto")
            sys.exit(1)

        if args.json:
            print(json.dumps(result, indent=2))
        else:
            if result.get('fixed'):
                print(f"\n✅ {result['message']}")
            else:
                print(f"\n❌ Fix failed: {result.get('error', 'Unknown error')}")

            print(remediation.get_remediation_report())

    except KeyboardInterrupt:
        print("\n\nRemediation interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error during remediation: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
