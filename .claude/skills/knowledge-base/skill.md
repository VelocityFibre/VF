---
skill_name: knowledge-base
description: Access Velocity Fibre infrastructure documentation via API
version: 1.0.0
category: documentation
keywords:
  - documentation
  - knowledge base
  - servers
  - database schema
  - deployment procedures
  - VF server
  - Hostinger VPS
  - Neon database
progressive_disclosure: true
---

# Knowledge Base API Skill

Provides programmatic access to Velocity Fibre's centralized knowledge base containing:
- Server documentation (VF Server, Hostinger VPS)
- Database schema (133 Neon PostgreSQL tables)
- SQL query library (50+ common queries)
- Deployment procedures
- Troubleshooting guides

## API Endpoints

**Base URL**: `https://api.docs.fibreflow.app`

### Search Documentation
```bash
GET /api/v1/search?q={query}&category={optional}
```
Search across all documentation files. Returns matching content with snippets.

**Parameters**:
- `q` (required): Search query (min 2 characters)
- `category` (optional): Filter by category (servers, databases, etc.)
- `format` (optional): Response format (json or text)

**Example**:
```bash
curl "https://api.docs.fibreflow.app/api/v1/search?q=deployment&category=servers"
```

### List All Files
```bash
GET /api/v1/files?category={optional}
```
List all documentation files with metadata.

### Get File Content
```bash
GET /api/v1/files/{path}?format={markdown|text}
```
Retrieve specific documentation file.

**Example**:
```bash
curl "https://api.docs.fibreflow.app/api/v1/files/servers/vf-server.md"
```

### Server Documentation
```bash
GET /api/v1/servers/{name}?format={markdown|text}
```
Get documentation for specific server.

**Available servers**:
- `vf-server` - VF Server (100.96.203.105)
- `hostinger-vps` - Hostinger VPS (72.60.17.245)
- `vf` - Alias for vf-server
- `hostinger` - Alias for hostinger-vps

**Example**:
```bash
curl "https://api.docs.fibreflow.app/api/v1/servers/vf-server"
```

### Database Queries
```bash
GET /api/v1/database/queries?format={text|json}
```
Get SQL query library (50+ common queries).

### Database Schema
```bash
GET /api/v1/database/schema?format={markdown|text}
```
Get Neon PostgreSQL schema overview (133 tables).

## Usage in Claude Code

When a user asks about infrastructure documentation, use this skill to fetch relevant information.

**Example queries**:
- "What services run on VF Server?"
- "Show me the deployment procedure for QFieldCloud"
- "What's the database schema for contractors?"
- "Give me SQL queries for material inventory"
- "How do I restart FibreFlow on the server?"

**Pattern**:
1. Determine what documentation is needed
2. Use appropriate endpoint (search for broad queries, specific endpoints for known resources)
3. Parse response and present relevant information to user

## Scripts

Scripts are in `.claude/skills/knowledge-base/scripts/`:

- `search.py` - Search documentation
- `get_server_docs.py` - Fetch server documentation
- `get_queries.py` - Fetch SQL query library
- `get_schema.py` - Fetch database schema

## Examples

### Search for deployment info
```python
./scripts/search.py --query "deployment procedure" --category servers
```

### Get VF Server documentation
```python
./scripts/get_server_docs.py --server vf-server
```

### Get database queries
```python
./scripts/get_queries.py
```

### Get database schema
```python
./scripts/get_schema.py
```

## Web Documentation

Full searchable documentation is also available at: **https://docs.fibreflow.app**

## Progressive Disclosure

This skill uses progressive disclosure - scripts are only loaded when needed. The API handles all heavy lifting server-side.
