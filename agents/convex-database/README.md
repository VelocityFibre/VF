# Convex Database Agent

**Natural Language Interface to Convex Backend with Claude**

---

## What This Does

The Convex Database Agent provides a **conversational interface** to your Convex backend. Manage tasks, check sync status, and analyze data using natural language.

**Example:**
```
You: "How many tasks do we have?"
Agent: "You currently have 0 tasks in the system."
```

---

## Quick Start

```bash
# Set environment variables
export ANTHROPIC_API_KEY="your_api_key"
export CONVEX_URL="https://quixotic-crow-802.convex.cloud"

# Run the agent
cd /home/louisdup/Agents/claude/
./venv/bin/python3 -c "
from agents.convex_database.agent import ConvexDatabaseAgent
import os

agent = ConvexDatabaseAgent(
    convex_url=os.getenv('CONVEX_URL'),
    anthropic_api_key=os.getenv('ANTHROPIC_API_KEY')
)

print(agent.chat('What tasks do we have?'))
"
```

---

## Key Features

### 1. Task Management
- List all tasks
- Add new tasks
- Update task status
- Delete tasks

### 2. Search & Filter
- Search tasks by title
- Filter by priority
- Filter by status

### 3. Analytics
- Task statistics
- Status distribution
- Priority breakdown

---

## Available Tools

```python
1. list_tasks()                      # Get all tasks
2. add_task(title, description, ...)   # Create new task
3. update_task(id, updates)          # Modify existing task
4. delete_task(id)                   # Remove task
5. search_tasks(query)               # Search by title
6. get_task_stats()                  # Get statistics
```

---

## Common Tasks

### Task 1: List Tasks

```python
response = agent.chat("Show me all tasks")
# Returns list of all tasks with details
```

### Task 2: Add Task

```python
response = agent.chat("Create a task to update documentation")
# Creates new task with AI-inferred details
```

### Task 3: Get Statistics

```python
response = agent.chat("How many high-priority tasks do we have?")
# Analyzes and reports task distribution
```

---

## Convex Backend

**URL:** https://quixotic-crow-802.convex.cloud
**Tables:** tasks (primary)
**API:** HTTP/JSON
**Deployment:** Serverless

---

## Related Documentation

- **Orchestrator System:** `../../orchestrator/README.md`
- **Convex Agent Guide:** `../../CONVEX_AGENT_GUIDE.md`
- **Project Summary:** `../../PROJECT_SUMMARY.md`

---

**Maintained by:** Agent Development Team
**Last Updated:** 2025-11-18
**Agent Type:** Backend Interface
**Model:** Claude 3 Haiku
**Cost:** ~$0.001 per query
