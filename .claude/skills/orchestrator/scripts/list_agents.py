#!/usr/bin/env python3
"""
List all registered agents and their status.
"""

import json
import argparse
import sys
from pathlib import Path

# Load registry
REGISTRY_PATH = Path(__file__).parent.parent.parent.parent.parent / "orchestrator" / "registry.json"

def load_registry():
    """Load agent registry from JSON file."""
    try:
        with open(REGISTRY_PATH, 'r') as f:
            return json.load(f)
    except Exception as e:
        print(json.dumps({"error": f"Failed to load registry: {str(e)}"}))
        sys.exit(1)

def list_agents(category=None):
    """List all agents, optionally filtered by category."""
    registry = load_registry()
    agents = registry.get("agents", [])

    if category:
        # Filter by category
        categories = registry.get("agent_categories", {})
        if category in categories:
            agent_ids = categories[category]
            agents = [a for a in agents if a["id"] in agent_ids]
        else:
            return {
                "error": f"Category '{category}' not found",
                "available_categories": list(categories.keys())
            }

    result = {
        "total": len(agents),
        "agents": []
    }

    for agent in agents:
        result["agents"].append({
            "id": agent["id"],
            "name": agent["name"],
            "status": agent.get("status", "unknown"),
            "type": agent.get("type", "unknown"),
            "description": agent["description"],
            "triggers": agent.get("triggers", [])[:5],  # First 5 triggers
            "model": agent.get("model", "unknown"),
            "cost_per_query": agent.get("cost_per_query", "unknown")
        })

    if category:
        result["category"] = category

    return result

def main():
    parser = argparse.ArgumentParser(description='List all registered agents')
    parser.add_argument('--category', help='Filter by category (infrastructure, database, data_management)')

    args = parser.parse_args()

    result = list_agents(args.category)
    print(json.dumps(result, indent=2))

    # Exit with error if error occurred
    if "error" in result:
        sys.exit(1)

if __name__ == "__main__":
    main()