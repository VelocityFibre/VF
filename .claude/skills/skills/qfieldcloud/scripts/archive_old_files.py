#!/usr/bin/env python3
"""
QFieldCloud Archive Old Project Files Script
Archives old GeoPackage files to reduce sync payload
"""

import os
import sys
import subprocess
import json
from datetime import datetime, timedelta
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

def format_size(bytes_val):
    """Format bytes to human readable"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if bytes_val < 1024.0:
            return f"{bytes_val:.2f} {unit}"
        bytes_val /= 1024.0
    return f"{bytes_val:.2f} TB"

class ProjectArchiver:
    def __init__(self):
        self.vps_host = os.getenv('QFIELDCLOUD_VPS_HOST', '72.61.166.168')
        self.vps_user = os.getenv('QFIELDCLOUD_VPS_USER', 'root')
        self.vps_password = os.getenv('QFIELDCLOUD_VPS_PASSWORD')
        # The main problematic project
        self.target_project = '063a1964-42fe-4fe8-9113-291fd5e00c3d'
        self.storage_path = '/var/lib/docker/volumes/qfieldcloud_storage/_data'

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

    def find_projects(self):
        """Find all projects and their sizes"""
        print(colored("\n🔍 Finding QFieldCloud Projects", "cyan", bold=True))
        print("=" * 60)

        # Find all project directories
        cmd = f"""find {self.storage_path}/files -maxdepth 1 -type d -name '*-*-*-*' | head -20"""
        projects = self.execute_ssh_command(cmd)

        if not projects:
            print(colored("No projects found", "yellow"))
            return []

        project_list = []
        for project_dir in projects.strip().split('\n'):
            if project_dir:
                project_id = os.path.basename(project_dir)
                # Get size
                size_cmd = f"du -sb {project_dir} | awk '{{print $1}}'"
                size = self.execute_ssh_command(size_cmd)
                if size:
                    project_list.append({
                        'id': project_id,
                        'path': project_dir,
                        'size': int(size.strip())
                    })

        # Sort by size
        project_list.sort(key=lambda x: x['size'], reverse=True)

        print(f"Found {len(project_list)} projects:")
        for proj in project_list[:5]:  # Show top 5
            print(f"  {proj['id']}: {format_size(proj['size'])}")

        return project_list

    def analyze_project_files(self, project_id=None):
        """Analyze files in a specific project"""
        if not project_id:
            project_id = self.target_project

        print(colored(f"\n📊 Analyzing Project: {project_id}", "cyan", bold=True))
        print("=" * 60)

        project_path = f"{self.storage_path}/files/{project_id}"

        # Get all .gpkg files with dates
        cmd = f"""find {project_path} -name '*.gpkg' -type f -exec ls -la {{}} \\; | awk '{{print $5, $9}}' | sort -rn"""
        files = self.execute_ssh_command(cmd)

        if not files:
            print("No GeoPackage files found")
            return [], []

        file_list = []
        total_size = 0
        for line in files.strip().split('\n'):
            if line:
                parts = line.split(maxsplit=1)
                if len(parts) == 2:
                    size = int(parts[0])
                    filepath = parts[1]
                    filename = os.path.basename(filepath)
                    file_list.append({
                        'name': filename,
                        'path': filepath,
                        'size': size
                    })
                    total_size += size

        print(f"Found {len(file_list)} GeoPackage files")
        print(f"Total size: {format_size(total_size)}")

        # Categorize files by date pattern
        old_files = []
        recent_files = []
        for f in file_list:
            # Check if filename contains date pattern (e.g., 241125 = Nov 24, 2025)
            if any(month in f['name'].lower() for month in ['251125', '261125', '271125', '201125', '211125', '241125']):
                old_files.append(f)
            else:
                recent_files.append(f)

        old_size = sum(f['size'] for f in old_files)
        recent_size = sum(f['size'] for f in recent_files)

        print(f"\nNovember 2025 files: {len(old_files)} files, {format_size(old_size)}")
        print(f"Recent/Other files: {len(recent_files)} files, {format_size(recent_size)}")

        if old_files:
            print("\nFiles to archive (November 2025):")
            for f in old_files[:10]:  # Show first 10
                print(f"  {f['name']}: {format_size(f['size'])}")

        return old_files, recent_files

    def create_archive(self, files_to_archive, project_id=None):
        """Create tar.gz archive of specified files"""
        if not project_id:
            project_id = self.target_project

        if not files_to_archive:
            print(colored("No files to archive", "yellow"))
            return None

        print(colored("\n📦 Creating Archive", "cyan", bold=True))
        print("=" * 60)

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        archive_name = f"qfield_archive_{project_id[:8]}_{timestamp}.tar.gz"
        archive_path = f"/root/{archive_name}"

        # Create file list for tar
        file_list = ' '.join([f"'{f['path']}'" for f in files_to_archive])
        total_size = sum(f['size'] for f in files_to_archive)

        print(f"Archiving {len(files_to_archive)} files ({format_size(total_size)})...")
        print(f"Archive: {archive_path}")

        # Create archive
        cmd = f"tar -czf {archive_path} {file_list} 2>/dev/null"
        result = self.execute_ssh_command(cmd, timeout=300)

        # Check archive size
        size_cmd = f"ls -lh {archive_path} | awk '{{print $5}}'"
        archive_size = self.execute_ssh_command(size_cmd)

        if archive_size:
            print(colored(f"✅ Archive created: {archive_size.strip()}", "green"))
            print(f"Compression ratio: {(1 - (os.path.getsize(archive_path) if os.path.exists(archive_path) else total_size*0.3)/total_size)*100:.1f}%")
            return archive_path
        else:
            print(colored("❌ Archive creation failed", "red"))
            return None

    def remove_archived_files(self, files_to_remove, dry_run=True):
        """Remove files that have been archived"""
        if not files_to_remove:
            return

        print(colored("\n🗑️ Removing Archived Files", "cyan", bold=True))
        print("=" * 60)

        total_size = sum(f['size'] for f in files_to_remove)

        if dry_run:
            print(colored(f"DRY RUN - Would remove {len(files_to_remove)} files ({format_size(total_size)})", "yellow"))
            for f in files_to_remove[:5]:
                print(f"  Would remove: {f['name']}")
        else:
            print(f"Removing {len(files_to_remove)} files...")
            removed = 0
            for f in files_to_remove:
                cmd = f"rm -f '{f['path']}'"
                if self.execute_ssh_command(cmd):
                    removed += 1

            print(colored(f"✅ Removed {removed} files, freed {format_size(total_size)}", "green"))

    def create_restore_script(self, archive_path, files_archived):
        """Create a script to restore archived files if needed"""
        if not archive_path:
            return

        print(colored("\n📝 Creating Restore Script", "cyan", bold=True))
        print("=" * 60)

        script_path = archive_path.replace('.tar.gz', '_restore.sh')

        script_content = f"""#!/bin/bash
# Restore script for archived QFieldCloud files
# Created: {datetime.now()}
# Archive: {archive_path}

echo "Restoring {len(files_archived)} files from archive..."
tar -xzf {archive_path} -C /

echo "Files restored. You may need to restart QFieldCloud services."
"""

        cmd = f"cat > {script_path} << 'EOF'\n{script_content}\nEOF"
        self.execute_ssh_command(cmd)

        # Make executable
        self.execute_ssh_command(f"chmod +x {script_path}")

        print(f"✅ Restore script: {script_path}")

def main():
    """Main execution"""
    import argparse

    parser = argparse.ArgumentParser(description='Archive old QFieldCloud project files')
    parser.add_argument('--project', help='Specific project ID to archive')
    parser.add_argument('--dry-run', action='store_true',
                       help='Show what would be done without removing files')
    parser.add_argument('--analyze-only', action='store_true',
                       help='Only analyze files without archiving')
    parser.add_argument('--all-projects', action='store_true',
                       help='Analyze all projects')

    args = parser.parse_args()

    archiver = ProjectArchiver()

    print(colored("📦 QFieldCloud File Archiver", "cyan", bold=True))
    print(f"Server: {archiver.vps_host}")

    try:
        if args.all_projects:
            # Find and analyze all projects
            projects = archiver.find_projects()
            if projects and len(projects) > 0:
                # Focus on the largest project
                target = projects[0]
                print(colored(f"\nFocusing on largest project: {target['id']}", "cyan"))
                old_files, recent_files = archiver.analyze_project_files(target['id'])
        else:
            # Analyze target project
            project_id = args.project or archiver.target_project
            old_files, recent_files = archiver.analyze_project_files(project_id)

        if args.analyze_only:
            print(colored("\n✅ Analysis complete (no changes made)", "green"))
            return

        if old_files:
            print(colored(f"\n📊 Archive Summary", "cyan", bold=True))
            print("=" * 60)
            print(f"Files to archive: {len(old_files)}")
            print(f"Space to reclaim: {format_size(sum(f['size'] for f in old_files))}")

            if not args.dry_run:
                response = input(colored("\nProceed with archiving? (y/N): ", "yellow"))
                if response.lower() != 'y':
                    print("Aborted.")
                    return

            # Create archive
            archive_path = archiver.create_archive(old_files, project_id)

            if archive_path:
                # Create restore script
                archiver.create_restore_script(archive_path, old_files)

                # Remove files
                archiver.remove_archived_files(old_files, dry_run=args.dry_run)

                if not args.dry_run:
                    print(colored("\n✅ Archiving completed successfully!", "green", bold=True))
                    print(f"Archive saved to: {archive_path}")
                    print(f"Space reclaimed: {format_size(sum(f['size'] for f in old_files))}")
        else:
            print(colored("\nNo old files found to archive", "yellow"))

        print(colored("\n📋 Next Steps:", "cyan"))
        print("1. Document configuration: python3 document_config.py")
        print("2. Run final readiness check: ./migration_readiness.sh")

    except Exception as e:
        print(colored(f"❌ Error: {str(e)}", "red"))
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()