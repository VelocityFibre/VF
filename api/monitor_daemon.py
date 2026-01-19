#!/usr/bin/env python3
"""
Proactive Monitoring Daemon for Claude Code
Automatically watches bash commands and detects problems in real-time
"""

import json
import os
import psutil
import subprocess
import time
from datetime import datetime, timedelta
from pathlib import Path
from collections import defaultdict, deque
from typing import Dict, List, Optional

# Configuration
LOG_FILE = Path("/home/louisdup/Agents/claude/logs/agent-commands.jsonl")
ALERT_LOG = Path("/home/louisdup/Agents/claude/logs/monitor-alerts.log")
CHECK_INTERVAL = 2  # seconds
ALERT_COOLDOWN = 60  # Don't spam same alert within 60s

LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
ALERT_LOG.parent.mkdir(parents=True, exist_ok=True)

class CommandMonitor:
    """Monitor bash commands and detect problematic patterns"""

    def __init__(self):
        self.recent_commands = deque(maxlen=100)
        self.last_alerts = {}  # Alert type -> timestamp
        self.tracked_pids = set()
        self.command_history = defaultdict(list)  # command -> [timestamps]

    def categorize_command(self, command: str) -> str:
        """Categorize command for monitoring"""
        cmd_lower = command.lower()

        if "vf_server" in cmd_lower:
            return "VF Server"
        elif "cloudflared" in cmd_lower or "tunnel" in cmd_lower:
            return "Cloudflare"
        elif any(x in cmd_lower for x in ["git", "clone", "push", "pull"]):
            return "Git"
        elif any(x in cmd_lower for x in ["ps", "tail", "grep", "ls", "ss", "netstat"]):
            return "Monitoring"
        elif any(x in cmd_lower for x in ["mkdir", "cp", "mv", "cat", "rm"]):
            return "File Ops"
        elif any(x in cmd_lower for x in ["npm", "pip", "yarn", "npx"]):
            return "Build"
        elif any(x in cmd_lower for x in ["systemctl", "service"]):
            return "System"
        else:
            return "Other"

    def determine_status(self, command: str) -> str:
        """Determine approval status based on command patterns"""
        cmd_lower = command.lower()

        # Dangerous patterns
        danger_patterns = ["rm -rf", "drop table", "delete from", "truncate table"]
        if any(pattern in cmd_lower for pattern in danger_patterns):
            return "blocked"

        # Important patterns
        notify_patterns = ["git push", "systemctl restart", "npm run build", "deploy", "pkill"]
        if any(pattern in cmd_lower for pattern in notify_patterns):
            return "notified"

        # Safe patterns
        safe_patterns = [
            "ps aux", "tail", "ls", "cat", "grep", "find", "ss", "netstat",
            "df", "free", "select", "mkdir", "pwd", "echo", "curl"
        ]
        if any(pattern in cmd_lower for pattern in safe_patterns):
            return "auto_approved"

        return "manual"

    def log_command(self, command: str, pid: int):
        """Log command to JSONL file"""
        # Skip monitoring commands and IDE background processes
        if "monitor" in command.lower() or "agent-commands" in command:
            return

        # Skip IDE/editor background processes (noise)
        if any(noise in command for noise in [
            "cpuUsage.sh",  # Windsurf CPU monitoring
            "electron",     # Editor processes
            "/node_modules/",
            "vscode-"
        ]):
            return

        entry = {
            "timestamp": datetime.now().isoformat(),
            "command": command,
            "status": self.determine_status(command),
            "category": self.categorize_command(command),
            "pid": pid,
            "agent": "claude"
        }

        with open(LOG_FILE, 'a') as f:
            f.write(json.dumps(entry) + '\n')

        self.recent_commands.append(entry)
        self.command_history[command].append(datetime.now())

    def detect_loops(self) -> Optional[Dict]:
        """Detect command loops"""
        now = datetime.now()
        cutoff = now - timedelta(seconds=30)

        for command, timestamps in self.command_history.items():
            # Clean old timestamps
            recent = [ts for ts in timestamps if ts > cutoff]
            self.command_history[command] = recent

            # Check for loops (3+ times in 30 seconds)
            if len(recent) >= 3:
                # Get unique timestamps (ignore parallel executions)
                unique_times = sorted(set(recent))

                # Need at least 3 different timestamps for a loop
                if len(unique_times) < 3:
                    continue

                # Calculate actual timespan
                timespan = (unique_times[-1] - unique_times[0]).total_seconds()

                # Only alert if there's actual time between executions
                if timespan >= 1:  # At least 1 second between first and last
                    return {
                        'type': 'LOOP',
                        'severity': 'HIGH',
                        'command': command[:80],
                        'count': len(unique_times),
                        'timespan': timespan,
                        'message': f"Command repeated {len(unique_times)} times in {timespan:.0f}s"
                    }
        return None

    def detect_stuck_operations(self) -> Optional[Dict]:
        """Detect if stuck on one operation type"""
        if len(self.recent_commands) < 10:
            return None

        # Count categories in last 20 commands
        categories = defaultdict(int)
        for cmd in list(self.recent_commands)[-20:]:
            categories[cmd['category']] += 1

        total = sum(categories.values())
        for category, count in categories.items():
            pct = (count / total * 100) if total > 0 else 0
            if pct > 70:  # 70% threshold
                return {
                    'type': 'STUCK',
                    'severity': 'MEDIUM',
                    'category': category,
                    'percentage': round(pct, 1),
                    'count': count,
                    'message': f"{category} operations at {pct:.0f}% (agent may be stuck)"
                }
        return None

    def send_alert(self, alert: Dict):
        """Send alert via desktop notification and log"""
        alert_key = f"{alert['type']}:{alert.get('command', alert.get('category', 'unknown'))}"
        now = datetime.now()

        # Check cooldown
        if alert_key in self.last_alerts:
            if (now - self.last_alerts[alert_key]).total_seconds() < ALERT_COOLDOWN:
                return

        self.last_alerts[alert_key] = now

        # Log alert
        with open(ALERT_LOG, 'a') as f:
            f.write(f"[{now.isoformat()}] {alert['severity']} - {alert['message']}\n")

        # Desktop notification
        try:
            subprocess.run([
                'notify-send',
                f"🚨 Claude Code Alert - {alert['type']}",
                alert['message'],
                '-u', 'critical' if alert['severity'] == 'HIGH' else 'normal',
                '-i', 'dialog-warning'
            ], check=False, timeout=1)
        except:
            pass  # Silent fail if notify-send not available

        print(f"🚨 ALERT: {alert['message']}")

    def get_bash_commands(self) -> List[Dict]:
        """Get current bash commands from running processes"""
        commands = []

        try:
            for proc in psutil.process_iter(['pid', 'name', 'cmdline', 'ppid']):
                try:
                    # Look for bash/sh processes
                    if proc.info['name'] in ['bash', 'sh', 'zsh']:
                        cmdline = proc.info['cmdline']
                        if cmdline and len(cmdline) > 1:
                            # Skip shell itself
                            if cmdline[1] != '-c':
                                continue

                            command = ' '.join(cmdline[2:]) if len(cmdline) > 2 else ''
                            if command and proc.info['pid'] not in self.tracked_pids:
                                commands.append({
                                    'pid': proc.info['pid'],
                                    'command': command
                                })
                                self.tracked_pids.add(proc.info['pid'])
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
        except Exception as e:
            print(f"Error scanning processes: {e}")

        return commands

    def run(self):
        """Main monitoring loop"""
        print("🔍 Claude Code Monitor Started")
        print(f"📊 Dashboard: http://localhost:8002/monitor")
        print(f"📝 Logs: {LOG_FILE}")
        print(f"🚨 Alerts: {ALERT_LOG}")
        print(f"⏱️  Checking every {CHECK_INTERVAL}s")
        print("\nPress Ctrl+C to stop\n")

        try:
            while True:
                # Get new bash commands
                commands = self.get_bash_commands()
                for cmd_info in commands:
                    self.log_command(cmd_info['command'], cmd_info['pid'])

                # Check for problems
                loop_alert = self.detect_loops()
                if loop_alert:
                    self.send_alert(loop_alert)

                stuck_alert = self.detect_stuck_operations()
                if stuck_alert:
                    self.send_alert(stuck_alert)

                # Clean old PIDs
                current_pids = {p.pid for p in psutil.process_iter(['pid'])}
                self.tracked_pids = self.tracked_pids.intersection(current_pids)

                time.sleep(CHECK_INTERVAL)

        except KeyboardInterrupt:
            print("\n\n✅ Monitor stopped")

if __name__ == "__main__":
    monitor = CommandMonitor()
    monitor.run()
