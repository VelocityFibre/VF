# Contractor Agent

**Specialized Agent for VF Contractor & Vendor Management**

---

## What This Does

The Contractor Agent specializes in managing VF contractors and vendors. It provides a natural language interface to contractor data stored in the Convex database.

**Example:**
```
You: "How many active contractors do we have?"
Agent: "You have 9 active contractors out of 20 total in the database."
```

---

## Quick Start

```bash
# Set environment variables
export ANTHROPIC_API_KEY="your_api_key"
export CONVEX_URL="https://quixotic-crow-802.convex.cloud"

# Run the agent
cd /home/louisdup/Agents/claude/agents/contractor-agent
../../venv/bin/python3 agent.py
```

---

## Key Features

### 1. Contractor Management
- List all contractors
- Search by company name
- View active/inactive contractors
- Add new contractors

### 2. Analytics & Insights
- Contractor statistics
- Active vs. inactive ratios
- Company name analysis

### 3. Intelligent Search
- Natural language queries
- Fuzzy matching
- Contextual results

---

## Available Tools

```python
1. list_contractors()            # List all contractors
2. search_contractors(query)     # Search by company name
3. get_contractor_stats()        # Get statistics
4. add_contractor(details)       # Add new contractor
```

---

## Common Tasks

### Task 1: List Contractors

```python
from agents.contractor_agent.agent import ContractorAgent

agent = ContractorAgent()
response = agent.chat("List all active contractors")
print(response)
```

### Task 2: Search Contractors

```python
response = agent.chat("Find contractors with 'Fiber' in the name")
```

### Task 3: Get Statistics

```python
response = agent.chat("How many contractors are active?")
```

---

## Data Schema

```json
{
  "company_name": "string",
  "email": "string (optional)",
  "phone": "string (optional)",
  "contact_person": "string (optional)",
  "address": "string (optional)",
  "is_active": "boolean",
  "neon_id": "string (optional)",
  "created_at": "number",
  "updated_at": "number"
}
```

---

## Integration with Orchestrator

**Routing Keywords:**
- contractor, contractors
- vendor, vendors
- company, companies
- supplier, suppliers

**Registry ID:** `contractor-agent`

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
