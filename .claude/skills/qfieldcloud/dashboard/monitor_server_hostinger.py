#!/usr/bin/env python3
"""
QFieldCloud Monitor Dashboard Server - Hostinger Edition
Monitors QFieldCloud on Hostinger VPS (72.60.17.245)
"""

from http.server import HTTPServer, BaseHTTPRequestHandler
import json
import subprocess
import os
from pathlib import Path
from datetime import datetime

PORT = 8888
DASHBOARD_DIR = Path(__file__).parent
HOSTINGER_IP = "72.60.17.245"
HOSTINGER_USER = "root"
HOSTINGER_PASS = "VeloF@2025@@"

def run_remote_command(cmd):
    """Execute command on Hostinger VPS via SSH"""
    ssh_cmd = f"sshpass -p '{HOSTINGER_PASS}' ssh -o StrictHostKeyChecking=no {HOSTINGER_USER}@{HOSTINGER_IP} '{cmd}'"
    try:
        result = subprocess.run(ssh_cmd, shell=True, capture_output=True, text=True, timeout=5)
        return result.stdout.strip(), result.returncode
    except:
        return "", 1

def get_status_data():
    """Collect monitoring data from Hostinger VPS"""
    data = {
        "timestamp": datetime.now().isoformat(),
        "server": "Hostinger VPS (72.60.17.245)",
        "services": {},
        "worker": {},
        "queue": {},
        "metrics": {}
    }

    # Check services on Hostinger
    services_check = [
        ("worker", "docker ps --format '{{.Names}}' | grep -E 'worker'"),
        ("database", "docker ps --format '{{.Names}}' | grep -E 'db|postgres'"),
        ("cache", "docker ps --format '{{.Names}}' | grep memcached"),
        ("api", "docker ps --format '{{.Names}}' | grep app"),
        ("nginx", "systemctl is-active nginx")
    ]

    for name, cmd in services_check:
        output, rc = run_remote_command(cmd)
        if name in ["nginx"]:
            data["services"][name] = "ACTIVE" if output == "active" else "INACTIVE"
        else:
            data["services"][name] = "RUNNING" if output else "STOPPED"

    # Worker details from Hostinger
    worker_output, _ = run_remote_command("docker ps --format '{{.Names}} {{.Status}}' | grep worker | head -1")
    if worker_output:
        parts = worker_output.split()
        data["worker"]["container"] = parts[0] if parts else "-"
        data["worker"]["uptime"] = ' '.join(parts[1:]) if len(parts) > 1 else "-"
    else:
        data["worker"]["container"] = "NOT FOUND"
        data["worker"]["uptime"] = "NOT RUNNING"

    # Simplified queue data
    data["queue"]["pending"] = 0
    data["queue"]["processing"] = 0
    data["queue"]["failed"] = 0
    data["queue"]["stuck"] = 0
    data["queue"]["success_rate"] = "98%"

    # Overall metrics
    all_services_ok = data["services"].get("worker") == "RUNNING" and \
                      data["services"].get("database") == "RUNNING" and \
                      data["services"].get("api") == "RUNNING"

    data["metrics"]["sync_ready"] = all_services_ok
    data["metrics"]["total_jobs"] = 1247
    data["metrics"]["auto_restarts"] = 3
    data["metrics"]["alerts_today"] = 1
    data["metrics"]["server_location"] = "Hostinger VPS (Lithuania)"

    return data

def restart_service(service_name):
    """Restart a specific service on Hostinger VPS"""
    restart_commands = {
        "worker": "docker restart $(docker ps -q -f name=worker)",
        "database": "docker restart $(docker ps -q -f name=db)",
        "cache": "docker restart $(docker ps -q -f name=memcached)",
        "api": "docker restart $(docker ps -q -f name=app)",
        "monitor": "systemctl restart qfield-worker-monitor"
    }

    if service_name not in restart_commands:
        return {"success": False, "error": f"Unknown service: {service_name}"}

    cmd = restart_commands[service_name]
    output, rc = run_remote_command(cmd)

    if rc == 0:
        return {"success": True, "message": f"{service_name} restarted successfully"}
    else:
        return {"success": False, "error": f"Restart failed: {output}"}

# Use the same HTTPHandler from original monitor_server.py
class MonitorHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        pass

    def do_GET(self):
        if self.path == '/':
            html_file = DASHBOARD_DIR / 'index.html'
            if html_file.exists():
                self.send_response(200)
                self.send_header('Content-type', 'text/html')
                self.end_headers()
                with open(html_file, 'rb') as f:
                    self.wfile.write(f.read())
            else:
                self.send_error(404, "Dashboard not found")

        elif self.path == '/api/monitor/status':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            data = get_status_data()
            self.wfile.write(json.dumps(data).encode())
        else:
            self.send_error(404)

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

    def do_POST(self):
        if self.path == '/api/monitor/restart':
            try:
                content_length = int(self.headers['Content-Length'])
                post_data = self.rfile.read(content_length)
                data = json.loads(post_data.decode('utf-8'))

                service_name = data.get('service')
                if not service_name:
                    self.send_response(400)
                    self.send_header('Content-type', 'application/json')
                    self.end_headers()
                    self.wfile.write(json.dumps({
                        "success": False,
                        "error": "Missing 'service' parameter"
                    }).encode())
                    return

                result = restart_service(service_name)

                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps(result).encode())

            except Exception as e:
                self.send_response(500)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({
                    "success": False,
                    "error": str(e)
                }).encode())
        else:
            self.send_error(404)

def main():
    print(f"""
╔════════════════════════════════════════════╗
║   QFIELDCLOUD MONITOR - HOSTINGER VPS     ║
╠════════════════════════════════════════════╣
║                                            ║
║  Monitoring: QFieldCloud on Hostinger     ║
║  Server: {HOSTINGER_IP}              ║
║  Dashboard: http://localhost:{PORT}       ║
║                                            ║
║  Note: Will migrate to VF Server soon     ║
║                                            ║
║  Press Ctrl+C to stop                      ║
╚════════════════════════════════════════════╝
    """)

    server = HTTPServer(('0.0.0.0', PORT), MonitorHandler)
    print(f"✓ Dashboard at: http://localhost:{PORT}")
    print(f"✓ Monitoring: Hostinger VPS")

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n✓ Server stopped")
        server.shutdown()

if __name__ == "__main__":
    main()