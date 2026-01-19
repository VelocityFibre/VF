#!/home/louisdup/Agents/claude/venv/bin/python3
"""
FF_React Status Monitor
Check the status of FibreFlow React application and related services
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

class FFReactMonitor:
    def __init__(self):
        self.server_host = os.getenv('VF_SERVER_HOST', '100.96.203.105')
        self.server_user = os.getenv('VF_SERVER_USER', 'louis')
        self.server_password = os.getenv('VF_SERVER_PASSWORD')

        self.processes = {
            'production': 'fibreflow-prod',
            'development': 'fibreflow-dev',
            'wa-monitor-prod': 'wa-monitor-prod',
            'wa-monitor-dev': 'wa-monitor-dev',
            'whatsapp-bridge': 'whatsapp-bridge-prod'
        }

    def execute_ssh_command(self, command, show_output=False):
        """Execute command on remote server via SSH"""
        ssh_cmd = ['ssh']

        ssh_options = [
            '-o', 'StrictHostKeyChecking=no',
            '-o', 'ConnectTimeout=10'
        ]
        ssh_cmd.extend(ssh_options)

        if self.server_password:
            ssh_cmd = ['sshpass', '-p', self.server_password] + ssh_cmd
            ssh_cmd.extend(['-o', 'PubkeyAuthentication=no'])

        ssh_cmd.append(f'{self.server_user}@{self.server_host}')
        ssh_cmd.append(command)

        try:
            result = subprocess.run(
                ssh_cmd,
                capture_output=True,
                text=True,
                timeout=30
            )

            if show_output and result.stdout:
                print(result.stdout)

            return result.returncode == 0, result.stdout

        except subprocess.TimeoutExpired:
            return False, "Command timed out"
        except Exception as e:
            return False, str(e)

    def get_pm2_status(self):
        """Get PM2 process status"""
        print("📊 PM2 Process Status")
        print("=" * 60)

        command = "pm2 jlist"
        success, output = self.execute_ssh_command(command)

        if not success:
            print("❌ Failed to get PM2 status")
            return False

        try:
            processes = json.loads(output)

            for proc in processes:
                name = proc.get('name', 'Unknown')
                status = proc.get('pm2_env', {}).get('status', 'unknown')

                # Only show FF-related processes
                if 'fibreflow' in name.lower() or 'wa-monitor' in name.lower() or 'whatsapp' in name.lower():
                    pm2_env = proc.get('pm2_env', {})
                    monit = proc.get('monit', {})

                    # Determine status emoji
                    status_emoji = "✅" if status == "online" else "❌"

                    print(f"\n🔹 {name}")
                    print(f"   Status: {status_emoji} {status}")
                    print(f"   PID: {proc.get('pid', 'N/A')}")
                    print(f"   Uptime: {self.format_uptime(pm2_env.get('pm_uptime'))}")
                    print(f"   Restarts: {pm2_env.get('restart_time', 0)}")
                    print(f"   CPU: {monit.get('cpu', 0)}%")
                    print(f"   Memory: {self.format_bytes(monit.get('memory', 0))}")

            return True

        except json.JSONDecodeError:
            print("❌ Failed to parse PM2 output")
            return False

    def format_uptime(self, timestamp):
        """Format uptime from timestamp"""
        if not timestamp:
            return "N/A"

        try:
            uptime_seconds = (datetime.now().timestamp() * 1000 - timestamp) / 1000
            days = int(uptime_seconds // 86400)
            hours = int((uptime_seconds % 86400) // 3600)
            minutes = int((uptime_seconds % 3600) // 60)

            parts = []
            if days > 0:
                parts.append(f"{days}d")
            if hours > 0:
                parts.append(f"{hours}h")
            if minutes > 0 or (days == 0 and hours == 0):
                parts.append(f"{minutes}m")

            return " ".join(parts)
        except:
            return "N/A"

    def format_bytes(self, bytes_value):
        """Format bytes to human readable"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if bytes_value < 1024.0:
                return f"{bytes_value:.1f} {unit}"
            bytes_value /= 1024.0
        return f"{bytes_value:.1f} TB"

    def check_server_resources(self):
        """Check server resource usage"""
        print("\n💻 Server Resources")
        print("=" * 60)

        # CPU usage
        command = "top -bn1 | grep 'Cpu(s)' | awk '{print $2}' | cut -d'%' -f1"
        success, cpu_output = self.execute_ssh_command(command)
        if success and cpu_output.strip():
            print(f"CPU Usage: {cpu_output.strip()}%")

        # Memory usage
        command = "free -h | awk '/^Mem:/ {printf \"Total: %s, Used: %s, Free: %s, Usage: %.1f%%\", $2, $3, $4, $3/$2*100}'"
        success, mem_output = self.execute_ssh_command(command)
        if success and mem_output:
            print(f"Memory: {mem_output}")

        # Disk usage
        command = "df -h / | awk 'NR==2 {printf \"Total: %s, Used: %s, Free: %s, Usage: %s\", $2, $3, $4, $5}'"
        success, disk_output = self.execute_ssh_command(command)
        if success and disk_output:
            print(f"Disk: {disk_output}")

        # Load average
        command = "uptime | awk -F'load average: ' '{print $2}'"
        success, load_output = self.execute_ssh_command(command)
        if success and load_output.strip():
            print(f"Load Average: {load_output.strip()}")

    def check_application_health(self, detailed=False):
        """Check application health endpoints"""
        print("\n🏥 Application Health Checks")
        print("=" * 60)

        health_checks = [
            ('Production App', 'curl -s -o /dev/null -w "%{http_code}" http://localhost:3005/api/health'),
            ('Development App', 'curl -s -o /dev/null -w "%{http_code}" http://localhost:3006/api/health'),
            ('WA Monitor API', 'curl -s -o /dev/null -w "%{http_code}" http://localhost:8080/health'),
            ('VLM Service', 'curl -s -o /dev/null -w "%{http_code}" http://localhost:8100/health'),
            ('Ollama', 'curl -s -o /dev/null -w "%{http_code}" http://localhost:11434/api/tags')
        ]

        for name, command in health_checks:
            success, output = self.execute_ssh_command(command)
            status_code = output.strip() if success else "Failed"

            if status_code == "200":
                print(f"✅ {name}: OK (200)")
            elif status_code == "404":
                print(f"⚠️  {name}: Endpoint not found (404)")
            elif status_code == "000":
                print(f"❌ {name}: Service not running")
            else:
                print(f"❌ {name}: {status_code}")

            if detailed and status_code == "200":
                # Get more details
                detail_command = command.replace('-o /dev/null -w "%{http_code}"', '')
                success, detail_output = self.execute_ssh_command(detail_command)
                if success and detail_output:
                    print(f"   Response: {detail_output[:100]}...")

    def check_recent_errors(self):
        """Check for recent errors in logs"""
        print("\n⚠️  Recent Errors (last 24 hours)")
        print("=" * 60)

        processes_to_check = ['fibreflow-prod', 'fibreflow-dev']

        for process in processes_to_check:
            command = f"pm2 logs {process} --err --nostream --lines 20 2>/dev/null | grep -E 'ERROR|Error|error' | head -5"
            success, output = self.execute_ssh_command(command)

            if success and output.strip():
                print(f"\n{process}:")
                for line in output.strip().split('\n')[:5]:
                    print(f"  • {line[:100]}...")
            else:
                print(f"\n{process}: No recent errors ✅")

    def get_git_info(self):
        """Get git information for deployments"""
        print("\n📦 Deployment Information")
        print("=" * 60)

        deployments = [
            ('Production', '/var/www/fibreflow'),
            ('Development', '/var/www/fibreflow-dev')
        ]

        for name, path in deployments:
            print(f"\n{name}:")

            # Get current branch
            command = f"cd {path} && git branch --show-current"
            success, branch = self.execute_ssh_command(command)
            if success:
                print(f"  Branch: {branch.strip()}")

            # Get latest commit
            command = f"cd {path} && git log -1 --oneline"
            success, commit = self.execute_ssh_command(command)
            if success:
                print(f"  Latest: {commit.strip()}")

            # Check for uncommitted changes
            command = f"cd {path} && git status --short"
            success, changes = self.execute_ssh_command(command)
            if success:
                if changes.strip():
                    print(f"  ⚠️  Uncommitted changes present")
                else:
                    print(f"  ✅ Working directory clean")

    def monitor(self, detailed=False, show_errors=True):
        """Run complete monitoring check"""
        print(f"\n🔍 FF_React Status Monitor")
        print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"🖥️  Server: {self.server_host}")
        print("=" * 60)

        # Run all checks
        self.get_pm2_status()
        self.check_server_resources()
        self.check_application_health(detailed)

        if show_errors:
            self.check_recent_errors()

        self.get_git_info()

        print("\n" + "=" * 60)
        print("✅ Status check complete")

def main():
    parser = argparse.ArgumentParser(description='Monitor FF_React application status')
    parser.add_argument(
        '--detailed',
        action='store_true',
        help='Show detailed health check responses'
    )
    parser.add_argument(
        '--no-errors',
        action='store_true',
        help='Skip error log check'
    )
    parser.add_argument(
        '--json',
        action='store_true',
        help='Output in JSON format (coming soon)'
    )

    args = parser.parse_args()

    monitor = FFReactMonitor()
    monitor.monitor(
        detailed=args.detailed,
        show_errors=not args.no_errors
    )

if __name__ == '__main__':
    main()