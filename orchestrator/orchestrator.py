#!/usr/bin/env python3
"""
Agent Orchestrator - Routes tasks to specialized agents
Acts as the central coordinator for the agent workforce

Phase 2 Enhancement: Integrated with ModelRouter for tiered Claude model selection
Phase 2.5 Enhancement: Integrated with SLAMonitor for data freshness guarantees
"""

import json
import os
import sys
import logging
from typing import Dict, List, Any, Optional
from pathlib import Path
from dataclasses import asdict

# Import model_router from same directory
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

from model_router import ModelRouter, ModelTierEnum

# Phase 2.5: Import SLA monitor
try:
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from harness.sla_monitor import SLAMonitor, SLAViolationError
except ImportError:
    logging.warning("SLAMonitor not available - SLA checks disabled")
    SLAMonitor = None
    SLAViolationError = None


class AgentOrchestrator:
    """
    Coordinates multiple specialized agents.
    Routes user requests to the appropriate agent based on context.
    """

    def __init__(self, registry_path: str = None):
        """
        Initialize orchestrator with agent registry and model router.

        Args:
            registry_path: Path to registry.json file
        """
        if registry_path is None:
            registry_path = Path(__file__).parent / "registry.json"

        self.registry_path = Path(registry_path)
        self.registry = self._load_registry()
        self.agents = {}  # Cached agent instances

        # Phase 2: Tiered model routing
        self.model_router = ModelRouter()

        # Phase 2.5: Data layer SLA monitoring
        self.sla_monitor = None
        if SLAMonitor:
            try:
                self.sla_monitor = SLAMonitor()
                logging.info("SLA monitoring enabled - data freshness guaranteed")
            except Exception as e:
                logging.warning(f"Failed to initialize SLA monitor: {e}")

    def _load_registry(self) -> Dict[str, Any]:
        """Load agent registry from JSON file."""
        try:
            with open(self.registry_path, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            raise FileNotFoundError(f"Agent registry not found at {self.registry_path}")
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid registry JSON: {e}")

    def list_agents(self) -> List[Dict[str, Any]]:
        """
        Get list of all registered agents.

        Returns:
            List of agent information dictionaries
        """
        return self.registry.get("agents", [])

    def get_agent_by_id(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """
        Get agent information by ID.

        Args:
            agent_id: Agent identifier (e.g., 'vps-monitor')

        Returns:
            Agent info dict or None if not found
        """
        for agent in self.registry.get("agents", []):
            if agent["id"] == agent_id:
                return agent
        return None

    def find_agent_for_task(self, task_description: str) -> List[Dict[str, str]]:
        """
        Find best agent(s) for a given task based on keywords.

        Args:
            task_description: User's task/question description

        Returns:
            List of matching agents with confidence scores
        """
        task_lower = task_description.lower()
        matches = []

        for agent in self.registry.get("agents", []):
            score = 0
            matched_triggers = []

            # Check trigger keywords
            for trigger in agent.get("triggers", []):
                if trigger.lower() in task_lower:
                    score += 1
                    matched_triggers.append(trigger)

            if score > 0:
                matches.append({
                    "agent_id": agent["id"],
                    "agent_name": agent["name"],
                    "confidence": score,
                    "matched_keywords": matched_triggers,
                    "description": agent["description"],
                    "path": agent["path"]
                })

        # Sort by confidence (highest first)
        matches.sort(key=lambda x: x["confidence"], reverse=True)

        return matches

    def route_task(self, task_description: str, auto_select: bool = False,
                   explicit_tier: Optional[str] = None, check_slas: bool = False) -> Dict[str, Any]:
        """
        Route a task to the appropriate agent with model tier selection and optional SLA checks.

        Args:
            task_description: User's task description
            auto_select: If True, automatically select best agent. If False, return options.
            explicit_tier: Optional model tier override ('haiku', 'sonnet', 'opus')
            check_slas: If True, verify data freshness before routing (Phase 2.5)

        Returns:
            Routing decision with agent info, confidence, model tier, and SLA status
        """
        matches = self.find_agent_for_task(task_description)

        # Phase 2: Classify task for model tier selection
        agent_name = matches[0]["agent_id"] if matches else None
        model_tier = self.model_router.classify_request(
            task=task_description,
            agent=agent_name,
            explicit_tier=explicit_tier
        )
        model_id = self.model_router.get_model_id(model_tier)
        cost_per_query = self.model_router.get_cost_per_query(model_tier)

        # Add model info to result
        model_info = {
            "tier": model_tier.value,
            "model_id": model_id,
            "cost_per_query": cost_per_query
        }

        # Phase 2.5: Check SLAs if requested
        sla_status = None
        if check_slas and self.sla_monitor:
            try:
                sla_results = self.sla_monitor.check_all_slas()
                violations = [c for c in sla_results["checks"] if c.status == "VIOLATION"]

                sla_status = {
                    "checked": True,
                    "all_ok": len(violations) == 0,
                    "violations": len(violations),
                    "details": [asdict(v) for v in violations] if violations else None
                }

                if violations:
                    logging.warning(f"⚠️  {len(violations)} SLA violation(s) detected")

            except Exception as e:
                logging.error(f"SLA check failed: {e}")
                sla_status = {
                    "checked": False,
                    "error": str(e)
                }

        # Build result with SLA status
        if not matches:
            result = {
                "status": "no_match",
                "message": "No specialized agent found for this task",
                "suggestion": "Consider handling with general capabilities or creating new agent",
                "model": model_info  # Still provide model recommendation
            }
        elif auto_select or len(matches) == 1:
            result = {
                "status": "routed",
                "agent": matches[0],
                "alternatives": matches[1:] if len(matches) > 1 else [],
                "model": model_info
            }
        else:
            result = {
                "status": "multiple_matches",
                "message": "Multiple agents can handle this task",
                "options": matches,
                "model": model_info
            }

        # Add SLA status if checked (Phase 2.5)
        if sla_status:
            result["sla_status"] = sla_status

        return result

    def get_agent_stats(self) -> Dict[str, Any]:
        """Get statistics about the agent workforce."""
        total = self.registry.get("total_agents", 0)
        categories = self.registry.get("agent_categories", {})

        stats = {
            "total_agents": total,
            "active_agents": len([a for a in self.list_agents() if a.get("status") == "active"]),
            "categories": {cat: len(agents) for cat, agents in categories.items()},
            "agent_types": {}
        }

        # Count by type
        for agent in self.list_agents():
            agent_type = agent.get("type", "unknown")
            stats["agent_types"][agent_type] = stats["agent_types"].get(agent_type, 0) + 1

        return stats

    def get_routing_stats(self) -> Dict[str, Any]:
        """
        Get model routing statistics from the integrated router.

        Returns:
            Dictionary with routing stats including:
            - Distribution by tier (haiku/sonnet/opus)
            - Cost savings vs baseline
            - Average cost per query
        """
        return self.model_router.get_routing_stats()

    def estimate_cost_savings(self, baseline_tier: str = "sonnet") -> Dict[str, float]:
        """
        Estimate cost savings from tiered routing.

        Args:
            baseline_tier: Baseline model to compare against ('haiku', 'sonnet', 'opus')

        Returns:
            Cost savings breakdown
        """
        baseline_enum = ModelTierEnum(baseline_tier)
        return self.model_router.estimate_cost_savings(baseline_enum)

    def explain_capabilities(self, agent_id: str) -> str:
        """
        Generate human-readable explanation of agent capabilities.

        Args:
            agent_id: Agent identifier

        Returns:
            Formatted explanation string
        """
        agent = self.get_agent_by_id(agent_id)
        if not agent:
            return f"Agent '{agent_id}' not found"

        explanation = f"""
╔══════════════════════════════════════════════════════════════════╗
║  {agent['name'].center(64)}  ║
╚══════════════════════════════════════════════════════════════════╝

📋 Description:
   {agent['description']}

🎯 What it can do:
"""

        capabilities = agent.get("capabilities", {})
        for category, items in capabilities.items():
            explanation += f"\n   {category.replace('_', ' ').title()}:\n"
            for item in items:
                explanation += f"   • {item}\n"

        explanation += f"""
🔑 Key triggers:
   {', '.join(agent.get('triggers', [])[:10])}

⚡ Performance:
   Model: {agent.get('model', 'N/A')}
   Avg Response: {agent.get('avg_response_time', 'N/A')}
   Cost per query: {agent.get('cost_per_query', 'N/A')}

📁 Location: {agent.get('path', 'N/A')}
"""

        return explanation


def main():
    """Demo the orchestrator."""
    print("🤖 Agent Orchestrator - Demo\n")

    orchestrator = AgentOrchestrator()

    # Show stats
    print("=" * 80)
    print("AGENT WORKFORCE STATISTICS")
    print("=" * 80)
    stats = orchestrator.get_agent_stats()
    print(json.dumps(stats, indent=2))

    # List all agents
    print("\n" + "=" * 80)
    print("REGISTERED AGENTS")
    print("=" * 80)
    for agent in orchestrator.list_agents():
        print(f"\n✓ {agent['name']} ({agent['id']})")
        print(f"  Type: {agent['type']}")
        print(f"  Status: {agent['status']}")
        print(f"  {agent['description'][:80]}...")

    # Test routing
    print("\n" + "=" * 80)
    print("TASK ROUTING EXAMPLES")
    print("=" * 80)

    test_tasks = [
        "What's the CPU usage on the VPS?",
        "Query the Neon database for active contractors",
        "Show me task statistics in Convex",
        "Check if nginx is running",
        "This doesn't match any agent"
    ]

    for task in test_tasks:
        print(f"\n📝 Task: \"{task}\"")
        result = orchestrator.route_task(task)
        print(f"   Status: {result['status']}")

        # Phase 2: Show model tier selection
        if 'model' in result:
            model_info = result['model']
            print(f"   🤖 Model: {model_info['tier'].upper()} ({model_info['model_id']})")
            print(f"   💰 Cost: ${model_info['cost_per_query']:.3f}/query")

        if result['status'] == 'routed':
            print(f"   → Routed to: {result['agent']['agent_name']}")
            print(f"   → Confidence: {result['agent']['confidence']} keyword matches")
            print(f"   → Matched: {', '.join(result['agent']['matched_keywords'])}")
        elif result['status'] == 'multiple_matches':
            print(f"   → {len(result['options'])} agents available:")
            for opt in result['options']:
                print(f"      • {opt['agent_name']} (score: {opt['confidence']})")
        else:
            print(f"   → {result['message']}")

    # Show capabilities
    print("\n" + "=" * 80)
    print("AGENT CAPABILITIES")
    print("=" * 80)
    print(orchestrator.explain_capabilities("vps-monitor"))

    # Phase 2: Show routing statistics
    print("\n" + "=" * 80)
    print("MODEL ROUTING STATISTICS (Phase 2)")
    print("=" * 80)
    routing_stats = orchestrator.get_routing_stats()

    if routing_stats['total_requests'] > 0:
        print(f"\nTotal requests: {routing_stats['total_requests']}")
        print("\nDistribution by tier:")
        for tier, percentage in routing_stats['tier_percentages'].items():
            count = routing_stats['by_tier'][tier]
            target = routing_stats['target_distribution'][tier]
            print(f"  {tier.upper():6} {count:2} requests ({percentage:5.1f}%) [target: {target}%]")

        print(f"\nAverage cost: ${routing_stats['average_cost']:.3f}/query")

        # Show cost savings
        savings = orchestrator.estimate_cost_savings()
        if savings['savings'] > 0:
            print(f"\nCost savings vs all-Sonnet baseline:")
            print(f"  Baseline: ${savings['baseline_cost']:.2f}")
            print(f"  Actual:   ${savings['actual_cost']:.2f}")
            print(f"  Savings:  ${savings['savings']:.2f} ({savings['savings_percentage']:.1f}%)")
    else:
        print("\n(No routing data yet - run some tasks first)")


if __name__ == "__main__":
    main()
