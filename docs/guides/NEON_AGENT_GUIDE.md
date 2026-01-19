# Neon PostgreSQL Agent - Complete Guide

**AI-Powered Natural Language Interface for Your Neon Database**

Built with Claude Agent SDK and PostgreSQL, this agent enables intelligent conversational access to your Neon database.

---

## Table of Contents

1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Quick Start](#quick-start)
4. [Configuration](#configuration)
5. [Using the Agent](#using-the-agent)
6. [Available Tools](#available-tools)
7. [Example Queries](#example-queries)
8. [Advanced Features](#advanced-features)
9. [API Reference](#api-reference)
10. [Troubleshooting](#troubleshooting)
11. [Production Deployment](#production-deployment)

---

## Overview

### What is the Neon Agent?

The Neon Agent is an AI-powered assistant that connects Claude AI with your Neon PostgreSQL database. It allows users to:

- **Query databases using natural language** instead of SQL
- **Analyze data and generate insights** automatically
- **Explore database schemas** without documentation
- **Generate reports** on demand
- **Maintain conversational context** across multiple queries

### Key Features

✅ **Natural Language Interface** - "Show me projects over budget" instead of writing SQL
✅ **Context-Aware** - Remembers previous queries in conversation
✅ **Safe Execution** - Uses parameterized queries to prevent SQL injection
✅ **Schema Discovery** - Automatically understands your database structure
✅ **Intelligent Analysis** - Provides insights, not just raw data
✅ **Multi-Turn Conversations** - "What about last month?" builds on previous context

---

## Architecture

### System Components

```
┌─────────────────────────────────────────────────────────────┐
│                        User Query                            │
│              "How many active contractors?"                  │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                      NeonAgent Class                         │
│  - Interprets natural language                              │
│  - Decides which tools to use                               │
│  - Formats responses                                        │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                   Claude AI (Anthropic)                      │
│  - Tool selection                                           │
│  - SQL generation                                           │
│  - Response composition                                     │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                   PostgresClient Class                       │
│  - Connection pooling                                       │
│  - Query execution                                          │
│  - Result formatting                                        │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                  Neon PostgreSQL Database                    │
│  - Your actual data                                         │
└─────────────────────────────────────────────────────────────┘
```

### Technology Stack

- **AI Model:** Claude 3 Haiku (fast & cost-effective) or Claude 3 Sonnet (more capable)
- **Database:** Neon PostgreSQL (serverless PostgreSQL)
- **Python Libraries:**
  - `anthropic` - Claude AI SDK
  - `psycopg2-binary` - PostgreSQL driver
  - `fastapi` - Optional API wrapper

---

## Quick Start

### Installation

1. **Install dependencies:**
```bash
# Using virtual environment (recommended)
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install packages
pip install anthropic psycopg2-binary
```

2. **Set up environment variables:**
```bash
# Create .env file
cat > .env <<EOF
# Anthropic API Key
ANTHROPIC_API_KEY=your_api_key_here

# Neon Database URL
NEON_DATABASE_URL=postgresql://user:password@host/dbname?sslmode=require
EOF
```

3. **Get your connection details:**
- **Anthropic API Key:** https://console.anthropic.com/account/keys
- **Neon Connection String:** Your Neon dashboard → Connection Details

### First Test

```bash
# Run basic test
python3 test_neon.py

# Run advanced analytics test
python3 test_neon_advanced.py

# Run interactive demo
python3 demo_neon_agent.py
```

---

## Configuration

### Environment Variables

```bash
# Required
ANTHROPIC_API_KEY=sk-ant-api03-xxx...
NEON_DATABASE_URL=postgresql://user:pass@host/db?sslmode=require

# Optional
AGENT_MODEL=claude-3-haiku-20240307  # Default model
AGENT_MAX_TOKENS=4096                # Response length limit
```

### Neon Connection String Format

```
postgresql://[username]:[password]@[host]/[database]?sslmode=require&channel_binding=require
```

**Example:**
```
postgresql://neondb_owner:npg_xxx@ep-dry-night-xxx.gwc.azure.neon.tech/neondb?sslmode=require&channel_binding=require
```

### Selecting Claude Model

```python
from neon_agent import NeonAgent

# Fast & cheap (recommended for most queries)
agent = NeonAgent(model="claude-3-haiku-20240307")

# More intelligent (better for complex analysis)
agent = NeonAgent(model="claude-3-5-sonnet-20241022")
```

**Model Comparison:**

| Model | Speed | Cost | Best For |
|-------|-------|------|----------|
| Haiku | ⚡⚡⚡ Fast | $ Cheap | Quick queries, data retrieval |
| Sonnet | ⚡⚡ Medium | $$ Medium | Complex analysis, insights |
| Opus | ⚡ Slower | $$$ Premium | Advanced reasoning (overkill) |

---

## Using the Agent

### Basic Usage

```python
from neon_agent import NeonAgent, load_env

# Load environment variables
load_env()

# Initialize agent
agent = NeonAgent()

# Ask questions
response = agent.chat("How many projects do we have?")
print(response)

# Follow-up questions (maintains context)
response = agent.chat("Which ones are over budget?")
print(response)

# Reset conversation
agent.reset_conversation()
```

### Example Session

```python
agent = NeonAgent()

# Query 1: Data exploration
response = agent.chat("What tables do we have in our database?")
# Agent lists all tables

# Query 2: Data analysis
response = agent.chat("Show me the top 5 contractors by performance score")
# Agent executes SELECT query with ORDER BY and LIMIT

# Query 3: Contextual follow-up
response = agent.chat("What about their safety scores?")
# Agent understands "their" refers to those 5 contractors

# Query 4: Complex analysis
response = agent.chat(
    "Compare average project costs between Q3 and Q4, "
    "broken down by project status"
)
# Agent generates grouped queries with date filtering
```

---

## Available Tools

The agent has access to these database tools:

### Schema Discovery Tools

#### `list_tables`
Lists all tables in the database.

**Example:**
```python
User: "What tables are in our database?"
Agent uses: list_tables()
```

#### `describe_table`
Gets detailed schema for a specific table.

**Parameters:**
- `table_name` (string): Name of the table

**Example:**
```python
User: "What columns does the projects table have?"
Agent uses: describe_table(table_name="projects")
```

#### `get_table_stats`
Gets statistics for a table (row count, size).

**Parameters:**
- `table_name` (string): Name of the table

**Example:**
```python
User: "How big is the contractors table?"
Agent uses: get_table_stats(table_name="contractors")
```

---

### Query Execution Tools

#### `execute_select`
Executes a SELECT query to retrieve data.

**Parameters:**
- `query` (string): SQL SELECT statement

**Example:**
```python
User: "Show me active projects"
Agent uses: execute_select(
    query="SELECT * FROM projects WHERE status = 'active'"
)
```

#### `execute_insert`
Executes an INSERT query to add data.

**Parameters:**
- `query` (string): SQL INSERT statement

**Example:**
```python
User: "Add a new contractor named Acme Corp"
Agent uses: execute_insert(
    query="INSERT INTO contractors (company_name) VALUES ('Acme Corp')"
)
```

#### `execute_update`
Executes an UPDATE query to modify data.

**Parameters:**
- `query` (string): SQL UPDATE statement

**Example:**
```python
User: "Mark project 123 as completed"
Agent uses: execute_update(
    query="UPDATE projects SET status = 'completed' WHERE id = 123"
)
```

#### `execute_delete`
Executes a DELETE query to remove data.

**Parameters:**
- `query` (string): SQL DELETE statement

**Example:**
```python
User: "Delete contractor with id 456"
Agent uses: execute_delete(
    query="DELETE FROM contractors WHERE id = 456"
)
```

---

### Analysis Tools

#### `count_rows`
Counts rows in a table with optional filtering.

**Parameters:**
- `table_name` (string): Name of the table
- `where_clause` (string, optional): WHERE condition

**Example:**
```python
User: "How many active contractors?"
Agent uses: count_rows(
    table_name="contractors",
    where_clause="status = 'active'"
)
```

---

## Example Queries

### Data Exploration

```python
# List all tables
"What tables do we have?"

# Describe schema
"Show me the structure of the projects table"

# Count records
"How many rows are in each table?"

# Sample data
"Show me 5 example rows from contractors"
```

### Business Intelligence

```python
# Project analysis
"What projects are over budget?"
"Show me project completion rates by status"
"Which projects started in Q3 2024?"

# Contractor analysis
"List contractors with performance score above 80"
"Which contractors have red RAG status?"
"Show me contractor safety scores sorted by performance"

# Financial analysis
"What's the total value of all active BOQs?"
"Compare estimated vs actual costs across projects"
"Show me spending by project phase"
```

### Advanced Queries

```python
# Multi-table joins
"Show me projects with their assigned contractors and current BOQ status"

# Aggregations
"Calculate average project duration by priority level"

# Trends
"Show me project start dates grouped by month for the last year"

# Insights
"Analyze our contractor ecosystem and identify patterns"
"Generate a comprehensive report on project health"
```

---

## Advanced Features

### Conversation Context

The agent maintains conversation history:

```python
agent = NeonAgent()

# Query 1
agent.chat("Show me all projects")

# Query 2 - builds on Query 1
agent.chat("Which ones are over budget?")
# Agent knows "ones" refers to projects

# Query 3 - continues context
agent.chat("What's the average budget for those?")
# Agent knows "those" refers to over-budget projects

# Reset when changing topic
agent.reset_conversation()
```

### Custom Context

Pass context to make queries page-aware:

```python
# In a project detail page
context = {
    "page": "project",
    "project_id": "123"
}

agent.chat("What's the status?", context=context)
# Agent knows to query project 123
```

### Structured Output

Request specific formats:

```python
# As table
"Show me contractors as a table with columns: name, status, score"

# As summary
"Summarize our BOQ approval status in 3 bullet points"

# As JSON
"Return project statistics as JSON"
```

---

## API Reference

### NeonAgent Class

```python
class NeonAgent:
    def __init__(
        self,
        model: str = "claude-3-haiku-20240307",
        connection_string: Optional[str] = None
    ):
        """
        Initialize the Neon Agent.

        Args:
            model: Claude model to use
            connection_string: PostgreSQL connection string
                             (uses NEON_DATABASE_URL env var if not provided)
        """

    def chat(self, user_message: str) -> str:
        """
        Send a message to the agent and get a response.

        Args:
            user_message: Natural language query

        Returns:
            Agent's response as string
        """

    def reset_conversation(self):
        """Clear conversation history."""
```

### PostgresClient Class

```python
class PostgresClient:
    def __init__(self, connection_string: str):
        """
        Initialize PostgreSQL client.

        Args:
            connection_string: PostgreSQL connection string
        """

    def execute_query(self, query: str, params: tuple = None) -> List[Dict]:
        """
        Execute a SELECT query.

        Args:
            query: SQL SELECT statement
            params: Query parameters for parameterized queries

        Returns:
            List of result rows as dictionaries
        """

    def execute_mutation(self, query: str, params: tuple = None) -> Dict:
        """
        Execute INSERT, UPDATE, or DELETE query.

        Args:
            query: SQL statement
            params: Query parameters

        Returns:
            Result dictionary with success status and row count
        """

    def list_tables(self) -> List[Dict]:
        """List all tables in the database."""

    def describe_table(self, table_name: str) -> List[Dict]:
        """Get schema information for a table."""

    def get_table_stats(self, table_name: str) -> Dict:
        """Get statistics for a table."""
```

---

## Troubleshooting

### Connection Issues

**Error:** `Failed to connect to database`

**Solutions:**
1. Check connection string format
2. Verify Neon database is running
3. Check SSL mode is set to `require`
4. Test connection directly:
```python
import psycopg2
conn = psycopg2.connect("your_connection_string")
```

### API Key Issues

**Error:** `ANTHROPIC_API_KEY environment variable not set`

**Solutions:**
1. Check `.env` file exists
2. Verify API key is correct
3. Run `load_env()` before creating agent
4. Check API key permissions at console.anthropic.com

### Query Failures

**Error:** Query returns empty results

**Possible causes:**
1. Table/column names are case-sensitive in PostgreSQL
2. Data doesn't match the query criteria
3. Table is actually empty

**Debug steps:**
```python
# Check table exists
agent.chat("What tables do we have?")

# Check table schema
agent.chat("Describe the projects table")

# Count rows
agent.chat("How many rows are in projects?")

# Sample data
agent.chat("Show me 3 example rows")
```

### Performance Issues

**Slow queries:**

1. **Use Haiku model** for simple queries:
```python
agent = NeonAgent(model="claude-3-haiku-20240307")
```

2. **Add indexes** to frequently queried columns
3. **Limit result sets** in your natural language:
   - "Show me the TOP 10 projects"
   - "Give me a summary, not all details"

---

## Production Deployment

### Security Best Practices

1. **Never commit `.env` files**
```bash
# Add to .gitignore
echo ".env" >> .gitignore
```

2. **Use environment variables in production**
```python
import os
api_key = os.getenv("ANTHROPIC_API_KEY")
```

3. **Implement rate limiting**
```python
from slowapi import Limiter
limiter = Limiter(key_func=get_remote_address)

@app.post("/agent/chat")
@limiter.limit("20/hour")
async def chat(request: ChatRequest):
    # Your code
```

4. **Add authentication**
```python
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer

security = HTTPBearer()

async def verify_token(credentials = Depends(security)):
    if credentials.credentials != VALID_TOKEN:
        raise HTTPException(status_code=401)
```

### Monitoring

Track these metrics:

```python
import time
import logging

class MonitoredNeonAgent(NeonAgent):
    def chat(self, user_message: str) -> str:
        start_time = time.time()

        try:
            response = super().chat(user_message)
            duration = time.time() - start_time

            logging.info({
                "query": user_message,
                "duration": duration,
                "success": True
            })

            return response
        except Exception as e:
            logging.error({
                "query": user_message,
                "error": str(e),
                "success": False
            })
            raise
```

### Scaling Considerations

**Connection Pooling:**
```python
from psycopg2.pool import ThreadedConnectionPool

pool = ThreadedConnectionPool(
    minconn=1,
    maxconn=10,
    dsn=connection_string
)
```

**Caching:**
```python
from functools import lru_cache

@lru_cache(maxsize=100)
def cached_query(query: str):
    return agent.chat(query)
```

**Async Support:**
```python
import asyncpg

class AsyncPostgresClient:
    async def execute_query(self, query: str):
        conn = await asyncpg.connect(connection_string)
        results = await conn.fetch(query)
        await conn.close()
        return results
```

---

## Cost Estimation

### Anthropic API Costs

**Claude Haiku (Recommended):**
- Input: $0.25 per million tokens
- Output: $1.25 per million tokens

**Typical query costs:**
- Simple query: ~$0.001 (1000 tokens)
- Complex analysis: ~$0.005 (5000 tokens)

**Monthly estimate:**
- 1000 queries/month: ~$3-5
- 5000 queries/month: ~$15-25
- 10000 queries/month: ~$30-50

### Hosting Costs

**Python Backend:**
- Railway/Render: $5-20/month
- Vercel: $0 (Hobby) or $20/month (Pro)
- Modal.com: Pay per use (~$5-15/month)

**Total:** ~$15-70/month for typical usage

---

## Support & Resources

### Documentation
- **Anthropic Docs:** https://docs.anthropic.com
- **Neon Docs:** https://neon.tech/docs
- **psycopg2 Docs:** https://www.psycopg.org/docs/

### Test Files
- `test_neon.py` - Basic connection test
- `test_neon_advanced.py` - Advanced analytics demo
- `demo_neon_agent.py` - Interactive demonstration

### Related Guides
- `NEON_AGENT_UI_RECOMMENDATIONS.md` - UI integration guide
- `CONVEX_AGENT_GUIDE.md` - Similar guide for Convex

---

## Changelog

### Version 1.0.0 (2025-10-31)
- ✅ Initial release
- ✅ PostgreSQL/Neon integration
- ✅ Claude Agent SDK implementation
- ✅ Schema discovery tools
- ✅ Query execution tools
- ✅ Conversation context support
- ✅ Comprehensive documentation

---

**Built with ❤️ using Claude Agent SDK**

For questions or issues, review the troubleshooting section or check the test files for working examples.
