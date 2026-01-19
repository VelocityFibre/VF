#!/usr/bin/env python3
"""
Agent Organigram - Visualize agent workforce structure
Shows relationships, capabilities, and routing logic
"""

import json
from pathlib import Path
from typing import Dict, List, Any


class AgentOrganigram:
    """Generates visual representation of agent workforce."""

    def __init__(self, registry_path: str = None):
        """Load agent registry."""
        if registry_path is None:
            registry_path = Path(__file__).parent / "registry.json"

        with open(registry_path, 'r') as f:
            self.registry = json.load(f)

    def generate_tree(self) -> str:
        """Generate ASCII tree view of agent hierarchy."""
        tree = """
╔══════════════════════════════════════════════════════════════════════╗
║                    AGENT WORKFORCE ORGANIGRAM                        ║
╚══════════════════════════════════════════════════════════════════════╝

                        👤 USER (You)
                              │
                              ▼
                    🧠 ORCHESTRATOR (Claude Code)
                    │
                    │  Decision Logic:
                    │  • Analyze user request
                    │  • Match keywords to agents
                    │  • Route to best specialist
                    │  • Coordinate multi-agent tasks
                    │
                    ├─────────────┬─────────────┬─────────────┐
                    │             │             │             │
                    ▼             ▼             ▼             ▼
"""

        agents_by_category = self.registry.get("agent_categories", {})

        for category, agent_ids in agents_by_category.items():
            tree += f"\n            📦 {category.upper()} AGENTS\n"
            tree += "            " + "─" * 30 + "\n"

            for agent_id in agent_ids:
                agent_info = self._get_agent(agent_id)
                if agent_info:
                    tree += f"            │\n"
                    tree += f"            ├─ 🤖 {agent_info['name']}\n"
                    tree += f"            │   ID: {agent_id}\n"
                    tree += f"            │   Model: {agent_info.get('model', 'N/A')}\n"
                    tree += f"            │   Tools: {len(agent_info.get('capabilities', {}))}\n"

            tree += "\n"

        tree += """
                    ROUTING FLOW:
                    ═══════════════════════════════════════════════

                    User Query → Orchestrator Analysis
                         │
                         ├─ Match keywords
                         ├─ Check capabilities
                         ├─ Calculate confidence
                         │
                         ▼
                    Select Best Agent(s)
                         │
                         ├─ Single match → Direct routing
                         ├─ Multiple matches → Present options
                         └─ No match → Escalate to general AI
                         │
                         ▼
                    Execute Agent Task
                         │
                         ├─ Agent uses specialized tools
                         ├─ Gathers data (DB/SSH/API)
                         ├─ AI analyzes results
                         │
                         ▼
                    Return to Orchestrator
                         │
                         ├─ Format response
                         ├─ Add context
                         └─ Present to user
"""

        return tree

    def generate_capability_matrix(self) -> str:
        """Generate capability matrix showing what each agent can do."""
        matrix = """
╔══════════════════════════════════════════════════════════════════════╗
║                     AGENT CAPABILITY MATRIX                          ║
╚══════════════════════════════════════════════════════════════════════╝

"""

        agents = self.registry.get("agents", [])

        # Header
        matrix += f"{'Agent':<25} {'Type':<15} {'Key Capabilities'}\n"
        matrix += "─" * 80 + "\n"

        for agent in agents:
            name = agent['name'][:24]
            agent_type = agent['type'][:14]
            capabilities = agent.get('capabilities', {})

            # Get first 3 capability categories
            caps_list = list(capabilities.keys())[:3]
            caps_str = ", ".join([c.replace('_', ' ') for c in caps_list])

            matrix += f"{name:<25} {agent_type:<15} {caps_str}\n"

            # Show tools count
            tools_count = sum(len(v) if isinstance(v, list) else 1 for v in capabilities.values())
            matrix += f"{'':25} {'':15} → {tools_count} tools available\n"
            matrix += "\n"

        return matrix

    def generate_keyword_map(self) -> str:
        """Generate keyword → agent routing map."""
        keyword_map = """
╔══════════════════════════════════════════════════════════════════════╗
║                    KEYWORD ROUTING REFERENCE                         ║
╚══════════════════════════════════════════════════════════════════════╝

When you say...              Orchestrator routes to:
───────────────────────────────────────────────────────────────────────

"""

        # Collect all keywords
        keyword_to_agents = {}

        for agent in self.registry.get("agents", []):
            for trigger in agent.get("triggers", []):
                if trigger not in keyword_to_agents:
                    keyword_to_agents[trigger] = []
                keyword_to_agents[trigger].append(agent['name'])

        # Show top keywords
        for keyword in sorted(list(keyword_to_agents.keys()))[:20]:
            agents = keyword_to_agents[keyword]
            keyword_map += f"  '{keyword}'".ljust(30) + f" → {', '.join(agents)}\n"

        keyword_map += "\n  ... and " + str(len(keyword_to_agents) - 20) + " more keywords\n"

        return keyword_map

    def generate_full_organigram(self) -> str:
        """Generate complete organigram with all visualizations."""
        full = self.generate_tree()
        full += "\n\n" + self.generate_capability_matrix()
        full += "\n\n" + self.generate_keyword_map()

        return full

    def _get_agent(self, agent_id: str) -> Dict[str, Any]:
        """Helper to get agent by ID."""
        for agent in self.registry.get("agents", []):
            if agent["id"] == agent_id:
                return agent
        return None


def main():
    """Display the organigram."""
    organigram = AgentOrganigram()

    print(organigram.generate_full_organigram())

    # Save to file
    output_path = Path(__file__).parent.parent / "AGENT_ORGANIGRAM.txt"
    with open(output_path, 'w') as f:
        f.write(organigram.generate_full_organigram())

    print(f"\n\n✅ Organigram saved to: {output_path}")


if __name__ == "__main__":
    main()
