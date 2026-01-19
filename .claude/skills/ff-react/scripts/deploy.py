#!/home/louisdup/Agents/claude/venv/bin/python3
"""
FF_React Deployment Script
Deploy FibreFlow React application to production or development environment
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

class FFReactDeployer:
    def __init__(self):
        self.server_host = os.getenv('VF_SERVER_HOST', '100.96.203.105')
        self.server_user = os.getenv('VF_SERVER_USER', 'louis')
        self.server_password = os.getenv('VF_SERVER_PASSWORD')

        # Environment configurations
        self.environments = {
            'production': {
                'path': '/var/www/fibreflow',
                'branch': 'master',
                'process': 'fibreflow-prod',
                'port': 3005,
                'url': 'app.fibreflow.app'
            },
            'development': {
                'path': '/var/www/fibreflow-dev',
                'branch': 'develop',
                'process': 'fibreflow-dev',
                'port': 3006,
                'url': 'dev.fibreflow.app'
            }
        }

    def execute_ssh_command(self, command, show_output=True):
        """Execute command on remote server via SSH"""
        ssh_cmd = ['ssh']

        # Add SSH options
        ssh_options = [
            '-o', 'StrictHostKeyChecking=no',
            '-o', 'ConnectTimeout=10'
        ]
        ssh_cmd.extend(ssh_options)

        # Add password if available (using sshpass)
        if self.server_password:
            ssh_cmd = ['sshpass', '-p', self.server_password] + ssh_cmd
            ssh_cmd.extend(['-o', 'PubkeyAuthentication=no'])

        # Add user@host and command
        ssh_cmd.append(f'{self.server_user}@{self.server_host}')
        ssh_cmd.append(command)

        try:
            result = subprocess.run(
                ssh_cmd,
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout for long operations
            )

            if show_output:
                if result.stdout:
                    print(result.stdout)
                if result.stderr and result.returncode != 0:
                    print(f"⚠️  Warning: {result.stderr}", file=sys.stderr)

            return result.returncode == 0, result.stdout

        except subprocess.TimeoutExpired:
            print("❌ Command timed out after 5 minutes")
            return False, ""
        except Exception as e:
            print(f"❌ SSH command failed: {e}")
            return False, ""

    def check_git_status(self, env_config):
        """Check git status before deployment"""
        print("📊 Checking git status...")

        command = f"cd {env_config['path']} && git status --short"
        success, output = self.execute_ssh_command(command)

        if output.strip():
            print("⚠️  Warning: Uncommitted changes detected:")
            print(output)
            response = input("Continue with deployment? (y/N): ")
            if response.lower() != 'y':
                return False

        return True

    def pull_latest_code(self, env_config):
        """Pull latest code from git"""
        print(f"📥 Pulling latest code from {env_config['branch']} branch...")

        commands = [
            f"cd {env_config['path']}",
            f"git fetch origin",
            f"git checkout {env_config['branch']}",
            f"git pull origin {env_config['branch']}"
        ]

        command = " && ".join(commands)
        success, output = self.execute_ssh_command(command)

        if not success:
            print("❌ Failed to pull latest code")
            return False

        print("✅ Code updated successfully")
        return True

    def install_dependencies(self, env_config):
        """Install npm dependencies"""
        print("📦 Installing dependencies...")

        command = f"cd {env_config['path']} && npm ci"
        success, output = self.execute_ssh_command(command, show_output=False)

        if not success:
            print("❌ Failed to install dependencies")
            return False

        print("✅ Dependencies installed")
        return True

    def build_application(self, env_config):
        """Build Next.js application"""
        print("🔨 Building application (this may take a few minutes)...")

        command = f"cd {env_config['path']} && npm run build"
        success, output = self.execute_ssh_command(command, show_output=False)

        if not success:
            print("❌ Build failed")
            print(output)
            return False

        print("✅ Build completed successfully")
        return True

    def restart_pm2_process(self, env_config):
        """Restart PM2 process"""
        print(f"🔄 Restarting PM2 process: {env_config['process']}...")

        command = f"pm2 restart {env_config['process']}"
        success, output = self.execute_ssh_command(command)

        if not success:
            print("❌ Failed to restart PM2 process")
            return False

        print("✅ Application restarted")
        return True

    def verify_deployment(self, env_config):
        """Verify deployment is working"""
        print("🔍 Verifying deployment...")

        # Check PM2 status
        command = f"pm2 show {env_config['process']} | grep status"
        success, output = self.execute_ssh_command(command, show_output=False)

        if "online" in output.lower():
            print(f"✅ Application is running at https://{env_config['url']}")
            return True
        else:
            print("⚠️  Application may not be running correctly")
            return False

    def deploy(self, environment, skip_build=False, force_restart=False):
        """Main deployment process"""
        if environment not in self.environments:
            print(f"❌ Unknown environment: {environment}")
            print(f"   Available: {', '.join(self.environments.keys())}")
            return False

        env_config = self.environments[environment]

        print(f"\n🚀 Deploying FF_React to {environment.upper()}")
        print(f"   URL: https://{env_config['url']}")
        print(f"   Branch: {env_config['branch']}")
        print(f"   Path: {env_config['path']}")
        print("="*50)

        # Deployment steps
        steps = [
            ("Git Status Check", lambda: self.check_git_status(env_config)),
            ("Pull Latest Code", lambda: self.pull_latest_code(env_config)),
            ("Install Dependencies", lambda: self.install_dependencies(env_config)),
        ]

        if not skip_build:
            steps.append(("Build Application", lambda: self.build_application(env_config)))

        steps.append(("Restart PM2", lambda: self.restart_pm2_process(env_config)))
        steps.append(("Verify Deployment", lambda: self.verify_deployment(env_config)))

        # Execute steps
        for step_name, step_func in steps:
            print(f"\n▶️  {step_name}...")
            if not step_func():
                print(f"\n❌ Deployment failed at: {step_name}")

                if force_restart:
                    print("⚠️  Force restart requested, attempting PM2 restart anyway...")
                    self.restart_pm2_process(env_config)

                return False

        print("\n✅ Deployment completed successfully!")
        print(f"🌐 Application available at: https://{env_config['url']}")
        return True

def main():
    parser = argparse.ArgumentParser(description='Deploy FF_React application')
    parser.add_argument(
        '--env',
        choices=['production', 'development'],
        required=True,
        help='Deployment environment'
    )
    parser.add_argument(
        '--skip-build',
        action='store_true',
        help='Skip build step (use existing build)'
    )
    parser.add_argument(
        '--force-restart',
        action='store_true',
        help='Force PM2 restart even if deployment fails'
    )

    args = parser.parse_args()

    # Safety check for production
    if args.env == 'production':
        print("\n⚠️  WARNING: Deploying to PRODUCTION")
        response = input("Are you sure? (type 'yes' to continue): ")
        if response.lower() != 'yes':
            print("Deployment cancelled")
            sys.exit(0)

    deployer = FFReactDeployer()
    success = deployer.deploy(
        args.env,
        skip_build=args.skip_build,
        force_restart=args.force_restart
    )

    sys.exit(0 if success else 1)

if __name__ == '__main__':
    main()