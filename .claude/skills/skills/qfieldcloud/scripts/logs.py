#!/home/louisdup/Agents/claude/venv/bin/python3
"""
QFieldCloud Log Viewer
View and analyze logs from QFieldCloud Docker services
"""

import os
import sys
import re
import argparse
import subprocess
from datetime import datetime, timedelta
from pathlib import Path

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

class QFieldCloudLogViewer:
    def __init__(self):
        self.vps_host = os.getenv('QFIELDCLOUD_VPS_HOST', '72.61.166.168')
        self.vps_user = os.getenv('QFIELDCLOUD_VPS_USER', 'root')
        self.vps_password = os.getenv('QFIELDCLOUD_VPS_PASSWORD')
        self.project_path = os.getenv('QFIELDCLOUD_PROJECT_PATH', '/opt/qfieldcloud')

        # Docker services
        self.services = {
            'nginx': 'Web server and reverse proxy',
            'app': 'Django application',
            'db': 'PostgreSQL database',
            'redis': 'Cache and message broker',
            'worker_wrapper': 'Background task worker',
            'minio': 'Object storage',
            'ofelia': 'Cron job scheduler'
        }

        # Color codes for terminal output
        self.colors = {
            'red': '\033[91m',
            'green': '\033[92m',
            'yellow': '\033[93m',
            'blue': '\033[94m',
            'magenta': '\033[95m',
            'cyan': '\033[96m',
            'white': '\033[97m',
            'reset': '\033[0m',
            'bold': '\033[1m'
        }

    def execute_ssh_command(self, command):
        """Execute command on VPS via SSH"""
        ssh_cmd = ['ssh']

        ssh_options = [
            '-o', 'StrictHostKeyChecking=no',
            '-o', 'ConnectTimeout=10'
        ]
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
                timeout=30
            )
            return result.returncode == 0, result.stdout
        except Exception as e:
            return False, str(e)

    def colorize_log_level(self, line):
        """Add colors to log levels"""
        # Error levels
        if re.search(r'\b(ERROR|FATAL|CRITICAL|Exception)\b', line, re.IGNORECASE):
            return f"{self.colors['red']}{line}{self.colors['reset']}"

        # Warning levels
        elif re.search(r'\b(WARN|WARNING)\b', line, re.IGNORECASE):
            return f"{self.colors['yellow']}{line}{self.colors['reset']}"

        # Info levels
        elif re.search(r'\b(INFO|LOG)\b', line, re.IGNORECASE):
            return f"{self.colors['cyan']}{line}{self.colors['reset']}"

        # Debug levels
        elif re.search(r'\b(DEBUG|TRACE)\b', line, re.IGNORECASE):
            return f"{self.colors['magenta']}{line}{self.colors['reset']}"

        # Success patterns
        elif re.search(r'\b(SUCCESS|COMPLETED|DONE|OK|200|201)\b', line, re.IGNORECASE):
            return f"{self.colors['green']}{line}{self.colors['reset']}"

        # HTTP error codes
        elif re.search(r'\b(404|500|502|503)\b', line):
            return f"{self.colors['red']}{line}{self.colors['reset']}"

        return line

    def format_timestamp(self, line):
        """Highlight timestamps in log lines"""
        # ISO timestamps
        pattern = r'(\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2})'
        line = re.sub(pattern, f"{self.colors['blue']}\\1{self.colors['reset']}", line)

        # Docker compose timestamps
        pattern = r'^(\S+\s+\|)'
        line = re.sub(pattern, f"{self.colors['yellow']}\\1{self.colors['reset']}", line)

        return line

    def view_service_logs(self, service='all', lines=50, follow=False, grep=None):
        """View logs for specific service(s)"""
        if service == 'all':
            print(f"\n📋 Logs for all services")
            service_arg = ""
        else:
            print(f"\n📋 Logs for: {service}")
            if service not in self.services:
                print(f"❌ Unknown service: {service}")
                print(f"Available: {', '.join(self.services.keys())}")
                return False
            service_arg = service

        print("=" * 60)

        # Build docker compose logs command
        cmd_parts = [f'cd {self.project_path}', '&&', 'docker compose', 'logs']

        if not follow:
            cmd_parts.extend(['--tail', str(lines)])

        if service_arg:
            cmd_parts.append(service_arg)

        if grep:
            cmd_parts.extend(['2>&1', '|', 'grep', '-i', f'"{grep}"'])

        command = ' '.join(cmd_parts)

        if follow:
            print(f"🔄 Following logs (Ctrl+C to stop)...")
            print("-" * 60)

            # Use subprocess directly for real-time following
            ssh_cmd = ['ssh']
            ssh_options = ['-o', 'StrictHostKeyChecking=no', '-o', 'ConnectTimeout=10']
            ssh_cmd.extend(ssh_options)

            if self.vps_password:
                ssh_cmd = ['sshpass', '-p', self.vps_password] + ssh_cmd
                ssh_cmd.extend(['-o', 'PubkeyAuthentication=no'])

            ssh_cmd.append(f'{self.vps_user}@{self.vps_host}')
            ssh_cmd.append(command)

            try:
                process = subprocess.Popen(ssh_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
                for line in process.stdout:
                    formatted = self.colorize_log_level(line.rstrip())
                    formatted = self.format_timestamp(formatted)
                    print(formatted)
            except KeyboardInterrupt:
                print("\n\n✋ Log following stopped")
                process.terminate()
        else:
            success, output = self.execute_ssh_command(command)

            if not success:
                print(f"❌ Failed to retrieve logs: {output}")
                return False

            # Process and display logs
            for line in output.splitlines():
                formatted = self.colorize_log_level(line)
                formatted = self.format_timestamp(formatted)
                print(formatted)

        return True

    def search_logs(self, pattern, service=None, context_lines=2):
        """Search for pattern in logs"""
        print(f"\n🔍 Searching for: '{pattern}'")
        print("=" * 60)

        services_to_search = []
        if service:
            services_to_search = [service]
        else:
            services_to_search = list(self.services.keys())

        total_matches = 0

        for svc in services_to_search:
            command = f"cd {self.project_path} && docker compose logs --tail 500 {svc} 2>&1 | grep -i -C {context_lines} '{pattern}'"
            success, output = self.execute_ssh_command(command)

            if success and output.strip():
                print(f"\n📁 {svc} ({self.services[svc]}):")
                print("-" * 40)

                for line in output.splitlines():
                    if pattern.lower() in line.lower():
                        # Highlight the pattern
                        highlighted = re.sub(
                            f"({pattern})",
                            f"{self.colors['bold']}{self.colors['yellow']}\\1{self.colors['reset']}",
                            line,
                            flags=re.IGNORECASE
                        )
                        print(highlighted)
                        total_matches += 1
                    else:
                        # Context lines
                        print(f"{self.colors['white']}{line}{self.colors['reset']}")

        print(f"\n📊 Found {total_matches} matches")
        return total_matches > 0

    def analyze_errors(self, hours=24):
        """Analyze error patterns in recent logs"""
        print(f"\n📊 Error Analysis (last {hours} hours)")
        print("=" * 60)

        error_patterns = {}
        total_errors = 0

        critical_services = ['app', 'nginx', 'worker_wrapper']

        for service in critical_services:
            command = f"cd {self.project_path} && docker compose logs --tail 1000 {service} 2>&1 | grep -E 'ERROR|Exception|Failed|Critical'"
            success, output = self.execute_ssh_command(command)

            if success and output.strip():
                print(f"\n{service}:")

                for line in output.splitlines()[:50]:  # Limit to 50 errors per service
                    total_errors += 1

                    # Try to categorize the error
                    if 'ConnectionError' in line or 'ECONNREFUSED' in line:
                        error_type = 'Connection Error'
                    elif 'TimeoutError' in line or 'timeout' in line.lower():
                        error_type = 'Timeout'
                    elif 'PermissionError' in line or 'permission denied' in line.lower():
                        error_type = 'Permission Denied'
                    elif 'DatabaseError' in line or 'psycopg2' in line:
                        error_type = 'Database Error'
                    elif '404' in line:
                        error_type = '404 Not Found'
                    elif '500' in line or 'Internal Server Error' in line:
                        error_type = '500 Internal Server Error'
                    elif '502' in line:
                        error_type = '502 Bad Gateway'
                    elif 'ImportError' in line or 'ModuleNotFoundError' in line:
                        error_type = 'Import Error'
                    elif 'KeyError' in line or 'AttributeError' in line:
                        error_type = 'Code Error'
                    else:
                        error_type = 'Other'

                    error_patterns[error_type] = error_patterns.get(error_type, 0) + 1

        if error_patterns:
            print("\n📈 Error Summary:")
            for error_type, count in sorted(error_patterns.items(), key=lambda x: x[1], reverse=True):
                percentage = (count / total_errors) * 100
                bar_length = int(percentage / 2)
                bar = '█' * bar_length
                print(f"  {error_type:25} {bar} {count} ({percentage:.1f}%)")

            print(f"\n  Total Errors: {total_errors}")
        else:
            print("✅ No errors found in recent logs")

    def export_logs(self, service, output_file, lines=1000):
        """Export logs to a file"""
        print(f"\n💾 Exporting {service} logs to {output_file}...")

        command = f"cd {self.project_path} && docker compose logs --tail {lines} {service} > /tmp/qfield_logs.txt 2>&1"
        success, output = self.execute_ssh_command(command)

        if not success:
            print(f"❌ Failed to export logs")
            return False

        # Download the file
        scp_cmd = ['scp']

        if self.vps_password:
            scp_cmd = ['sshpass', '-p', self.vps_password] + scp_cmd

        scp_cmd.extend([
            f'{self.vps_user}@{self.vps_host}:/tmp/qfield_logs.txt',
            output_file
        ])

        try:
            subprocess.run(scp_cmd, check=True)
            print(f"✅ Logs exported to {output_file}")

            # Clean up remote file
            self.execute_ssh_command("rm /tmp/qfield_logs.txt")
            return True
        except Exception as e:
            print(f"❌ Failed to download logs: {e}")
            return False

    def list_services(self):
        """List available services"""
        print("\n📦 Available QFieldCloud Services")
        print("=" * 60)

        for service, description in self.services.items():
            print(f"  • {service:15} - {description}")

def main():
    parser = argparse.ArgumentParser(description='View QFieldCloud logs')
    parser.add_argument(
        '--service',
        default='all',
        help='Service to view logs from (default: all)'
    )
    parser.add_argument(
        '--lines',
        type=int,
        default=50,
        help='Number of log lines to display'
    )
    parser.add_argument(
        '--follow',
        action='store_true',
        help='Follow logs in real-time'
    )
    parser.add_argument(
        '--grep',
        help='Filter logs with pattern'
    )
    parser.add_argument(
        '--search',
        help='Search for pattern in logs'
    )
    parser.add_argument(
        '--analyze',
        action='store_true',
        help='Analyze error patterns'
    )
    parser.add_argument(
        '--export',
        help='Export logs to file'
    )
    parser.add_argument(
        '--list',
        action='store_true',
        help='List available services'
    )

    args = parser.parse_args()

    viewer = QFieldCloudLogViewer()

    if args.list:
        viewer.list_services()
    elif args.search:
        viewer.search_logs(args.search, args.service if args.service != 'all' else None)
    elif args.analyze:
        viewer.analyze_errors()
    elif args.export:
        viewer.export_logs(args.service, args.export, args.lines)
    else:
        viewer.view_service_logs(
            service=args.service,
            lines=args.lines,
            follow=args.follow,
            grep=args.grep
        )

if __name__ == '__main__':
    main()