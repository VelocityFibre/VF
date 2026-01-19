# Project Agent

**Specialized Agent for VF Fiber Optic Project Management**

---

## What This Does

The Project Agent specializes in managing VF fiber optic projects. It provides a natural language interface to project data stored in the Convex database.

**Example:**
```
You: "Show me all active projects"
Agent: "You have 2 active projects: Lawley and Mohadin."
```

---

## Quick Start

```bash
# Set environment variables
export ANTHROPIC_API_KEY="your_api_key"
export CONVEX_URL="https://quixotic-crow-802.convex.cloud"

# Run the agent
cd /home/louisdup/Agents/claude/agents/project-agent
../../venv/bin/python3 agent.py
```

---

## Key Features

### 1. Project Management
- List all projects
- Search by name or location
- Filter by status (active, planning, completed, on hold, cancelled)
- Add new projects

### 2. Status Tracking
- Monitor project lifecycle
- Track active vs. completed projects
- Identify projects on hold

### 3. Analytics & Insights
- Project statistics by status
- Location-based analysis
- Portfolio overview

---

## Available Tools

```python
1. list_projects()            # List all projects
2. search_projects(query)     # Search by name
3. get_project_stats()        # Get statistics by status
4. add_project(details)       # Add new project
```

---

## Common Tasks

### Task 1: List Projects

```python
from agents.project_agent.agent import ProjectAgent

agent = ProjectAgent()
response = agent.chat("List all projects")
print(response)
```

### Task 2: Search Projects

```python
response = agent.chat("Show me projects in Lawley")
```

### Task 3: Get Statistics

```python
response = agent.chat("How many active projects do we have?")
```

---

## Data Schema

```json
{
  "name": "string",
  "description": "string (optional)",
  "status": "active|planning|completed|on_hold|cancelled",
  "contractor_id": "ID (optional)",
  "location": "string (optional)",
  "budget": "number (optional)",
  "start_date": "number (optional)",
  "end_date": "number (optional)",
  "neon_id": "string (optional)",
  "created_at": "number",
  "updated_at": "number"
}
```

---

## Integration with Orchestrator

**Routing Keywords:**
- project, projects
- site, sites
- deployment, rollout
- installation
- fiber deployment

**Registry ID:** `project-agent`

---

## Related Documentation

- **Orchestrator System:** `../../orchestrator/README.md`
- **Agent Workforce Guide:** `../../AGENT_WORKFORCE_GUIDE.md`

---

**Maintained by:** Agent Development Team
**Last Updated:** 2025-11-18
**Agent Type:** Data Management
**Model:** Claude 3 Haiku
**Cost:** ~$0.001 per query
