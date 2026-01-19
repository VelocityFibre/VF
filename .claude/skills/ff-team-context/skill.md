---
name: ff-team-context
version: 1.0.0
description: FF App team WhatsApp context bridge for shared team memory
author: Claude
tags: [team, context, whatsapp, bridge, tasks, decisions]
requires: []
---

# FF Team Context Skill

Access shared team context from the FF App WhatsApp group, including tasks, decisions, and important discussions.

## Overview

This skill provides access to the FF App developer group context that's automatically synced from WhatsApp. Both Louis and Hein's Claude instances can access the same shared memory.

## Quick Commands

### Get Recent Context
```bash
python scripts/get_context.py
```

### Get My Tasks
```bash
python scripts/get_tasks.py louis  # or hein
```

### Force Sync
```bash
python scripts/force_sync.py
```

## Context Files

The bridge maintains these files:
- `/home/louisdup/Agents/claude/TEAM_CONTEXT.md` - Human-readable team context
- `/home/louisdup/Agents/claude/TEAM_TASKS.json` - Machine-readable task list
- `/home/louisdup/Agents/claude/TEAM_DECISIONS.json` - Team decisions

## Message Patterns

### Task Assignment
- `TASK: Fix the auth bug @louis`
- `TODO: Update docs @hein`
- `Louis will deploy to production`
- `Hein should check the tests`

### Decisions
- `DECIDED: Switch to Neon for auth`
- `DECISION: Use TypeScript for new modules`
- `We agreed to deploy on Fridays`

### Questions for Claude
- `@claude how do we optimize this query?`
- `QUESTION: Best practice for error handling?`

### Bug Reports
- `BUG: Login failing in production`
- `ISSUE: Memory leak in worker`

## Module Location

The bridge service runs at:
`/home/louisdup/Agents/claude/agents/ff-team-bridge/`

## Usage Examples

### Check Recent Discussions
```python
# Get last 24 hours of team context
context = get_team_context(hours=24)
print(f"Recent tasks: {len(context['tasks'])}")
print(f"Recent decisions: {len(context['decisions'])}")
```

### Get Your Tasks
```python
# Get tasks assigned to you
tasks = get_my_tasks("louis")
for task in tasks:
    print(f"- {task['description']} ({task['status']})")
```

### Search Decisions
```python
# Find specific decisions
decisions = search_decisions("database")
for d in decisions:
    print(f"- {d['description']} by {d['made_by']}")
```

## Related Skills

- `wa-monitor` - WhatsApp monitoring service
- `database-operations` - Database queries