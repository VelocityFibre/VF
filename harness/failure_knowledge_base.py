#!/usr/bin/env python3
"""
Failure Knowledge Base - Phase 1.5 (Reflection & Self-Improvement)

Persistent storage and retrieval of learned patterns from failed agent attempts.
Enables self-improving agents that avoid repeating past mistakes.

City Planning Analogy: Like a city's historical archive of infrastructure failures
that inform future planning decisions (e.g., "Don't build on flood plains").

Part of Vibe Coding Transformation - see docs/VIBE_CODING_TRANSFORMATION.md
"""

import json
import re
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class FailurePattern:
    """A learned pattern from a failed attempt."""
    timestamp: str
    feature_id: int
    agent_name: str
    error_type: str  # "ImportError", "TestFailure", "TimeoutError", etc.
    error_pattern: str  # Regex or signature of the error
    affected_module: str  # File/module where error occurred
    context: Dict[str, Any]  # Additional context (dependencies, env vars, etc.)
    learnings: List[str]  # Reusable knowledge extracted
    suggestions: List[str]  # Actionable improvements for next attempt
    frequency: int = 1  # How many times we've seen this pattern
    last_seen: Optional[str] = None


class FailureKnowledgeBase:
    """
    Persistent storage of learned patterns from failed attempts.

    Like a city's historical archive that tracks:
    - Which bridges collapsed (and why)
    - Which roads flooded (and when)
    - Which buildings had foundation issues (and how to prevent)

    Usage:
        kb = FailureKnowledgeBase()

        # After a failed attempt
        kb.store_failure(
            feature_id=1,
            agent_name="neon-agent",
            error_type="ImportError",
            error_pattern="No module named 'psycopg2'",
            affected_module="agents/neon_agent/database.py",
            learnings=["psycopg2-binary must be in requirements.txt"],
            suggestions=["Add psycopg2-binary to requirements/base.txt"]
        )

        # Before next attempt
        relevant = kb.get_relevant_learnings(
            agent_name="neon-agent",
            feature_desc="Database connection handling"
        )
        # Returns: Learned patterns to avoid
    """

    def __init__(
        self,
        storage_path: Path = Path("harness/learned_patterns.json")
    ):
        """
        Initialize knowledge base.

        Args:
            storage_path: Path to JSON file storing patterns
        """
        self.storage_path = Path(storage_path)
        self.patterns: List[FailurePattern] = []

        # Create storage directory if needed
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)

        # Load existing patterns
        self._load_patterns()

        logger.info(
            f"FailureKnowledgeBase initialized with {len(self.patterns)} patterns"
        )

    def _load_patterns(self) -> None:
        """Load patterns from storage file."""
        if not self.storage_path.exists():
            logger.info("No existing patterns found, starting fresh")
            return

        try:
            with open(self.storage_path) as f:
                data = json.load(f)

            self.patterns = [
                FailurePattern(**pattern)
                for pattern in data.get("patterns", [])
            ]

            logger.info(f"Loaded {len(self.patterns)} existing patterns")

        except Exception as e:
            logger.error(f"Failed to load patterns: {e}")
            self.patterns = []

    def _save_patterns(self) -> None:
        """Save patterns to storage file."""
        try:
            data = {
                "version": "1.0",
                "last_updated": datetime.now().isoformat(),
                "total_patterns": len(self.patterns),
                "patterns": [asdict(p) for p in self.patterns]
            }

            with open(self.storage_path, 'w') as f:
                json.dump(data, f, indent=2)

            logger.debug(f"Saved {len(self.patterns)} patterns")

        except Exception as e:
            logger.error(f"Failed to save patterns: {e}")

    def store_failure(
        self,
        feature_id: int,
        agent_name: str,
        error_type: str,
        error_pattern: str,
        affected_module: str,
        learnings: List[str],
        suggestions: List[str],
        context: Optional[Dict[str, Any]] = None
    ) -> FailurePattern:
        """
        Store a failure pattern in knowledge base.

        Args:
            feature_id: Feature that failed
            agent_name: Agent being built
            error_type: Type of error (ImportError, TestFailure, etc.)
            error_pattern: Error signature or regex
            affected_module: Module where error occurred
            learnings: Reusable knowledge extracted
            suggestions: Actionable improvements
            context: Additional context

        Returns:
            Created FailurePattern
        """
        # Check if we've seen this pattern before
        existing = self._find_similar_pattern(
            error_type=error_type,
            error_pattern=error_pattern,
            agent_name=agent_name
        )

        if existing:
            # Update existing pattern
            existing.frequency += 1
            existing.last_seen = datetime.now().isoformat()

            # Merge learnings and suggestions (avoid duplicates)
            existing.learnings = list(set(existing.learnings + learnings))
            existing.suggestions = list(set(existing.suggestions + suggestions))

            logger.info(
                f"Updated existing pattern (frequency: {existing.frequency}): "
                f"{error_type} in {agent_name}"
            )

            pattern = existing

        else:
            # Create new pattern
            pattern = FailurePattern(
                timestamp=datetime.now().isoformat(),
                feature_id=feature_id,
                agent_name=agent_name,
                error_type=error_type,
                error_pattern=error_pattern,
                affected_module=affected_module,
                context=context or {},
                learnings=learnings,
                suggestions=suggestions,
                frequency=1,
                last_seen=datetime.now().isoformat()
            )

            self.patterns.append(pattern)

            logger.info(
                f"Stored new failure pattern: {error_type} in {agent_name}"
            )

        # Save to disk
        self._save_patterns()

        return pattern

    def _find_similar_pattern(
        self,
        error_type: str,
        error_pattern: str,
        agent_name: str
    ) -> Optional[FailurePattern]:
        """
        Find existing pattern similar to this error.

        Args:
            error_type: Type of error
            error_pattern: Error signature
            agent_name: Agent name

        Returns:
            Matching FailurePattern or None
        """
        for pattern in self.patterns:
            if (pattern.error_type == error_type and
                pattern.agent_name == agent_name and
                pattern.error_pattern == error_pattern):
                return pattern

        return None

    def get_relevant_learnings(
        self,
        agent_name: str,
        feature_desc: str = "",
        max_results: int = 10
    ) -> List[FailurePattern]:
        """
        Retrieve learned patterns relevant to current task.

        Args:
            agent_name: Agent being built
            feature_desc: Feature description (for keyword matching)
            max_results: Maximum patterns to return

        Returns:
            List of relevant FailurePatterns, sorted by relevance
        """
        relevant = []

        for pattern in self.patterns:
            relevance_score = 0

            # Exact agent name match (high relevance)
            if pattern.agent_name == agent_name:
                relevance_score += 10

            # Partial agent name match (medium relevance)
            elif agent_name in pattern.agent_name or pattern.agent_name in agent_name:
                relevance_score += 5

            # Keyword overlap in feature description
            if feature_desc:
                pattern_keywords = self._extract_keywords(
                    pattern.affected_module + " " + " ".join(pattern.learnings)
                )
                feature_keywords = self._extract_keywords(feature_desc)

                overlap = len(pattern_keywords & feature_keywords)
                relevance_score += overlap

            # Boost frequently seen patterns
            if pattern.frequency > 3:
                relevance_score += 2

            if relevance_score > 0:
                relevant.append((relevance_score, pattern))

        # Sort by relevance score (descending)
        relevant.sort(key=lambda x: x[0], reverse=True)

        # Return top N patterns
        return [pattern for _, pattern in relevant[:max_results]]

    def _extract_keywords(self, text: str) -> set:
        """Extract keywords from text (simple tokenization)."""
        # Remove special characters, lowercase, split
        words = re.findall(r'\b\w+\b', text.lower())

        # Filter out common stop words
        stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for'}
        keywords = {w for w in words if w not in stop_words and len(w) > 2}

        return keywords

    def get_pattern_by_error_type(
        self,
        error_type: str,
        agent_name: Optional[str] = None
    ) -> List[FailurePattern]:
        """
        Get all patterns for a specific error type.

        Args:
            error_type: Type of error to filter by
            agent_name: Optional agent name filter

        Returns:
            List of matching FailurePatterns
        """
        patterns = [p for p in self.patterns if p.error_type == error_type]

        if agent_name:
            patterns = [p for p in patterns if p.agent_name == agent_name]

        return patterns

    def get_top_errors(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get most frequent error patterns.

        Args:
            limit: Number of top errors to return

        Returns:
            List of error summaries sorted by frequency
        """
        # Group by error type + agent
        error_counts = {}

        for pattern in self.patterns:
            key = f"{pattern.error_type}:{pattern.agent_name}"
            if key not in error_counts:
                error_counts[key] = {
                    "error_type": pattern.error_type,
                    "agent_name": pattern.agent_name,
                    "count": 0,
                    "examples": []
                }

            error_counts[key]["count"] += pattern.frequency
            error_counts[key]["examples"].append(pattern.error_pattern)

        # Sort by count
        top_errors = sorted(
            error_counts.values(),
            key=lambda x: x["count"],
            reverse=True
        )

        return top_errors[:limit]

    def get_stats(self) -> Dict[str, Any]:
        """
        Get knowledge base statistics.

        Returns:
            Dictionary with stats about patterns
        """
        total_patterns = len(self.patterns)
        total_failures = sum(p.frequency for p in self.patterns)

        # Count by error type
        by_error_type = {}
        for pattern in self.patterns:
            by_error_type[pattern.error_type] = by_error_type.get(
                pattern.error_type, 0
            ) + pattern.frequency

        # Count by agent
        by_agent = {}
        for pattern in self.patterns:
            by_agent[pattern.agent_name] = by_agent.get(
                pattern.agent_name, 0
            ) + pattern.frequency

        return {
            "total_patterns": total_patterns,
            "total_failures_tracked": total_failures,
            "by_error_type": by_error_type,
            "by_agent": by_agent,
            "most_common_errors": self.get_top_errors(5)
        }

    def clear_old_patterns(self, days: int = 30) -> int:
        """
        Remove patterns older than specified days.

        Args:
            days: Age threshold in days

        Returns:
            Number of patterns removed
        """
        from datetime import timedelta

        cutoff = datetime.now() - timedelta(days=days)

        original_count = len(self.patterns)

        self.patterns = [
            p for p in self.patterns
            if datetime.fromisoformat(p.timestamp) > cutoff
        ]

        removed = original_count - len(self.patterns)

        if removed > 0:
            self._save_patterns()
            logger.info(f"Removed {removed} patterns older than {days} days")

        return removed


if __name__ == "__main__":
    # Example usage
    print("Failure Knowledge Base - Phase 1.5 Demo")
    print("=" * 70)
    print()

    # Initialize knowledge base
    kb = FailureKnowledgeBase()

    # Simulate storing some failure patterns
    print("Storing failure patterns...")
    print()

    # Failure 1: Import error
    kb.store_failure(
        feature_id=1,
        agent_name="neon-agent",
        error_type="ImportError",
        error_pattern="No module named 'psycopg2'",
        affected_module="agents/neon_agent/database.py",
        learnings=["psycopg2-binary must be in requirements.txt"],
        suggestions=["Add 'psycopg2-binary>=2.9.0' to requirements/base.txt"]
    )

    # Failure 2: Test timeout
    kb.store_failure(
        feature_id=2,
        agent_name="vlm-evaluator",
        error_type="TimeoutError",
        error_pattern="VLM request exceeded 30s timeout",
        affected_module="agents/vlm_evaluator/image_processor.py",
        learnings=["VLM processing needs 60s timeout minimum"],
        suggestions=["Increase timeout to 60s", "Add retry logic for VLM calls"]
    )

    # Failure 3: Test failure
    kb.store_failure(
        feature_id=3,
        agent_name="qfield-sync",
        error_type="TestFailure",
        error_pattern="AssertionError: Expected 5 records, got 3",
        affected_module="tests/test_qfield_sync.py",
        learnings=["Mock data setup incomplete", "Need to seed test database"],
        suggestions=["Add test fixtures", "Create setup_test_data() helper"]
    )

    print(f"✅ Stored {len(kb.patterns)} failure patterns")
    print()

    # Retrieve relevant learnings
    print("Retrieving relevant learnings for neon-agent...")
    print()

    relevant = kb.get_relevant_learnings(
        agent_name="neon-agent",
        feature_desc="Database connection and query handling"
    )

    for i, pattern in enumerate(relevant, 1):
        print(f"{i}. {pattern.error_type}: {pattern.error_pattern}")
        print(f"   Learnings: {', '.join(pattern.learnings)}")
        print(f"   Suggestions: {', '.join(pattern.suggestions)}")
        print()

    # Get statistics
    print("Knowledge base statistics:")
    print()
    stats = kb.get_stats()
    print(f"Total patterns: {stats['total_patterns']}")
    print(f"Total failures tracked: {stats['total_failures_tracked']}")
    print(f"By error type: {stats['by_error_type']}")
    print(f"By agent: {stats['by_agent']}")
    print()

    print("=" * 70)
    print("✅ Demo complete - knowledge base is learning from failures!")
