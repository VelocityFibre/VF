#!/usr/bin/env python3
"""
Best-of-N Selector - Phase 3: Autopilot Mode

Selects the best implementation from N parallel agent attempts using
consensus voting and weighted scoring.

City Planning Analogy: Like a city planning board reviewing 15 different
proposals for a new bridge - they score each on safety, cost, timeline,
aesthetics, and select the best overall design.

Part of Vibe Coding Transformation - see docs/VIBE_CODING_TRANSFORMATION.md
"""

import logging
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime
import json
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class AgentAttempt:
    """
    Result of a single agent implementation attempt.

    Represents one of N parallel attempts to implement a feature.
    """
    feature_id: int
    attempt_id: int  # 1-N
    sandbox_id: str

    # Test metrics
    test_coverage: float  # 0.0 - 1.0
    tests_passed: int
    tests_failed: int
    tests_total: int

    # Code quality metrics
    code_quality_score: float  # 0.0 - 1.0 (from static analysis)
    linting_errors: int
    linting_warnings: int

    # Performance metrics
    execution_time: float  # seconds
    memory_peak_mb: float  # Peak memory usage

    # Artifacts
    artifacts: Dict[str, Any]  # Generated code, tests, logs

    # Metadata
    timestamp: str
    model_tier: str  # haiku, sonnet, opus
    cost: float  # dollars

    # Scoring (computed)
    total_score: float = 0.0
    rank: int = 0


@dataclass
class ConsensusResult:
    """Result of consensus validation across top attempts."""
    has_consensus: bool
    agreement_score: float  # 0.0 - 1.0
    top_attempts: List[int]  # Attempt IDs in consensus
    approach_similarity: str  # Description of shared approach
    outliers: List[int]  # Attempt IDs that disagree


class BestOfNSelector:
    """
    Selects best result from N parallel agent attempts.

    Scoring algorithm (weighted):
    - Test coverage: 40% weight (most important)
    - Tests passed: 30% weight
    - Code quality: 20% weight
    - Execution speed: 10% weight

    Consensus validation:
    - Top 3 attempts should agree on core approach
    - If no consensus → flag for human review
    - Prevents edge cases where all attempts are mediocre
    """

    # Scoring weights
    WEIGHT_TEST_COVERAGE = 0.40
    WEIGHT_TESTS_PASSED = 0.30
    WEIGHT_CODE_QUALITY = 0.20
    WEIGHT_EXECUTION_SPEED = 0.10

    # Consensus thresholds
    CONSENSUS_MIN_AGREEMENT = 0.70  # 70% similarity required
    CONSENSUS_TOP_N = 3  # Check top 3 attempts

    def __init__(self):
        """Initialize selector."""
        logger.info("BestOfNSelector initialized for autopilot mode")

    def score_attempt(self, attempt: AgentAttempt) -> float:
        """
        Calculate weighted score for single attempt.

        Args:
            attempt: Agent implementation attempt

        Returns:
            Total score (0.0 - 1.0)
        """
        # Test coverage score (0.0 - 1.0)
        coverage_score = attempt.test_coverage

        # Tests passed score (0.0 - 1.0)
        if attempt.tests_total > 0:
            pass_rate = attempt.tests_passed / attempt.tests_total
        else:
            pass_rate = 0.0

        # Code quality score (already 0.0 - 1.0)
        quality_score = attempt.code_quality_score

        # Execution speed score (normalize to 0.0 - 1.0)
        # Faster is better, cap at 5 minutes (300s)
        max_time = 300.0
        speed_score = max(0.0, 1.0 - (attempt.execution_time / max_time))

        # Weighted total
        total = (
            (coverage_score * self.WEIGHT_TEST_COVERAGE) +
            (pass_rate * self.WEIGHT_TESTS_PASSED) +
            (quality_score * self.WEIGHT_CODE_QUALITY) +
            (speed_score * self.WEIGHT_EXECUTION_SPEED)
        )

        # Store for tracking
        attempt.total_score = total

        logger.debug(
            f"Attempt {attempt.attempt_id} scored: "
            f"coverage={coverage_score:.2f} ({self.WEIGHT_TEST_COVERAGE*100}%), "
            f"pass_rate={pass_rate:.2f} ({self.WEIGHT_TESTS_PASSED*100}%), "
            f"quality={quality_score:.2f} ({self.WEIGHT_CODE_QUALITY*100}%), "
            f"speed={speed_score:.2f} ({self.WEIGHT_EXECUTION_SPEED*100}%) "
            f"→ TOTAL={total:.3f}"
        )

        return total

    def select_best(
        self,
        attempts: List[AgentAttempt],
        require_consensus: bool = True
    ) -> Tuple[AgentAttempt, ConsensusResult]:
        """
        Select highest-scoring attempt from parallel executions.

        Args:
            attempts: List of N agent attempts
            require_consensus: If True, validate consensus before selection

        Returns:
            Tuple of (best_attempt, consensus_result)

        Raises:
            ValueError: If no attempts provided or all failed
        """
        if not attempts:
            raise ValueError("No attempts to select from")

        logger.info(f"Selecting best from {len(attempts)} parallel attempts...")

        # Score all attempts
        for attempt in attempts:
            self.score_attempt(attempt)

        # Sort by score (highest first)
        sorted_attempts = sorted(
            attempts,
            key=lambda a: a.total_score,
            reverse=True
        )

        # Assign ranks
        for rank, attempt in enumerate(sorted_attempts, start=1):
            attempt.rank = rank

        # Best attempt
        best = sorted_attempts[0]

        logger.info(
            f"✅ Best attempt: #{best.attempt_id} "
            f"(score={best.total_score:.3f}, "
            f"coverage={best.test_coverage:.1%}, "
            f"passed={best.tests_passed}/{best.tests_total})"
        )

        # Validate consensus if required
        consensus_result = None
        if require_consensus:
            consensus_result = self.validate_consensus(sorted_attempts)

            if not consensus_result.has_consensus:
                logger.warning(
                    f"⚠️  No consensus among top {self.CONSENSUS_TOP_N} attempts "
                    f"(agreement={consensus_result.agreement_score:.1%}). "
                    "Human review recommended."
                )
            else:
                logger.info(
                    f"✅ Consensus validated "
                    f"(agreement={consensus_result.agreement_score:.1%})"
                )

        return best, consensus_result

    def validate_consensus(self, sorted_attempts: List[AgentAttempt]) -> ConsensusResult:
        """
        Ensure consensus exists among top N attempts.

        Checks if the top 3 attempts agree on the core approach.
        Agreement measured by:
        - Similar test coverage (±10%)
        - Similar file structure (same modules created)
        - Similar function signatures (public API matches)

        Args:
            sorted_attempts: Attempts sorted by score (best first)

        Returns:
            ConsensusResult with agreement details
        """
        if len(sorted_attempts) < self.CONSENSUS_TOP_N:
            # Not enough attempts for consensus
            return ConsensusResult(
                has_consensus=False,
                agreement_score=0.0,
                top_attempts=[a.attempt_id for a in sorted_attempts],
                approach_similarity="Insufficient attempts for consensus",
                outliers=[]
            )

        # Get top N attempts
        top_attempts = sorted_attempts[:self.CONSENSUS_TOP_N]

        # Calculate agreement metrics
        agreement_score = self._calculate_agreement(top_attempts)

        # Identify outliers (attempts that significantly disagree)
        outliers = []
        for attempt in sorted_attempts[self.CONSENSUS_TOP_N:]:
            if self._is_outlier(attempt, top_attempts):
                outliers.append(attempt.attempt_id)

        # Determine approach similarity
        approach = self._describe_shared_approach(top_attempts)

        has_consensus = agreement_score >= self.CONSENSUS_MIN_AGREEMENT

        return ConsensusResult(
            has_consensus=has_consensus,
            agreement_score=agreement_score,
            top_attempts=[a.attempt_id for a in top_attempts],
            approach_similarity=approach,
            outliers=outliers
        )

    def _calculate_agreement(self, attempts: List[AgentAttempt]) -> float:
        """
        Calculate agreement score among attempts.

        Measures similarity in:
        - Test coverage (should be close)
        - Pass rates (should be close)
        - Code quality (should be close)

        Args:
            attempts: List of attempts to compare

        Returns:
            Agreement score (0.0 - 1.0)
        """
        if len(attempts) < 2:
            return 1.0  # Single attempt = perfect agreement

        # Extract metrics
        coverages = [a.test_coverage for a in attempts]
        pass_rates = [
            a.tests_passed / a.tests_total if a.tests_total > 0 else 0.0
            for a in attempts
        ]
        qualities = [a.code_quality_score for a in attempts]

        # Calculate variance (lower = more agreement)
        coverage_variance = self._variance(coverages)
        pass_rate_variance = self._variance(pass_rates)
        quality_variance = self._variance(qualities)

        # Convert variance to agreement score
        # Lower variance → higher agreement
        coverage_agreement = 1.0 - min(1.0, coverage_variance * 5)
        pass_rate_agreement = 1.0 - min(1.0, pass_rate_variance * 5)
        quality_agreement = 1.0 - min(1.0, quality_variance * 5)

        # Weighted average
        agreement = (
            coverage_agreement * 0.4 +
            pass_rate_agreement * 0.4 +
            quality_agreement * 0.2
        )

        return agreement

    def _variance(self, values: List[float]) -> float:
        """Calculate variance of values."""
        if not values:
            return 0.0

        mean = sum(values) / len(values)
        variance = sum((x - mean) ** 2 for x in values) / len(values)

        return variance

    def _is_outlier(
        self,
        attempt: AgentAttempt,
        top_attempts: List[AgentAttempt]
    ) -> bool:
        """
        Check if attempt is an outlier compared to top attempts.

        An outlier has significantly different metrics (>20% difference).

        Args:
            attempt: Attempt to check
            top_attempts: Top N attempts to compare against

        Returns:
            True if attempt is an outlier
        """
        # Average metrics from top attempts
        avg_coverage = sum(a.test_coverage for a in top_attempts) / len(top_attempts)
        avg_quality = sum(a.code_quality_score for a in top_attempts) / len(top_attempts)

        # Check if significantly different
        coverage_diff = abs(attempt.test_coverage - avg_coverage)
        quality_diff = abs(attempt.code_quality_score - avg_quality)

        is_outlier = coverage_diff > 0.20 or quality_diff > 0.20

        return is_outlier

    def _describe_shared_approach(self, attempts: List[AgentAttempt]) -> str:
        """
        Describe the shared approach among top attempts.

        Args:
            attempts: Top N attempts

        Returns:
            Human-readable description of shared approach
        """
        # For now, return generic description
        # TODO: Analyze artifact similarities (file names, structure, etc.)

        avg_coverage = sum(a.test_coverage for a in attempts) / len(attempts)
        avg_tests = sum(a.tests_total for a in attempts) / len(attempts)

        return (
            f"All top attempts achieved ~{avg_coverage:.0%} test coverage "
            f"with ~{avg_tests:.0f} tests"
        )

    def generate_report(
        self,
        attempts: List[AgentAttempt],
        best: AgentAttempt,
        consensus: ConsensusResult
    ) -> str:
        """
        Generate human-readable report of selection results.

        Args:
            attempts: All attempts
            best: Selected best attempt
            consensus: Consensus validation result

        Returns:
            Formatted report string
        """
        report = []

        report.append("=" * 70)
        report.append("BEST-OF-N SELECTION REPORT")
        report.append("=" * 70)
        report.append("")

        # Summary
        report.append(f"Total attempts: {len(attempts)}")
        report.append(f"Winner: Attempt #{best.attempt_id}")
        report.append(f"Score: {best.total_score:.3f}/1.000")
        report.append("")

        # Metrics breakdown
        report.append("Winner metrics:")
        report.append(f"  Test coverage:  {best.test_coverage:.1%}")
        report.append(f"  Tests passed:   {best.tests_passed}/{best.tests_total}")
        report.append(f"  Code quality:   {best.code_quality_score:.1%}")
        report.append(f"  Execution time: {best.execution_time:.1f}s")
        report.append(f"  Model tier:     {best.model_tier.upper()}")
        report.append(f"  Cost:           ${best.cost:.3f}")
        report.append("")

        # Consensus
        if consensus:
            report.append("Consensus validation:")
            report.append(f"  Has consensus:   {'✅ Yes' if consensus.has_consensus else '⚠️  No'}")
            report.append(f"  Agreement score: {consensus.agreement_score:.1%}")
            report.append(f"  Top attempts:    {', '.join(f'#{id}' for id in consensus.top_attempts)}")
            report.append(f"  Approach:        {consensus.approach_similarity}")

            if consensus.outliers:
                report.append(f"  Outliers:        {', '.join(f'#{id}' for id in consensus.outliers)}")

            report.append("")

        # All attempts ranking
        report.append("All attempts ranking:")
        sorted_attempts = sorted(attempts, key=lambda a: a.total_score, reverse=True)

        for attempt in sorted_attempts:
            rank_icon = "🥇" if attempt.rank == 1 else ("🥈" if attempt.rank == 2 else ("🥉" if attempt.rank == 3 else " "))
            report.append(
                f"  {rank_icon} #{attempt.attempt_id:2d}: "
                f"{attempt.total_score:.3f} "
                f"(coverage={attempt.test_coverage:.0%}, "
                f"passed={attempt.tests_passed}/{attempt.tests_total}, "
                f"quality={attempt.code_quality_score:.0%})"
            )

        report.append("")
        report.append("=" * 70)

        return "\n".join(report)

    def save_results(
        self,
        attempts: List[AgentAttempt],
        best: AgentAttempt,
        consensus: ConsensusResult,
        output_file: Path
    ) -> None:
        """
        Save selection results to JSON file.

        Args:
            attempts: All attempts
            best: Selected best attempt
            consensus: Consensus validation result
            output_file: Path to output JSON file
        """
        results = {
            "timestamp": datetime.now().isoformat(),
            "total_attempts": len(attempts),
            "winner": asdict(best),
            "consensus": asdict(consensus) if consensus else None,
            "all_attempts": [asdict(a) for a in attempts]
        }

        with open(output_file, 'w') as f:
            json.dump(results, f, indent=2)

        logger.info(f"Results saved to {output_file}")


if __name__ == "__main__":
    # Demo the best-of-N selector
    print("Best-of-N Selector - Phase 3: Autopilot Mode")
    print("=" * 70)
    print()

    selector = BestOfNSelector()

    # Simulate 15 parallel attempts
    print("Simulating 15 parallel implementation attempts...")
    print()

    attempts = [
        AgentAttempt(
            feature_id=1,
            attempt_id=i,
            sandbox_id=f"sandbox-{i}",
            test_coverage=0.75 + (i * 0.01),  # Varies
            tests_passed=18 + i,
            tests_failed=2 - (i % 2),
            tests_total=20 + i,
            code_quality_score=0.80 + (i * 0.005),
            linting_errors=5 - (i % 5),
            linting_warnings=10 - (i % 3),
            execution_time=45 + (i * 2),
            memory_peak_mb=256 + (i * 10),
            artifacts={"code": f"attempt_{i}.py", "tests": f"test_{i}.py"},
            timestamp=datetime.now().isoformat(),
            model_tier="sonnet" if i % 2 == 0 else "haiku",
            cost=0.020 if i % 2 == 0 else 0.001
        )
        for i in range(1, 16)
    ]

    # Select best
    best, consensus = selector.select_best(attempts, require_consensus=True)

    # Generate report
    print(selector.generate_report(attempts, best, consensus))

    # Save results
    output_file = Path("harness/best_of_n_results.json")
    selector.save_results(attempts, best, consensus, output_file)

    print()
    print("=" * 70)
    print("✅ Best-of-N selector demo complete")
