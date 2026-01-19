---
id: database-operations
name: Database Operations
description: Natural language interface to Neon PostgreSQL database. Query business data, analyze schema, retrieve contractor/project/BOQ information.
triggers: [database, sql, query, neon, postgresql, table, contractor, project, boq, schema, data]
estimated_tokens: 600
complexity: simple
---

# Database Operations Skill

## Overview

Connect to FibreFlow's Neon PostgreSQL database (104 tables) for fiber optic business operations. Natural language interface to query contractors, projects, BOQs, RFQs, suppliers, clients, and infrastructure data.

## Capabilities

### Schema Discovery
- List all tables in database
- Describe table structure (columns, types, constraints)
- Get table statistics (row counts, sizes)

### Data Querying
- Execute SELECT queries for data retrieval
- Business intelligence queries
- Multi-table joins and analysis

### Data Modification
- INSERT new records
- UPDATE existing records
- DELETE records (use with caution)

## Database Context

**Connection**: Uses `NEON_DATABASE_URL` environment variable

**Key Tables** (104 total):
- `contractors` - 20 total (9 active)
- `projects` - Project management
- `boq` - Bill of Quantities
- `rfq` - Request for Quote
- `suppliers` - Material suppliers
- `clients` - Customer information
- `foto_ai_reviews` - AI evaluation results for DR installations (27+ records)
- Performance tracking, approval workflows, material tracking

## Tools

All tools are Python scripts in `scripts/` directory.

### list_tables
Lists all tables in the database.

**Usage**:
```bash
./scripts/list_tables.py
```

**Returns**: JSON array of table names and types

---

### describe_table
Get detailed schema for a specific table.

**Usage**:
```bash
./scripts/describe_table.py --table TABLE_NAME
```

**Parameters**:
- `--table`: Name of the table to describe

**Returns**: Column names, data types, constraints, nullability

---

### table_stats
Get statistics for a table (row count, size).

**Usage**:
```bash
./scripts/table_stats.py --table TABLE_NAME
```

**Parameters**:
- `--table`: Name of the table

**Returns**: Row count, total size, table size

---

### execute_query
Execute a SELECT query to retrieve data.

**Usage**:
```bash
./scripts/execute_query.py --query "SELECT ..." [--limit LIMIT]
```

**Parameters**:
- `--query`: SQL SELECT statement
- `--limit`: Optional row limit (default: 100)

**Returns**: Query results as JSON

**Safety**: Read-only, SELECT queries only

---

### execute_insert
Insert new data into a table.

**Usage**:
```bash
./scripts/execute_insert.py --query "INSERT INTO ..."
```

**Parameters**:
- `--query`: SQL INSERT statement

**Returns**: Rows affected, status

**Warning**: Modifies database. Verify query before executing.

---

### execute_update
Update existing records.

**Usage**:
```bash
./scripts/execute_update.py --query "UPDATE ..."
```

**Parameters**:
- `--query`: SQL UPDATE statement

**Returns**: Rows affected, status

**Warning**: Modifies database. Use WHERE clause to avoid mass updates.

---

### execute_delete
Delete records from table.

**Usage**:
```bash
./scripts/execute_delete.py --query "DELETE FROM ..."
```

**Parameters**:
- `--query`: SQL DELETE statement

**Returns**: Rows deleted, status

**Warning**: DESTRUCTIVE. Always use WHERE clause. Consider backup first.

## Workflow Examples

### Example 1: Count Active Contractors
```bash
# Step 1: Find contractors table
./scripts/list_tables.py | grep contractor

# Step 2: Check table structure
./scripts/describe_table.py --table contractors

# Step 3: Query active contractors
./scripts/execute_query.py --query "SELECT COUNT(*) FROM contractors WHERE status = 'active'"
```

### Example 2: Business Intelligence Query
```bash
# Multi-table analysis: contractors on recent projects
./scripts/execute_query.py --query "
  SELECT
    c.name,
    c.phone,
    p.project_name,
    p.status
  FROM contractors c
  JOIN project_assignments pa ON c.id = pa.contractor_id
  JOIN projects p ON pa.project_id = p.id
  WHERE p.created_at > NOW() - INTERVAL '30 days'
  ORDER BY p.created_at DESC
" --limit 50
```

### Example 3: Schema Exploration
```bash
# Understand database structure before querying
./scripts/list_tables.py
./scripts/describe_table.py --table boq
./scripts/table_stats.py --table boq
```

## Error Handling

All scripts return errors in JSON format:

```json
{
  "error": "Connection failed",
  "details": "NEON_DATABASE_URL not set",
  "query": "SELECT * FROM contractors"
}
```

**Common errors**:
- **Connection failed**: Check `NEON_DATABASE_URL` environment variable
- **Table not found**: Verify table name with `list_tables.py`
- **Permission denied**: Check database user permissions
- **Syntax error**: Validate SQL syntax

## When to Use This Skill

✅ **Use for**:
- Simple data lookups ("How many contractors?")
- Business intelligence queries
- Schema discovery
- Cross-domain queries needing database data

❌ **Don't use for**:
- Complex multi-hour database analysis (escalate to specialist)
- Database schema changes (requires specialist)
- Performance optimization (requires specialist)
- Bulk data migrations (requires specialist)

## Performance Notes

- Queries have default 100 row limit (use `--limit` to override)
- Connection pooling handled by scripts
- For large datasets, consider pagination
- Complex joins may be slow on 104-table schema

## Security

- **Read queries**: Safe, no modifications
- **Write queries**: Always preview before executing
- **DELETE queries**: EXTREMELY DANGEROUS - always use WHERE clause
- **SQL injection**: Scripts use parameterized queries where possible
- **Credentials**: Never log or expose `NEON_DATABASE_URL`

## Context Efficiency

**Progressive Disclosure**:
- This skill.md: ~600 tokens
- Script source code: NOT loaded (file system execution)
- Results: Loaded only after execution

**Total context**: ~1000 tokens for typical query (skill + results)

**Compare to**: Full agent implementation (~5000 tokens in context)

## Maintenance

**Adding new operations**:
1. Create Python script in `scripts/`
2. Add tool documentation section above
3. Update capabilities list
4. Test with sample data

**Modifying existing tools**:
- Scripts are just Python files - edit directly
- Changes take effect immediately (no redeployment)
- Version in Git for history

## Dependencies

```bash
# Python packages required
pip install psycopg2-binary python-dotenv

# Environment variables
export NEON_DATABASE_URL="postgresql://user:pass@host/db"
```

See `scripts/requirements.txt` for exact versions.
