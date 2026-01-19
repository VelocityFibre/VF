#!/usr/bin/env python3
"""
VPS Monitor Dashboard Server - Prototype
Monitors VPS system resources, services, and security
"""

from http.server import HTTPServer, BaseHTTPRequestHandler
import json
import subprocess
import os
from pathlib import Path
from datetime import datetime
import re

PORT = 8889
DASHBOARD_DIR = Path(__file__).parent

# Configuration
HOSTINGER_IP = "72.60.17.245"
HOSTINGER_USER = "root"
HOSTINGER_PASS = "VeloF@2025@@"
MONITOR_MODE = "local"  # "local" or "remote" - Start with local for fast demo

def run_command(cmd):
    """Execute command locally or remotely based on MONITOR_MODE"""
    if MONITOR_MODE == "remote":
        ssh_cmd = f"sshpass -p '{HOSTINGER_PASS}' ssh -o StrictHostKeyChecking=no {HOSTINGER_USER}@{HOSTINGER_IP} '{cmd}'"
        try:
            result = subprocess.run(ssh_cmd, shell=True, capture_output=True, text=True, timeout=10)
            return result.stdout.strip(), result.returncode
        except:
            return "", 1
    else:
        # Local execution
        try:
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=5)
            return result.stdout.strip(), result.returncode
        except:
            return "", 1

def get_cpu_usage():
    """Get CPU usage percentage"""
    output, rc = run_command("top -bn1 | grep 'Cpu(s)' | awk '{print $2}' | cut -d'%' -f1")
    if rc == 0 and output:
        try:
            return float(output)
        except:
            pass
    return 0.0

def get_memory_usage():
    """Get memory usage percentage"""
    output, rc = run_command("free | grep Mem | awk '{print ($3/$2) * 100.0}'")
    if rc == 0 and output:
        try:
            return round(float(output), 1)
        except:
            pass
    return 0.0

def get_disk_usage():
    """Get disk usage percentage for root partition"""
    output, rc = run_command("df -h / | tail -1 | awk '{print $5}' | sed 's/%//'")
    if rc == 0 and output:
        try:
            return int(output)
        except:
            pass
    return 0

def get_load_average():
    """Get 1-minute load average"""
    output, rc = run_command("uptime | awk -F'load average:' '{print $2}' | awk -F',' '{print $1}' | xargs")
    if rc == 0 and output:
        return output
    return "0.0"

def get_uptime():
    """Get system uptime in human-readable format"""
    output, rc = run_command("uptime -p | sed 's/up //'")
    if rc == 0 and output:
        # Shorten format
        output = output.replace("days", "d").replace("day", "d")
        output = output.replace("hours", "h").replace("hour", "h")
        output = output.replace("minutes", "m").replace("minute", "m")
        output = output.replace(", ", " ")
        return output
    return "0d 0h"

def check_service_systemctl(service_name):
    """Check service status using systemctl"""
    output, rc = run_command(f"systemctl is-active {service_name}")
    if output == "active":
        return "ACTIVE"
    else:
        return "INACTIVE"

def check_pm2_status():
    """Check PM2 fibreflow-prod process"""
    output, rc = run_command("pm2 list | grep fibreflow-prod | awk '{print $10}'")
    if output == "online":
        return "online"
    else:
        return "STOPPED"

def check_docker_status():
    """Check if Docker daemon is running"""
    output, rc = run_command("docker ps > /dev/null 2>&1 && echo 'RUNNING' || echo 'STOPPED'")
    return output if output else "UNKNOWN"

def check_cloudflared_status():
    """Check if Cloudflare tunnel is running"""
    output, rc = run_command("ps aux | grep '[c]loudflared tunnel run' | wc -l")
    if output and int(output) > 0:
        return "RUNNING"
    else:
        return "STOPPED"

def check_firewall_status():
    """Check UFW firewall status"""
    output, rc = run_command("sudo ufw status | grep -i 'status:' | awk '{print $2}'")
    if "active" in output.lower():
        return "ACTIVE"
    else:
        return "INACTIVE"

def count_open_ports():
    """Count number of open/listening ports"""
    output, rc = run_command("ss -tln | grep LISTEN | wc -l")
    if rc == 0 and output:
        return output
    return "0"

def count_connections():
    """Count active network connections"""
    output, rc = run_command("ss -tn state established | wc -l")
    if rc == 0 and output:
        # Subtract 1 for header line
        count = int(output) - 1 if int(output) > 0 else 0
        return str(count)
    return "0"

def count_failed_ssh():
    """Count failed SSH attempts in last 24 hours"""
    output, rc = run_command("grep 'Failed password' /var/log/auth.log 2>/dev/null | grep '$(date +%b) $(date +%d)' | wc -l")
    if rc == 0 and output:
        return output
    return "0"

def count_security_updates():
    """Count available security updates"""
    output, rc = run_command("apt list --upgradable 2>/dev/null | grep -i security | wc -l")
    if rc == 0 and output:
        return output
    return "0"

def get_status_data():
    """Collect all monitoring data"""
    data = {
        "timestamp": datetime.now().isoformat(),
        "server_name": f"Hostinger VPS ({HOSTINGER_IP})" if MONITOR_MODE == "remote" else "Local Server",
        "resources": {
            "cpu_percent": get_cpu_usage(),
            "memory_percent": get_memory_usage(),
            "disk_percent": get_disk_usage(),
            "load_avg": get_load_average(),
            "uptime": get_uptime()
        },
        "services": {
            "pm2": check_pm2_status(),
            "nginx": check_service_systemctl("nginx"),
            "postgresql": check_service_systemctl("postgresql"),
            "docker": check_docker_status(),
            "cloudflared": check_cloudflared_status()
        },
        "security": {
            "firewall": check_firewall_status(),
            "open_ports": count_open_ports(),
            "connections": count_connections(),
            "failed_ssh": count_failed_ssh(),
            "updates": count_security_updates()
        }
    }

    return data

def restart_service(service_name):
    """Restart a service"""
    restart_commands = {
        "pm2": "pm2 restart fibreflow-prod",
        "nginx": "systemctl restart nginx",
        "postgresql": "systemctl restart postgresql",
        "docker": "systemctl restart docker",
        "cloudflared": "pkill cloudflared && sleep 2 && cd ~ && nohup ./cloudflared tunnel run vf-downloads > /tmp/cloudflared.log 2>&1 &"
    }

    if service_name not in restart_commands:
        return {"success": False, "error": f"Unknown service: {service_name}"}

    cmd = restart_commands[service_name]
    output, rc = run_command(cmd)

    if rc == 0 or "cloudflared" in service_name:  # cloudflared returns non-zero but works
        return {"success": True, "message": f"{service_name} restarted"}
    else:
        return {"success": False, "error": f"Restart failed: {output}"}

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

        elif self.path == '/api/vps/status':
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
        if self.path == '/api/vps/restart':
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
    mode_str = f"Remote ({HOSTINGER_IP})" if MONITOR_MODE == "remote" else "Local"

    print(f"""
╔════════════════════════════════════════════╗
║       VPS MONITOR - PROTOTYPE v1.0        ║
╠════════════════════════════════════════════╣
║                                            ║
║  Mode: {mode_str:38} ║
║  Port: {PORT:38} ║
║  Dashboard: http://localhost:{PORT}       ║
║                                            ║
║  Features:                                 ║
║  • System resources (CPU, RAM, Disk)       ║
║  • Services status (PM2, Nginx, etc.)      ║
║  • Network & security metrics              ║
║  • Manual service restart buttons          ║
║  • Auto-refresh every 30s                  ║
║                                            ║
║  Press Ctrl+C to stop                      ║
╚════════════════════════════════════════════╝
    """)

    server = HTTPServer(('0.0.0.0', PORT), MonitorHandler)
    print(f"✓ Dashboard: http://localhost:{PORT}")
    print(f"✓ API: http://localhost:{PORT}/api/vps/status")
    print()

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n✓ Server stopped")
        server.shutdown()

if __name__ == "__main__":
    main()
