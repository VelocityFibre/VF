"""
Pattern Learning & Feedback System

Learns from developer decisions to improve prediction accuracy over time.
This is the self-improving intelligence layer that makes FibreFlow smarter with usage.

Learning Sources:
    1. Approval/Rejection: Which tasks get approved vs dismissed?
    2. Manual Edits: How do developers modify generated code?
    3. Reverted Fixes: Which auto-fixes get manually reverted?
    4. Test Failures: Which patterns cause tests to fail?

Learning Loop:
    System Suggests Fix → Developer Action → Log Decision → Update Weights → Improve Future

Architecture:
    Feedback Database (SQLite) → Pattern Weights → Confidence Scoring → Better Suggestions

Usage:
    from shared.pattern_learner import PatternLearner

    learner = PatternLearner()

    # Log developer decision
    learner.log_feedback(
        task_id="task-001",
        action="approved",
        time_to_decision=5.2
    )

    # Update pattern weights
    learner.update_weights()

    # Get improved confidence
    confidence = learner.get_pattern_confidence("unused_import")
    print(f"Confidence: {confidence:.2f}")
"""

import os
import sqlite3
import json
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from pathlib import Path


class PatternLearner:
    """Learns from developer feedback to improve pattern matching."""

    # Initial pattern weights (will be adjusted based on feedback)
    DEFAULT_WEIGHTS = {
        "unused_import": 0.9,  # High confidence initially
        "trailing_whitespace": 0.95,
        "missing_docstring": 0.7,
        "print_debug": 0.8,
        "todo_formatting": 0.85,
        "n_plus_one_query": 0.6,  # Medium confidence (harder to fix)
        "missing_error_handling": 0.5,
        "broad_exception": 0.7,
        "test_stub_generation": 0.65
    }

    # Weight adjustment deltas
    ADJUSTMENT_DELTAS = {
        "approved": +0.1,  # Increase confidence
        "rejected": -0.2,  # Decrease confidence more
        "edited": -0.05,   # Slight decrease (partial success)
        "reverted": -0.3   # Large decrease (failure)
    }

    # Minimum samples before adjusting weights
    MIN_SAMPLES_FOR_ADJUSTMENT = 3

    def __init__(self, db_path: str = "memory/feedback.db"):
        """Initialize pattern learner.

        Args:
            db_path: Path to SQLite feedback database
        """
        self.db_path = db_path
        self._ensure_database()

    def _ensure_database(self):
        """Create database tables if they don't exist."""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Feedback log table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS feedback_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                task_id TEXT NOT NULL,
                task_type TEXT NOT NULL,
                description TEXT NOT NULL,
                confidence_was REAL NOT NULL,
                developer_action TEXT NOT NULL,
                developer_edit TEXT,
                time_to_decision_seconds REAL,
                timestamp TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Pattern weights table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS pattern_weights (
                pattern_type TEXT PRIMARY KEY,
                current_weight REAL NOT NULL,
                initial_weight REAL NOT NULL,
                total_samples INTEGER DEFAULT 0,
                approved_count INTEGER DEFAULT 0,
                rejected_count INTEGER DEFAULT 0,
                edited_count INTEGER DEFAULT 0,
                reverted_count INTEGER DEFAULT 0,
                last_updated TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Initialize default weights
        for pattern, weight in self.DEFAULT_WEIGHTS.items():
            cursor.execute("""
                INSERT OR IGNORE INTO pattern_weights
                (pattern_type, current_weight, initial_weight)
                VALUES (?, ?, ?)
            """, (pattern, weight, weight))

        # Learning statistics table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS learning_stats (
                stat_date TEXT PRIMARY KEY,
                total_feedback INTEGER DEFAULT 0,
                approval_rate REAL DEFAULT 0.0,
                rejection_rate REAL DEFAULT 0.0,
                edit_rate REAL DEFAULT 0.0,
                revert_rate REAL DEFAULT 0.0,
                average_time_to_decision REAL DEFAULT 0.0,
                patterns_adjusted INTEGER DEFAULT 0
            )
        """)

        conn.commit()
        conn.close()

    def log_feedback(
        self,
        task_id: str,
        task_type: str,
        description: str,
        confidence_was: float,
        action: str,
        edit_content: Optional[str] = None,
        time_to_decision: Optional[float] = None
    ) -> Dict[str, Any]:
        """Log developer feedback for a task.

        Args:
            task_id: Unique task identifier
            task_type: Type of task (e.g., "unused_import")
            description: Task description
            confidence_was: Confidence level when suggested
            action: Developer action (approved/rejected/edited/reverted)
            edit_content: If edited, what was changed
            time_to_decision: Seconds to make decision

        Returns:
            Dict with feedback log status
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Validate action
            valid_actions = ["approved", "rejected", "edited", "reverted"]

            if action not in valid_actions:
                return {
                    "success": False,
                    "error": f"Invalid action. Must be one of: {valid_actions}"
                }

            # Log feedback
            cursor.execute("""
                INSERT INTO feedback_log
                (task_id, task_type, description, confidence_was, developer_action, developer_edit, time_to_decision_seconds)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (task_id, task_type, description, confidence_was, action, edit_content, time_to_decision))

            # Update pattern statistics
            cursor.execute(f"""
                UPDATE pattern_weights
                SET total_samples = total_samples + 1,
                    {action}_count = {action}_count + 1,
                    last_updated = ?
                WHERE pattern_type = ?
            """, (datetime.utcnow().isoformat(), task_type))

            conn.commit()
            conn.close()

            return {
                "success": True,
                "task_id": task_id,
                "action": action,
                "logged_at": datetime.utcnow().isoformat()
            }

        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to log feedback: {str(e)}"
            }

    def update_weights(self, min_samples: int = None) -> Dict[str, Any]:
        """Update pattern weights based on accumulated feedback.

        Args:
            min_samples: Minimum samples required for adjustment (default: 3)

        Returns:
            Dict with update statistics
        """
        try:
            if min_samples is None:
                min_samples = self.MIN_SAMPLES_FOR_ADJUSTMENT

            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Get patterns with enough samples
            cursor.execute("""
                SELECT pattern_type, current_weight, initial_weight,
                       total_samples, approved_count, rejected_count, edited_count, reverted_count
                FROM pattern_weights
                WHERE total_samples >= ?
            """, (min_samples,))

            rows = cursor.fetchall()

            updates = []

            for row in rows:
                pattern, current_weight, initial_weight, total, approved, rejected, edited, reverted = row

                # Calculate weighted adjustment
                total_adjustment = 0.0
                total_adjustment += approved * self.ADJUSTMENT_DELTAS["approved"]
                total_adjustment += rejected * self.ADJUSTMENT_DELTAS["rejected"]
                total_adjustment += edited * self.ADJUSTMENT_DELTAS["edited"]
                total_adjustment += reverted * self.ADJUSTMENT_DELTAS["reverted"]

                # Calculate average adjustment per sample
                avg_adjustment = total_adjustment / total

                # Apply adjustment to current weight
                new_weight = current_weight + avg_adjustment

                # Clamp between 0.1 and 1.0
                new_weight = max(0.1, min(1.0, new_weight))

                # Update database
                cursor.execute("""
                    UPDATE pattern_weights
                    SET current_weight = ?,
                        last_updated = ?
                    WHERE pattern_type = ?
                """, (new_weight, datetime.utcnow().isoformat(), pattern))

                updates.append({
                    "pattern": pattern,
                    "old_weight": current_weight,
                    "new_weight": new_weight,
                    "delta": new_weight - current_weight,
                    "samples": total
                })

            conn.commit()
            conn.close()

            return {
                "success": True,
                "patterns_updated": len(updates),
                "updates": updates
            }

        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to update weights: {str(e)}"
            }

    def get_pattern_confidence(self, pattern_type: str) -> float:
        """Get current confidence weight for a pattern.

        Args:
            pattern_type: Pattern type (e.g., "unused_import")

        Returns:
            Confidence weight (0.0-1.0)
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute("""
                SELECT current_weight
                FROM pattern_weights
                WHERE pattern_type = ?
            """, (pattern_type,))

            row = cursor.fetchone()
            conn.close()

            if row:
                return row[0]
            else:
                # Return default if pattern not found
                return self.DEFAULT_WEIGHTS.get(pattern_type, 0.5)

        except Exception as e:
            print(f"Warning: Failed to get pattern confidence: {e}")
            return 0.5

    def get_all_weights(self) -> Dict[str, float]:
        """Get all current pattern weights.

        Returns:
            Dict mapping pattern type to confidence weight
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute("""
                SELECT pattern_type, current_weight
                FROM pattern_weights
            """)

            rows = cursor.fetchall()
            conn.close()

            return {row[0]: row[1] for row in rows}

        except Exception as e:
            print(f"Warning: Failed to get weights: {e}")
            return self.DEFAULT_WEIGHTS.copy()

    def get_pattern_statistics(self, pattern_type: str) -> Dict[str, Any]:
        """Get detailed statistics for a pattern.

        Args:
            pattern_type: Pattern type

        Returns:
            Dict with pattern statistics
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute("""
                SELECT current_weight, initial_weight, total_samples,
                       approved_count, rejected_count, edited_count, reverted_count,
                       last_updated
                FROM pattern_weights
                WHERE pattern_type = ?
            """, (pattern_type,))

            row = cursor.fetchone()
            conn.close()

            if not row:
                return {
                    "success": False,
                    "error": f"Pattern '{pattern_type}' not found"
                }

            current, initial, total, approved, rejected, edited, reverted, updated = row

            # Calculate rates
            approval_rate = (approved / total * 100) if total > 0 else 0
            rejection_rate = (rejected / total * 100) if total > 0 else 0
            edit_rate = (edited / total * 100) if total > 0 else 0
            revert_rate = (reverted / total * 100) if total > 0 else 0

            return {
                "success": True,
                "pattern_type": pattern_type,
                "current_weight": current,
                "initial_weight": initial,
                "weight_delta": current - initial,
                "total_samples": total,
                "approved": approved,
                "rejected": rejected,
                "edited": edited,
                "reverted": reverted,
                "approval_rate": approval_rate,
                "rejection_rate": rejection_rate,
                "edit_rate": edit_rate,
                "revert_rate": revert_rate,
                "last_updated": updated
            }

        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to get statistics: {str(e)}"
            }

    def get_learning_summary(self, days: int = 7) -> Dict[str, Any]:
        """Get learning summary for recent period.

        Args:
            days: Number of days to analyze

        Returns:
            Dict with learning summary
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Get feedback from last N days
            cutoff_date = (datetime.utcnow() - timedelta(days=days)).isoformat()

            cursor.execute("""
                SELECT COUNT(*) as total,
                       SUM(CASE WHEN developer_action = 'approved' THEN 1 ELSE 0 END) as approved,
                       SUM(CASE WHEN developer_action = 'rejected' THEN 1 ELSE 0 END) as rejected,
                       SUM(CASE WHEN developer_action = 'edited' THEN 1 ELSE 0 END) as edited,
                       SUM(CASE WHEN developer_action = 'reverted' THEN 1 ELSE 0 END) as reverted,
                       AVG(time_to_decision_seconds) as avg_time
                FROM feedback_log
                WHERE timestamp > ?
            """, (cutoff_date,))

            row = cursor.fetchone()

            if not row or row[0] == 0:
                conn.close()
                return {
                    "success": True,
                    "period_days": days,
                    "total_feedback": 0,
                    "message": "No feedback data in this period"
                }

            total, approved, rejected, edited, reverted, avg_time = row

            # Get patterns that improved/degraded
            cursor.execute("""
                SELECT pattern_type, current_weight - initial_weight as delta
                FROM pattern_weights
                WHERE total_samples > 0
                ORDER BY ABS(current_weight - initial_weight) DESC
                LIMIT 5
            """)

            top_changes = [
                {"pattern": row[0], "delta": row[1]}
                for row in cursor.fetchall()
            ]

            conn.close()

            return {
                "success": True,
                "period_days": days,
                "total_feedback": total,
                "approved": approved or 0,
                "rejected": rejected or 0,
                "edited": edited or 0,
                "reverted": reverted or 0,
                "approval_rate": (approved / total * 100) if total > 0 and approved else 0,
                "rejection_rate": (rejected / total * 100) if total > 0 and rejected else 0,
                "average_decision_time_seconds": avg_time or 0,
                "top_pattern_changes": top_changes
            }

        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to get learning summary: {str(e)}"
            }

    def simulate_feedback(self, num_samples: int = 50) -> Dict[str, Any]:
        """Simulate feedback for demonstration purposes.

        Args:
            num_samples: Number of feedback samples to generate

        Returns:
            Dict with simulation results
        """
        import random

        patterns = list(self.DEFAULT_WEIGHTS.keys())
        actions = ["approved", "rejected", "edited", "reverted"]

        # Weighted probabilities (more approvals than rejections)
        action_weights = [0.5, 0.2, 0.2, 0.1]

        for i in range(num_samples):
            pattern = random.choice(patterns)
            action = random.choices(actions, weights=action_weights)[0]
            confidence = self.get_pattern_confidence(pattern)

            self.log_feedback(
                task_id=f"sim-{i}",
                task_type=pattern,
                description=f"Simulated {pattern} task",
                confidence_was=confidence,
                action=action,
                time_to_decision=random.uniform(1.0, 30.0)
            )

        # Update weights based on feedback
        update_result = self.update_weights(min_samples=5)

        return {
            "success": True,
            "samples_generated": num_samples,
            "weights_updated": update_result.get("patterns_updated", 0)
        }


if __name__ == "__main__":
    """Demo usage of Pattern Learner."""
    print("=== Pattern Learning & Feedback System Demo ===\n")

    learner = PatternLearner()

    # Show initial weights
    print("Initial Pattern Weights:")
    weights = learner.get_all_weights()

    for pattern, weight in sorted(weights.items(), key=lambda x: x[1], reverse=True):
        print(f"  {pattern}: {weight:.2f}")
    print()

    # Simulate feedback
    print("Simulating 50 developer feedback samples...\n")

    sim_result = learner.simulate_feedback(num_samples=50)

    if sim_result["success"]:
        print(f"✓ Simulated {sim_result['samples_generated']} feedback samples")
        print(f"✓ Updated {sim_result['weights_updated']} pattern weights")
        print()

    # Show updated weights
    print("Updated Pattern Weights:")
    new_weights = learner.get_all_weights()

    for pattern, weight in sorted(new_weights.items(), key=lambda x: x[1], reverse=True):
        delta = weight - weights[pattern]
        arrow = "↑" if delta > 0 else "↓" if delta < 0 else "→"
        print(f"  {pattern}: {weight:.2f} ({arrow} {delta:+.2f})")
    print()

    # Show statistics for a specific pattern
    print("Detailed Statistics for 'unused_import':")
    stats = learner.get_pattern_statistics("unused_import")

    if stats["success"]:
        print(f"  Current Weight: {stats['current_weight']:.2f}")
        print(f"  Weight Delta: {stats['weight_delta']:+.2f}")
        print(f"  Total Samples: {stats['total_samples']}")
        print(f"  Approval Rate: {stats['approval_rate']:.1f}%")
        print(f"  Rejection Rate: {stats['rejection_rate']:.1f}%")
        print(f"  Edit Rate: {stats['edit_rate']:.1f}%")
        print(f"  Revert Rate: {stats['revert_rate']:.1f}%")
    print()

    # Show learning summary
    print("Learning Summary (Last 7 Days):")
    summary = learner.get_learning_summary(days=7)

    if summary["success"] and summary.get("total_feedback", 0) > 0:
        print(f"  Total Feedback: {summary['total_feedback']}")
        print(f"  Approval Rate: {summary['approval_rate']:.1f}%")
        print(f"  Rejection Rate: {summary['rejection_rate']:.1f}%")
        print(f"  Avg Decision Time: {summary['average_decision_time_seconds']:.1f}s")
        print()
        print("  Top Pattern Changes:")

        for change in summary['top_pattern_changes']:
            arrow = "↑" if change['delta'] > 0 else "↓"
            print(f"    {arrow} {change['pattern']}: {change['delta']:+.2f}")
    else:
        print(f"  {summary.get('message', 'No data available')}")
