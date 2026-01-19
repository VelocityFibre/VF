"""
Live Data Correlation Engine

Connects VPS metrics with git commits to understand real-world impact of code changes.
Enables predictive analysis and consequence awareness.

Architecture:
    Git Commit → Capture VPS Baseline → Deploy → Capture Delta → Analyze Impact

Features:
    - Track VPS metrics pre/post commit (CPU, RAM, disk, response time)
    - Correlate performance changes with code changes
    - Alert when commits cause degradation
    - Build historical database for prediction
    - Generate impact scores for commits

Usage:
    from shared.live_data_correlator import LiveDataCorrelator

    correlator = LiveDataCorrelator()

    # Capture baseline before commit
    baseline = correlator.capture_baseline(commit_hash="abc123")

    # Deploy changes...

    # Capture delta after commit
    result = correlator.capture_delta(commit_hash="abc123")
    print(f"Impact: {result['impact_score']}")

Database Schema:
    - commit_metrics table: commit_hash, timestamp, metrics_before, metrics_after, delta, impact_score
    - alert_history table: commit_hash, alert_level, timestamp, notified
"""

import os
import json
import sqlite3
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
import subprocess


class LiveDataCorrelator:
    """Correlates VPS metrics with git commits for impact analysis."""

    # Impact thresholds
    THRESHOLDS = {
        "critical": {
            "cpu_delta": 20.0,  # +20% CPU
            "ram_delta": 30.0,  # +30% RAM
            "response_time_delta": 100  # +100ms
        },
        "high": {
            "cpu_delta": 10.0,
            "ram_delta": 15.0,
            "response_time_delta": 50
        },
        "medium": {
            "cpu_delta": 5.0,
            "ram_delta": 10.0,
            "response_time_delta": 25
        },
        "low": {
            "cpu_delta": 2.0,
            "ram_delta": 5.0,
            "response_time_delta": 10
        }
    }

    def __init__(self, db_path: str = "memory/commit_metrics.db"):
        """Initialize correlator with SQLite database.

        Args:
            db_path: Path to SQLite database for metrics storage
        """
        self.db_path = db_path
        self._ensure_database()

    def _ensure_database(self):
        """Create database tables if they don't exist."""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Commit metrics table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS commit_metrics (
                commit_hash TEXT PRIMARY KEY,
                timestamp TEXT NOT NULL,
                metrics_before TEXT NOT NULL,
                metrics_after TEXT,
                delta TEXT,
                impact_score TEXT,
                files_changed TEXT,
                alert_triggered INTEGER DEFAULT 0,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Alert history table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS alert_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                commit_hash TEXT NOT NULL,
                alert_level TEXT NOT NULL,
                reason TEXT NOT NULL,
                timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
                notified INTEGER DEFAULT 0,
                FOREIGN KEY (commit_hash) REFERENCES commit_metrics(commit_hash)
            )
        """)

        # Prediction model table (for future ML)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS prediction_model (
                file_pattern TEXT PRIMARY KEY,
                avg_cpu_impact REAL DEFAULT 0.0,
                avg_ram_impact REAL DEFAULT 0.0,
                avg_response_time_impact REAL DEFAULT 0.0,
                sample_count INTEGER DEFAULT 0,
                last_updated TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)

        conn.commit()
        conn.close()

    def capture_baseline(self, commit_hash: str, files_changed: List[str] = None) -> Dict[str, Any]:
        """Capture VPS metrics baseline before commit deployment.

        Args:
            commit_hash: Git commit hash
            files_changed: List of files modified in commit

        Returns:
            Dict with baseline metrics and status
        """
        try:
            # Get current VPS metrics
            metrics = self._get_vps_metrics()

            if not metrics["success"]:
                return {
                    "success": False,
                    "error": "Failed to capture VPS metrics",
                    "details": metrics.get("error")
                }

            # Store baseline in database
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute("""
                INSERT OR REPLACE INTO commit_metrics
                (commit_hash, timestamp, metrics_before, files_changed)
                VALUES (?, ?, ?, ?)
            """, (
                commit_hash,
                datetime.utcnow().isoformat(),
                json.dumps(metrics["data"]),
                json.dumps(files_changed or [])
            ))

            conn.commit()
            conn.close()

            return {
                "success": True,
                "commit_hash": commit_hash,
                "baseline_captured": True,
                "metrics": metrics["data"]
            }

        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to capture baseline: {str(e)}"
            }

    def capture_delta(self, commit_hash: str, wait_seconds: int = 60) -> Dict[str, Any]:
        """Capture VPS metrics delta after commit deployment.

        Args:
            commit_hash: Git commit hash
            wait_seconds: Seconds to wait before capturing (let metrics stabilize)

        Returns:
            Dict with delta metrics, impact score, and alerts
        """
        try:
            # Get new metrics
            metrics = self._get_vps_metrics()

            if not metrics["success"]:
                return {
                    "success": False,
                    "error": "Failed to capture VPS metrics",
                    "details": metrics.get("error")
                }

            # Retrieve baseline
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute("""
                SELECT metrics_before, files_changed
                FROM commit_metrics
                WHERE commit_hash = ?
            """, (commit_hash,))

            row = cursor.fetchone()

            if not row:
                conn.close()
                return {
                    "success": False,
                    "error": f"No baseline found for commit {commit_hash[:7]}"
                }

            metrics_before = json.loads(row[0])
            files_changed = json.loads(row[1]) if row[1] else []

            # Calculate delta
            delta = self._calculate_delta(metrics_before, metrics["data"])

            # Calculate impact score
            impact_score, impact_reasons = self._calculate_impact_score(delta)

            # Check if alert needed
            alert_triggered = impact_score in ["critical", "high"]

            # Update database
            cursor.execute("""
                UPDATE commit_metrics
                SET metrics_after = ?,
                    delta = ?,
                    impact_score = ?,
                    alert_triggered = ?
                WHERE commit_hash = ?
            """, (
                json.dumps(metrics["data"]),
                json.dumps(delta),
                impact_score,
                1 if alert_triggered else 0,
                commit_hash
            ))

            # Log alert if needed
            if alert_triggered:
                cursor.execute("""
                    INSERT INTO alert_history (commit_hash, alert_level, reason)
                    VALUES (?, ?, ?)
                """, (commit_hash, impact_score, "; ".join(impact_reasons)))

            conn.commit()
            conn.close()

            # Update prediction model
            self._update_prediction_model(files_changed, delta)

            return {
                "success": True,
                "commit_hash": commit_hash,
                "metrics_before": metrics_before,
                "metrics_after": metrics["data"],
                "delta": delta,
                "impact_score": impact_score,
                "impact_reasons": impact_reasons,
                "alert_triggered": alert_triggered,
                "files_changed": files_changed
            }

        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to capture delta: {str(e)}"
            }

    def _get_vps_metrics(self) -> Dict[str, Any]:
        """Get current VPS metrics from VPS Monitor agent.

        Returns:
            Dict with success flag and metrics data
        """
        try:
            # Use VPS Monitor agent to get current metrics
            from agents.vps_monitor.agent import VPSMonitorAgent

            api_key = os.getenv("ANTHROPIC_API_KEY")
            if not api_key:
                return {
                    "success": False,
                    "error": "ANTHROPIC_API_KEY not set"
                }

            agent = VPSMonitorAgent(api_key)

            # Get health metrics
            result = agent._check_vps_health()

            if not result.get("success"):
                return {
                    "success": False,
                    "error": result.get("error", "Unknown error")
                }

            # Extract relevant metrics
            metrics = {
                "cpu_percent": result.get("cpu_usage", 0.0),
                "ram_percent": result.get("memory_usage", {}).get("percent", 0.0),
                "disk_percent": result.get("disk_usage", {}).get("percent", 0.0),
                "timestamp": datetime.utcnow().isoformat()
            }

            # TODO: Add response time monitoring (requires API health check endpoint)
            # For now, use placeholder
            metrics["avg_response_time_ms"] = 150  # Placeholder

            return {
                "success": True,
                "data": metrics
            }

        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to get VPS metrics: {str(e)}"
            }

    def _calculate_delta(self, before: Dict[str, Any], after: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate delta between two metric snapshots.

        Args:
            before: Baseline metrics
            after: Current metrics

        Returns:
            Dict with delta values
        """
        return {
            "cpu_delta": after["cpu_percent"] - before["cpu_percent"],
            "ram_delta": after["ram_percent"] - before["ram_percent"],
            "disk_delta": after["disk_percent"] - before["disk_percent"],
            "response_time_delta": after["avg_response_time_ms"] - before["avg_response_time_ms"],
            "duration_minutes": (
                datetime.fromisoformat(after["timestamp"]) -
                datetime.fromisoformat(before["timestamp"])
            ).total_seconds() / 60
        }

    def _calculate_impact_score(self, delta: Dict[str, Any]) -> tuple[str, List[str]]:
        """Calculate impact score based on delta thresholds.

        Args:
            delta: Metric deltas

        Returns:
            Tuple of (impact_score, reasons)
        """
        reasons = []

        # Check critical thresholds
        if abs(delta["cpu_delta"]) >= self.THRESHOLDS["critical"]["cpu_delta"]:
            reasons.append(f"CPU {'increased' if delta['cpu_delta'] > 0 else 'decreased'} by {abs(delta['cpu_delta']):.1f}%")
            return "critical", reasons

        if abs(delta["ram_delta"]) >= self.THRESHOLDS["critical"]["ram_delta"]:
            reasons.append(f"RAM {'increased' if delta['ram_delta'] > 0 else 'decreased'} by {abs(delta['ram_delta']):.1f}%")
            return "critical", reasons

        if abs(delta["response_time_delta"]) >= self.THRESHOLDS["critical"]["response_time_delta"]:
            reasons.append(f"Response time {'increased' if delta['response_time_delta'] > 0 else 'decreased'} by {abs(delta['response_time_delta']):.0f}ms")
            return "critical", reasons

        # Check high thresholds
        if abs(delta["cpu_delta"]) >= self.THRESHOLDS["high"]["cpu_delta"]:
            reasons.append(f"CPU changed by {abs(delta['cpu_delta']):.1f}%")
            return "high", reasons

        if abs(delta["ram_delta"]) >= self.THRESHOLDS["high"]["ram_delta"]:
            reasons.append(f"RAM changed by {abs(delta['ram_delta']):.1f}%")
            return "high", reasons

        if abs(delta["response_time_delta"]) >= self.THRESHOLDS["high"]["response_time_delta"]:
            reasons.append(f"Response time changed by {abs(delta['response_time_delta']):.0f}ms")
            return "high", reasons

        # Check medium thresholds
        if abs(delta["cpu_delta"]) >= self.THRESHOLDS["medium"]["cpu_delta"]:
            reasons.append(f"CPU changed by {abs(delta['cpu_delta']):.1f}%")
            return "medium", reasons

        if abs(delta["ram_delta"]) >= self.THRESHOLDS["medium"]["ram_delta"]:
            reasons.append(f"RAM changed by {abs(delta['ram_delta']):.1f}%")
            return "medium", reasons

        if abs(delta["response_time_delta"]) >= self.THRESHOLDS["medium"]["response_time_delta"]:
            reasons.append(f"Response time changed by {abs(delta['response_time_delta']):.0f}ms")
            return "medium", reasons

        # Check low thresholds
        if abs(delta["cpu_delta"]) >= self.THRESHOLDS["low"]["cpu_delta"]:
            reasons.append(f"Minor CPU change: {abs(delta['cpu_delta']):.1f}%")
            return "low", reasons

        if abs(delta["ram_delta"]) >= self.THRESHOLDS["low"]["ram_delta"]:
            reasons.append(f"Minor RAM change: {abs(delta['ram_delta']):.1f}%")
            return "low", reasons

        if abs(delta["response_time_delta"]) >= self.THRESHOLDS["low"]["response_time_delta"]:
            reasons.append(f"Minor response time change: {abs(delta['response_time_delta']):.0f}ms")
            return "low", reasons

        # No significant change
        return "none", ["Metrics within noise threshold"]

    def _update_prediction_model(self, files_changed: List[str], delta: Dict[str, Any]):
        """Update prediction model with new data point.

        Args:
            files_changed: List of files modified
            delta: Metric deltas observed
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            for file_path in files_changed:
                # Extract file pattern (e.g., agents/*.py, shared/*.py)
                parts = file_path.split('/')
                pattern = f"{parts[0]}/*.{file_path.split('.')[-1]}" if len(parts) > 1 else file_path

                # Get current model data
                cursor.execute("""
                    SELECT avg_cpu_impact, avg_ram_impact, avg_response_time_impact, sample_count
                    FROM prediction_model
                    WHERE file_pattern = ?
                """, (pattern,))

                row = cursor.fetchone()

                if row:
                    # Update running average
                    avg_cpu, avg_ram, avg_response, count = row
                    new_count = count + 1

                    new_avg_cpu = (avg_cpu * count + delta["cpu_delta"]) / new_count
                    new_avg_ram = (avg_ram * count + delta["ram_delta"]) / new_count
                    new_avg_response = (avg_response * count + delta["response_time_delta"]) / new_count

                    cursor.execute("""
                        UPDATE prediction_model
                        SET avg_cpu_impact = ?,
                            avg_ram_impact = ?,
                            avg_response_time_impact = ?,
                            sample_count = ?,
                            last_updated = ?
                        WHERE file_pattern = ?
                    """, (new_avg_cpu, new_avg_ram, new_avg_response, new_count, datetime.utcnow().isoformat(), pattern))
                else:
                    # Insert new pattern
                    cursor.execute("""
                        INSERT INTO prediction_model
                        (file_pattern, avg_cpu_impact, avg_ram_impact, avg_response_time_impact, sample_count)
                        VALUES (?, ?, ?, ?, 1)
                    """, (pattern, delta["cpu_delta"], delta["ram_delta"], delta["response_time_delta"]))

            conn.commit()
            conn.close()

        except Exception as e:
            print(f"Warning: Failed to update prediction model: {e}")

    def predict_impact(self, files_changed: List[str]) -> Dict[str, Any]:
        """Predict impact of commit based on files changed.

        Args:
            files_changed: List of files that will be modified

        Returns:
            Dict with predicted impact scores
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            predictions = []

            for file_path in files_changed:
                # Extract file pattern
                parts = file_path.split('/')
                pattern = f"{parts[0]}/*.{file_path.split('.')[-1]}" if len(parts) > 1 else file_path

                # Get prediction data
                cursor.execute("""
                    SELECT avg_cpu_impact, avg_ram_impact, avg_response_time_impact, sample_count
                    FROM prediction_model
                    WHERE file_pattern = ?
                """, (pattern,))

                row = cursor.fetchone()

                if row:
                    predictions.append({
                        "file": file_path,
                        "pattern": pattern,
                        "predicted_cpu_delta": row[0],
                        "predicted_ram_delta": row[1],
                        "predicted_response_time_delta": row[2],
                        "confidence": min(row[3] / 10.0, 1.0)  # Confidence increases with samples (max 1.0)
                    })

            conn.close()

            if not predictions:
                return {
                    "success": True,
                    "has_prediction": False,
                    "message": "No historical data for these file patterns"
                }

            # Aggregate predictions
            avg_cpu = sum(p["predicted_cpu_delta"] for p in predictions) / len(predictions)
            avg_ram = sum(p["predicted_ram_delta"] for p in predictions) / len(predictions)
            avg_response = sum(p["predicted_response_time_delta"] for p in predictions) / len(predictions)
            avg_confidence = sum(p["confidence"] for p in predictions) / len(predictions)

            # Calculate predicted impact score
            predicted_delta = {
                "cpu_delta": avg_cpu,
                "ram_delta": avg_ram,
                "response_time_delta": avg_response
            }
            predicted_impact, reasons = self._calculate_impact_score(predicted_delta)

            return {
                "success": True,
                "has_prediction": True,
                "predicted_impact": predicted_impact,
                "predicted_delta": predicted_delta,
                "reasons": reasons,
                "confidence": avg_confidence,
                "file_predictions": predictions
            }

        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to predict impact: {str(e)}"
            }

    def get_recent_alerts(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent performance alerts.

        Args:
            limit: Maximum number of alerts to return

        Returns:
            List of alert dicts
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute("""
                SELECT
                    ah.commit_hash,
                    ah.alert_level,
                    ah.reason,
                    ah.timestamp,
                    cm.files_changed
                FROM alert_history ah
                JOIN commit_metrics cm ON ah.commit_hash = cm.commit_hash
                ORDER BY ah.timestamp DESC
                LIMIT ?
            """, (limit,))

            rows = cursor.fetchall()
            conn.close()

            return [
                {
                    "commit_hash": row[0],
                    "alert_level": row[1],
                    "reason": row[2],
                    "timestamp": row[3],
                    "files_changed": json.loads(row[4]) if row[4] else []
                }
                for row in rows
            ]

        except Exception as e:
            print(f"Error retrieving alerts: {e}")
            return []

    def get_commit_history(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Get historical commit metrics.

        Args:
            limit: Maximum number of commits to return

        Returns:
            List of commit metric dicts
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute("""
                SELECT
                    commit_hash,
                    timestamp,
                    impact_score,
                    delta,
                    files_changed,
                    alert_triggered
                FROM commit_metrics
                WHERE metrics_after IS NOT NULL
                ORDER BY timestamp DESC
                LIMIT ?
            """, (limit,))

            rows = cursor.fetchall()
            conn.close()

            return [
                {
                    "commit_hash": row[0],
                    "timestamp": row[1],
                    "impact_score": row[2],
                    "delta": json.loads(row[3]) if row[3] else {},
                    "files_changed": json.loads(row[4]) if row[4] else [],
                    "alert_triggered": bool(row[5])
                }
                for row in rows
            ]

        except Exception as e:
            print(f"Error retrieving commit history: {e}")
            return []


if __name__ == "__main__":
    """Demo usage of LiveDataCorrelator."""
    print("=== Live Data Correlator Demo ===\n")

    correlator = LiveDataCorrelator()

    # Get latest commit
    try:
        commit_hash = subprocess.check_output(
            ["git", "rev-parse", "HEAD"],
            text=True
        ).strip()

        files_changed = subprocess.check_output(
            ["git", "diff-tree", "--no-commit-id", "--name-only", "-r", commit_hash],
            text=True
        ).strip().split('\n')

        print(f"Latest commit: {commit_hash[:7]}")
        print(f"Files changed: {len(files_changed)}")
        print()

        # Capture baseline
        print("Capturing baseline metrics...")
        baseline = correlator.capture_baseline(commit_hash, files_changed)

        if baseline["success"]:
            print(f"✓ Baseline captured: {baseline['metrics']}")
            print()

            # Simulate deployment wait
            print("(In production: deploy changes, wait 60 seconds)")
            print()

            # Capture delta (without actual deployment in demo)
            print("Capturing delta metrics...")
            delta = correlator.capture_delta(commit_hash)

            if delta["success"]:
                print(f"✓ Impact Score: {delta['impact_score']}")
                print(f"  Reasons: {', '.join(delta['impact_reasons'])}")
                print(f"  Delta: CPU {delta['delta']['cpu_delta']:+.1f}%, RAM {delta['delta']['ram_delta']:+.1f}%")
                if delta["alert_triggered"]:
                    print(f"  ⚠️ ALERT TRIGGERED")
                print()
        else:
            print(f"✗ Failed: {baseline['error']}")

        # Show prediction for future commits
        print("Prediction for similar commits:")
        prediction = correlator.predict_impact(files_changed)

        if prediction["success"] and prediction["has_prediction"]:
            print(f"  Predicted Impact: {prediction['predicted_impact']}")
            print(f"  Confidence: {prediction['confidence']*100:.0f}%")
            print(f"  Predicted Delta: CPU {prediction['predicted_delta']['cpu_delta']:+.1f}%, "
                  f"RAM {prediction['predicted_delta']['ram_delta']:+.1f}%")
        else:
            print(f"  {prediction.get('message', 'No prediction available')}")
        print()

        # Show recent alerts
        print("Recent Alerts:")
        alerts = correlator.get_recent_alerts(limit=5)

        if alerts:
            for alert in alerts:
                print(f"  [{alert['alert_level'].upper()}] {alert['commit_hash'][:7]}: {alert['reason']}")
        else:
            print("  No recent alerts")
        print()

    except Exception as e:
        print(f"Demo error: {e}")
