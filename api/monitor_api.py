#!/usr/bin/env python3
"""
FastAPI server for Auto-Approval Monitoring Dashboard
Serves real-time monitoring data for the web UI
"""

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path
import json
import uvicorn
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import asyncio
from collections import defaultdict, deque, Counter

app = FastAPI(title="Auto-Approval Monitor API")

# Enable CORS for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class MonitorData:
    """Manages monitoring data for the dashboard"""

    def __init__(self):
        self.log_dir = Path("/home/louisdup/Agents/claude/logs")
        self.log_file = self.log_dir / "auto-approved-commands.log"
        self.json_log = self.log_dir / "agent-commands.jsonl"

        # In-memory stats
        self.stats = {
            "total": 0,
            "auto_approved": 0,
            "blocked": 0,
            "notified": 0,
            "manual": 0,
            "last_updated": datetime.now().isoformat()
        }

        # Recent commands (keep last 100)
        self.recent_commands = deque(maxlen=100)

        # Command categories
        self.categories = defaultdict(int)

        # Load initial data
        self.refresh_data()

    def refresh_data(self):
        """Refresh data from log files"""
        if not self.json_log.exists():
            # Create empty log if doesn't exist
            self.json_log.touch()
            return

        # Reset stats
        self.stats = {
            "total": 0,
            "auto_approved": 0,
            "blocked": 0,
            "notified": 0,
            "manual": 0,
            "last_updated": datetime.now().isoformat()
        }

        # Read log file
        try:
            with open(self.json_log, 'r') as f:
                lines = f.readlines()

                for line in lines:
                    try:
                        entry = json.loads(line)
                        self.process_entry(entry)
                    except json.JSONDecodeError:
                        continue
        except Exception as e:
            print(f"Error reading log: {e}")

    def process_entry(self, entry: Dict):
        """Process a log entry and update stats"""
        self.stats["total"] += 1

        status = entry.get("status", "unknown").lower()

        if "auto_approved" in status:
            self.stats["auto_approved"] += 1
        elif "blocked" in status:
            self.stats["blocked"] += 1
        elif "notif" in status:
            self.stats["notified"] += 1
        else:
            self.stats["manual"] += 1

        # Categorize command
        command = entry.get("command", "")
        category = self.categorize_command(command)
        self.categories[category] += 1

        # Add to recent commands
        self.recent_commands.append({
            "timestamp": entry.get("timestamp", ""),
            "command": command[:100],
            "status": status,
            "category": category
        })

    def categorize_command(self, command: str) -> str:
        """Categorize command type"""
        cmd_lower = command.lower()

        if "vf_server" in cmd_lower:
            return "VF Server"
        elif "cloudflared" in cmd_lower:
            return "Cloudflare"
        elif any(x in cmd_lower for x in ["git", "clone", "push", "pull"]):
            return "Git"
        elif any(x in cmd_lower for x in ["ps", "tail", "grep", "ls"]):
            return "Monitoring"
        elif any(x in cmd_lower for x in ["mkdir", "cp", "mv", "cat"]):
            return "File Ops"
        elif any(x in cmd_lower for x in ["npm", "pip", "yarn"]):
            return "Build"
        elif any(x in cmd_lower for x in ["systemctl", "service"]):
            return "System"
        else:
            return "Other"

    def get_dashboard_data(self) -> Dict:
        """Get data for dashboard display"""
        self.refresh_data()

        # Calculate percentages
        total = self.stats["total"] or 1

        return {
            "stats": {
                "total": self.stats["total"],
                "auto_approved": self.stats["auto_approved"],
                "auto_approved_pct": round((self.stats["auto_approved"] / total) * 100, 1),
                "blocked": self.stats["blocked"],
                "blocked_pct": round((self.stats["blocked"] / total) * 100, 1),
                "notified": self.stats["notified"],
                "manual": self.stats["manual"],
                "time_saved": self.stats["auto_approved"] * 3.5,
                "last_updated": self.stats["last_updated"]
            },
            "recent_commands": list(self.recent_commands)[-20:],  # Last 20
            "categories": dict(self.categories),
            "performance": {
                "manual_time_per_cmd": 3.5,
                "auto_time_per_cmd": 0.001,
                "speedup_factor": 3500,
                "efficiency_gain": 99.97
            },
            "alerts": self.detect_problems()
        }

    def detect_problems(self) -> List[Dict]:
        """Detect problematic agent behavior patterns"""
        problems = []

        # Get commands from last 5 minutes
        cutoff = datetime.now() - timedelta(minutes=5)
        recent = []

        for cmd in self.recent_commands:
            try:
                ts = datetime.fromisoformat(cmd['timestamp'])
                if ts > cutoff:
                    # Create a copy with timestamp_obj for analysis
                    cmd_copy = cmd.copy()
                    cmd_copy['timestamp_obj'] = ts
                    recent.append(cmd_copy)
            except:
                continue

        if not recent:
            return problems

        # Detect loops
        command_times = defaultdict(list)
        for cmd in recent:
            command_text = cmd.get('command', '')
            if 'timestamp_obj' in cmd:
                command_times[command_text].append(cmd['timestamp_obj'])

        for command, timestamps in command_times.items():
            if len(timestamps) >= 3:  # 3+ repetitions
                for i in range(len(timestamps) - 2):
                    window = timestamps[i:i + 3]
                    time_span = (window[-1] - window[0]).total_seconds()
                    if time_span <= 30:  # Within 30 seconds
                        problems.append({
                            'type': 'LOOP',
                            'severity': 'HIGH',
                            'command': command[:80],
                            'count': len(window),
                            'timespan': time_span,
                            'description': f"Command repeated {len(window)} times in {time_span:.0f}s"
                        })
                        break

        # Detect retries (failed commands repeated)
        retry_sequences = []
        for i in range(len(recent) - 2):
            if (recent[i]['command'] == recent[i+1]['command'] == recent[i+2]['command']):
                statuses = [recent[i]['status'], recent[i+1]['status'], recent[i+2]['status']]
                if any(s in ['blocked', 'manual'] for s in statuses):
                    problems.append({
                        'type': 'RETRY',
                        'severity': 'MEDIUM',
                        'command': recent[i]['command'][:80],
                        'count': 3,
                        'statuses': statuses,
                        'description': f"Command retried after failures"
                    })
                    break

        # Detect stuck operations (one category > 80%)
        cat_counts = Counter()
        for cmd in recent:
            cat_counts[cmd.get('category', 'Other')] += 1

        total = sum(cat_counts.values())
        for category, count in cat_counts.items():
            pct = (count / total * 100) if total > 0 else 0
            if pct > 80:
                problems.append({
                    'type': 'STUCK',
                    'severity': 'MEDIUM',
                    'category': category,
                    'percentage': round(pct, 1),
                    'count': count,
                    'description': f"{category} operations at {pct:.0f}% (agent may be stuck)"
                })

        # Detect rapid fire (>50 commands/minute)
        if len(recent) > 0:
            time_range = (recent[-1]['timestamp_obj'] - recent[0]['timestamp_obj']).total_seconds()
            if time_range > 0:
                rate = (len(recent) / time_range) * 60  # Commands per minute
                if rate > 50:
                    problems.append({
                        'type': 'RAPID_FIRE',
                        'severity': 'HIGH',
                        'rate': round(rate, 0),
                        'count': len(recent),
                        'description': f"{rate:.0f} commands/minute (possible loop)"
                    })

        return problems

    def add_test_data(self):
        """Add test data for demo purposes"""
        test_commands = [
            ("VF_SERVER_PASSWORD='***' .claude/skills/vf-server/scripts/execute.py 'ps aux'", "auto_approved"),
            ("mkdir /tmp/test", "auto_approved"),
            ("rm -rf /important", "blocked"),
            ("systemctl restart nginx", "notified"),
            ("cloudflared tunnel route dns", "auto_approved"),
            ("git push origin main", "notified"),
            ("tail -f /var/log/app.log", "auto_approved"),
            ("DROP TABLE users", "blocked"),
        ]

        for cmd, status in test_commands:
            entry = {
                "timestamp": datetime.now().isoformat(),
                "command": cmd,
                "status": status,
                "agent": "test"
            }

            # Write to log
            with open(self.json_log, 'a') as f:
                f.write(json.dumps(entry) + '\n')

            self.process_entry(entry)

# Initialize monitor data
monitor = MonitorData()

@app.get("/api/monitor/stats")
async def get_stats():
    """Get current monitoring statistics"""
    return JSONResponse(monitor.get_dashboard_data())

@app.get("/api/monitor/refresh")
async def refresh_data():
    """Force refresh of monitoring data"""
    monitor.refresh_data()
    return {"status": "refreshed", "timestamp": datetime.now().isoformat()}

@app.get("/api/monitor/test")
async def add_test_data():
    """Add test data for demonstration"""
    monitor.add_test_data()
    return {"status": "test data added"}

@app.get("/monitor")
async def monitor_dashboard():
    """Serve the monitoring dashboard HTML"""
    html_path = Path(__file__).parent.parent / "public" / "monitor.html"

    if not html_path.exists():
        raise HTTPException(status_code=404, detail="Monitor dashboard not found")

    with open(html_path, 'r') as f:
        return HTMLResponse(content=f.read())

@app.get("/")
async def root():
    """Redirect to monitor dashboard"""
    return HTMLResponse(content="""
    <html>
        <head>
            <meta http-equiv="refresh" content="0; url=/monitor">
        </head>
        <body style="background: black; color: white; font-family: monospace;">
            Redirecting to monitor dashboard...
        </body>
    </html>
    """)

if __name__ == "__main__":
    import sys

    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8002

    print(f"\n🚀 Auto-Approval Monitor API starting on port {port}")
    print(f"📊 Dashboard: http://localhost:{port}/monitor")
    print(f"📡 API: http://localhost:{port}/api/monitor/stats")
    print("\nPress Ctrl+C to stop\n")

    uvicorn.run(app, host="0.0.0.0", port=port, log_level="error")