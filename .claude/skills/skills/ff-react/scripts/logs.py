#!/home/louisdup/Agents/claude/venv/bin/python3
"""
FF_React Log Viewer
View and analyze logs from FibreFlow React application
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

class FFReactLogViewer:
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
            return result.returncode == 0, result.stdout
        except Exception as e:
            return False, str(e)

    def colorize_log_level(self, line):
        """Add colors to log levels"""
        # Error levels
        if re.search(r'\b(ERROR|FATAL|CRITICAL)\b', line, re.IGNORECASE):
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
        elif re.search(r'\b(SUCCESS|COMPLETED|DONE|OK|✅)\b', line, re.IGNORECASE):
            return f"{self.colors['green']}{line}{self.colors['reset']}"

        return line

    def format_timestamp(self, line):
        """Highlight timestamps in log lines"""
        # ISO timestamps
        pattern = r'(\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2})'
        line = re.sub(pattern, f"{self.colors['blue']}\\1{self.colors['reset']}", line)

        # PM2 timestamps
        pattern = r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})'
        line = re.sub(pattern, f"{self.colors['blue']}\\1{self.colors['reset']}", line)

        return line

    def view_pm2_logs(self, process_name, lines=50, error_only=False, follow=False):
        """View PM2 logs for a specific process"""
        print(f"\n📋 Logs for: {process_name}")
        print("=" * 60)

        # Build PM2 logs command
        cmd_parts = ['pm2', 'logs', process_name]

        if not follow:
            cmd_parts.append('--nostream')

        if error_only:
            cmd_parts.append('--err')

        cmd_parts.extend(['--lines', str(lines)])

        command = ' '.join(cmd_parts)

        if follow:
            print(f"🔄 Following logs (Ctrl+C to stop)...")
            print("-" * 60)

            # Use subprocess directly for real-time following
            ssh_cmd = ['ssh']
            ssh_options = ['-o', 'StrictHostKeyChecking=no', '-o', 'ConnectTimeout=10']
            ssh_cmd.extend(ssh_options)

            if self.server_password:
                ssh_cmd = ['sshpass', '-p', self.server_password] + ssh_cmd
                ssh_cmd.extend(['-o', 'PubkeyAuthentication=no'])

            ssh_cmd.append(f'{self.server_user}@{self.server_host}')
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

    def search_logs(self, pattern, process_name=None, context_lines=2):
        """Search for pattern in logs"""
        print(f"\n🔍 Searching for: '{pattern}'")
        print("=" * 60)

        processes_to_search = []
        if process_name:
            if process_name in self.processes:
                processes_to_search = [self.processes[process_name]]
            else:
                processes_to_search = [process_name]
        else:
            # Search all FF-related processes
            processes_to_search = ['fibreflow-prod', 'fibreflow-dev']

        total_matches = 0

        for proc in processes_to_search:
            command = f"pm2 logs {proc} --nostream --lines 1000 | grep -i -C {context_lines} '{pattern}'"
            success, output = self.execute_ssh_command(command)

            if success and output.strip():
                print(f"\n📁 {proc}:")
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

        for name, proc in [('Production', 'fibreflow-prod'), ('Development', 'fibreflow-dev')]:
            command = f"pm2 logs {proc} --err --nostream --lines 500 | grep -E 'ERROR|Error|error'"
            success, output = self.execute_ssh_command(command)

            if success and output.strip():
                print(f"\n{name}:")

                for line in output.splitlines()[:50]:  # Limit to 50 errors
                    total_errors += 1

                    # Try to categorize the error
                    if 'ECONNREFUSED' in line:
                        error_type = 'Connection Refused'
                    elif 'ENOENT' in line:
                        error_type = 'File Not Found'
                    elif 'TypeError' in line:
                        error_type = 'Type Error'
                    elif 'ReferenceError' in line:
                        error_type = 'Reference Error'
                    elif 'SyntaxError' in line:
                        error_type = 'Syntax Error'
                    elif 'timeout' in line.lower():
                        error_type = 'Timeout'
                    elif 'permission' in line.lower():
                        error_type = 'Permission Denied'
                    elif 'database' in line.lower() or 'sql' in line.lower():
                        error_type = 'Database Error'
                    else:
                        error_type = 'Other'

                    error_patterns[error_type] = error_patterns.get(error_type, 0) + 1

        if error_patterns:
            print("\n📈 Error Summary:")
            for error_type, count in sorted(error_patterns.items(), key=lambda x: x[1], reverse=True):
                percentage = (count / total_errors) * 100
                bar_length = int(percentage / 2)
                bar = '█' * bar_length
                print(f"  {error_type:20} {bar} {count} ({percentage:.1f}%)")

            print(f"\n  Total Errors: {total_errors}")
        else:
            print("✅ No errors found in recent logs")

    def export_logs(self, process_name, output_file, lines=1000):
        """Export logs to a file"""
        print(f"\n💾 Exporting logs for {process_name} to {output_file}...")

        command = f"pm2 logs {process_name} --nostream --lines {lines} --raw"
        success, output = self.execute_ssh_command(command)

        if not success:
            print(f"❌ Failed to export logs")
            return False

        try:
            with open(output_file, 'w') as f:
                f.write(output)
            print(f"✅ Logs exported to {output_file} ({len(output.splitlines())} lines)")
            return True
        except Exception as e:
            print(f"❌ Failed to write file: {e}")
            return False

def main():
    parser = argparse.ArgumentParser(description='View FF_React application logs')
    parser.add_argument(
        '--env',
        choices=['production', 'development', 'wa-monitor-prod', 'wa-monitor-dev'],
        default='production',
        help='Environment to view logs from'
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
        '--errors',
        action='store_true',
        help='Show only error logs'
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

    args = parser.parse_args()

    viewer = FFReactLogViewer()

    # Get process name
    process_name = viewer.processes.get(args.env, args.env)

    if args.search:
        viewer.search_logs(args.search, args.env)
    elif args.analyze:
        viewer.analyze_errors()
    elif args.export:
        viewer.export_logs(process_name, args.export, args.lines)
    else:
        viewer.view_pm2_logs(
            process_name,
            lines=args.lines,
            error_only=args.errors,
            follow=args.follow
        )

if __name__ == '__main__':
    main()