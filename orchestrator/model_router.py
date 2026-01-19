#!/usr/bin/env python3
"""
Model Router - Phase 2 (Tiered Routing)

Intelligent routing of requests to appropriate Claude model based on complexity.
Routes 70% to Haiku, 25% to Sonnet, 5% to Opus for 80% cost reduction.

Cost Structure:
- Haiku:  $0.001/query - Simple operations (read, status, health checks)
- Sonnet: $0.020/query - Complex operations (generate, analyze, test)
- Opus:   $0.120/query - Critical operations (architecture, production)

City Planning Analogy: Like a city's transportation system routing vehicles
based on cargo - bicycles for documents, trucks for furniture, semis for construction.

Part of Vibe Coding Transformation - see docs/VIBE_CODING_TRANSFORMATION.md
"""

import re
from typing import Literal, Dict, Any, Optional
from enum import Enum
from dataclasses import dataclass
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Type definitions
ModelTier = Literal["haiku", "sonnet", "opus"]


class ModelTierEnum(Enum):
    """Model tier enumeration."""
    HAIKU = "haiku"
    SONNET = "sonnet"
    OPUS = "opus"


@dataclass
class ModelConfig:
    """Configuration for a model tier."""
    tier: ModelTierEnum
    model_id: str
    cost_per_query: float
    description: str
    max_context_window: int


# Model configurations
MODEL_CONFIGS = {
    ModelTierEnum.HAIKU: ModelConfig(
        tier=ModelTierEnum.HAIKU,
        model_id="claude-3-haiku-20240307",
        cost_per_query=0.001,
        description="Fast, lightweight model for simple operations",
        max_context_window=200_000
    ),
    ModelTierEnum.SONNET: ModelConfig(
        tier=ModelTierEnum.SONNET,
        model_id="claude-3-5-sonnet-20241022",
        cost_per_query=0.020,
        description="Balanced model for complex reasoning",
        max_context_window=200_000
    ),
    ModelTierEnum.OPUS: ModelConfig(
        tier=ModelTierEnum.OPUS,
        model_id="claude-3-opus-20240229",
        cost_per_query=0.120,
        description="Most capable model for critical tasks",
        max_context_window=200_000
    )
}


class ModelRouter:
    """
    Routes requests to appropriate Claude model based on complexity.

    Classification logic:
    - Haiku (70% of requests): Simple, read-only, status checks
    - Sonnet (25% of requests): Complex reasoning, code generation
    - Opus (5% of requests): Critical decisions, production deploys

    Usage:
        router = ModelRouter()

        # Classify a task
        tier = router.classify_request(
            task="Check VPS health status",
            agent="vps-monitor"
        )
        # Returns: ModelTierEnum.HAIKU

        # Get model ID for API call
        model_id = router.get_model_id(tier)
        # Returns: "claude-3-haiku-20240307"
    """

    def __init__(self):
        """Initialize router with classification rules."""
        self.configs = MODEL_CONFIGS

        # Classification patterns
        self.haiku_patterns = self._build_haiku_patterns()
        self.sonnet_patterns = self._build_sonnet_patterns()
        self.opus_patterns = self._build_opus_patterns()

        # Track routing decisions for analysis
        self.routing_history: list[Dict[str, Any]] = []

        logger.info("ModelRouter initialized for tiered routing")

    def _build_haiku_patterns(self) -> list[re.Pattern]:
        """Build regex patterns that trigger Haiku routing."""
        patterns = [
            # Read operations
            r'\b(read|view|show|display|list|get)\b',
            r'\b(check|verify|validate)\b',
            r'\b(status|health|ping|uptime)\b',

            # Simple queries
            r'\b(count|sum|total|average)\b',
            r'\b(find|search|lookup|fetch)\b',

            # File operations
            r'\b(ls|cat|head|tail|grep)\b',
            r'\b(exists|file|directory|path)\b',

            # Git operations (simple)
            r'\b(git status|git log|git diff|git branch)\b',

            # Database queries (simple)
            r'\bSELECT\b.*\bFROM\b.*\bWHERE\b',  # Simple SELECT queries
            r'\b(count|fetch|query)\b.*\brecords?\b',

            # Simple transformations
            r'\b(format|parse|extract)\b',
            r'\b(convert|transform)\b.*\b(json|csv|xml)\b',

            # Monitoring and metrics
            r'\b(monitor|metric|log|track)\b',
            r'\b(measure|report|summary)\b',
        ]

        return [re.compile(p, re.IGNORECASE) for p in patterns]

    def _build_sonnet_patterns(self) -> list[re.Pattern]:
        """Build regex patterns that explicitly trigger Sonnet routing."""
        patterns = [
            # Code generation
            r'\b(generate|create|write|implement)\b.*\b(code|function|class|test)\b',

            # Analysis (not system-wide)
            r'\b(analyze|evaluate|assess|review)\b.*\b(code|data|results)\b',

            # Complex transformations
            r'\b(refactor|optimize|improve)\b',

            # Testing
            r'\b(test|debug|troubleshoot)\b',

            # Design (not architecture)
            r'\b(design|plan)\b.*\b(feature|component|module)\b',
        ]

        return [re.compile(p, re.IGNORECASE) for p in patterns]

    def _build_opus_patterns(self) -> list[re.Pattern]:
        """Build regex patterns that trigger Opus routing."""
        patterns = [
            # Critical production operations
            r'\b(deploy|release)\b.*\b(production|prod)\b',
            r'\bproduction\b.*\b(deploy|release|push)\b',

            # System-wide architecture (not simple design)
            r'\b(architect|redesign|refactor)\b.*\b(entire|system|infrastructure)\b',

            # Critical emergencies
            r'\b(critical|urgent|emergency)\b.*\b(production|outage|down)\b',

            # Security analysis (not simple checks)
            r'\b(security audit|vulnerability assessment|penetration test)\b',

            # Explicit user flags
            r'--model\s+opus',
            r'use opus model',
            r'needs? opus',
        ]

        return [re.compile(p, re.IGNORECASE) for p in patterns]

    def classify_request(
        self,
        task: str,
        agent: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
        explicit_tier: Optional[ModelTier] = None
    ) -> ModelTierEnum:
        """
        Classify request and determine appropriate model tier.

        Args:
            task: Task description or prompt
            agent: Agent name (optional, for agent-specific rules)
            context: Additional context (optional)
            explicit_tier: User-specified tier override (optional)

        Returns:
            ModelTierEnum indicating which model to use
        """
        # Check for explicit override
        if explicit_tier:
            tier = ModelTierEnum(explicit_tier)
            logger.info(f"Using explicit tier override: {tier.value}")
            return tier

        # Check task length (very short = likely simple)
        if len(task) < 50:
            # Short tasks are likely simple queries
            for pattern in self.haiku_patterns:
                if pattern.search(task):
                    self._log_routing(task, agent, ModelTierEnum.HAIKU, "pattern_match")
                    return ModelTierEnum.HAIKU

        # Priority order: Opus > Sonnet > Haiku > Default (Sonnet)
        # This ensures critical tasks get Opus, complex tasks get Sonnet, simple gets Haiku

        # Check for Opus patterns first (critical/production)
        for pattern in self.opus_patterns:
            if pattern.search(task):
                self._log_routing(task, agent, ModelTierEnum.OPUS, "pattern_match")
                return ModelTierEnum.OPUS

        # Check for Haiku patterns (simple/read)
        for pattern in self.haiku_patterns:
            if pattern.search(task):
                self._log_routing(task, agent, ModelTierEnum.HAIKU, "pattern_match")
                return ModelTierEnum.HAIKU

        # Check for Sonnet patterns (complex but not critical)
        for pattern in self.sonnet_patterns:
            if pattern.search(task):
                self._log_routing(task, agent, ModelTierEnum.SONNET, "pattern_match")
                return ModelTierEnum.SONNET

        # Agent-specific rules
        if agent:
            tier = self._classify_by_agent(agent, task)
            if tier:
                self._log_routing(task, agent, tier, "agent_rule")
                return tier

        # Default to Sonnet for ambiguous cases
        self._log_routing(task, agent, ModelTierEnum.SONNET, "default")
        return ModelTierEnum.SONNET

    def _classify_by_agent(
        self,
        agent: str,
        task: str
    ) -> Optional[ModelTierEnum]:
        """
        Apply agent-specific classification rules.

        Args:
            agent: Agent name
            task: Task description

        Returns:
            ModelTierEnum or None if no specific rule applies
        """
        agent_lower = agent.lower()

        # Lightweight agents → Haiku
        lightweight_agents = [
            'vps-monitor',
            'health-check',
            'file-ops',
            'status-checker'
        ]

        for lightweight in lightweight_agents:
            if lightweight in agent_lower:
                return ModelTierEnum.HAIKU

        # Complex agents → Sonnet
        complex_agents = [
            'vlm-evaluator',
            'image-processor',
            'code-generator',
            'test-writer'
        ]

        for complex_agent in complex_agents:
            if complex_agent in agent_lower:
                return ModelTierEnum.SONNET

        # No specific rule
        return None

    def get_model_id(self, tier: ModelTierEnum) -> str:
        """
        Get Anthropic model ID for a tier.

        Args:
            tier: Model tier

        Returns:
            Model ID string for Anthropic API
        """
        return self.configs[tier].model_id

    def get_cost_per_query(self, tier: ModelTierEnum) -> float:
        """
        Get cost per query for a tier.

        Args:
            tier: Model tier

        Returns:
            Cost in dollars per query
        """
        return self.configs[tier].cost_per_query

    def _log_routing(
        self,
        task: str,
        agent: Optional[str],
        tier: ModelTierEnum,
        reason: str
    ) -> None:
        """Log routing decision for analysis."""
        self.routing_history.append({
            "task": task[:100],  # First 100 chars
            "agent": agent,
            "tier": tier.value,
            "reason": reason,
            "cost": self.get_cost_per_query(tier)
        })

        logger.debug(
            f"Routed to {tier.value}: {task[:50]}... "
            f"(reason: {reason}, agent: {agent})"
        )

    def get_routing_stats(self) -> Dict[str, Any]:
        """
        Get statistics about routing decisions.

        Returns:
            Dictionary with routing statistics
        """
        if not self.routing_history:
            return {
                "total_requests": 0,
                "by_tier": {},
                "total_cost": 0.0,
                "average_cost": 0.0
            }

        total = len(self.routing_history)

        # Count by tier
        by_tier = {}
        for decision in self.routing_history:
            tier = decision["tier"]
            by_tier[tier] = by_tier.get(tier, 0) + 1

        # Calculate percentages
        tier_percentages = {
            tier: (count / total) * 100
            for tier, count in by_tier.items()
        }

        # Calculate costs
        total_cost = sum(d["cost"] for d in self.routing_history)
        average_cost = total_cost / total if total > 0 else 0.0

        return {
            "total_requests": total,
            "by_tier": by_tier,
            "tier_percentages": tier_percentages,
            "total_cost": total_cost,
            "average_cost": average_cost,
            "target_distribution": {
                "haiku": 70.0,
                "sonnet": 25.0,
                "opus": 5.0
            }
        }

    def estimate_cost_savings(
        self,
        baseline_model: ModelTierEnum = ModelTierEnum.SONNET
    ) -> Dict[str, float]:
        """
        Estimate cost savings compared to baseline.

        Args:
            baseline_model: Model tier to compare against (default: Sonnet)

        Returns:
            Dictionary with cost comparison
        """
        if not self.routing_history:
            return {
                "baseline_cost": 0.0,
                "actual_cost": 0.0,
                "savings": 0.0,
                "savings_percentage": 0.0
            }

        baseline_cost_per_query = self.get_cost_per_query(baseline_model)
        total_requests = len(self.routing_history)

        baseline_cost = baseline_cost_per_query * total_requests
        actual_cost = sum(d["cost"] for d in self.routing_history)

        savings = baseline_cost - actual_cost
        savings_percentage = (savings / baseline_cost * 100) if baseline_cost > 0 else 0

        return {
            "baseline_cost": baseline_cost,
            "actual_cost": actual_cost,
            "savings": savings,
            "savings_percentage": savings_percentage
        }


if __name__ == "__main__":
    # Example usage and testing
    print("Model Router - Phase 2 Tiered Routing")
    print("=" * 70)
    print()

    router = ModelRouter()

    # Test cases (realistic distribution)
    test_cases = [
        # Haiku tasks (70% - simple operations)
        ("Check VPS health status", "vps-monitor"),
        ("List all database records", "database-ops"),
        ("Read configuration file", "file-ops"),
        ("Count total users in database", "database-ops"),
        ("Format JSON response", "api-handler"),
        ("Show git status", "git-ops"),
        ("Fetch recent logs", "monitoring"),
        ("Display current metrics", "metrics"),
        ("Get file contents", "file-ops"),
        ("Check service uptime", "health-check"),
        ("List available endpoints", "api"),
        ("Show database schema", "database-ops"),
        ("Find user by ID", "user-service"),
        ("Validate input format", "validator"),

        # Sonnet tasks (25% - complex operations)
        ("Generate test suite for authentication module", "test-generator"),
        ("Evaluate image quality using VLM", "vlm-evaluator"),
        ("Analyze code performance bottlenecks", "code-analyzer"),
        ("Implement new API endpoint", "backend-dev"),
        ("Debug failing integration test", "test-debugger"),

        # Opus tasks (5% - critical operations)
        ("Deploy to production environment", "deployment-agent"),
    ]

    print("Testing classification...")
    print()

    for task, agent in test_cases:
        tier = router.classify_request(task, agent)
        model_id = router.get_model_id(tier)
        cost = router.get_cost_per_query(tier)

        print(f"Task: {task[:50]}...")
        print(f"  Agent: {agent or 'N/A'}")
        print(f"  → Routed to: {tier.value.upper()}")
        print(f"    Model: {model_id}")
        print(f"    Cost: ${cost:.3f}/query")
        print()

    # Show statistics
    print("=" * 70)
    print("Routing Statistics:")
    print()

    stats = router.get_routing_stats()
    print(f"Total requests: {stats['total_requests']}")
    print(f"Distribution:")
    for tier, percentage in stats['tier_percentages'].items():
        count = stats['by_tier'][tier]
        target = stats['target_distribution'][tier]
        print(f"  {tier.upper():6} {count:2} requests ({percentage:5.1f}%) [target: {target}%]")

    print()
    print(f"Total cost: ${stats['total_cost']:.3f}")
    print(f"Average cost: ${stats['average_cost']:.3f}/query")

    # Show cost savings
    print()
    print("=" * 70)
    print("Cost Savings (vs baseline Sonnet):")
    print()

    savings = router.estimate_cost_savings()
    print(f"Baseline cost (all Sonnet): ${savings['baseline_cost']:.2f}")
    print(f"Actual cost (tiered):       ${savings['actual_cost']:.2f}")
    print(f"Savings:                    ${savings['savings']:.2f} ({savings['savings_percentage']:.1f}%)")
    print()

    print("=" * 70)
    print("✅ Model router ready for integration!")
