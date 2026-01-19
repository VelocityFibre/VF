#!/usr/bin/env python3
"""
VPS Monitor Agent - Claude Agent SDK Integration
Monitors Hostinger VPS (srv1092611.hstgr.cloud) using SSH and Claude AI.
"""

import os
import json
import subprocess
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional

# Add project root to path for shared imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from shared.base_agent import BaseAgent


class SSHVPSClient:
    """
    Client for monitoring VPS via SSH.
    Collects system metrics and status information.
    """

    def __init__(self, hostname: str, ssh_user: str = "root", ssh_key_path: str = None):
        """
        Initialize SSH VPS client.

        Args:
            hostname: VPS hostname or IP (e.g., srv1092611.hstgr.cloud)
            ssh_user: SSH username (default: root)
            ssh_key_path: Path to SSH private key (optional)
        """
        self.hostname = hostname
        self.ssh_user = ssh_user
        self.ssh_key_path = ssh_key_path or os.path.expanduser("~/.ssh/id_ed25519")

    def _run_ssh_command(self, command: str) -> Dict[str, Any]:
        """
        Execute command on VPS via SSH.

        Args:
            command: Shell command to execute

        Returns:
            Dict with stdout, stderr, and exit_code
        """
        try:
            ssh_cmd = [
                "ssh",
                "-o", "StrictHostKeyChecking=no",
                "-o", "UserKnownHostsFile=/dev/null",
                "-o", "LogLevel=ERROR"
            ]

            if self.ssh_key_path and os.path.exists(self.ssh_key_path):
                ssh_cmd.extend(["-i", self.ssh_key_path])

            ssh_cmd.append(f"{self.ssh_user}@{self.hostname}")
            ssh_cmd.append(command)

            result = subprocess.run(
                ssh_cmd,
                capture_output=True,
                text=True,
                timeout=30
            )

            return {
                "stdout": result.stdout.strip(),
                "stderr": result.stderr.strip(),
                "exit_code": result.returncode,
                "success": result.returncode == 0
            }
        except subprocess.TimeoutExpired:
            return {"error": "SSH command timed out", "success": False}
        except Exception as e:
            return {"error": str(e), "success": False}

    def get_system_info(self) -> Dict[str, Any]:
        """Get basic system information."""
        result = self._run_ssh_command("""
            echo "hostname=$(hostname)"
            echo "os=$(cat /etc/os-release | grep PRETTY_NAME | cut -d= -f2 | tr -d '"')"
            echo "kernel=$(uname -r)"
            echo "uptime=$(uptime -p)"
        """)

        if not result["success"]:
            return {"error": result.get("error", result.get("stderr"))}

        info = {}
        for line in result["stdout"].split("\n"):
            if "=" in line:
                key, value = line.split("=", 1)
                info[key] = value
        return info

    def get_cpu_usage(self) -> Dict[str, Any]:
        """Get CPU usage statistics."""
        result = self._run_ssh_command("""
            top -bn1 | grep "Cpu(s)" | sed "s/.*, *\\([0-9.]*\\)%* id.*/\\1/" | awk '{print 100 - $1}'
        """)

        if not result["success"]:
            return {"error": result.get("error")}

        try:
            cpu_percent = float(result["stdout"])
            return {
                "cpu_percent": round(cpu_percent, 1),
                "status": "critical" if cpu_percent > 90 else "warning" if cpu_percent > 80 else "normal"
            }
        except (ValueError, KeyError, TypeError) as e:
            return {"error": f"Failed to parse CPU usage: {e}"}

    def get_memory_usage(self) -> Dict[str, Any]:
        """Get memory usage statistics."""
        result = self._run_ssh_command("""
            free -m | awk 'NR==2{printf "total=%s used=%s free=%s percent=%.1f", $2,$3,$4,$3*100/$2 }'
        """)

        if not result["success"]:
            return {"error": result.get("error")}

        mem = {}
        for item in result["stdout"].split():
            if "=" in item:
                key, value = item.split("=")
                try:
                    mem[key] = float(value) if '.' in value else int(value)
                except (ValueError, TypeError) as e:
                    mem[key] = value

        if "percent" in mem:
            mem["status"] = "critical" if mem["percent"] > 95 else "warning" if mem["percent"] > 85 else "normal"

        return mem

    def get_disk_usage(self) -> Dict[str, Any]:
        """Get disk usage statistics."""
        result = self._run_ssh_command("""
            df -h / | awk 'NR==2{printf "size=%s used=%s available=%s percent=%s", $2,$3,$4,$5}'
        """)

        if not result["success"]:
            return {"error": result.get("error")}

        disk = {}
        for item in result["stdout"].split():
            if "=" in item:
                key, value = item.split("=")
                disk[key] = value

        if "percent" in disk:
            try:
                percent_num = float(disk["percent"].rstrip("%"))
                disk["percent_num"] = percent_num
                disk["status"] = "critical" if percent_num > 90 else "warning" if percent_num > 80 else "normal"
            except (ValueError, AttributeError, TypeError) as e:
                pass  # Keep raw percent string if parsing fails

        return disk

    def get_top_processes(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get top processes by CPU usage."""
        result = self._run_ssh_command(f"""
            ps aux --sort=-%cpu | head -n {limit + 1} | tail -n {limit} | awk '{{printf "%s|%s|%s|%s\\n", $2,$3,$4,$11}}'
        """)

        if not result["success"]:
            return [{"error": result.get("error")}]

        processes = []
        for line in result["stdout"].split("\n"):
            if line.strip():
                parts = line.split("|")
                if len(parts) == 4:
                    processes.append({
                        "pid": parts[0],
                        "cpu": parts[1],
                        "mem": parts[2],
                        "command": parts[3]
                    })
        return processes

    def get_network_stats(self) -> Dict[str, Any]:
        """Get network statistics."""
        result = self._run_ssh_command("""
            cat /proc/net/dev | grep -E 'eth0|ens' | head -1 | awk '{printf "rx_bytes=%s tx_bytes=%s", $2, $10}'
        """)

        if not result["success"]:
            return {"error": result.get("error")}

        network = {}
        for item in result["stdout"].split():
            if "=" in item:
                key, value = item.split("=")
                try:
                    # Convert bytes to GB
                    gb = int(value) / (1024**3)
                    network[key] = round(gb, 2)
                    network[f"{key}_raw"] = int(value)
                except (ValueError, TypeError, ZeroDivisionError) as e:
                    network[key] = value  # Keep raw value if conversion fails

        return network

    def get_load_average(self) -> Dict[str, Any]:
        """Get system load average."""
        result = self._run_ssh_command("""
            cat /proc/loadavg | awk '{printf "1min=%s 5min=%s 15min=%s", $1,$2,$3}'
        """)

        if not result["success"]:
            return {"error": result.get("error")}

        load = {}
        for item in result["stdout"].split():
            if "=" in item:
                key, value = item.split("=")
                try:
                    load[key] = float(value)
                except (ValueError, TypeError) as e:
                    load[key] = value  # Keep raw value if conversion fails

        return load

    def get_services_status(self) -> List[Dict[str, Any]]:
        """Get status of key services."""
        services = ["nginx", "neon-agent", "postgresql", "docker"]
        result = self._run_ssh_command("""
            for svc in nginx neon-agent postgresql docker; do
                if systemctl is-active --quiet $svc 2>/dev/null; then
                    echo "$svc=running"
                else
                    echo "$svc=stopped"
                fi
            done
        """)

        if not result["success"]:
            return [{"error": result.get("error")}]

        services_status = []
        for line in result["stdout"].split("\n"):
            if "=" in line:
                name, status = line.split("=")
                services_status.append({
                    "name": name,
                    "status": status,
                    "healthy": status == "running"
                })

        return services_status


class VPSMonitorAgent(BaseAgent):
    """
    AI-powered VPS monitoring agent using Claude.
    Provides natural language interface to VPS metrics.
    Inherits common agent functionality from BaseAgent.
    """

    def __init__(self, vps_hostname: str, anthropic_api_key: str, ssh_user: str = "root"):
        """
        Initialize VPS monitoring agent.

        Args:
            vps_hostname: VPS hostname or IP
            anthropic_api_key: Anthropic API key for Claude
            ssh_user: SSH username
        """
        # Initialize base agent with Claude 3.5 Haiku model
        super().__init__(
            anthropic_api_key=anthropic_api_key,
            model="claude-3-5-haiku-20241022",
            max_tokens=4096
        )

        # Initialize VPS-specific client
        self.vps = SSHVPSClient(vps_hostname, ssh_user)

    def define_tools(self) -> List[Dict[str, Any]]:
        """Define tools available to the agent."""
        return [
            {
                "name": "get_system_info",
                "description": "Get basic system information including hostname, OS version, kernel, and uptime.",
                "input_schema": {
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            },
            {
                "name": "get_cpu_usage",
                "description": "Get current CPU usage percentage and status (normal/warning/critical).",
                "input_schema": {
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            },
            {
                "name": "get_memory_usage",
                "description": "Get memory usage statistics including total, used, free memory in MB and usage percentage.",
                "input_schema": {
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            },
            {
                "name": "get_disk_usage",
                "description": "Get disk space usage for root partition including total size, used space, available space, and percentage.",
                "input_schema": {
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            },
            {
                "name": "get_top_processes",
                "description": "Get list of top processes by CPU usage with PID, CPU%, memory%, and command name.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "limit": {
                            "type": "integer",
                            "description": "Number of top processes to return (default: 10)",
                            "default": 10
                        }
                    },
                    "required": []
                }
            },
            {
                "name": "get_network_stats",
                "description": "Get network statistics including received and transmitted data in GB.",
                "input_schema": {
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            },
            {
                "name": "get_load_average",
                "description": "Get system load average for 1, 5, and 15 minutes. Load above CPU count indicates high system load.",
                "input_schema": {
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            },
            {
                "name": "get_services_status",
                "description": "Check status of key services (nginx, neon-agent, postgresql, docker) to see if they're running.",
                "input_schema": {
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            },
            {
                "name": "get_full_health_report",
                "description": "Get comprehensive health report including all metrics: CPU, memory, disk, processes, services, and network.",
                "input_schema": {
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            }
        ]

    def execute_tool(self, tool_name: str, tool_input: Dict[str, Any]) -> str:
        """Execute a tool and return results as JSON string."""
        try:
            if tool_name == "get_system_info":
                result = self.vps.get_system_info()

            elif tool_name == "get_cpu_usage":
                result = self.vps.get_cpu_usage()

            elif tool_name == "get_memory_usage":
                result = self.vps.get_memory_usage()

            elif tool_name == "get_disk_usage":
                result = self.vps.get_disk_usage()

            elif tool_name == "get_top_processes":
                limit = tool_input.get("limit", 10)
                result = self.vps.get_top_processes(limit)

            elif tool_name == "get_network_stats":
                result = self.vps.get_network_stats()

            elif tool_name == "get_load_average":
                result = self.vps.get_load_average()

            elif tool_name == "get_services_status":
                result = self.vps.get_services_status()

            elif tool_name == "get_full_health_report":
                result = {
                    "timestamp": subprocess.run(["date", "+%Y-%m-%d %H:%M:%S"], capture_output=True, text=True).stdout.strip(),
                    "system": self.vps.get_system_info(),
                    "cpu": self.vps.get_cpu_usage(),
                    "memory": self.vps.get_memory_usage(),
                    "disk": self.vps.get_disk_usage(),
                    "load": self.vps.get_load_average(),
                    "services": self.vps.get_services_status(),
                    "network": self.vps.get_network_stats(),
                    "top_processes": self.vps.get_top_processes(5)
                }

            else:
                result = {"error": f"Unknown tool: {tool_name}"}

            return json.dumps(result, indent=2)

        except Exception as e:
            return json.dumps({"error": str(e), "tool": tool_name})

    def get_system_prompt(self) -> str:
        """
        Get VPS monitoring agent system prompt.

        Returns:
            System prompt with server specs and analysis guidelines
        """
        return f"""You are an expert VPS monitoring assistant for the Hostinger server: {self.vps.hostname}

Server Specs:
- Hostname: srv1092611.hstgr.cloud
- IP: 72.60.17.245
- Location: Lithuania - Vilnius
- OS: Ubuntu 24.04 LTS
- CPU: 2 cores
- Memory: 8 GB
- Disk: 100 GB
- Bandwidth: 8 TB/month

Your role is to:
- Monitor server health (CPU, RAM, disk, network)
- Identify performance issues and bottlenecks
- Provide actionable recommendations
- Alert on concerning metrics
- Track running services and processes

METRIC THRESHOLDS (for 2-core server):
- CPU: >80% sustained is concerning, >90% is critical
- RAM: >85% is concerning, >95% is critical
- Disk: >80% is concerning, >90% is critical
- Load average: >2.0 (1min) is high for 2 cores

ANALYSIS GUIDELINES:
1. Always provide specific metrics with units
2. Compare current values to thresholds
3. Identify the root cause when possible
4. Prioritize critical issues first
5. Suggest concrete actions to resolve issues

When reporting metrics:
- Use clear formatting (e.g., "CPU: 45% (normal)")
- Highlight warnings with status indicators
- List top resource consumers
- Provide historical context when relevant

Be concise but thorough. Focus on actionable insights."""


def main():
    """Example usage."""
    anthropic_api_key = os.getenv("ANTHROPIC_API_KEY")
    vps_hostname = os.getenv("VPS_HOSTNAME", "srv1092611.hstgr.cloud")

    if not anthropic_api_key:
        print("Error: ANTHROPIC_API_KEY not found")
        return

    print(f"🚀 Initializing VPS Monitor Agent for {vps_hostname}...\n")
    agent = VPSMonitorAgent(vps_hostname, anthropic_api_key)

    # Example queries
    queries = [
        "What's the current system status?",
        "Check CPU and memory usage",
        "Are there any issues I should know about?"
    ]

    for query in queries:
        print(f"💬 User: {query}")
        response = agent.chat(query)
        print(f"🤖 Agent: {response}\n")
        print("-" * 80 + "\n")


if __name__ == "__main__":
    main()
