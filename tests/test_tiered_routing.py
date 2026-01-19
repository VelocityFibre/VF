#!/usr/bin/env python3
"""
Test Suite for Phase 2: Tiered Model Routing

Tests the complete tiered routing system including:
- Model classification accuracy
- Orchestrator integration
- Sandbox manager integration
- Cost calculations
- Edge cases

Run with: ./venv/bin/pytest tests/test_tiered_routing.py -v
"""

import pytest
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from orchestrator.model_router import ModelRouter, ModelTierEnum


class TestModelRouterClassification:
    """Test model classification logic."""

    def setup_method(self):
        """Initialize router for each test."""
        self.router = ModelRouter()

    def test_haiku_simple_operations(self):
        """Test that simple operations route to Haiku."""
        haiku_tasks = [
            "Check VPS health status",
            "List all database records",
            "Read configuration file",
            "Show git status",
            "Count total users in database",
            "Display current metrics"
        ]

        for task in haiku_tasks:
            tier = self.router.classify_request(task)
            assert tier == ModelTierEnum.HAIKU, f"Task '{task}' should route to Haiku"

    def test_sonnet_complex_operations(self):
        """Test that complex operations route to Sonnet."""
        sonnet_tasks = [
            "Generate test suite for authentication module",
            "Analyze code performance bottlenecks",
            "Implement new API endpoint",
            "Debug failing integration test",
            "Refactor database connection pool"
        ]

        for task in sonnet_tasks:
            tier = self.router.classify_request(task)
            assert tier == ModelTierEnum.SONNET, f"Task '{task}' should route to Sonnet"

    def test_opus_critical_operations(self):
        """Test that critical operations route to Opus."""
        opus_tasks = [
            "Deploy to production environment",
            "Critical production outage - system down",
            "Architect entire system infrastructure",
            "Release to production servers"
        ]

        for task in opus_tasks:
            tier = self.router.classify_request(task)
            assert tier == ModelTierEnum.OPUS, f"Task '{task}' should route to Opus"

    def test_explicit_tier_override(self):
        """Test that explicit tier overrides classification."""
        task = "Simple status check"

        # Normal classification (should be Haiku)
        normal_tier = self.router.classify_request(task)
        assert normal_tier == ModelTierEnum.HAIKU

        # Override to Opus
        override_tier = self.router.classify_request(task, explicit_tier="opus")
        assert override_tier == ModelTierEnum.OPUS

    def test_agent_specific_rules(self):
        """Test agent-specific classification rules."""
        # VPS monitor should use Haiku
        tier = self.router.classify_request(
            "Monitor CPU usage",
            agent="vps-monitor"
        )
        assert tier == ModelTierEnum.HAIKU

        # VLM evaluator should use Sonnet
        tier = self.router.classify_request(
            "Evaluate image quality",
            agent="vlm-evaluator"
        )
        assert tier == ModelTierEnum.SONNET

    def test_distribution_target(self):
        """Test that classification achieves target distribution."""
        # Realistic task distribution
        tasks = [
            # 14 Haiku tasks (70%)
            ("Check status", None),
            ("List files", None),
            ("Read logs", None),
            ("Show metrics", None),
            ("Count records", None),
            ("Fetch data", None),
            ("Display info", None),
            ("View config", None),
            ("Get status", None),
            ("Check health", None),
            ("List users", None),
            ("Show schema", None),
            ("Find record", None),
            ("Validate input", None),

            # 5 Sonnet tasks (25%)
            ("Generate tests", None),
            ("Analyze performance", None),
            ("Implement feature", None),
            ("Debug issue", None),
            ("Refactor code", None),

            # 1 Opus task (5%)
            ("Deploy to production", None),
        ]

        tier_counts = {"haiku": 0, "sonnet": 0, "opus": 0}

        for task, agent in tasks:
            tier = self.router.classify_request(task, agent)
            tier_counts[tier.value] += 1

        # Check distribution (allow ±5% tolerance)
        total = len(tasks)
        haiku_pct = (tier_counts["haiku"] / total) * 100
        sonnet_pct = (tier_counts["sonnet"] / total) * 100
        opus_pct = (tier_counts["opus"] / total) * 100

        assert 65 <= haiku_pct <= 75, f"Haiku: {haiku_pct}% (target: 70%)"
        assert 20 <= sonnet_pct <= 30, f"Sonnet: {sonnet_pct}% (target: 25%)"
        assert 0 <= opus_pct <= 10, f"Opus: {opus_pct}% (target: 5%)"


class TestCostCalculations:
    """Test cost tracking and calculations."""

    def setup_method(self):
        """Initialize router for each test."""
        self.router = ModelRouter()

    def test_cost_per_query(self):
        """Test cost retrieval for each tier."""
        assert self.router.get_cost_per_query(ModelTierEnum.HAIKU) == 0.001
        assert self.router.get_cost_per_query(ModelTierEnum.SONNET) == 0.020
        assert self.router.get_cost_per_query(ModelTierEnum.OPUS) == 0.120

    def test_routing_stats_tracking(self):
        """Test that routing decisions are tracked."""
        # Execute some classifications
        self.router.classify_request("Check status")
        self.router.classify_request("Generate code")
        self.router.classify_request("Deploy production")

        stats = self.router.get_routing_stats()

        assert stats["total_requests"] == 3
        assert "by_tier" in stats
        assert "tier_percentages" in stats
        assert "total_cost" in stats
        assert "average_cost" in stats

    def test_cost_savings_calculation(self):
        """Test cost savings estimation."""
        # Simulate 70/25/5 distribution with 20 requests
        tasks = (
            ["Check status"] * 14 +  # 14 Haiku
            ["Generate code"] * 5 +   # 5 Sonnet
            ["Deploy production"] * 1  # 1 Opus
        )

        for task in tasks:
            self.router.classify_request(task)

        savings = self.router.estimate_cost_savings(ModelTierEnum.SONNET)

        # All-Sonnet baseline: 20 * $0.020 = $0.40
        assert savings["baseline_cost"] == 0.40

        # Actual cost: (14 * $0.001) + (5 * $0.020) + (1 * $0.120)
        #            = $0.014 + $0.100 + $0.120 = $0.234
        expected_actual = (14 * 0.001) + (5 * 0.020) + (1 * 0.120)
        assert abs(savings["actual_cost"] - expected_actual) < 0.001

        # Savings should be positive
        assert savings["savings"] > 0
        assert savings["savings_percentage"] > 0


class TestOrchestratorIntegration:
    """Test orchestrator integration with model router."""

    def setup_method(self):
        """Initialize orchestrator for each test."""
        from orchestrator.orchestrator import AgentOrchestrator
        self.orchestrator = AgentOrchestrator()

    def test_routing_includes_model_info(self):
        """Test that route_task includes model information."""
        result = self.orchestrator.route_task("Check VPS CPU usage")

        assert "model" in result
        assert "tier" in result["model"]
        assert "model_id" in result["model"]
        assert "cost_per_query" in result["model"]

    def test_explicit_tier_propagation(self):
        """Test that explicit tier is passed to router."""
        result = self.orchestrator.route_task(
            "Simple task",
            explicit_tier="opus"
        )

        assert result["model"]["tier"] == "opus"

    def test_routing_stats_available(self):
        """Test that routing stats are accessible."""
        # Execute some routings
        self.orchestrator.route_task("Check status")
        self.orchestrator.route_task("Generate code")

        stats = self.orchestrator.get_routing_stats()
        assert "total_requests" in stats


class TestEdgeCases:
    """Test edge cases and error handling."""

    def setup_method(self):
        """Initialize router for each test."""
        self.router = ModelRouter()

    def test_empty_task(self):
        """Test classification with empty task."""
        tier = self.router.classify_request("")
        # Should default to Sonnet
        assert tier == ModelTierEnum.SONNET

    def test_very_long_task(self):
        """Test classification with very long task description."""
        long_task = "Check status " * 1000  # 13,000 characters
        tier = self.router.classify_request(long_task)
        # Should still classify correctly
        assert tier == ModelTierEnum.HAIKU

    def test_ambiguous_task(self):
        """Test task with mixed signals."""
        # Short task with both simple and complex keywords
        # Short tasks (<50 chars) prioritize Haiku if they match
        task = "Check status and deploy to production"
        tier = self.router.classify_request(task)
        # This matches Haiku "check status" pattern (short task optimization)
        assert tier == ModelTierEnum.HAIKU

        # Longer task with deployment keyword should route to Opus
        long_task = "I need you to check the current system status and then deploy the changes to the production environment with full monitoring"
        tier_long = self.router.classify_request(long_task)
        # Opus patterns checked first for longer tasks
        assert tier_long == ModelTierEnum.OPUS

    def test_unknown_agent(self):
        """Test classification with unknown agent."""
        tier = self.router.classify_request(
            "Some task",
            agent="unknown-agent-xyz"
        )
        # Should still work, use default rules
        assert tier in [ModelTierEnum.HAIKU, ModelTierEnum.SONNET, ModelTierEnum.OPUS]

    def test_invalid_explicit_tier(self):
        """Test handling of invalid explicit tier."""
        with pytest.raises(ValueError):
            self.router.classify_request(
                "Some task",
                explicit_tier="invalid-tier"
            )


class TestEndToEnd:
    """End-to-end integration tests."""

    def test_full_workflow(self):
        """Test complete workflow from task to cost tracking."""
        from orchestrator.orchestrator import AgentOrchestrator

        orchestrator = AgentOrchestrator()

        # Execute various tasks
        tasks = [
            "Check VPS health",
            "Query database for contractors",
            "Generate test suite",
            "Deploy to production"
        ]

        results = []
        for task in tasks:
            result = orchestrator.route_task(task)
            results.append(result)

        # Verify all have model info
        for result in results:
            assert "model" in result
            assert result["model"]["tier"] in ["haiku", "sonnet", "opus"]

        # Check routing stats
        stats = orchestrator.get_routing_stats()
        assert stats["total_requests"] == len(tasks)

        # Check cost savings
        savings = orchestrator.estimate_cost_savings()
        assert savings["baseline_cost"] > 0
        assert savings["actual_cost"] > 0


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v", "--tb=short"])
