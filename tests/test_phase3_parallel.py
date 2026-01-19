#!/usr/bin/env python3
"""
Tests for Phase 3: Parallel Execution Components

Tests the Auto-Claude integration Phase 3 components:
- DependencyGraph: Dependency analysis and level computation
- RateLimitHandler: Rate limit handling with exponential backoff
"""

import pytest
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from harness.dependency_graph import DependencyGraph
from harness.rate_limit_handler import RateLimitHandler


# ============================================================================
# DependencyGraph Tests
# ============================================================================

@pytest.mark.unit
@pytest.mark.phase3
def test_dependency_graph_no_dependencies():
    """Test features with no dependencies are all in level 0."""
    features = [
        {"id": 1, "dependencies": []},
        {"id": 2, "dependencies": []},
        {"id": 3, "dependencies": []},
    ]

    graph = DependencyGraph(features)
    levels = graph.compute_levels()

    assert len(levels) == 1
    assert set(levels[0]) == {1, 2, 3}


@pytest.mark.unit
@pytest.mark.phase3
def test_dependency_graph_linear_chain():
    """Test linear dependency chain produces sequential levels."""
    features = [
        {"id": 1, "dependencies": []},
        {"id": 2, "dependencies": [1]},
        {"id": 3, "dependencies": [2]},
        {"id": 4, "dependencies": [3]},
    ]

    graph = DependencyGraph(features)
    levels = graph.compute_levels()

    assert len(levels) == 4
    assert levels[0] == [1]
    assert levels[1] == [2]
    assert levels[2] == [3]
    assert levels[3] == [4]


@pytest.mark.unit
@pytest.mark.phase3
def test_dependency_graph_parallel_branches():
    """Test parallel branches are grouped correctly."""
    features = [
        {"id": 1, "dependencies": []},
        {"id": 2, "dependencies": []},
        {"id": 3, "dependencies": [1]},
        {"id": 4, "dependencies": [2]},
        {"id": 5, "dependencies": [3, 4]},
    ]

    graph = DependencyGraph(features)
    levels = graph.compute_levels()

    assert len(levels) == 3
    assert set(levels[0]) == {1, 2}  # No dependencies
    assert set(levels[1]) == {3, 4}  # Depend on level 0
    assert levels[2] == [5]          # Depends on level 1


@pytest.mark.unit
@pytest.mark.phase3
def test_dependency_graph_circular_dependency():
    """Test that circular dependencies are detected."""
    features = [
        {"id": 1, "dependencies": [2]},
        {"id": 2, "dependencies": [1]},
    ]

    graph = DependencyGraph(features)

    with pytest.raises(ValueError, match="Circular dependency"):
        graph.compute_levels()


@pytest.mark.unit
@pytest.mark.phase3
def test_dependency_graph_invalid_dependency():
    """Test that invalid dependency IDs are detected."""
    features = [
        {"id": 1, "dependencies": [999]},  # 999 doesn't exist
    ]

    graph = DependencyGraph(features)

    with pytest.raises(ValueError, match="non-existent feature"):
        graph.validate_dependencies()


@pytest.mark.unit
@pytest.mark.phase3
def test_dependency_graph_stats():
    """Test statistics calculation."""
    features = [
        {"id": 1, "dependencies": []},
        {"id": 2, "dependencies": []},
        {"id": 3, "dependencies": [1, 2]},
    ]

    graph = DependencyGraph(features)
    stats = graph.get_level_stats()

    assert stats['total_levels'] == 2
    assert stats['total_features'] == 3
    assert stats['max_parallelism'] == 2
    assert stats['avg_parallelism'] == 1.5


@pytest.mark.unit
@pytest.mark.phase3
def test_dependency_graph_complex_case():
    """Test complex dependency graph (realistic scenario)."""
    # Realistic agent build scenario
    features = [
        # Scaffolding (level 0)
        {"id": 1, "category": "1_scaffolding", "dependencies": []},
        {"id": 2, "category": "1_scaffolding", "dependencies": []},

        # Base implementation (level 1)
        {"id": 3, "category": "2_base", "dependencies": [1, 2]},
        {"id": 4, "category": "2_base", "dependencies": [3]},

        # Tools (level 2-3)
        {"id": 5, "category": "3_tools", "dependencies": [4]},
        {"id": 6, "category": "3_tools", "dependencies": [5]},

        # Testing (can start early, level 1)
        {"id": 7, "category": "4_testing", "dependencies": [1, 2]},
        {"id": 8, "category": "4_testing", "dependencies": [3, 7]},
    ]

    graph = DependencyGraph(features)
    levels = graph.compute_levels()
    stats = graph.get_level_stats()

    # Verify correct grouping
    assert len(levels) >= 4
    assert set(levels[0]) == {1, 2}  # Scaffolding
    assert {3, 7} == set(levels[1])  # Base + test file can start together
    assert stats['total_features'] == 8


# ============================================================================
# RateLimitHandler Tests
# ============================================================================

@pytest.mark.unit
@pytest.mark.phase3
def test_rate_limit_handler_exponential_backoff():
    """Test exponential backoff calculation."""
    handler = RateLimitHandler(initial_delay=1.0, max_delay=60.0)

    # Check exponential growth
    delay_1 = handler.get_delay(0)  # Attempt 1
    delay_2 = handler.get_delay(1)  # Attempt 2
    delay_3 = handler.get_delay(2)  # Attempt 3

    # Should roughly double each time (with jitter)
    assert 1.0 <= delay_1 <= 2.0
    assert 2.0 <= delay_2 <= 4.0
    assert 4.0 <= delay_3 <= 8.0


@pytest.mark.unit
@pytest.mark.phase3
def test_rate_limit_handler_max_delay():
    """Test that delay is capped at max_delay."""
    handler = RateLimitHandler(initial_delay=1.0, max_delay=60.0)

    # Large attempt number should be capped
    delay = handler.get_delay(20)

    assert delay <= 61.0  # Max delay + jitter (max 1.0)


@pytest.mark.unit
@pytest.mark.phase3
def test_rate_limit_handler_should_retry():
    """Test retry decision logic."""
    handler = RateLimitHandler(max_retries=5)

    assert handler.should_retry(0) == True
    assert handler.should_retry(4) == True
    assert handler.should_retry(5) == False
    assert handler.should_retry(10) == False


@pytest.mark.unit
@pytest.mark.phase3
def test_rate_limit_handler_tracking():
    """Test rate limit tracking."""
    handler = RateLimitHandler()

    # Simulate some rate limits
    handler.rate_limit_count = 5
    handler.consecutive_rate_limits = 3

    assert handler.should_reduce_workers(threshold=3) == True
    assert handler.should_reduce_workers(threshold=5) == False

    # Reset consecutive count
    handler.reset_consecutive_count()
    assert handler.consecutive_rate_limits == 0


@pytest.mark.unit
@pytest.mark.phase3
def test_rate_limit_handler_recommendation():
    """Test worker reduction recommendation."""
    handler = RateLimitHandler()

    # No rate limits - no recommendation
    recommendation = handler.get_recommendation(current_workers=6)
    assert recommendation is None

    # Many consecutive rate limits - should recommend reduction
    handler.consecutive_rate_limits = 4
    recommendation = handler.get_recommendation(current_workers=6)
    assert recommendation == 3  # Should halve workers

    # Already at 1 worker - don't go below 1
    recommendation = handler.get_recommendation(current_workers=1)
    assert recommendation == 1


@pytest.mark.unit
@pytest.mark.phase3
def test_rate_limit_handler_stats():
    """Test statistics generation."""
    handler = RateLimitHandler()

    handler.rate_limit_count = 10
    handler.consecutive_rate_limits = 2

    stats = handler.get_stats()

    assert stats['total_rate_limits'] == 10
    assert stats['consecutive_rate_limits'] == 2
    assert 'should_reduce_workers' in stats
    assert 'last_rate_limit' in stats


# ============================================================================
# Integration Tests (Lighter)
# ============================================================================

@pytest.mark.integration
@pytest.mark.phase3
def test_dependency_graph_visualization():
    """Test that visualization generates without errors."""
    features = [
        {"id": 1, "description": "Feature 1", "dependencies": []},
        {"id": 2, "description": "Feature 2", "dependencies": [1]},
    ]

    graph = DependencyGraph(features)
    viz = graph.visualize_levels()

    assert "Level 0" in viz
    assert "Level 1" in viz
    assert "Feature 1" in viz
    assert "Feature 2" in viz


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v", "--tb=short"])
