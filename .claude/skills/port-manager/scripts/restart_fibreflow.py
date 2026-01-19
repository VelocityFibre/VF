#!/usr/bin/env python3
"""
Safely restart FibreFlow on port 3005
Handles multiple instances, ensures clean restart
"""
import subprocess
import time
import json
import os
import sys

def execute_on_server(cmd):
    """Execute command on VF server"""
    password = os.getenv('VF_SERVER_PASSWORD', 'VeloAdmin2025!')
    execute_script = os.path.join(os.path.dirname(__file__), '../../vf-server/scripts/execute.py')

    result = subprocess.run(
        [execute_script, cmd],
        env={'VF_SERVER_PASSWORD': password},
        capture_output=True,
        text=True
    )

    if result.returncode != 0:
        return None, result.stderr

    try:
        output = json.loads(result.stdout)
        return output.get('output', ''), output.get('error')
    except:
        return result.stdout, result.stderr

def restart_fibreflow():
    """Safely restart FibreFlow service"""

    print("🔄 Restarting FibreFlow on port 3005...")
    print("-" * 50)

    # Step 1: Check current status
    print("📍 Checking current processes...")
    output, error = execute_on_server('ps aux | grep "[n]ext-server" | grep -v grep')

    if output:
        print("Current Next.js processes:")
        for line in output.strip().split('\n'):
            parts = line.split()
            if len(parts) > 10:
                user = parts[0]
                pid = parts[1]
                print(f"  • User: {user:8} PID: {pid}")

    # Step 2: Find processes on port 3005
    print("\n🔍 Identifying processes on port 3005...")
    output, error = execute_on_server('lsof -ti:3005 2>/dev/null')

    pids = []
    if output:
        pids = output.strip().split('\n')
        print(f"  Found PIDs on port 3005: {', '.join(pids)}")

    # Step 3: Kill all processes on port 3005
    if pids:
        print("\n⚠️  Stopping existing processes...")
        for pid in pids:
            if pid.strip():
                cmd = f'kill -9 {pid} 2>/dev/null'
                execute_on_server(cmd)
                print(f"  • Killed PID {pid}")

        # Wait for port to be released
        time.sleep(3)

    # Step 4: Ensure environment is loaded
    print("\n🔧 Setting up environment...")

    # Check if .env.production exists and has DATABASE_URL
    output, error = execute_on_server('cat /srv/data/apps/fibreflow/.env.production 2>/dev/null | grep DATABASE_URL | head -1')

    if not output or 'DATABASE_URL' not in output:
        print("❌ DATABASE_URL not found in .env.production!")
        return False

    print("  ✅ DATABASE_URL configured")

    # Step 5: Start FibreFlow with proper environment
    print("\n🚀 Starting FibreFlow...")

    start_cmd = '''
    cd /srv/data/apps/fibreflow && \
    source .env.production && \
    export DATABASE_URL && \
    PORT=3005 NODE_ENV=production nohup npm run start </dev/null >/tmp/fibreflow.log 2>&1 & \
    echo $!
    '''

    output, error = execute_on_server(start_cmd)

    if output:
        new_pid = output.strip().split('\n')[-1]
        print(f"  • Started with PID: {new_pid}")

    # Step 6: Wait for startup
    print("\n⏳ Waiting for service to start...")
    time.sleep(8)

    # Step 7: Verify it's running
    print("\n✅ Verifying service status...")

    # Check if port is listening
    output, error = execute_on_server('ss -tlnp 2>/dev/null | grep :3005')

    if output and '3005' in output:
        print("  ✅ Port 3005 is listening")
    else:
        print("  ❌ Port 3005 is NOT listening")

        # Check logs for errors
        output, error = execute_on_server('tail -20 /tmp/fibreflow.log 2>/dev/null')
        if output:
            print("\n📋 Recent logs:")
            print(output)

        return False

    # Step 8: Test the API
    print("\n🧪 Testing API endpoint...")
    test_cmd = 'curl -s -w "\\n%{http_code}" "http://localhost:3005/api/foto-reviews/pending?limit=1" | tail -1'
    output, error = execute_on_server(test_cmd)

    if output:
        status_code = output.strip()
        if status_code == '200':
            print(f"  ✅ API responding with status: {status_code}")
        elif status_code == '500':
            print(f"  ⚠️  API returned error: {status_code}")
            print("  Note: This might be an application error, not a port issue")
        else:
            print(f"  ❓ API status: {status_code}")

    # Final status
    print("\n" + "=" * 50)
    output, error = execute_on_server('ps aux | grep "[n]ext-server" | grep 3005')

    if output:
        print("✅ FibreFlow restarted successfully!")
        print(f"🌐 Access at: http://100.96.203.105:3005/")
    else:
        print("⚠️  FibreFlow may not have started correctly")
        print("Check logs at: /tmp/fibreflow.log")

    return True

if __name__ == '__main__':
    restart_fibreflow()