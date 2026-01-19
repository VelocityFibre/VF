#!/home/louisdup/Agents/claude/venv/bin/python3
"""
QFieldCloud Prevention System Manager
Interact with the self-healing prevention system
"""

import os
import sys
import json
import argparse
import subprocess
from datetime import datetime
from pathlib import Path

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

class PreventionSystemManager:
    def __init__(self):
        self.vps_host = os.getenv('QFIELDCLOUD_VPS_HOST', '72.61.166.168')
        self.vps_user = os.getenv('QFIELDCLOUD_VPS_USER', 'root')
        self.ssh_key = os.path.expanduser('~/.ssh/qfield_vps')
        self.project_path = os.getenv('QFIELDCLOUD_PROJECT_PATH', '/opt/qfieldcloud')
        self.local_qfield_path = '/home/louisdup/VF/Apps/QFieldCloud'

    def execute_ssh_command(self, command, show_output=False):
        """Execute command on VPS via SSH"""
        ssh_cmd = [
            'ssh',
            '-i', self.ssh_key,
            '-o', 'StrictHostKeyChecking=no',
            '-o', 'ConnectTimeout=10',
            f'{self.vps_user}@{self.vps_host}',
            command
        ]

        try:
            result = subprocess.run(
                ssh_cmd,
                capture_output=True,
                text=True,
                timeout=30
            )

            if show_output and result.stdout:
                print(result.stdout)

            return result.returncode == 0, result.stdout, result.stderr

        except subprocess.TimeoutExpired:
            return False, "", "Command timed out"
        except Exception as e:
            return False, "", str(e)

    def execute_local_command(self, command, show_output=False):
        """Execute command locally"""
        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=30
            )

            if show_output and result.stdout:
                print(result.stdout)

            return result.returncode == 0, result.stdout, result.stderr

        except Exception as e:
            return False, "", str(e)

    def check_status(self):
        """Check prevention system status"""
        print("🛡️  Prevention System Status")
        print("=" * 70)

        # 1. Monitor Daemon
        print("\n📡 Monitor Daemon:")
        success, stdout, stderr = self.execute_local_command(
            "systemctl is-active qfield-monitor"
        )

        if success and stdout.strip() == "active":
            print("   ✅ Running")

            # Get last check time
            success, stdout, _ = self.execute_local_command(
                "tail -1 /var/log/qfield_monitor.log 2>/dev/null"
            )
            if success and stdout:
                try:
                    # Extract timestamp from log line
                    timestamp = stdout.split(' - ')[0]
                    print(f"   Last check: {timestamp}")
                except:
                    pass
        else:
            print("   ❌ Not running")

        # 2. Cron Jobs
        print("\n⏰ Cron Jobs:")
        success, stdout, _ = self.execute_local_command(
            "crontab -l 2>/dev/null | grep -c qfield"
        )

        if success:
            count = stdout.strip()
            if count == "5":
                print(f"   ✅ All installed ({count}/5)")
            else:
                print(f"   ⚠️  Incomplete ({count}/5 installed)")
        else:
            print("   ❌ Not installed (0/5)")

        # 3. Disk Space
        print("\n💾 VPS Disk Space:")
        success, stdout, _ = self.execute_ssh_command(
            "df -h /var/lib/docker | tail -1"
        )

        if success and stdout:
            parts = stdout.split()
            if len(parts) >= 5:
                size = parts[1]
                used = parts[2]
                avail = parts[3]
                percent = parts[4]

                percent_num = int(percent.rstrip('%'))
                if percent_num < 80:
                    status = "✅"
                elif percent_num < 90:
                    status = "⚠️"
                else:
                    status = "❌"

                print(f"   {status} Used: {used} / {size} ({percent})")
                print(f"   Available: {avail}")

        # 4. Worker Status
        print("\n⚙️  Worker Containers:")
        success, stdout, _ = self.execute_ssh_command(
            f"cd {self.project_path} && docker compose ps worker_wrapper --format json 2>/dev/null"
        )

        if success and stdout:
            worker_count = len([line for line in stdout.strip().split('\n') if line])
            if worker_count >= 2:
                print(f"   ✅ {worker_count} workers running")
            else:
                print(f"   ⚠️  Only {worker_count} workers (expected 2)")
        else:
            print("   ❌ No workers detected")

        # 5. Recent Interventions
        print("\n🔧 Recent Interventions:")
        success, stdout, _ = self.execute_local_command(
            "grep -i 'restarting\\|intervention' /var/log/qfield_monitor.log 2>/dev/null | tail -3"
        )

        if success and stdout.strip():
            for line in stdout.strip().split('\n'):
                print(f"   • {line[:100]}")
        else:
            print("   ✅ None (all healthy)")

        print("\n" + "=" * 70)

    def view_monitor_logs(self, lines=50, follow=False):
        """View monitor daemon logs"""
        print(f"📋 Monitor Daemon Logs (last {lines} lines)")
        print("=" * 70)

        if follow:
            cmd = "tail -f /var/log/qfield_monitor.log"
            print("Following logs (Ctrl+C to exit)...\n")
        else:
            cmd = f"tail -{lines} /var/log/qfield_monitor.log 2>/dev/null"

        self.execute_local_command(cmd, show_output=True)

    def control_monitor(self, action):
        """Control monitor daemon"""
        valid_actions = ['start', 'stop', 'restart', 'status']

        if action not in valid_actions:
            print(f"❌ Invalid action: {action}")
            print(f"Valid actions: {', '.join(valid_actions)}")
            return

        print(f"🔧 Monitor Daemon: {action}")
        print("=" * 70)

        if action == 'status':
            cmd = "systemctl status qfield-monitor --no-pager"
            self.execute_local_command(cmd, show_output=True)
        else:
            cmd = f"sudo systemctl {action} qfield-monitor"
            success, stdout, stderr = self.execute_local_command(cmd)

            if success:
                print(f"✅ Monitor daemon {action}ed successfully")
            else:
                print(f"❌ Failed to {action} monitor daemon")
                if stderr:
                    print(f"Error: {stderr}")

    def run_maintenance(self, script=None):
        """Run maintenance scripts"""
        scripts = {
            'quick': 'qfield_quick_check.sh',
            'cleanup': 'qfield_cleanup.sh',
            'restart': 'qfield_scheduled_restart.sh',
            'daily': 'qfield_daily_maintenance.sh',
            'stats': 'qfield_stats.sh'
        }

        if script and script not in scripts:
            print(f"❌ Unknown script: {script}")
            print(f"Available: {', '.join(scripts.keys())}")
            return

        if script:
            # Run specific script
            script_name = scripts[script]
            script_path = f"{self.local_qfield_path}/{script_name}"

            if not os.path.exists(script_path):
                print(f"❌ Script not found: {script_path}")
                return

            print(f"🔧 Running: {script_name}")
            print("=" * 70)

            cmd = f"cd {self.local_qfield_path} && ./{script_name}"
            self.execute_local_command(cmd, show_output=True)
        else:
            # Run all quick maintenance
            print("🔧 Running Quick Maintenance")
            print("=" * 70)

            for name, script_name in [('quick', 'qfield_quick_check.sh'),
                                       ('stats', 'qfield_stats.sh')]:
                script_path = f"{self.local_qfield_path}/{script_name}"

                if os.path.exists(script_path):
                    print(f"\n▶ {script_name}:")
                    cmd = f"cd {self.local_qfield_path} && ./{script_name}"
                    self.execute_local_command(cmd, show_output=True)

    def view_stats(self):
        """View usage statistics"""
        stats_file = '/tmp/qfield_stats_local.json'

        print("📊 QFieldCloud Usage Statistics")
        print("=" * 70)

        if not os.path.exists(stats_file):
            print("⚠️  No statistics file found")
            print(f"Run: cd {self.local_qfield_path} && ./qfield_stats.sh")
            return

        try:
            with open(stats_file, 'r') as f:
                stats = json.load(f)

            print(f"\n📅 Timestamp: {stats.get('timestamp', 'N/A')}")
            print(f"\n👥 Users: {stats.get('users', 0)}")
            print(f"📁 Projects: {stats.get('projects', 0)}")

            jobs_24h = stats.get('jobs_24h', {})
            print("\n📋 Jobs (24 hours):")
            print(f"   Total: {jobs_24h.get('total', 0)}")
            print(f"   Success: {jobs_24h.get('success', 0)}")
            print(f"   Failed: {jobs_24h.get('failed', 0)}")
            print(f"   Queued: {jobs_24h.get('queued', 0)}")

            # Calculate success rate
            total = jobs_24h.get('total', 0)
            if total > 0:
                success_rate = (jobs_24h.get('success', 0) / total) * 100
                if success_rate >= 95:
                    status = "✅ Excellent"
                elif success_rate >= 90:
                    status = "⚠️  Good"
                else:
                    status = "❌ Poor"
                print(f"\n   Success Rate: {success_rate:.1f}% {status}")

        except Exception as e:
            print(f"❌ Error reading stats: {e}")

        print("\n" + "=" * 70)

    def check_cron_jobs(self):
        """Check cron job configuration"""
        print("⏰ Cron Jobs Configuration")
        print("=" * 70)

        expected_jobs = [
            ('*/5 * * * *', 'qfield_quick_check.sh', 'Quick health check'),
            ('*/30 * * * *', 'qfield_cleanup.sh', 'Docker cleanup'),
            ('0 */4 * * *', 'qfield_scheduled_restart.sh', 'Preventive restart'),
            ('0 2 * * *', 'qfield_daily_maintenance.sh', 'Daily maintenance'),
            ('0 6 * * *', 'qfield_stats.sh', 'Usage statistics')
        ]

        success, stdout, _ = self.execute_local_command("crontab -l 2>/dev/null")

        if not success:
            print("❌ No crontab found")
            return

        installed = stdout

        for schedule, script, description in expected_jobs:
            if script in installed:
                print(f"✅ {description}")
                print(f"   Schedule: {schedule}")
                print(f"   Script: {script}")
            else:
                print(f"❌ {description}")
                print(f"   Missing: {script}")
            print()

        print("=" * 70)

def main():
    parser = argparse.ArgumentParser(
        description='QFieldCloud Prevention System Manager',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --status                    Check prevention system health
  %(prog)s --monitor-logs              View monitor daemon logs
  %(prog)s --monitor-logs --follow     Follow monitor logs in real-time
  %(prog)s --control start             Start monitor daemon
  %(prog)s --control stop              Stop monitor daemon
  %(prog)s --run-maintenance           Run quick maintenance scripts
  %(prog)s --run-maintenance --script quick   Run specific script
  %(prog)s --stats                     View usage statistics
  %(prog)s --check-cron                Check cron job configuration
        """
    )

    parser.add_argument('--status', action='store_true',
                        help='Check prevention system status')
    parser.add_argument('--monitor-logs', action='store_true',
                        help='View monitor daemon logs')
    parser.add_argument('--follow', action='store_true',
                        help='Follow logs in real-time (use with --monitor-logs)')
    parser.add_argument('--lines', type=int, default=50,
                        help='Number of log lines to show (default: 50)')
    parser.add_argument('--control', choices=['start', 'stop', 'restart', 'status'],
                        help='Control monitor daemon')
    parser.add_argument('--run-maintenance', action='store_true',
                        help='Run maintenance scripts')
    parser.add_argument('--script', choices=['quick', 'cleanup', 'restart', 'daily', 'stats'],
                        help='Specific maintenance script to run')
    parser.add_argument('--stats', action='store_true',
                        help='View usage statistics')
    parser.add_argument('--check-cron', action='store_true',
                        help='Check cron job configuration')

    args = parser.parse_args()

    # If no arguments, show status by default
    if len(sys.argv) == 1:
        args.status = True

    manager = PreventionSystemManager()

    try:
        if args.status:
            manager.check_status()

        if args.monitor_logs:
            manager.view_monitor_logs(lines=args.lines, follow=args.follow)

        if args.control:
            manager.control_monitor(args.control)

        if args.run_maintenance:
            manager.run_maintenance(args.script)

        if args.stats:
            manager.view_stats()

        if args.check_cron:
            manager.check_cron_jobs()

    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
