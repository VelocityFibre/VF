#!/usr/bin/env python3
"""
QFieldCloud Database Optimization Script
Optimizes PostgreSQL database for migration and performance
"""

import os
import sys
import subprocess
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

class DatabaseOptimizer:
    def __init__(self):
        self.vps_host = os.getenv('QFIELDCLOUD_VPS_HOST', '72.61.166.168')
        self.vps_user = os.getenv('QFIELDCLOUD_VPS_USER', 'root')
        self.vps_password = os.getenv('QFIELDCLOUD_VPS_PASSWORD')
        self.db_container = 'qfieldcloud-db-1'
        self.db_user = 'qfieldcloud_db_admin'
        self.db_name = 'qfieldcloud_db'

    def execute_ssh_command(self, command, timeout=30, show_output=False):
        """Execute command on VPS via SSH"""
        ssh_cmd = ['ssh', '-o', 'StrictHostKeyChecking=no', '-o', 'ConnectTimeout=10']

        if self.vps_password:
            ssh_cmd = ['sshpass', '-p', self.vps_password] + ssh_cmd
            ssh_cmd.extend(['-o', 'PubkeyAuthentication=no'])

        ssh_cmd.append(f'{self.vps_user}@{self.vps_host}')
        ssh_cmd.append(command)

        try:
            result = subprocess.run(ssh_cmd, capture_output=True, text=True, timeout=timeout)
            if show_output and result.stdout:
                print(result.stdout)
            return result.stdout if result.returncode == 0 else None
        except subprocess.TimeoutExpired:
            print(colored("Command timed out", "yellow"))
            return None
        except Exception as e:
            print(colored(f"Error: {str(e)}", "red"))
            return None

    def get_database_size(self):
        """Get current database size"""
        cmd = f"""docker exec {self.db_container} psql -U {self.db_user} -d {self.db_name} -t -c "
            SELECT pg_size_pretty(pg_database_size('{self.db_name}'));" 2>/dev/null"""
        result = self.execute_ssh_command(cmd)
        return result.strip() if result else "Unknown"

    def get_table_sizes(self):
        """Get sizes of largest tables"""
        cmd = f"""docker exec {self.db_container} psql -U {self.db_user} -d {self.db_name} -c "
            SELECT
                schemaname||'.'||tablename AS table,
                pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size,
                pg_total_relation_size(schemaname||'.'||tablename) as bytes
            FROM pg_tables
            WHERE schemaname NOT IN ('pg_catalog', 'information_schema')
            ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC
            LIMIT 10;" 2>/dev/null"""
        return self.execute_ssh_command(cmd)

    def backup_database(self):
        """Create database backup before optimization"""
        print(colored("\n💾 Creating Database Backup", "cyan", bold=True))
        print("=" * 60)

        backup_file = f"/root/qfield_db_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.sql"

        # Create backup
        print(f"Backing up to {backup_file}...")
        cmd = f"""docker exec {self.db_container} pg_dump -U {self.db_user} {self.db_name} > {backup_file}"""

        result = self.execute_ssh_command(cmd, timeout=300)

        # Check backup size
        size_cmd = f"ls -lh {backup_file} | awk '{{print $5}}'"
        size = self.execute_ssh_command(size_cmd)

        if size:
            print(colored(f"✅ Backup created: {backup_file} ({size.strip()})", "green"))
            return backup_file
        else:
            print(colored("⚠️  Backup may have failed", "yellow"))
            return None

    def vacuum_database(self):
        """Run VACUUM FULL ANALYZE on database"""
        print(colored("\n🔧 Running VACUUM FULL ANALYZE", "cyan", bold=True))
        print("=" * 60)
        print("This will lock tables and may take several minutes...")

        # Run VACUUM FULL on entire database
        cmd = f"""docker exec {self.db_container} psql -U {self.db_user} -d {self.db_name} -c "
            SET statement_timeout = 0;
            VACUUM FULL ANALYZE;" 2>&1"""

        result = self.execute_ssh_command(cmd, timeout=600)

        if result and "VACUUM" in result:
            print(colored("✅ VACUUM FULL completed", "green"))
            return True
        else:
            print(colored("⚠️  VACUUM may have issues", "yellow"))
            if result:
                print(result)
            return False

    def reindex_database(self):
        """Reindex all tables in database"""
        print(colored("\n🗂️ Reindexing Database", "cyan", bold=True))
        print("=" * 60)
        print("Rebuilding all indexes...")

        cmd = f"""docker exec {self.db_container} psql -U {self.db_user} -d {self.db_name} -c "
            REINDEX DATABASE {self.db_name};" 2>&1"""

        result = self.execute_ssh_command(cmd, timeout=300)

        if result and "REINDEX" in result:
            print(colored("✅ REINDEX completed", "green"))
            return True
        else:
            print(colored("⚠️  REINDEX may have issues", "yellow"))
            if result:
                print(result)
            return False

    def add_performance_indexes(self):
        """Add indexes for common query patterns"""
        print(colored("\n📈 Adding Performance Indexes", "cyan", bold=True))
        print("=" * 60)

        indexes = [
            ("idx_job_status_created", "core_job(status, created_at)", "Speed up job queue queries"),
            ("idx_job_project_created", "core_job(project_id, created_at)", "Speed up project job queries"),
            ("idx_job_type_status", "core_job(type, status)", "Speed up job type filtering"),
            ("idx_job_started_at", "core_job(started_at) WHERE started_at IS NOT NULL", "Speed up active job queries"),
            ("idx_job_finished_at", "core_job(finished_at) WHERE finished_at IS NOT NULL", "Speed up completed job queries"),
        ]

        created = 0
        for index_name, index_def, description in indexes:
            print(f"\nCreating {index_name}: {description}")
            cmd = f"""docker exec {self.db_container} psql -U {self.db_user} -d {self.db_name} -c "
                CREATE INDEX IF NOT EXISTS {index_name} ON {index_def};" 2>&1"""

            result = self.execute_ssh_command(cmd)
            if result:
                if "CREATE INDEX" in result:
                    print(colored(f"  ✅ Created: {index_name}", "green"))
                    created += 1
                elif "already exists" in result.lower():
                    print(f"  ℹ️ Already exists: {index_name}")
                else:
                    print(colored(f"  ⚠️ Issue with {index_name}", "yellow"))

        print(f"\n✅ Created {created} new indexes")
        return True

    def analyze_tables(self):
        """Update table statistics"""
        print(colored("\n📊 Updating Table Statistics", "cyan", bold=True))
        print("=" * 60)

        cmd = f"""docker exec {self.db_container} psql -U {self.db_user} -d {self.db_name} -c "
            ANALYZE;" 2>&1"""

        result = self.execute_ssh_command(cmd)
        if result and "ANALYZE" in result:
            print(colored("✅ Statistics updated", "green"))
            return True
        return False

    def check_bloat(self):
        """Check for table and index bloat"""
        print(colored("\n🔍 Checking Table Bloat", "cyan", bold=True))
        print("=" * 60)

        # Query to estimate bloat
        cmd = f"""docker exec {self.db_container} psql -U {self.db_user} -d {self.db_name} -c "
            SELECT
                schemaname || '.' || tablename AS table,
                pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS total_size,
                pg_size_pretty(pg_relation_size(schemaname||'.'||tablename)) AS table_size,
                pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename) - pg_relation_size(schemaname||'.'||tablename)) AS index_size
            FROM pg_tables
            WHERE schemaname NOT IN ('pg_catalog', 'information_schema')
            ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC
            LIMIT 5;" 2>/dev/null"""

        result = self.execute_ssh_command(cmd)
        if result:
            print("Top 5 tables by size:")
            print(result)
        return True

def main():
    """Main execution"""
    import argparse

    parser = argparse.ArgumentParser(description='QFieldCloud Database Optimization')
    parser.add_argument('--skip-backup', action='store_true',
                       help='Skip database backup (not recommended)')
    parser.add_argument('--skip-vacuum', action='store_true',
                       help='Skip VACUUM FULL')
    parser.add_argument('--skip-reindex', action='store_true',
                       help='Skip REINDEX')
    parser.add_argument('--skip-indexes', action='store_true',
                       help='Skip adding performance indexes')
    parser.add_argument('--check-only', action='store_true',
                       help='Only check database status without optimization')

    args = parser.parse_args()

    optimizer = DatabaseOptimizer()

    print(colored("🔌 QFieldCloud Database Optimization", "cyan", bold=True))
    print(f"Server: {optimizer.vps_host}")
    print("=" * 60)

    try:
        # Get initial size
        print(colored("\n📊 Initial Database Status", "cyan"))
        initial_size = optimizer.get_database_size()
        print(f"Database size: {initial_size}")

        # Show table sizes
        table_sizes = optimizer.get_table_sizes()
        if table_sizes:
            print("\nLargest tables:")
            print(table_sizes)

        if args.check_only:
            print(colored("\n✅ Check complete (no changes made)", "green"))
            return

        # Backup database
        if not args.skip_backup:
            backup_file = optimizer.backup_database()
            if not backup_file:
                response = input(colored("\n⚠️  Backup failed. Continue anyway? (y/N): ", "yellow"))
                if response.lower() != 'y':
                    print("Aborted.")
                    return

        # Run optimization steps
        if not args.skip_vacuum:
            optimizer.vacuum_database()

        if not args.skip_reindex:
            optimizer.reindex_database()

        if not args.skip_indexes:
            optimizer.add_performance_indexes()

        # Always update statistics
        optimizer.analyze_tables()

        # Check final status
        print(colored("\n📊 Final Database Status", "cyan", bold=True))
        print("=" * 60)
        final_size = optimizer.get_database_size()
        print(f"Initial size: {initial_size}")
        print(f"Final size: {final_size}")

        # Check for bloat
        optimizer.check_bloat()

        print(colored("\n✅ Database optimization completed!", "green", bold=True))
        print(colored("\n📋 Next Steps:", "cyan"))
        print("1. Archive old project files: python3 archive_old_files.py")
        print("2. Document configuration: python3 document_config.py")
        print("3. Run final readiness check: python3 migration_readiness.sh")

    except Exception as e:
        print(colored(f"❌ Error during optimization: {str(e)}", "red"))
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()