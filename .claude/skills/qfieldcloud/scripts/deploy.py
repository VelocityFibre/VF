#!/home/louisdup/Agents/claude/venv/bin/python3
"""
QFieldCloud Deployment Script
Deploy QFieldCloud updates from GitHub to production
"""

import os
import sys
import argparse
import subprocess
from datetime import datetime
from pathlib import Path

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

class QFieldCloudDeployer:
    def __init__(self):
        self.vps_host = os.getenv('QFIELDCLOUD_VPS_HOST', '72.61.166.168')
        self.vps_user = os.getenv('QFIELDCLOUD_VPS_USER', 'root')
        self.vps_password = os.getenv('QFIELDCLOUD_VPS_PASSWORD')
        self.project_path = os.getenv('QFIELDCLOUD_PROJECT_PATH', '/opt/qfieldcloud')

    def execute_ssh_command(self, command, show_output=True):
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
                timeout=600  # 10 minute timeout for long operations
            )

            if show_output:
                if result.stdout:
                    print(result.stdout)
                if result.stderr and result.returncode != 0:
                    print(f"⚠️  Warning: {result.stderr}", file=sys.stderr)

            return result.returncode == 0, result.stdout

        except subprocess.TimeoutExpired:
            print("❌ Command timed out after 10 minutes")
            return False, ""
        except Exception as e:
            print(f"❌ SSH command failed: {e}")
            return False, ""

    def backup_database(self):
        """Create database backup before deployment"""
        print("💾 Creating database backup...")

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_file = f"qfieldcloud_backup_{timestamp}.sql"

        command = f"""cd {self.project_path} && \
            docker compose exec -T db pg_dump -U qfieldcloud_db_admin qfieldcloud_db > /tmp/{backup_file} && \
            echo "Backup saved to /tmp/{backup_file}" """

        success, output = self.execute_ssh_command(command)

        if success:
            print(f"✅ Database backup created: /tmp/{backup_file}")
            return True
        else:
            print("❌ Failed to create database backup")
            return False

    def check_git_status(self):
        """Check git status before deployment"""
        print("📊 Checking git status...")

        command = f"cd {self.project_path} && git status --short"
        success, output = self.execute_ssh_command(command)

        if output.strip():
            print("⚠️  Warning: Uncommitted changes detected:")
            print(output)
            response = input("Continue with deployment? (y/N): ")
            if response.lower() != 'y':
                return False

        # Check current branch
        command = f"cd {self.project_path} && git branch --show-current"
        success, branch = self.execute_ssh_command(command)

        if success:
            print(f"Current branch: {branch.strip()}")

        return True

    def pull_latest_code(self, branch='master'):
        """Pull latest code from GitHub"""
        print(f"📥 Pulling latest code from {branch} branch...")

        commands = [
            f"cd {self.project_path}",
            f"git fetch origin",
            f"git checkout {branch}",
            f"git pull origin {branch}"
        ]

        command = " && ".join(commands)
        success, output = self.execute_ssh_command(command)

        if not success:
            print("❌ Failed to pull latest code")
            return False

        print("✅ Code updated successfully")
        return True

    def update_submodules(self):
        """Update git submodules"""
        print("📦 Updating submodules...")

        command = f"cd {self.project_path} && git submodule update --recursive"
        success, output = self.execute_ssh_command(command)

        if success:
            print("✅ Submodules updated")
            return True
        else:
            print("⚠️  Failed to update submodules (may not have any)")
            return True  # Don't fail deployment if no submodules

    def build_docker_images(self):
        """Build Docker images"""
        print("🔨 Building Docker images (this may take several minutes)...")

        command = f"cd {self.project_path} && docker compose build"
        success, output = self.execute_ssh_command(command, show_output=False)

        if not success:
            print("❌ Failed to build Docker images")
            return False

        print("✅ Docker images built successfully")
        return True

    def run_migrations(self):
        """Run Django database migrations"""
        print("🔄 Running database migrations...")

        command = f"cd {self.project_path} && docker compose exec -T app python manage.py migrate"
        success, output = self.execute_ssh_command(command)

        if not success:
            print("❌ Failed to run migrations")
            return False

        print("✅ Migrations completed")
        return True

    def collect_static_files(self):
        """Collect Django static files"""
        print("📁 Collecting static files...")

        command = f"cd {self.project_path} && docker compose exec -T app python manage.py collectstatic --noinput"
        success, output = self.execute_ssh_command(command, show_output=False)

        if not success:
            print("❌ Failed to collect static files")
            return False

        print("✅ Static files collected")
        return True

    def restart_services(self, service=None):
        """Restart Docker services"""
        if service:
            print(f"🔄 Restarting {service} service...")
            command = f"cd {self.project_path} && docker compose restart {service}"
        else:
            print("🔄 Restarting all services...")
            command = f"cd {self.project_path} && docker compose restart"

        success, output = self.execute_ssh_command(command)

        if not success:
            print(f"❌ Failed to restart {'services' if not service else service}")
            return False

        print(f"✅ {'Services' if not service else service} restarted")
        return True

    def verify_deployment(self):
        """Verify deployment is working"""
        print("🔍 Verifying deployment...")

        # Check API status
        command = 'curl -s -o /dev/null -w "%{http_code}" https://qfield.fibreflow.app/api/v1/status/'
        success, output = self.execute_ssh_command(command, show_output=False)

        if success and output.strip() == "200":
            print("✅ API is responding (200 OK)")

            # Check all services are running
            command = f"cd {self.project_path} && docker compose ps | grep -c 'Up'"
            success, count = self.execute_ssh_command(command, show_output=False)

            if success and int(count.strip()) > 0:
                print(f"✅ {count.strip()} services are running")
                return True
        else:
            print("⚠️  API may not be responding correctly")

        return False

    def deploy(self, branch='master', skip_backup=False, skip_build=False,
               migrate=True, collectstatic=True, restart=True):
        """Main deployment process"""
        print(f"\n🚀 Deploying QFieldCloud")
        print(f"   Server: {self.vps_host}")
        print(f"   Branch: {branch}")
        print(f"   Path: {self.project_path}")
        print("="*50)

        # Deployment steps
        steps = []

        if not skip_backup:
            steps.append(("Database Backup", lambda: self.backup_database()))

        steps.extend([
            ("Git Status Check", lambda: self.check_git_status()),
            ("Pull Latest Code", lambda: self.pull_latest_code(branch)),
            ("Update Submodules", lambda: self.update_submodules()),
        ])

        if not skip_build:
            steps.append(("Build Docker Images", lambda: self.build_docker_images()))

        if migrate:
            steps.append(("Run Migrations", lambda: self.run_migrations()))

        if collectstatic:
            steps.append(("Collect Static Files", lambda: self.collect_static_files()))

        if restart:
            steps.append(("Restart Services", lambda: self.restart_services()))

        steps.append(("Verify Deployment", lambda: self.verify_deployment()))

        # Execute steps
        for step_name, step_func in steps:
            print(f"\n▶️  {step_name}...")
            if not step_func():
                print(f"\n❌ Deployment failed at: {step_name}")

                if step_name != "Database Backup":
                    print("\n⚠️  Consider restoring from backup if issues persist")

                return False

        print("\n✅ Deployment completed successfully!")
        print(f"🌐 Application available at: https://qfield.fibreflow.app")
        return True

    def rollback(self, commit_hash):
        """Rollback to a specific commit"""
        print(f"⏮️ Rolling back to commit: {commit_hash}")

        commands = [
            f"cd {self.project_path}",
            f"git reset --hard {commit_hash}",
            "docker compose build",
            "docker compose up -d"
        ]

        for cmd in commands:
            success, output = self.execute_ssh_command(cmd)
            if not success:
                print(f"❌ Rollback failed at: {cmd}")
                return False

        print("✅ Rollback completed")
        return True

def main():
    parser = argparse.ArgumentParser(description='Deploy QFieldCloud application')
    parser.add_argument(
        '--branch',
        default='master',
        help='Git branch to deploy (default: master)'
    )
    parser.add_argument(
        '--skip-backup',
        action='store_true',
        help='Skip database backup'
    )
    parser.add_argument(
        '--skip-build',
        action='store_true',
        help='Skip Docker image build'
    )
    parser.add_argument(
        '--no-migrate',
        action='store_true',
        help='Skip database migrations'
    )
    parser.add_argument(
        '--no-collectstatic',
        action='store_true',
        help='Skip collecting static files'
    )
    parser.add_argument(
        '--no-restart',
        action='store_true',
        help='Skip service restart'
    )
    parser.add_argument(
        '--rollback',
        help='Rollback to specific commit hash'
    )

    args = parser.parse_args()

    # Safety check for production
    if not args.skip_backup and args.branch == 'master':
        print("\n⚠️  WARNING: Deploying to PRODUCTION")
        print("   A database backup will be created")
        response = input("Continue? (type 'yes' to proceed): ")
        if response.lower() != 'yes':
            print("Deployment cancelled")
            sys.exit(0)

    deployer = QFieldCloudDeployer()

    if args.rollback:
        success = deployer.rollback(args.rollback)
    else:
        success = deployer.deploy(
            branch=args.branch,
            skip_backup=args.skip_backup,
            skip_build=args.skip_build,
            migrate=not args.no_migrate,
            collectstatic=not args.no_collectstatic,
            restart=not args.no_restart
        )

    sys.exit(0 if success else 1)

if __name__ == '__main__':
    main()