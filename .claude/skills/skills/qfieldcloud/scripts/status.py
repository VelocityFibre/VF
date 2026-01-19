#!/home/louisdup/Agents/claude/venv/bin/python3
"""
QFieldCloud Status Monitor
Check the status of QFieldCloud Docker services and health
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

class QFieldCloudMonitor:
    def __init__(self):
        self.vps_host = os.getenv('QFIELDCLOUD_VPS_HOST', '72.61.166.168')
        self.vps_user = os.getenv('QFIELDCLOUD_VPS_USER', 'root')
        self.vps_password = os.getenv('QFIELDCLOUD_VPS_PASSWORD')
        self.project_path = os.getenv('QFIELDCLOUD_PROJECT_PATH', '/opt/qfieldcloud')

        # Docker services to monitor
        self.services = [
            'nginx',
            'app',
            'db',
            'redis',
            'worker_wrapper',
            'minio',
            'ofelia'
        ]

    def execute_ssh_command(self, command, show_output=False):
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
                timeout=30
            )

            if show_output and result.stdout:
                print(result.stdout)

            return result.returncode == 0, result.stdout

        except subprocess.TimeoutExpired:
            return False, "Command timed out"
        except Exception as e:
            return False, str(e)

    def check_docker_services(self):
        """Check Docker container status"""
        print("🐳 Docker Services Status")
        print("=" * 60)

        command = f"cd {self.project_path} && docker compose ps --format json 2>/dev/null"
        success, output = self.execute_ssh_command(command)

        if not success:
            # Try alternative command
            command = f"cd {self.project_path} && docker ps --format json --filter label=com.docker.compose.project=qfieldcloud"
            success, output = self.execute_ssh_command(command)

        if not success:
            print("❌ Failed to get Docker status")
            return False

        try:
            # Process docker output
            containers = []
            for line in output.strip().split('\n'):
                if line:
                    try:
                        containers.append(json.loads(line))
                    except:
                        pass

            if not containers:
                # Try parsing as docker compose ps output
                command = f"cd {self.project_path} && docker compose ps"
                success, output = self.execute_ssh_command(command)

                if success:
                    print(output)
                    return True
            else:
                # Display container status
                for container in containers:
                    name = container.get('Names', container.get('Name', 'Unknown'))
                    state = container.get('State', 'unknown')
                    status = container.get('Status', '')

                    # Clean up name
                    if '/' in name:
                        name = name.replace('/', '')

                    # Find matching service
                    service_name = None
                    for service in self.services:
                        if service in name.lower():
                            service_name = service
                            break

                    if service_name:
                        status_emoji = "✅" if state == "running" else "❌"
                        print(f"\n🔹 {service_name}")
                        print(f"   Status: {status_emoji} {state}")
                        print(f"   Container: {name}")
                        print(f"   Uptime: {status}")

            return True

        except Exception as e:
            print(f"❌ Error parsing Docker output: {e}")
            return False

    def check_api_health(self):
        """Check QFieldCloud API health"""
        print("\n🏥 API Health Check")
        print("=" * 60)

        # Check main API endpoint
        command = 'curl -s -o /dev/null -w "%{http_code}" https://qfield.fibreflow.app/api/v1/status/'
        success, status_code = self.execute_ssh_command(command)

        if success:
            code = status_code.strip()
            if code == "200":
                print("✅ API Status: OK (200)")

                # Get detailed status
                command = 'curl -s https://qfield.fibreflow.app/api/v1/status/'
                success, response = self.execute_ssh_command(command)

                if success and response:
                    try:
                        status_data = json.loads(response)
                        print(f"   Database: {status_data.get('database', 'unknown')}")
                        print(f"   Storage: {status_data.get('storage', 'unknown')}")
                        print(f"   Version: {status_data.get('version', 'unknown')}")
                    except:
                        pass
            else:
                print(f"❌ API Status: {code}")
        else:
            print("❌ API health check failed")

        # Check other endpoints
        endpoints = [
            ('/swagger/', 'API Documentation'),
            ('/admin/', 'Admin Interface'),
            ('/', 'Web Interface')
        ]

        for endpoint, name in endpoints:
            command = f'curl -s -o /dev/null -w "%{{http_code}}" https://qfield.fibreflow.app{endpoint}'
            success, status_code = self.execute_ssh_command(command)

            if success:
                code = status_code.strip()
                if code in ["200", "301", "302"]:
                    print(f"✅ {name}: OK ({code})")
                else:
                    print(f"❌ {name}: {code}")

    def check_server_resources(self):
        """Check VPS resource usage"""
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

        # Docker disk usage
        command = "docker system df | grep 'Images\\|Containers\\|Volumes' | awk '{print $1 \": \" $2}'"
        success, docker_output = self.execute_ssh_command(command)
        if success and docker_output:
            print(f"\nDocker Usage:")
            for line in docker_output.strip().split('\n'):
                print(f"  {line}")

    def check_database_status(self):
        """Check PostgreSQL database status"""
        print("\n🗄️ Database Status")
        print("=" * 60)

        # Check if database container is running
        command = f"cd {self.project_path} && docker compose exec -T db pg_isready -U qfieldcloud_db_admin 2>/dev/null"
        success, output = self.execute_ssh_command(command)

        if success and "accepting connections" in output:
            print("✅ PostgreSQL is accepting connections")

            # Get database size
            command = f"""cd {self.project_path} && docker compose exec -T db psql -U qfieldcloud_db_admin -d qfieldcloud_db -c "SELECT pg_database_size('qfieldcloud_db'), pg_size_pretty(pg_database_size('qfieldcloud_db'))" -t 2>/dev/null"""
            success, size_output = self.execute_ssh_command(command)

            if success and size_output:
                size_parts = size_output.strip().split('|')
                if len(size_parts) > 1:
                    print(f"   Database Size: {size_parts[1].strip()}")
        else:
            print("❌ PostgreSQL is not responding")

    def check_recent_errors(self):
        """Check for recent errors in logs"""
        print("\n⚠️ Recent Errors (last hour)")
        print("=" * 60)

        services_to_check = ['app', 'nginx', 'worker_wrapper']

        for service in services_to_check:
            command = f"cd {self.project_path} && docker compose logs --tail 50 {service} 2>&1 | grep -i 'error\\|exception\\|failed' | tail -5"
            success, output = self.execute_ssh_command(command)

            if success and output.strip():
                print(f"\n{service}:")
                for line in output.strip().split('\n')[:5]:
                    print(f"  • {line[:100]}...")
            else:
                print(f"\n{service}: No recent errors ✅")

    def check_ssl_certificate(self):
        """Check SSL certificate status"""
        print("\n🔐 SSL Certificate Status")
        print("=" * 60)

        command = "echo | openssl s_client -servername qfield.fibreflow.app -connect qfield.fibreflow.app:443 2>/dev/null | openssl x509 -noout -dates"
        success, output = self.execute_ssh_command(command)

        if success and output:
            for line in output.strip().split('\n'):
                if 'notAfter' in line:
                    expiry = line.split('=')[1]
                    print(f"Certificate expires: {expiry}")

                    # Check if expiring soon
                    command = f"echo | openssl s_client -servername qfield.fibreflow.app -connect qfield.fibreflow.app:443 2>/dev/null | openssl x509 -noout -checkend 604800"
                    success, check_output = self.execute_ssh_command(command)

                    if success:
                        if "will not expire" in check_output:
                            print("✅ Certificate valid for more than 7 days")
                        else:
                            print("⚠️ Certificate expires within 7 days!")
        else:
            print("❌ Could not check certificate status")

    def monitor(self, detailed=False):
        """Run complete monitoring check"""
        print(f"\n🔍 QFieldCloud Status Monitor")
        print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"🖥️ Server: {self.vps_host}")
        print(f"🌐 URL: https://qfield.fibreflow.app")
        print("=" * 60)

        # Run all checks
        self.check_docker_services()
        self.check_api_health()
        self.check_server_resources()
        self.check_database_status()

        if detailed:
            self.check_recent_errors()
            self.check_ssl_certificate()

        print("\n" + "=" * 60)
        print("✅ Status check complete")

def main():
    parser = argparse.ArgumentParser(description='Monitor QFieldCloud status')
    parser.add_argument(
        '--detailed',
        action='store_true',
        help='Show detailed checks including errors and SSL'
    )
    parser.add_argument(
        '--json',
        action='store_true',
        help='Output in JSON format (coming soon)'
    )

    args = parser.parse_args()

    monitor = QFieldCloudMonitor()
    monitor.monitor(detailed=args.detailed)

if __name__ == '__main__':
    main()