---
description: Execute natural language database query against Neon PostgreSQL
argument-hint: [natural-language-query]
---

# Natural Language Database Query

Execute the following query against the Neon PostgreSQL database:

**Query**: $ARGUMENTS

## Execution Process

### Step 1: Activate Neon Agent Context

Load the Neon database agent from `neon_agent.py` which provides natural language to SQL translation.

### Step 2: Convert to SQL

Use the Neon agent to:
1. Parse the natural language query
2. Identify relevant tables from the 104-table schema
3. Generate optimized SQL query
4. Validate query safety (read-only, no destructive operations)

**Database Schema Context**:
- **Contractors**: 20 total, 9 active (companies, contact info, status)
- **Projects**: 2 active (fiber optic deployments)
- **BOQs**: Bill of Quantities (project materials and costs)
- **RFQs**: Request for Quotations
- **Clients**: Customer information
- **Suppliers**: Material suppliers
- **Performance Tracking**: Metrics and KPIs
- **Approval Workflows**: Multi-stage approval processes

### Step 3: Execute Query

```python
from neon_agent import NeonAgent

agent = NeonAgent()
response = agent.chat("$ARGUMENTS")
print(response)
```

### Step 4: Format Results

Present results as:

```markdown
## Query Results

**Original Query**: $ARGUMENTS

**Generated SQL**:
```sql
[SQL query that was executed]
```

**Results**:
[Formatted table or list of results]

**Row Count**: X records

**Insights**:
- [Key insight 1]
- [Key insight 2]
- [Patterns or anomalies noticed]

**Performance**:
- Execution time: Xms
- Tables accessed: [list]
```

## Safety Checks

Before executing:
- ✅ Verify query is read-only (SELECT, not INSERT/UPDATE/DELETE)
- ✅ Check for potentially expensive operations (full table scans)
- ✅ Validate table names exist in schema
- ⚠️ Warn if query might return large result sets

If query is:
- **Destructive (INSERT/UPDATE/DELETE)**: Request explicit confirmation
- **Expensive (millions of rows)**: Suggest adding LIMIT clause
- **Invalid (bad table names)**: Suggest corrections

## Common Query Patterns

### Contractor Queries
```
- "List all active contractors with contact information"
- "Show contractor performance metrics"
- "Find contractors in [region/city]"
```

### Project Queries
```
- "Show current project status and progress"
- "List all projects with budget vs actual costs"
- "Find projects in [city/region]"
```

### Financial Queries
```
- "Calculate total BOQ value for project X"
- "Show RFQ status and responses"
- "List pending invoices by contractor"
```

### Performance Queries
```
- "Show top performing contractors by completion rate"
- "Find projects behind schedule"
- "Calculate average project profit margins"
```

## Database Connection

**Connection**: Uses `NEON_DATABASE_URL` from environment
**Schema**: Production database with 104 tables
**Read/Write**: Agent defaults to read-only for safety

## Advanced Features

### Aggregations
The agent can handle:
- COUNT, SUM, AVG, MIN, MAX
- GROUP BY and ORDER BY
- HAVING clauses
- Subqueries

### Joins
Automatic table joining for related data:
- Contractors ↔ Projects
- Projects ↔ BOQs ↔ Materials
- RFQs ↔ Suppliers ↔ Quotes

### Filtering
Support for:
- Date ranges
- Status filters
- Geographic filters
- Numeric comparisons

## Error Handling

If query fails:
1. Show clear error message
2. Explain likely cause
3. Suggest corrected query
4. Provide relevant schema information

## Output Format

Always provide:
- ✅ Original natural language query
- ✅ Generated SQL (for transparency)
- ✅ Formatted results
- ✅ Row count
- ✅ Key insights
- ✅ Performance metrics
- ⚠️ Any warnings or suggestions

## Examples

### Example 1: Simple List
**Query**: "List all active contractors"
**SQL**: `SELECT name, email, phone FROM contractors WHERE status = 'active'`
**Results**: [Table of contractors]

### Example 2: Aggregation
**Query**: "How many contractors do we have by region?"
**SQL**: `SELECT region, COUNT(*) as count FROM contractors GROUP BY region ORDER BY count DESC`
**Results**: [Region count table]

### Example 3: Complex Join
**Query**: "Show project progress with contractor names"
**SQL**: [Multi-table JOIN]
**Results**: [Combined data table]

## Integration Notes

This command uses the Neon agent from `neon_agent.py`, which:
- Maintains conversation history for follow-up queries
- Understands FibreFlow domain terminology
- Has access to complete schema definitions
- Uses Claude Haiku for cost-effective queries
- Provides intelligent SQL optimization

For complex analytical queries, consider using Claude Sonnet (better reasoning) by setting `ANTHROPIC_MODEL=claude-sonnet-4.5` before querying.
