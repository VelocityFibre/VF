#!/usr/bin/env python3
"""
Confidence Scoring System for Proactive Tasks

Analyzes discovered tasks and assigns confidence scores (high/medium/low)
based on risk assessment, context analysis, and auto-fix feasibility.

Part of FibreFlow Proactive Agent System.
"""

from typing import Dict, Any, Literal
from datetime import datetime
import re


ConfidenceLevel = Literal["high", "medium", "low"]


class ConfidenceScorer:
    """Scores proactive task suggestions with confidence levels"""

    # High confidence: Safe, trivial, zero risk
    HIGH_CONFIDENCE_PATTERNS = {
        "unused_import": {
            "patterns": [r"unused import", r"imported but unused"],
            "risk": "none",
            "auto_fixable": True,
            "effort_minutes": 1
        },
        "missing_docstring": {
            "patterns": [r"missing docstring", r"no docstring"],
            "risk": "none",
            "auto_fixable": True,
            "effort_minutes": 2
        },
        "todo_comment": {
            "patterns": [r"# TODO", r"# FIXME", r"# HACK"],
            "risk": "none",
            "auto_fixable": False,
            "effort_minutes": 5
        },
        "missing_test": {
            "patterns": [r"no test coverage", r"function.*without test"],
            "risk": "low",
            "auto_fixable": True,
            "effort_minutes": 5
        },
        "trailing_whitespace": {
            "patterns": [r"trailing whitespace", r"whitespace at end"],
            "risk": "none",
            "auto_fixable": True,
            "effort_minutes": 1
        }
    }

    # Medium confidence: Requires review, some risk
    MEDIUM_CONFIDENCE_PATTERNS = {
        "performance_optimization": {
            "patterns": [r"N\+1 query", r"inefficient", r"could be optimized"],
            "risk": "medium",
            "auto_fixable": False,
            "effort_minutes": 15
        },
        "code_duplication": {
            "patterns": [r"duplicate", r"repeated code"],
            "risk": "medium",
            "auto_fixable": False,
            "effort_minutes": 20
        },
        "missing_error_handling": {
            "patterns": [r"no error handling", r"missing try.*except"],
            "risk": "medium",
            "auto_fixable": True,
            "effort_minutes": 10
        },
        "deprecated_usage": {
            "patterns": [r"deprecated", r"outdated"],
            "risk": "medium",
            "auto_fixable": False,
            "effort_minutes": 15
        }
    }

    # Low confidence: Complex, high risk, needs careful review
    LOW_CONFIDENCE_PATTERNS = {
        "security_issue": {
            "patterns": [r"SQL injection", r"XSS", r"security"],
            "risk": "high",
            "auto_fixable": False,
            "effort_minutes": 30
        },
        "architecture_change": {
            "patterns": [r"refactor", r"redesign", r"architecture"],
            "risk": "high",
            "auto_fixable": False,
            "effort_minutes": 120
        },
        "breaking_change": {
            "patterns": [r"breaking change", r"backward compatibility"],
            "risk": "high",
            "auto_fixable": False,
            "effort_minutes": 60
        }
    }

    def score_task(
        self,
        task_description: str,
        task_type: str,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Score a task and return confidence level with reasoning.

        Args:
            task_description: What the task is
            task_type: Category (bug_fix, test_coverage, security, etc.)
            context: {file, line, code_snippet, recent_changes}

        Returns:
            {
                confidence: "high" | "medium" | "low",
                reasoning: str,
                auto_fixable: bool,
                estimated_effort: int (minutes),
                risk_level: "none" | "low" | "medium" | "high"
            }
        """
        description_lower = task_description.lower()

        # Check high confidence patterns first
        for pattern_name, pattern_info in self.HIGH_CONFIDENCE_PATTERNS.items():
            if any(re.search(p, description_lower) for p in pattern_info["patterns"]):
                return {
                    "confidence": "high",
                    "reasoning": f"Trivial fix ({pattern_name}), zero risk",
                    "auto_fixable": pattern_info["auto_fixable"],
                    "estimated_effort": pattern_info["effort_minutes"],
                    "risk_level": pattern_info["risk"]
                }

        # Check medium confidence patterns
        for pattern_name, pattern_info in self.MEDIUM_CONFIDENCE_PATTERNS.items():
            if any(re.search(p, description_lower) for p in pattern_info["patterns"]):
                return {
                    "confidence": "medium",
                    "reasoning": f"Requires review ({pattern_name}), moderate complexity",
                    "auto_fixable": pattern_info["auto_fixable"],
                    "estimated_effort": pattern_info["effort_minutes"],
                    "risk_level": pattern_info["risk"]
                }

        # Check low confidence patterns
        for pattern_name, pattern_info in self.LOW_CONFIDENCE_PATTERNS.items():
            if any(re.search(p, description_lower) for p in pattern_info["patterns"]):
                return {
                    "confidence": "low",
                    "reasoning": f"High risk ({pattern_name}), careful review needed",
                    "auto_fixable": pattern_info["auto_fixable"],
                    "estimated_effort": pattern_info["effort_minutes"],
                    "risk_level": pattern_info["risk"]
                }

        # Context-based scoring for unmatched patterns
        return self._score_by_context(task_description, task_type, context)

    def _score_by_context(
        self,
        description: str,
        task_type: str,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Score based on context when pattern matching fails"""
        file = context.get("file", "")

        # Security-related files = low confidence
        if any(keyword in file for keyword in ["auth", "security", "crypto", "password"]):
            return {
                "confidence": "low",
                "reasoning": "Security-sensitive file, manual review required",
                "auto_fixable": False,
                "estimated_effort": 30,
                "risk_level": "high"
            }

        # Test files = medium confidence (safe to modify)
        if "test" in file or file.startswith("tests/"):
            return {
                "confidence": "medium",
                "reasoning": "Test file, relatively safe to modify",
                "auto_fixable": True,
                "estimated_effort": 10,
                "risk_level": "low"
            }

        # Documentation = high confidence
        if file.endswith(".md") or file.endswith(".rst"):
            return {
                "confidence": "high",
                "reasoning": "Documentation file, safe to update",
                "auto_fixable": True,
                "estimated_effort": 5,
                "risk_level": "none"
            }

        # Default: medium confidence
        return {
            "confidence": "medium",
            "reasoning": "Unknown pattern, requires review",
            "auto_fixable": False,
            "estimated_effort": 15,
            "risk_level": "medium"
        }


class ProactivityQueue:
    """Manages the proactive task queue with CRUD operations"""

    def __init__(self, queue_file: str = "shared/proactivity_queue.json"):
        self.queue_file = queue_file
        self.scorer = ConfidenceScorer()

    def load_queue(self) -> Dict[str, Any]:
        """Load queue from JSON file"""
        import json
        from pathlib import Path

        queue_path = Path(self.queue_file)
        if not queue_path.exists():
            return {
                "version": "1.0",
                "last_updated": datetime.utcnow().isoformat() + "Z",
                "total_tasks": 0,
                "high_confidence": 0,
                "medium_confidence": 0,
                "low_confidence": 0,
                "tasks": []
            }

        with open(queue_path) as f:
            return json.load(f)

    def save_queue(self, queue: Dict[str, Any]) -> None:
        """Save queue to JSON file"""
        import json
        from pathlib import Path

        queue["last_updated"] = datetime.utcnow().isoformat() + "Z"

        queue_path = Path(self.queue_file)
        queue_path.parent.mkdir(parents=True, exist_ok=True)

        with open(queue_path, 'w') as f:
            json.dump(queue, f, indent=2)

    def add_task(
        self,
        task_type: str,
        description: str,
        file: str,
        line: int = None,
        context: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Add a new task to the queue with automatic confidence scoring.

        Args:
            task_type: Category (bug_fix, test_coverage, security, etc.)
            description: Human-readable description
            file: File path where issue found
            line: Line number (optional)
            context: Additional context for scoring

        Returns:
            Created task object
        """
        queue = self.load_queue()

        # Generate task ID
        task_id = f"task-{len(queue['tasks']) + 1:03d}"

        # Score confidence
        context = context or {}
        context.update({"file": file, "line": line})
        score_result = self.scorer.score_task(description, task_type, context)

        # Create task
        task = {
            "id": task_id,
            "type": task_type,
            "description": description,
            "file": file,
            "line": line,
            "confidence": score_result["confidence"],
            "reasoning": score_result["reasoning"],
            "auto_fixable": score_result["auto_fixable"],
            "estimated_effort": score_result["estimated_effort"],
            "risk_level": score_result["risk_level"],
            "created_at": datetime.utcnow().isoformat() + "Z",
            "status": "queued",
            "age_hours": 0
        }

        # Add to queue
        queue["tasks"].append(task)
        queue["total_tasks"] = len(queue["tasks"])
        queue[f"{score_result['confidence']}_confidence"] += 1

        self.save_queue(queue)
        return task

    def get_tasks(
        self,
        filter_confidence: str = "all",
        filter_type: str = None,
        sort_by: str = "confidence",
        limit: int = 50
    ) -> Dict[str, Any]:
        """
        Retrieve tasks with filtering and sorting.

        Args:
            filter_confidence: "high", "medium", "low", "all"
            filter_type: Task type filter (optional)
            sort_by: "confidence", "age", "effort"
            limit: Max tasks to return

        Returns:
            {total_tasks, filtered_tasks, tasks: [...]}
        """
        queue = self.load_queue()
        tasks = queue["tasks"]

        # Filter by confidence
        if filter_confidence != "all":
            tasks = [t for t in tasks if t["confidence"] == filter_confidence]

        # Filter by type
        if filter_type:
            tasks = [t for t in tasks if t["type"] == filter_type]

        # Sort
        if sort_by == "confidence":
            confidence_order = {"high": 0, "medium": 1, "low": 2}
            tasks = sorted(tasks, key=lambda t: confidence_order.get(t["confidence"], 3))
        elif sort_by == "age":
            tasks = sorted(tasks, key=lambda t: t["created_at"], reverse=True)
        elif sort_by == "effort":
            tasks = sorted(tasks, key=lambda t: t["estimated_effort"])

        # Limit
        tasks = tasks[:limit]

        return {
            "total_tasks": queue["total_tasks"],
            "filtered_tasks": len(tasks),
            "tasks": tasks
        }

    def update_task(self, task_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
        """Update task fields"""
        queue = self.load_queue()

        for task in queue["tasks"]:
            if task["id"] == task_id:
                task.update(updates)
                self.save_queue(queue)
                return task

        raise ValueError(f"Task {task_id} not found")

    def remove_task(self, task_id: str) -> bool:
        """Remove task from queue"""
        queue = self.load_queue()

        initial_count = len(queue["tasks"])
        queue["tasks"] = [t for t in queue["tasks"] if t["id"] != task_id]

        if len(queue["tasks"]) < initial_count:
            queue["total_tasks"] = len(queue["tasks"])

            # Recalculate confidence counts
            queue["high_confidence"] = len([t for t in queue["tasks"] if t["confidence"] == "high"])
            queue["medium_confidence"] = len([t for t in queue["tasks"] if t["confidence"] == "medium"])
            queue["low_confidence"] = len([t for t in queue["tasks"] if t["confidence"] == "low"])

            self.save_queue(queue)
            return True

        return False


# Example usage
if __name__ == "__main__":
    # Demo: Add some tasks
    queue = ProactivityQueue()

    # High confidence: Unused import
    task1 = queue.add_task(
        task_type="code_quality",
        description="Unused import 'datetime' in neon_agent.py",
        file="agents/neon-database/agent.py",
        line=12
    )
    print(f"✓ Added {task1['id']}: {task1['confidence']} confidence")

    # Medium confidence: Missing error handling
    task2 = queue.add_task(
        task_type="bug_fix",
        description="No error handling in execute_query() method",
        file="agents/neon-database/agent.py",
        line=156,
        context={"code_snippet": "def execute_query(self, query):"}
    )
    print(f"✓ Added {task2['id']}: {task2['confidence']} confidence")

    # Low confidence: Security issue
    task3 = queue.add_task(
        task_type="security",
        description="Potential SQL injection in query concatenation",
        file="neon_agent.py",
        line=234,
        context={"code_snippet": "query = 'SELECT * FROM ' + table"}
    )
    print(f"✓ Added {task3['id']}: {task3['confidence']} confidence")

    # Retrieve high confidence tasks
    result = queue.get_tasks(filter_confidence="high", limit=10)
    print(f"\n{result['filtered_tasks']} high-confidence tasks:")
    for task in result["tasks"]:
        print(f"  - {task['id']}: {task['description']}")
