#!/usr/bin/env python3
"""
Advanced improvements for the auto-approval system
Adds ML pattern learning, anomaly detection, and better integration
"""

import json
import time
import os
import sys
from pathlib import Path
from datetime import datetime, timedelta
from collections import defaultdict, Counter
from typing import Dict, List, Tuple, Optional
import hashlib
import yaml
import pickle
import re
import subprocess
from dataclasses import dataclass, asdict
from enum import Enum

# For ML features (optional, will gracefully degrade if not available)
try:
    import numpy as np
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.naive_bayes import MultinomialNB
    from sklearn.model_selection import train_test_split
    ML_AVAILABLE = True
except ImportError:
    ML_AVAILABLE = False

# For advanced monitoring
try:
    from rich.console import Console
    from rich.progress import track
    from rich.table import Table
    from rich.panel import Panel
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False


class ApprovalStatus(Enum):
    """Command approval status"""
    AUTO_APPROVED = "auto_approved"
    BLOCKED = "blocked"
    MANUAL_REVIEW = "manual_review"
    LEARNED_SAFE = "learned_safe"
    ANOMALY_DETECTED = "anomaly_detected"


@dataclass
class CommandPattern:
    """Represents a command pattern with metadata"""
    pattern: str
    category: str
    risk_level: int  # 0-10
    frequency: int
    last_seen: datetime
    auto_approve: bool
    learned: bool = False


class AdvancedAutoApproval:
    """Enhanced auto-approval system with ML and advanced features"""

    def __init__(self):
        self.config_dir = Path.home() / "Agents/claude/.claude"
        self.data_dir = self.config_dir / "approval_data"
        self.data_dir.mkdir(exist_ok=True)

        self.patterns_file = self.data_dir / "learned_patterns.json"
        self.ml_model_file = self.data_dir / "approval_model.pkl"
        self.analytics_file = self.data_dir / "analytics.json"

        self.console = Console() if RICH_AVAILABLE else None
        self.command_history = []
        self.learned_patterns = self.load_learned_patterns()
        self.ml_model = None
        self.vectorizer = None

        if ML_AVAILABLE:
            self.load_ml_model()

    def load_learned_patterns(self) -> Dict[str, CommandPattern]:
        """Load previously learned command patterns"""
        if self.patterns_file.exists():
            with open(self.patterns_file, 'r') as f:
                data = json.load(f)
                return {
                    k: CommandPattern(**v) if isinstance(v, dict) else v
                    for k, v in data.items()
                }
        return {}

    def save_learned_patterns(self):
        """Save learned patterns to disk"""
        with open(self.patterns_file, 'w') as f:
            data = {
                k: asdict(v) if hasattr(v, '__dict__') else v
                for k, v in self.learned_patterns.items()
            }
            # Convert datetime objects to strings
            for pattern_data in data.values():
                if 'last_seen' in pattern_data and hasattr(pattern_data['last_seen'], 'isoformat'):
                    pattern_data['last_seen'] = pattern_data['last_seen'].isoformat()
            json.dump(data, f, indent=2, default=str)

    def load_ml_model(self):
        """Load or initialize ML model for pattern learning"""
        if not ML_AVAILABLE:
            return

        if self.ml_model_file.exists():
            with open(self.ml_model_file, 'rb') as f:
                model_data = pickle.load(f)
                self.ml_model = model_data['model']
                self.vectorizer = model_data['vectorizer']
        else:
            # Initialize new model
            self.vectorizer = TfidfVectorizer(max_features=100, ngram_range=(1, 3))
            self.ml_model = MultinomialNB()

    def save_ml_model(self):
        """Save ML model to disk"""
        if not ML_AVAILABLE or not self.ml_model:
            return

        with open(self.ml_model_file, 'wb') as f:
            pickle.dump({
                'model': self.ml_model,
                'vectorizer': self.vectorizer
            }, f)

    def learn_from_history(self, command: str, approved: bool):
        """Learn from user's approval decisions"""
        # Extract pattern from command
        pattern = self.extract_pattern(command)
        pattern_hash = hashlib.md5(pattern.encode()).hexdigest()

        if pattern_hash not in self.learned_patterns:
            self.learned_patterns[pattern_hash] = CommandPattern(
                pattern=pattern,
                category=self.categorize_command(command),
                risk_level=self.assess_risk_level(command),
                frequency=1,
                last_seen=datetime.now(),
                auto_approve=approved,
                learned=True
            )
        else:
            # Update existing pattern
            p = self.learned_patterns[pattern_hash]
            p.frequency += 1
            p.last_seen = datetime.now()

            # Update approval status if consistently approved
            if approved and p.frequency > 5:
                p.auto_approve = True

        self.save_learned_patterns()

        # Update ML model if available
        if ML_AVAILABLE and len(self.command_history) > 50:
            self.train_ml_model()

    def train_ml_model(self):
        """Train ML model on command history"""
        if not ML_AVAILABLE or len(self.command_history) < 50:
            return

        # Prepare training data
        X = [cmd for cmd, _ in self.command_history]
        y = [1 if approved else 0 for _, approved in self.command_history]

        # Split data
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

        # Transform and train
        X_train_vec = self.vectorizer.fit_transform(X_train)
        self.ml_model.fit(X_train_vec, y_train)

        # Test accuracy
        X_test_vec = self.vectorizer.transform(X_test)
        accuracy = self.ml_model.score(X_test_vec, y_test)

        if self.console:
            self.console.print(f"[green]ML Model trained with {accuracy:.2%} accuracy[/green]")

        self.save_ml_model()

    def predict_safety(self, command: str) -> Tuple[bool, float]:
        """Use ML to predict if command is safe"""
        if not ML_AVAILABLE or not self.ml_model:
            return False, 0.0

        try:
            command_vec = self.vectorizer.transform([command])
            prediction = self.ml_model.predict(command_vec)[0]
            probability = self.ml_model.predict_proba(command_vec)[0].max()
            return bool(prediction), float(probability)
        except:
            return False, 0.0

    def detect_anomalies(self, command: str) -> bool:
        """Detect anomalous commands"""
        # Check for unusual patterns
        anomalies = [
            # Base64 encoded commands (potential obfuscation)
            r'base64\s+-d',
            r'echo\s+[A-Za-z0-9+/=]{20,}\s*\|\s*base64',

            # Suspicious downloads
            r'curl.*\|\s*sh',
            r'wget.*\|\s*bash',

            # Hidden processes
            r'nohup.*&\s*disown',

            # Suspicious network activity
            r'nc\s+-l',  # netcat listener
            r'python.*-m.*SimpleHTTPServer',

            # Credential harvesting patterns
            r'find.*\-name.*\.ssh',
            r'grep.*password',
            r'history.*\|\s*grep',
        ]

        for pattern in anomalies:
            if re.search(pattern, command, re.IGNORECASE):
                return True

        # Check against historical baseline
        if len(self.command_history) > 100:
            # Command length anomaly
            avg_length = np.mean([len(cmd) for cmd, _ in self.command_history[-100:]]) if ML_AVAILABLE else 50
            if len(command) > avg_length * 3:
                return True

        return False

    def extract_pattern(self, command: str) -> str:
        """Extract generalizable pattern from command"""
        # Replace specific values with placeholders
        pattern = command

        # Replace file paths
        pattern = re.sub(r'/[\w/.-]+', '/PATH', pattern)

        # Replace IP addresses
        pattern = re.sub(r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}', 'IP_ADDR', pattern)

        # Replace ports
        pattern = re.sub(r':\d{2,5}', ':PORT', pattern)

        # Replace long strings
        pattern = re.sub(r'[A-Za-z0-9]{20,}', 'LONG_STRING', pattern)

        return pattern

    def categorize_command(self, command: str) -> str:
        """Categorize command type"""
        categories = {
            'cloudflare': ['cloudflared', 'tunnel', 'dns'],
            'monitoring': ['ps', 'top', 'htop', 'ss', 'netstat', 'tail', 'grep'],
            'file_ops': ['cp', 'mv', 'mkdir', 'touch', 'cat', 'less', 'more'],
            'network': ['curl', 'wget', 'ping', 'traceroute', 'dig', 'nslookup'],
            'git': ['git', 'clone', 'pull', 'push', 'commit'],
            'process': ['kill', 'pkill', 'systemctl', 'service'],
            'database': ['SELECT', 'INSERT', 'UPDATE', 'psql', 'mysql'],
            'build': ['npm', 'yarn', 'pip', 'cargo', 'make'],
        }

        for category, keywords in categories.items():
            if any(keyword in command.lower() for keyword in keywords):
                return category

        return 'other'

    def assess_risk_level(self, command: str) -> int:
        """Assess risk level of command (0-10)"""
        risk_score = 0

        # High risk keywords
        high_risk = ['rm -rf', 'DROP', 'DELETE', 'kill -9', 'sudo', 'chmod 777']
        for keyword in high_risk:
            if keyword in command:
                risk_score += 3

        # Medium risk
        medium_risk = ['restart', 'stop', 'kill', 'truncate', 'mv', 'UPDATE']
        for keyword in medium_risk:
            if keyword in command:
                risk_score += 2

        # Pipes and redirects increase risk
        risk_score += command.count('|') * 0.5
        risk_score += command.count('>') * 0.5

        # Long commands are riskier
        if len(command) > 100:
            risk_score += 1
        if len(command) > 200:
            risk_score += 1

        return min(int(risk_score), 10)

    def generate_analytics(self) -> Dict:
        """Generate analytics about approval patterns"""
        analytics = {
            'timestamp': datetime.now().isoformat(),
            'total_commands': len(self.command_history),
            'learned_patterns': len(self.learned_patterns),
            'categories': defaultdict(int),
            'risk_distribution': defaultdict(int),
            'approval_rate': 0,
            'ml_accuracy': 0,
            'anomalies_detected': 0,
            'time_saved_hours': 0
        }

        # Analyze patterns
        for pattern in self.learned_patterns.values():
            analytics['categories'][pattern.category] += pattern.frequency
            risk_bucket = f"risk_{pattern.risk_level//3}"  # 0-2, 3-5, 6-8, 9-10
            analytics['risk_distribution'][risk_bucket] += pattern.frequency

        # Calculate approval rate
        if self.command_history:
            approved = sum(1 for _, approved in self.command_history if approved)
            analytics['approval_rate'] = approved / len(self.command_history)

        # Time saved (3.5 seconds per auto-approval)
        auto_approved = sum(p.frequency for p in self.learned_patterns.values() if p.auto_approve)
        analytics['time_saved_hours'] = (auto_approved * 3.5) / 3600

        # Save analytics
        with open(self.analytics_file, 'w') as f:
            json.dump(analytics, f, indent=2)

        return analytics

    def display_dashboard(self):
        """Display enhanced monitoring dashboard"""
        if not RICH_AVAILABLE:
            print("Rich library not available. Install with: pip install rich")
            return

        analytics = self.generate_analytics()

        # Create main table
        table = Table(title="🚀 Auto-Approval System Analytics", show_header=True)
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="green")

        # Add metrics
        table.add_row("Total Commands", str(analytics['total_commands']))
        table.add_row("Learned Patterns", str(analytics['learned_patterns']))
        table.add_row("Approval Rate", f"{analytics['approval_rate']*100:.1f}%")
        table.add_row("Time Saved", f"{analytics['time_saved_hours']:.1f} hours")

        # Category breakdown
        table.add_section()
        table.add_row("[bold]Categories[/bold]", "")
        for category, count in analytics['categories'].items():
            table.add_row(f"  {category}", str(count))

        # Risk distribution
        table.add_section()
        table.add_row("[bold]Risk Levels[/bold]", "")
        for risk, count in sorted(analytics['risk_distribution'].items()):
            table.add_row(f"  {risk}", str(count))

        # Display
        self.console.print(table)

        # Show recent patterns
        recent_panel = Panel.fit(
            "\n".join([f"• {p.pattern[:50]}..." for p in list(self.learned_patterns.values())[-5:]]),
            title="Recent Learned Patterns"
        )
        self.console.print(recent_panel)

    def optimize_config(self):
        """Optimize configuration based on usage patterns"""
        config_file = Path.home() / "Agents/claude/.claude/approved-commands.yaml"

        # Load current config
        with open(config_file, 'r') as f:
            config = yaml.safe_load(f)

        # Add frequently approved patterns
        frequent_patterns = [
            p for p in self.learned_patterns.values()
            if p.frequency > 10 and p.auto_approve and p.risk_level < 3
        ]

        for pattern in frequent_patterns:
            # Check if pattern already exists
            exists = any(
                pattern.pattern in existing['pattern']
                for existing in config.get('auto_approve', [])
            )

            if not exists:
                config['auto_approve'].append({
                    'pattern': pattern.pattern,
                    'description': f"Auto-learned: {pattern.category}",
                    'learned': True,
                    'frequency': pattern.frequency
                })

        # Save optimized config
        with open(config_file, 'w') as f:
            yaml.dump(config, f, default_flow_style=False)

        if self.console:
            self.console.print(f"[green]✅ Optimized config with {len(frequent_patterns)} new patterns[/green]")


def main():
    """Main improvement runner"""
    system = AdvancedAutoApproval()

    print("\n🚀 Advanced Auto-Approval System Improvements")
    print("=" * 50)

    # Run improvements
    improvements = [
        ("Pattern Learning", system.load_learned_patterns),
        ("Analytics Generation", system.generate_analytics),
        ("Configuration Optimization", system.optimize_config),
        ("Dashboard Display", system.display_dashboard)
    ]

    for name, func in improvements:
        print(f"\n▶️ Running: {name}")
        try:
            result = func()
            print(f"  ✅ {name} completed")
        except Exception as e:
            print(f"  ❌ {name} failed: {e}")

    # Show ML status
    if ML_AVAILABLE:
        print("\n🤖 Machine Learning Status: Available")
        print("  The system will learn from your approval patterns over time")
    else:
        print("\n🤖 Machine Learning Status: Not Available")
        print("  Install scikit-learn for ML features: pip install scikit-learn")

    # Recommendations
    print("\n💡 Next Steps:")
    print("1. Let the system learn from your patterns for a few days")
    print("2. Review analytics weekly with: ./scripts/improve-auto-approval.py")
    print("3. The system will automatically optimize patterns")
    print("4. Check anomaly detection alerts in logs")


if __name__ == "__main__":
    main()