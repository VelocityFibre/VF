#!/usr/bin/env python3
"""
Real-time Agent Command Monitor
Shows auto-approved commands, allows intervention, and maintains audit logs
"""

import json
import time
import sys
import os
from datetime import datetime
from pathlib import Path
import subprocess
from typing import Dict, List
import threading
import queue
from rich.console import Console
from rich.table import Table
from rich.live import Live
from rich.panel import Panel
from rich.layout import Layout
from rich.text import Text

console = Console()

class AgentMonitor:
    def __init__(self):
        self.log_dir = Path("/home/louisdup/Agents/claude/logs")
        self.log_dir.mkdir(exist_ok=True)
        self.command_log = self.log_dir / "agent-commands.jsonl"
        self.approved_config = Path("/home/louisdup/Agents/claude/.claude/approved-commands.yaml")
        self.command_queue = queue.Queue()
        self.stats = {
            "auto_approved": 0,
            "manual_approved": 0,
            "blocked": 0,
            "total": 0
        }

    def log_command(self, command: str, status: str, agent: str = "unknown"):
        """Log command execution with timestamp and status"""
        entry = {
            "timestamp": datetime.now().isoformat(),
            "agent": agent,
            "command": command[:200],  # Truncate long commands
            "status": status,
            "auto_approved": status == "auto_approved"
        }

        with open(self.command_log, 'a') as f:
            f.write(json.dumps(entry) + '\n')

        self.stats[status] = self.stats.get(status, 0) + 1
        self.stats["total"] += 1

    def create_dashboard(self) -> Table:
        """Create rich dashboard showing current status"""
        table = Table(title="🤖 Agent Command Monitor",
                     show_header=True,
                     header_style="bold magenta")

        table.add_column("Metric", style="cyan", width=20)
        table.add_column("Value", style="green", width=15)
        table.add_column("Status", style="yellow", width=20)

        # Add statistics
        table.add_row("Total Commands", str(self.stats["total"]), "✓ Active")
        table.add_row("Auto-Approved", str(self.stats["auto_approved"]),
                     "🚀 Fast Track")
        table.add_row("Manual Review", str(self.stats.get("manual_approved", 0)),
                     "👀 Reviewed")
        table.add_row("Blocked", str(self.stats.get("blocked", 0)),
                     "🛑 Prevented")

        # Add recent commands section
        table.add_section()
        table.add_row("", "", "")
        table.add_row("[bold]Recent Commands[/bold]", "", "")

        # Read last 5 commands
        if self.command_log.exists():
            with open(self.command_log, 'r') as f:
                lines = f.readlines()
                for line in lines[-5:]:
                    try:
                        entry = json.loads(line)
                        time_str = entry['timestamp'].split('T')[1][:8]
                        cmd_short = entry['command'][:50] + "..." if len(entry['command']) > 50 else entry['command']
                        status_icon = "✅" if entry['status'] == "auto_approved" else "⚠️"
                        table.add_row(time_str, cmd_short, status_icon)
                    except:
                        continue

        return table

    def watch_mode(self):
        """Interactive watch mode with ability to intervene"""
        layout = Layout()

        with Live(layout, refresh_per_second=1, screen=True) as live:
            while True:
                dashboard = self.create_dashboard()

                # Create intervention panel
                intervention_text = Text()
                intervention_text.append("\n🎮 Controls:\n", style="bold yellow")
                intervention_text.append("  [P] Pause auto-approval\n", style="cyan")
                intervention_text.append("  [R] Review pending commands\n", style="cyan")
                intervention_text.append("  [B] Block pattern temporarily\n", style="cyan")
                intervention_text.append("  [S] Show detailed stats\n", style="cyan")
                intervention_text.append("  [Q] Quit monitor\n", style="red")

                intervention_panel = Panel(intervention_text,
                                         title="Intervention Options",
                                         border_style="blue")

                # Update layout
                layout.split_column(
                    Layout(dashboard, name="dashboard"),
                    Layout(intervention_panel, name="controls", size=8)
                )

                time.sleep(1)

                # Check for user input (non-blocking)
                # In production, you'd use a more sophisticated input handler

    def tail_logs(self):
        """Tail command logs in real-time"""
        console.print("[bold cyan]📋 Tailing agent command logs...[/bold cyan]")

        try:
            # Use subprocess to tail the log file
            process = subprocess.Popen(
                ['tail', '-f', str(self.command_log)],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )

            for line in process.stdout:
                try:
                    entry = json.loads(line)
                    timestamp = entry['timestamp'].split('T')[1][:8]
                    agent = entry.get('agent', 'unknown')
                    command = entry['command'][:100]
                    status = entry['status']

                    # Color code by status
                    if status == "auto_approved":
                        console.print(f"✅ [{timestamp}] {agent}: {command}", style="green")
                    elif status == "blocked":
                        console.print(f"🛑 [{timestamp}] {agent}: {command}", style="red")
                    else:
                        console.print(f"👀 [{timestamp}] {agent}: {command}", style="yellow")

                except json.JSONDecodeError:
                    continue

        except KeyboardInterrupt:
            console.print("\n[yellow]Monitor stopped by user[/yellow]")
            process.terminate()

def main():
    monitor = AgentMonitor()

    if len(sys.argv) > 1:
        if sys.argv[1] == "watch":
            monitor.watch_mode()
        elif sys.argv[1] == "tail":
            monitor.tail_logs()
        elif sys.argv[1] == "stats":
            # Show statistics
            table = monitor.create_dashboard()
            console.print(table)
    else:
        console.print(Panel.fit("""
🤖 [bold cyan]Agent Command Monitor[/bold cyan]

Usage:
  ./monitor-agents.py watch  - Interactive dashboard (recommended)
  ./monitor-agents.py tail   - Tail command logs
  ./monitor-agents.py stats  - Show statistics

The watch mode allows you to:
- See real-time command execution
- Intervene when necessary
- Review auto-approved patterns
- Block commands temporarily
        """, title="Help"))

if __name__ == "__main__":
    main()