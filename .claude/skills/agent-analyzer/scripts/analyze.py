#!/usr/bin/env python3
"""
Agent Behavior Analyzer
Detects loops, retries, stuck operations, and other problematic patterns
"""

import json
import sys
import os
from pathlib import Path
from datetime import datetime, timedelta
from collections import defaultdict, Counter
from typing import Dict, List, Tuple, Optional
import argparse
import time

# Add rich for better output if available
try:
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    from rich.text import Text
    RICH_AVAILABLE = True
    console = Console()
except ImportError:
    RICH_AVAILABLE = False
    console = None


class AgentBehaviorAnalyzer:
    """Analyzes agent command patterns to detect problems"""

    def __init__(self, log_path: str = None):
        # Default log path
        if log_path is None:
            log_path = "/home/louisdup/Agents/claude/logs/agent-commands.jsonl"

        self.log_path = Path(log_path)
        self.commands = []
        self.problems = []

        # Thresholds for detection
        self.thresholds = {
            "loop_repetitions": 3,           # Same command 3+ times
            "loop_time_window": 30,          # Within 30 seconds
            "rapid_fire_rate": 50,           # Commands per minute
            "stuck_dominance": 80,           # One category >80%
            "retry_attempts": 3,             # Failed attempts before alert
            "high_manual_rate": 50,          # Manual review >50%
            "anomaly_spike": 300,           # 300% increase in rate
        }

        # Load command log
        self.load_commands()

    def load_commands(self, minutes_back: int = 60):
        """Load commands from log file"""
        if not self.log_path.exists():
            print(f"Log file not found: {self.log_path}")
            return

        self.commands = []
        cutoff_time = datetime.now() - timedelta(minutes=minutes_back)

        try:
            with open(self.log_path, 'r') as f:
                for line in f:
                    try:
                        entry = json.loads(line)
                        # Parse timestamp
                        timestamp = datetime.fromisoformat(entry.get('timestamp', ''))

                        # Only include recent commands
                        if timestamp > cutoff_time:
                            entry['timestamp_obj'] = timestamp
                            self.commands.append(entry)
                    except:
                        continue
        except Exception as e:
            print(f"Error loading commands: {e}")

    def detect_loops(self) -> List[Dict]:
        """Detect command loops"""
        loops_found = []

        # Group commands by content
        command_times = defaultdict(list)

        for cmd in self.commands:
            command_text = cmd.get('command', '')
            timestamp = cmd.get('timestamp_obj')
            if timestamp:
                command_times[command_text].append(timestamp)

        # Check for repetitions
        for command, timestamps in command_times.items():
            if len(timestamps) >= self.thresholds['loop_repetitions']:
                # Check if they're within time window
                for i in range(len(timestamps) - self.thresholds['loop_repetitions'] + 1):
                    window = timestamps[i:i + self.thresholds['loop_repetitions']]
                    time_span = (window[-1] - window[0]).total_seconds()

                    if time_span <= self.thresholds['loop_time_window']:
                        loops_found.append({
                            'type': 'LOOP',
                            'severity': 'HIGH',
                            'command': command[:100],
                            'repetitions': len(window),
                            'time_span': time_span,
                            'timestamps': [t.isoformat() for t in window],
                            'description': f"Command repeated {len(window)} times in {time_span:.1f} seconds"
                        })
                        break

        return loops_found

    def detect_retries(self) -> List[Dict]:
        """Detect retry patterns"""
        retries_found = []

        # Look for sequences with same command and failure status
        retry_sequences = []
        current_sequence = []
        last_command = None

        for cmd in self.commands:
            command_text = cmd.get('command', '')
            status = cmd.get('status', '').lower()

            # Check if this is a retry
            if command_text == last_command and status in ['blocked', 'manual', 'failed']:
                if not current_sequence:
                    # Start new sequence (include previous matching command)
                    current_sequence = [self.commands[self.commands.index(cmd) - 1]] if self.commands.index(cmd) > 0 else []
                current_sequence.append(cmd)
            else:
                # Sequence ended
                if len(current_sequence) >= self.thresholds['retry_attempts']:
                    retry_sequences.append(current_sequence)
                current_sequence = []

            last_command = command_text

        # Process retry sequences
        for sequence in retry_sequences:
            retries_found.append({
                'type': 'RETRY',
                'severity': 'MEDIUM',
                'command': sequence[0].get('command', '')[:100],
                'attempts': len(sequence),
                'statuses': [cmd.get('status', 'unknown') for cmd in sequence],
                'time_span': (sequence[-1]['timestamp_obj'] - sequence[0]['timestamp_obj']).total_seconds(),
                'description': f"Command retried {len(sequence)} times with failures"
            })

        return retries_found

    def detect_stuck_operations(self) -> List[Dict]:
        """Detect stuck agent operations"""
        stuck_found = []

        # Analyze category distribution
        categories = Counter()
        for cmd in self.commands:
            category = self.categorize_command(cmd.get('command', ''))
            categories[category] += 1

        total_commands = sum(categories.values())

        # Check for dominance
        for category, count in categories.items():
            percentage = (count / total_commands * 100) if total_commands > 0 else 0

            if percentage > self.thresholds['stuck_dominance']:
                stuck_found.append({
                    'type': 'STUCK',
                    'severity': 'MEDIUM',
                    'category': category,
                    'percentage': percentage,
                    'count': count,
                    'total': total_commands,
                    'description': f"{category} operations dominate at {percentage:.1f}% of commands"
                })

        return stuck_found

    def detect_rapid_fire(self) -> List[Dict]:
        """Detect rapid command execution"""
        rapid_fire_found = []

        # Calculate commands per minute in sliding windows
        window_size = 60  # 1 minute in seconds

        for i in range(len(self.commands) - 1):
            window_start = self.commands[i]['timestamp_obj']
            window_end = window_start + timedelta(seconds=window_size)

            # Count commands in window
            commands_in_window = 0
            for j in range(i, len(self.commands)):
                if self.commands[j]['timestamp_obj'] <= window_end:
                    commands_in_window += 1
                else:
                    break

            if commands_in_window > self.thresholds['rapid_fire_rate']:
                rapid_fire_found.append({
                    'type': 'RAPID_FIRE',
                    'severity': 'HIGH',
                    'rate': commands_in_window,
                    'window_start': window_start.isoformat(),
                    'window_end': window_end.isoformat(),
                    'description': f"{commands_in_window} commands/minute detected (threshold: {self.thresholds['rapid_fire_rate']})"
                })
                break  # Only report first occurrence

        return rapid_fire_found

    def detect_inefficiency(self) -> List[Dict]:
        """Detect inefficient patterns"""
        inefficiencies = []

        # Check manual review rate
        status_counts = Counter()
        for cmd in self.commands:
            status = cmd.get('status', 'unknown').lower()
            status_counts[status] += 1

        total = sum(status_counts.values())
        if total > 0:
            manual_rate = (status_counts.get('manual', 0) + status_counts.get('manual_review', 0)) / total * 100

            if manual_rate > self.thresholds['high_manual_rate']:
                inefficiencies.append({
                    'type': 'INEFFICIENT',
                    'severity': 'LOW',
                    'manual_rate': manual_rate,
                    'manual_count': status_counts.get('manual', 0) + status_counts.get('manual_review', 0),
                    'total': total,
                    'description': f"High manual review rate: {manual_rate:.1f}% (threshold: {self.thresholds['high_manual_rate']}%)"
                })

        return inefficiencies

    def categorize_command(self, command: str) -> str:
        """Categorize command type"""
        cmd_lower = command.lower()

        if 'vf_server' in cmd_lower:
            return 'VF_Server'
        elif 'cloudflared' in cmd_lower:
            return 'Cloudflare'
        elif any(x in cmd_lower for x in ['git', 'clone', 'push', 'pull', 'commit']):
            return 'Git'
        elif any(x in cmd_lower for x in ['ps', 'tail', 'grep', 'ls', 'top']):
            return 'Monitoring'
        elif any(x in cmd_lower for x in ['mkdir', 'cp', 'mv', 'cat', 'rm']):
            return 'File_Ops'
        elif any(x in cmd_lower for x in ['npm', 'pip', 'yarn', 'cargo']):
            return 'Build'
        elif any(x in cmd_lower for x in ['systemctl', 'service']):
            return 'System'
        elif any(x in cmd_lower for x in ['curl', 'wget', 'http']):
            return 'Network'
        else:
            return 'Other'

    def analyze(self) -> Dict:
        """Run full analysis"""
        self.problems = []

        # Run all detections
        self.problems.extend(self.detect_loops())
        self.problems.extend(self.detect_retries())
        self.problems.extend(self.detect_stuck_operations())
        self.problems.extend(self.detect_rapid_fire())
        self.problems.extend(self.detect_inefficiency())

        # Sort by severity
        severity_order = {'HIGH': 0, 'MEDIUM': 1, 'LOW': 2}
        self.problems.sort(key=lambda x: severity_order.get(x['severity'], 999))

        return {
            'timestamp': datetime.now().isoformat(),
            'commands_analyzed': len(self.commands),
            'problems_found': len(self.problems),
            'problems': self.problems
        }

    def display_results(self, results: Dict, verbose: bool = False):
        """Display analysis results"""
        if RICH_AVAILABLE:
            self._display_rich(results, verbose)
        else:
            self._display_plain(results, verbose)

    def _display_rich(self, results: Dict, verbose: bool):
        """Display with rich formatting"""
        # Header
        console.print(Panel.fit(
            f"[bold cyan]Agent Behavior Analysis[/bold cyan]\n"
            f"Commands analyzed: {results['commands_analyzed']}\n"
            f"Problems found: {results['problems_found']}",
            border_style="cyan"
        ))

        if not results['problems']:
            console.print("[bold green]✅ No problems detected![/bold green]")
            return

        # Problems table
        table = Table(title="Detected Problems", show_header=True)
        table.add_column("Type", style="cyan")
        table.add_column("Severity", width=10)
        table.add_column("Description", style="white")

        for problem in results['problems']:
            # Color code severity
            if problem['severity'] == 'HIGH':
                severity = "[bold red]HIGH[/bold red]"
            elif problem['severity'] == 'MEDIUM':
                severity = "[yellow]MEDIUM[/yellow]"
            else:
                severity = "[green]LOW[/green]"

            table.add_row(
                problem['type'],
                severity,
                problem['description']
            )

        console.print(table)

        # Detailed view
        if verbose:
            console.print("\n[bold]Detailed Problem Analysis:[/bold]\n")
            for i, problem in enumerate(results['problems'], 1):
                console.print(f"[bold cyan]Problem {i}: {problem['type']}[/bold cyan]")
                for key, value in problem.items():
                    if key not in ['type', 'description']:
                        console.print(f"  {key}: {value}")
                console.print()

    def _display_plain(self, results: Dict, verbose: bool):
        """Display with plain text formatting"""
        print("\n" + "="*60)
        print("AGENT BEHAVIOR ANALYSIS")
        print("="*60)
        print(f"Commands analyzed: {results['commands_analyzed']}")
        print(f"Problems found: {results['problems_found']}")
        print()

        if not results['problems']:
            print("✅ No problems detected!")
            return

        print("DETECTED PROBLEMS:")
        print("-"*60)

        for problem in results['problems']:
            print(f"\n[{problem['severity']}] {problem['type']}")
            print(f"  {problem['description']}")

            if verbose:
                for key, value in problem.items():
                    if key not in ['type', 'severity', 'description']:
                        print(f"    {key}: {value}")

    def monitor_mode(self, interval: int = 10):
        """Real-time monitoring mode"""
        print(f"Starting real-time monitoring (checking every {interval} seconds)...")
        print("Press Ctrl+C to stop\n")

        last_problem_count = 0

        try:
            while True:
                # Reload and analyze
                self.load_commands(minutes_back=5)  # Last 5 minutes
                results = self.analyze()

                # Only show if new problems
                if results['problems_found'] > last_problem_count:
                    if RICH_AVAILABLE:
                        console.clear()
                    else:
                        print("\n" + "="*60)

                    self.display_results(results)

                    # Alert on high severity
                    high_severity = [p for p in results['problems'] if p['severity'] == 'HIGH']
                    if high_severity:
                        print("\n🚨 ALERT: High severity problems detected!")
                        for problem in high_severity:
                            print(f"  - {problem['type']}: {problem['description']}")

                last_problem_count = results['problems_found']
                time.sleep(interval)

        except KeyboardInterrupt:
            print("\n\nMonitoring stopped.")


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='Analyze agent behavior for problems')
    parser.add_argument('--monitor', action='store_true', help='Run in real-time monitoring mode')
    parser.add_argument('--last', type=str, default='60m', help='Analyze last N minutes (e.g., 10m, 1h)')
    parser.add_argument('--verbose', action='store_true', help='Show detailed problem information')
    parser.add_argument('--log', type=str, help='Path to log file')

    args = parser.parse_args()

    # Parse time window
    time_str = args.last.lower()
    if time_str.endswith('m'):
        minutes = int(time_str[:-1])
    elif time_str.endswith('h'):
        minutes = int(time_str[:-1]) * 60
    else:
        minutes = 60

    # Create analyzer
    analyzer = AgentBehaviorAnalyzer(log_path=args.log)

    if args.monitor:
        # Real-time monitoring
        analyzer.monitor_mode()
    else:
        # Single analysis
        analyzer.load_commands(minutes_back=minutes)
        results = analyzer.analyze()
        analyzer.display_results(results, verbose=args.verbose)

        # Exit code based on problems
        if results['problems_found'] > 0:
            sys.exit(1)  # Problems found
        else:
            sys.exit(0)  # All clear


if __name__ == "__main__":
    main()