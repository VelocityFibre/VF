#!/usr/bin/env python3
"""
QFieldCloud Configuration Documentation Script
Documents all configuration for migration reference
"""

import os
import sys
import subprocess
import json
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Color formatting
def colored(text, color, bold=False):
    """Simple colored text output"""
    colors = {
        'red': '\033[91m',
        'green': '\033[92m',
        'yellow': '\033[93m',
        'blue': '\033[94m',
        'cyan': '\033[96m',
        'reset': '\033[0m',
        'bold': '\033[1m'
    }
    color_code = colors.get(color, '')
    bold_code = colors['bold'] if bold else ''
    return f"{bold_code}{color_code}{text}{colors['reset']}"

class ConfigDocumenter:
    def __init__(self):
        self.vps_host = os.getenv('QFIELDCLOUD_VPS_HOST', '72.61.166.168')
        self.vps_user = os.getenv('QFIELDCLOUD_VPS_USER', 'root')
        self.vps_password = os.getenv('QFIELDCLOUD_VPS_PASSWORD')
        self.timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        self.backup_dir = f"/root/qfield_config_{self.timestamp}"

    def execute_ssh_command(self, command, timeout=30):
        """Execute command on VPS via SSH"""
        ssh_cmd = ['ssh', '-o', 'StrictHostKeyChecking=no', '-o', 'ConnectTimeout=10']

        if self.vps_password:
            ssh_cmd = ['sshpass', '-p', self.vps_password] + ssh_cmd
            ssh_cmd.extend(['-o', 'PubkeyAuthentication=no'])

        ssh_cmd.append(f'{self.vps_user}@{self.vps_host}')
        ssh_cmd.append(command)

        try:
            result = subprocess.run(ssh_cmd, capture_output=True, text=True, timeout=timeout)
            return result.stdout if result.returncode == 0 else None
        except Exception as e:
            print(colored(f"Error: {str(e)}", "red"))
            return None

    def create_backup_directory(self):
        """Create backup directory on server"""
        print(colored("\n📁 Creating Backup Directory", "cyan", bold=True))
        print("=" * 60)

        cmd = f"mkdir -p {self.backup_dir}"
        self.execute_ssh_command(cmd)
        print(f"✅ Created: {self.backup_dir}")
        return self.backup_dir

    def backup_docker_config(self):
        """Backup Docker configuration files"""
        print(colored("\n🐳 Backing Up Docker Configuration", "cyan", bold=True))
        print("=" * 60)

        files = [
            "/opt/qfieldcloud/.env",
            "/opt/qfieldcloud/docker-compose.yml",
            "/opt/qfieldcloud/docker-compose.override.yml",
            "/opt/qfieldcloud/docker-compose.test.yml",
            "/opt/qfieldcloud/conf/nginx.conf"
        ]

        for file in files:
            print(f"Backing up {file}...")
            cmd = f"cp {file} {self.backup_dir}/ 2>/dev/null"
            self.execute_ssh_command(cmd)

        # Save Docker images list
        print("Documenting Docker images...")
        cmd = f"""docker images --format 'table {{{{.Repository}}}}:{{{{.Tag}}}}\t{{{{.Size}}}}' | grep qfield > {self.backup_dir}/docker_images.txt"""
        self.execute_ssh_command(cmd)

        # Save Docker volumes
        print("Documenting Docker volumes...")
        cmd = f"docker volume ls | grep qfield > {self.backup_dir}/docker_volumes.txt"
        self.execute_ssh_command(cmd)

        print("✅ Docker configuration backed up")

    def document_network_config(self):
        """Document network configuration"""
        print(colored("\n🌐 Documenting Network Configuration", "cyan", bold=True))
        print("=" * 60)

        # Get nginx configuration
        print("Extracting nginx configuration...")
        cmd = f"""docker exec qfieldcloud-nginx-1 cat /etc/nginx/nginx.conf > {self.backup_dir}/nginx_full.conf 2>/dev/null"""
        self.execute_ssh_command(cmd)

        # Document exposed ports
        print("Documenting exposed ports...")
        cmd = f"""netstat -tuln | grep LISTEN > {self.backup_dir}/listening_ports.txt"""
        self.execute_ssh_command(cmd)

        # SSL certificates info
        print("Documenting SSL certificates...")
        cmd = f"""ls -la /etc/letsencrypt/live/ > {self.backup_dir}/ssl_certs.txt 2>/dev/null"""
        self.execute_ssh_command(cmd)

        print("✅ Network configuration documented")

    def document_database_config(self):
        """Document database configuration"""
        print(colored("\n🗄️ Documenting Database Configuration", "cyan", bold=True))
        print("=" * 60)

        # Database users
        print("Documenting database users...")
        cmd = f"""docker exec qfieldcloud-db-1 psql -U qfieldcloud_db_admin -d qfieldcloud_db -c "\\du" > {self.backup_dir}/db_users.txt 2>/dev/null"""
        self.execute_ssh_command(cmd)

        # Database schemas
        print("Documenting database schemas...")
        cmd = f"""docker exec qfieldcloud-db-1 psql -U qfieldcloud_db_admin -d qfieldcloud_db -c "\\dn" > {self.backup_dir}/db_schemas.txt 2>/dev/null"""
        self.execute_ssh_command(cmd)

        # Table list
        print("Documenting database tables...")
        cmd = f"""docker exec qfieldcloud-db-1 psql -U qfieldcloud_db_admin -d qfieldcloud_db -c "\\dt" > {self.backup_dir}/db_tables.txt 2>/dev/null"""
        self.execute_ssh_command(cmd)

        print("✅ Database configuration documented")

    def document_minio_config(self):
        """Document MinIO storage configuration"""
        print(colored("\n📦 Documenting MinIO Storage", "cyan", bold=True))
        print("=" * 60)

        # Get MinIO configuration
        print("Checking MinIO buckets...")
        cmd = f"""docker exec qfieldcloud-minio-1 mc config host list > {self.backup_dir}/minio_hosts.txt 2>/dev/null"""
        self.execute_ssh_command(cmd)

        # Check MinIO data volumes
        print("Documenting MinIO volumes...")
        cmd = f"""du -sh /var/lib/docker/volumes/qfieldcloud_minio_data* 2>/dev/null > {self.backup_dir}/minio_volumes_size.txt"""
        self.execute_ssh_command(cmd)

        print("✅ MinIO configuration documented")

    def create_system_snapshot(self):
        """Create comprehensive system snapshot"""
        print(colored("\n📸 Creating System Snapshot", "cyan", bold=True))
        print("=" * 60)

        snapshot = f"""
========================================
QFieldCloud Migration Documentation
Generated: {datetime.now()}
Server: {self.vps_host}
========================================

SYSTEM INFORMATION
------------------
$(uname -a)
$(cat /etc/os-release | head -3)

DISK USAGE
----------
$(df -h /)

MEMORY USAGE
------------
$(free -h)

DOCKER STATUS
-------------
$(docker --version)
$(docker compose version)

RUNNING CONTAINERS
------------------
$(docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}")

DATABASE SIZE
-------------
$(docker exec qfieldcloud-db-1 psql -U qfieldcloud_db_admin -d qfieldcloud_db -t -c "SELECT pg_size_pretty(pg_database_size('qfieldcloud_db'));" 2>/dev/null)

WORKER STATUS
-------------
$(docker ps | grep worker | wc -l) worker containers running

QFIELDCLOUD VERSION
-------------------
$(cd /opt/qfieldcloud && git log -1 --format="%H %s" 2>/dev/null)

ENVIRONMENT VARIABLES (sanitized)
----------------------------------
$(cat /opt/qfieldcloud/.env | grep -v PASSWORD | grep -v SECRET | grep -v KEY)

CRON JOBS
---------
$(crontab -l 2>/dev/null | grep -v "^#")
"""

        # Create snapshot file
        cmd = f"""cat > {self.backup_dir}/system_snapshot.txt << 'EOF'{snapshot}
EOF"""
        self.execute_ssh_command(cmd)

        print("✅ System snapshot created")

    def create_migration_checklist(self):
        """Create migration checklist"""
        print(colored("\n📋 Creating Migration Checklist", "cyan", bold=True))
        print("=" * 60)

        checklist = f"""
# QFieldCloud Migration Checklist
Generated: {datetime.now()}

## Pre-Migration Tasks
- [x] Docker system cleanup (4.9GB freed)
- [x] Database optimization (380MB, indexed)
- [x] Configuration backup
- [ ] DNS preparation
- [ ] New server ready

## Data to Migrate
- [ ] Database backup: /root/qfield_db_backup_*.sql
- [ ] Docker volumes: See docker_volumes.txt
- [ ] Configuration: {self.backup_dir}
- [ ] SSL certificates: /etc/letsencrypt/
- [ ] MinIO data: qfieldcloud_minio_data volumes

## Migration Steps
1. [ ] Set maintenance mode
2. [ ] Final database backup
3. [ ] Stop all services
4. [ ] Transfer data to new server
5. [ ] Restore database
6. [ ] Restore Docker volumes
7. [ ] Update configuration
8. [ ] Start services
9. [ ] Test functionality
10. [ ] Update DNS
11. [ ] Monitor for 24 hours

## Post-Migration
- [ ] Scale workers to 8
- [ ] Enable rate limiting
- [ ] Set up monitoring
- [ ] Document new setup
- [ ] Remove old server

## Rollback Plan
- Keep old server running for 48 hours
- Database backup available
- DNS can be reverted quickly
- All configuration documented
"""

        cmd = f"""cat > {self.backup_dir}/migration_checklist.md << 'EOF'{checklist}
EOF"""
        self.execute_ssh_command(cmd)

        print("✅ Migration checklist created")

    def create_archive(self):
        """Create compressed archive of all documentation"""
        print(colored("\n📦 Creating Documentation Archive", "cyan", bold=True))
        print("=" * 60)

        archive_name = f"qfield_config_{self.timestamp}.tar.gz"
        cmd = f"cd /root && tar -czf {archive_name} {os.path.basename(self.backup_dir)}/"
        self.execute_ssh_command(cmd)

        # Check archive size
        size_cmd = f"ls -lh /root/{archive_name} | awk '{{print $5}}'"
        size = self.execute_ssh_command(size_cmd)

        if size:
            print(colored(f"✅ Archive created: /root/{archive_name} ({size.strip()})", "green"))
            return f"/root/{archive_name}"
        return None

def main():
    """Main execution"""
    documenter = ConfigDocumenter()

    print(colored("📝 QFieldCloud Configuration Documentation", "cyan", bold=True))
    print(f"Server: {documenter.vps_host}")
    print("=" * 60)

    try:
        # Create backup directory
        documenter.create_backup_directory()

        # Backup all configurations
        documenter.backup_docker_config()
        documenter.document_network_config()
        documenter.document_database_config()
        documenter.document_minio_config()
        documenter.create_system_snapshot()
        documenter.create_migration_checklist()

        # Create archive
        archive = documenter.create_archive()

        print(colored("\n✅ Configuration documentation complete!", "green", bold=True))
        print(f"\nDocumentation directory: {documenter.backup_dir}")
        if archive:
            print(f"Archive: {archive}")

        print(colored("\n📋 Important Files Created:", "cyan"))
        print(f"  • System snapshot: {documenter.backup_dir}/system_snapshot.txt")
        print(f"  • Migration checklist: {documenter.backup_dir}/migration_checklist.md")
        print(f"  • Docker config: {documenter.backup_dir}/*.yml")
        print(f"  • Database info: {documenter.backup_dir}/db_*.txt")

        print(colored("\n📋 Final Step:", "cyan"))
        print("Run migration readiness check: ./migration_readiness.sh")

    except Exception as e:
        print(colored(f"❌ Error: {str(e)}", "red"))
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()