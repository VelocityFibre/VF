#!/usr/bin/env python3
"""
Get statistics about the agent workforce.
"""

import json
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

def get_workforce_stats():
    """Get statistics about the agent workforce."""
    registry = load_registry()
    agents = registry.get("agents", [])
    categories = registry.get("agent_categories", {})

    stats = {
        "total_agents": len(agents),
        "active_agents": len([a for a in agents if a.get("status") == "active"]),
        "inactive_agents": len([a for a in agents if a.get("status") != "active"]),
        "categories": {},
        "agent_types": {},
        "models_used": {},
        "average_cost": None,
        "agents_by_status": {
            "active": [],
            "inactive": []
        }
    }

    # Count by category
    for cat, agent_ids in categories.items():
        stats["categories"][cat] = len(agent_ids)

    # Analyze agents
    total_cost = 0
    cost_count = 0

    for agent in agents:
        # By type
        agent_type = agent.get("type", "unknown")
        stats["agent_types"][agent_type] = stats["agent_types"].get(agent_type, 0) + 1

        # By model
        model = agent.get("model", "unknown")
        stats["models_used"][model] = stats["models_used"].get(model, 0) + 1

        # By status
        if agent.get("status") == "active":
            stats["agents_by_status"]["active"].append({
                "id": agent["id"],
                "name": agent["name"]
            })
        else:
            stats["agents_by_status"]["inactive"].append({
                "id": agent["id"],
                "name": agent["name"]
            })

        # Calculate average cost
        cost = agent.get("cost_per_query", "")
        if cost and cost.startswith("$"):
            try:
                cost_value = float(cost.replace("$", ""))
                total_cost += cost_value
                cost_count += 1
            except:
                pass

    if cost_count > 0:
        stats["average_cost"] = f"${total_cost / cost_count:.3f}"

    # Add summary
    stats["summary"] = {
        "operational_status": "fully operational" if stats["inactive_agents"] == 0 else "partially operational",
        "coverage": {
            "infrastructure": "vps-monitor" in [a["id"] for a in agents],
            "database": any(a["id"] in ["neon-database", "convex-database"] for a in agents),
            "business_data": any(a["id"] in ["contractor-agent", "project-agent"] for a in agents)
        }
    }

    return stats

def main():
    result = get_workforce_stats()
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    main()