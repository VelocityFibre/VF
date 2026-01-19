# Neon Database Agent

**Natural Language Interface to PostgreSQL with Claude**

---

## What This Does

The Neon Database Agent provides a **conversational interface** to your Neon PostgreSQL database. Ask questions in plain English and get intelligent responses with properly formatted data.

**Example:**
```
You: "How many active contractors do we have?"
Agent: "You have 9 active contractors out of 20 total."
```

---

## Quick Start

```bash
# Set environment variables
export ANTHROPIC_API_KEY="your_api_key"
export NEON_DATABASE_URL="postgresql://user:pass@host/db?sslmode=require"

# Run the agent
cd /home/louisdup/Agents/claude/
./venv/bin/python3 -c "
from agents.neon_database.agent import NeonDatabaseAgent
import os

agent = NeonDatabaseAgent(
    database_url=os.getenv('NEON_DATABASE_URL'),
    anthropic_api_key=os.getenv('ANTHROPIC_API_KEY')
)

print(agent.chat('What tables do we have?'))
"
```

---

## Key Features

### 1. Schema Discovery
- List all tables in database
- Describe table structure
- Get table statistics (row counts)

### 2. Data Querying
- Execute SELECT queries
- Filter, sort, and aggregate data
- Join multiple tables

### 3. Business Intelligence
- Analyze data patterns
- Generate insights
- Provide recommendations

---

## Available Tools

```python
1. list_tables()              # List all database tables
2. describe_table(name)       # Get table schema
3. get_table_stats(name)      # Count rows in table
4. execute_select(query)      # Run SELECT queries
5. count_rows(table, where)   # Count with conditions
```

---

## Common Tasks

### Task 1: Explore Database Schema

```python
response = agent.chat("What tables are available?")
# Lists all 104 tables in the database
```

### Task 2: Query Data

```python
response = agent.chat("Show me all active contractors")
# Executes SELECT query and formats results
```

### Task 3: Business Analytics

```python
response = agent.chat("Which projects are over budget?")
# Analyzes project data and provides insights
```

---

## Database Overview

**Database:** Neon PostgreSQL (Serverless)
**Tables:** 104 tables including:
- Projects, contractors, clients
- BOQs, RFQs, quotes, suppliers
- Tasks, meetings, reports
- Material tracking, equipment

**Business Domain:** Fiber optic network deployment & construction

---

## Related Documentation

- **Orchestrator System:** `../../orchestrator/README.md`
- **Neon Agent Guide:** `../../NEON_AGENT_GUIDE.md`
- **Project Summary:** `../../PROJECT_SUMMARY.md`

---

**Maintained by:** Agent Development Team
**Last Updated:** 2025-11-18
**Agent Type:** Database Interface
**Model:** Claude 3 Haiku
**Cost:** ~$0.001 per query
