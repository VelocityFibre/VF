# FibreFlow MCP Servers Guide
**Model Context Protocol Integration for Enhanced Capabilities**

**Date**: 2025-11-26
**Status**: Phase 3 - MCP Server Configuration

---

## What are MCP Servers?

**Model Context Protocol (MCP)** is a standardized way to connect AI assistants to external tools and services. MCP servers provide Claude Code with additional capabilities beyond its built-in tools.

### Benefits for FibreFlow
- **Documentation Lookup**: Instant access to Python/FastAPI/PostgreSQL docs
- **Browser Automation**: Automated UI testing of production interface
- **Database Access**: Direct SQL queries from Claude
- **Custom Tools**: Build FibreFlow-specific MCP servers

---

## Recommended MCP Servers for FibreFlow

### Priority 1: Essential MCPs

#### 1. Context7 - Documentation Lookup ⭐⭐⭐
**Purpose**: Up-to-date documentation for Python, FastAPI, PostgreSQL, pytest

**Why FibreFlow Needs It**:
- Instant access to latest FastAPI middleware patterns
- PostgreSQL query optimization examples
- Python library documentation
- pytest best practices

**Installation**:
```json
// Add to .claude/settings.local.json under "mcpServers"
{
  "context7": {
    "command": "npx",
    "args": ["-y", "@upstash/context7"]
  }
}
```

**Usage**:
```
Use context7 to fetch latest FastAPI middleware documentation
Use context7 for PostgreSQL parameterized query examples
Use context7 to get pytest fixture best practices
```

**Supported Libraries**:
- Python (3.10+)
- FastAPI
- PostgreSQL / psycopg2
- pytest
- SQLAlchemy
- Anthropic SDK

---

#### 2. Playwright MCP - Browser Automation ⭐⭐⭐
**Purpose**: Automated web interface testing

**Why FibreFlow Needs It**:
- Powers the `@ui-tester` sub-agent
- Test production interface at http://72.60.17.245/
- Generate automated test scripts
- Screenshot capture on failures

**Two Options**:

**Option A: ExecuteAutomation Playwright MCP** (Recommended)
```json
{
  "playwright-mcp": {
    "command": "npx",
    "args": ["-y", "@executeautomation/playwright-mcp-server"]
  }
}
```

**Features**:
- Browser automation (Chrome, Firefox, Safari)
- API testing capabilities
- Screenshot and video recording
- Integration with Claude Desktop, Cline, Cursor

**Option B: Microsoft Playwright MCP**
```json
{
  "playwright": {
    "command": "npx",
    "args": ["-y", "@microsoft/playwright-mcp"]
  }
}
```

**Features**:
- Structured accessibility snapshots
- No screenshots required (uses DOM analysis)
- Optimized for LLM interaction

**Recommendation**: Start with ExecuteAutomation version for FibreFlow's UI testing needs.

**Usage**:
```
@ui-tester Test the FibreFlow web interface
Navigate to http://72.60.17.245 and verify chat works
Take screenshot of production homepage
```

---

#### 3. PostgreSQL MCP - Database Access ⭐⭐
**Purpose**: Direct database queries from Claude

**Why FibreFlow Might Need It**:
- Direct SQL execution from Claude Code
- EXPLAIN ANALYZE for query optimization
- Index tuning recommendations
- Database health checks

**Option: Postgres MCP Pro**
```json
{
  "postgres-mcp": {
    "command": "npx",
    "args": ["-y", "postgres-mcp-pro"],
    "env": {
      "DATABASE_URI": "${NEON_DATABASE_URL}"
    }
  }
}
```

**Features**:
- Safe SQL execution (read-only by default)
- EXPLAIN plans for optimization
- Index analysis
- Health monitoring

**Security Note**: Only use with read-only credentials or careful permissions.

**Usage**:
```
Use postgres-mcp to analyze query performance
Get EXPLAIN plan for contractor lookup query
Suggest indexes for frequently queried columns
```

---

### Priority 2: Python Development MCPs

#### 4. Python REPL MCP - Code Execution ⭐
**Purpose**: Execute Python code in isolated environment

```json
{
  "python-repl": {
    "command": "npx",
    "args": ["-y", "@modelcontextprotocol/server-python"]
  }
}
```

**Use Cases**:
- Quick Python calculations
- Test code snippets
- Data transformations
- Algorithm prototyping

---

#### 5. GitHub MCP - Repository Management ⭐
**Purpose**: Enhanced GitHub operations

```json
{
  "github": {
    "command": "npx",
    "args": ["-y", "@modelcontextprotocol/server-github"],
    "env": {
      "GITHUB_TOKEN": "${GITHUB_TOKEN}"
    }
  }
}
```

**Features**:
- Create issues
- Manage pull requests
- Search repositories
- View file history

---

### Priority 3: Advanced/Optional MCPs

#### 6. Filesystem MCP - File Operations
**Purpose**: Advanced file system operations

```json
{
  "filesystem": {
    "command": "npx",
    "args": ["-y", "@modelcontextprotocol/server-filesystem", "/path/to/allowed/directory"]
  }
}
```

**Use Cases**:
- Bulk file operations
- Directory analysis
- File searching

**Security**: Restrict to specific directories only

---

#### 7. Slack MCP - Team Notifications
**Purpose**: Send deployment/alert notifications

```json
{
  "slack": {
    "command": "npx",
    "args": ["-y", "@modelcontextprotocol/server-slack"],
    "env": {
      "SLACK_BOT_TOKEN": "${SLACK_BOT_TOKEN}"
    }
  }
}
```

**Use Cases**:
- Deployment notifications
- Error alerts
- Team updates

---

## Installation Guide

### Step 1: Locate Settings File

FibreFlow's Claude Code settings are in:
```
/home/louisdup/Agents/claude/.claude/settings.local.json
```

### Step 2: Add MCP Servers

Edit `.claude/settings.local.json` and add `mcpServers` section:

```json
{
  "permissions": {
    "allow": [
      // ... existing permissions
    ]
  },
  "outputStyle": "Explanatory",
  "mcpServers": {
    "context7": {
      "command": "npx",
      "args": ["-y", "@upstash/context7"]
    },
    "playwright-mcp": {
      "command": "npx",
      "args": ["-y", "@executeautomation/playwright-mcp-server"]
    },
    "postgres-mcp": {
      "command": "npx",
      "args": ["-y", "postgres-mcp-pro"],
      "env": {
        "DATABASE_URI": "${NEON_DATABASE_URL}"
      }
    }
  }
}
```

### Step 3: Restart Claude Code

Restart Claude Code to load the new MCP servers.

### Step 4: Verify Installation

Test each MCP server:

**Context7**:
```
Use context7 to fetch latest FastAPI documentation
```

**Playwright**:
```
Navigate to http://72.60.17.245 using playwright
```

**PostgreSQL**:
```
Use postgres-mcp to list all tables in the database
```

---

## Configuration Best Practices

### Security

**1. Use Environment Variables**:
```json
{
  "postgres-mcp": {
    "env": {
      "DATABASE_URI": "${NEON_DATABASE_URL}"  // From .env
    }
  }
}
```

**2. Read-Only Database Access**:
Create separate read-only credentials for MCP database access:
```sql
CREATE USER mcp_readonly WITH PASSWORD 'secure_password';
GRANT CONNECT ON DATABASE fibreflow TO mcp_readonly;
GRANT USAGE ON SCHEMA public TO mcp_readonly;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO mcp_readonly;
```

**3. Restrict Filesystem Access**:
Only allow specific directories:
```json
{
  "filesystem": {
    "args": ["-y", "@modelcontextprotocol/server-filesystem", "/home/louisdup/Agents/claude"]
  }
}
```

### Performance

**1. Use npx with -y flag** for auto-install:
```json
"args": ["-y", "package-name"]  // Auto-install if not cached
```

**2. Monitor MCP server resource usage**:
```bash
# Check running MCP processes
ps aux | grep mcp
```

**3. Disable unused MCPs**:
Comment out or remove MCPs you're not actively using.

---

## MCP Server Troubleshooting

### Common Issues

#### Issue: MCP server not responding
**Symptoms**: "MCP server timeout" errors

**Diagnosis**:
1. Check if server is running: `ps aux | grep [mcp-name]`
2. Check Claude Code logs
3. Verify network connectivity

**Solution**:
```bash
# Restart Claude Code
# Or manually install MCP package
npx @upstash/context7
```

#### Issue: Permission denied
**Symptoms**: "Access denied" errors

**Diagnosis**:
Check `.claude/settings.local.json` permissions

**Solution**:
Add to `permissions.allow`:
```json
"permissions": {
  "allow": [
    "MCP(context7:*)",
    "MCP(playwright-mcp:*)"
  ]
}
```

#### Issue: Environment variable not found
**Symptoms**: "${VAR_NAME} not defined"

**Diagnosis**:
Check `.env` file has the variable

**Solution**:
```bash
# Add to .env
GITHUB_TOKEN=ghp_xxxxxxxxxxxxx
SLACK_BOT_TOKEN=xoxb-xxxxxxxxxxxxx
```

---

## Usage Examples

### Example 1: Documentation Lookup with Context7

```
User: Use context7 to show me how to create async middleware in FastAPI

Context7: Fetching latest FastAPI middleware docs...

[Returns up-to-date documentation with code examples]
```

**Value**: No need to manually search docs or risk using outdated examples.

### Example 2: UI Testing with Playwright

```
User: @ui-tester Test the FibreFlow web interface

UI Tester: Using Playwright MCP to test http://72.60.17.245...

[Navigates to site, tests chat interface, generates report with screenshots]
```

**Value**: Automated browser testing without manual clicking.

### Example 3: Database Analysis with PostgreSQL MCP

```
User: Use postgres-mcp to analyze the performance of contractor queries

PostgreSQL MCP: Analyzing queries on contractors table...

EXPLAIN ANALYZE results:
- Sequential scan on 20 rows (fast)
- Recommend index on email column (frequent lookups)
- Recommend index on status + created_at for filtered queries

[Provides specific CREATE INDEX commands]
```

**Value**: Expert query optimization without manual EXPLAIN analysis.

---

## Building Custom MCP Servers for FibreFlow

### Use Case: FibreFlow-Specific MCP Server

Create custom MCP server for FibreFlow-specific operations:

**Example: Agent Registry MCP**
```python
# fibreflow_mcp.py
from fastmcp import FastMCP

mcp = FastMCP("FibreFlow Agent Registry")

@mcp.tool()
def list_agents() -> dict:
    """List all registered FibreFlow agents"""
    import json
    with open('orchestrator/registry.json') as f:
        return json.load(f)

@mcp.tool()
def get_agent_triggers(agent_name: str) -> list:
    """Get trigger keywords for specific agent"""
    registry = list_agents()
    for agent in registry:
        if agent['name'] == agent_name:
            return agent['triggers']
    return []

if __name__ == "__main__":
    mcp.run()
```

**Configuration**:
```json
{
  "fibreflow-mcp": {
    "command": "python",
    "args": ["/home/louisdup/Agents/claude/fibreflow_mcp.py"]
  }
}
```

**Usage**:
```
Use fibreflow-mcp to list all agents
Get trigger keywords for vps_monitor agent using fibreflow-mcp
```

---

## MCP Server Recommendations by Use Case

### For Development
- ✅ **Context7** - Documentation lookup
- ✅ **Python REPL** - Code execution
- ⚠️ **GitHub** - If using GitHub frequently

### For Testing
- ✅ **Playwright MCP** - UI testing
- ⚠️ **PostgreSQL MCP** - Database testing (use read-only credentials)

### For Production Monitoring
- ⚠️ **Slack** - Deployment notifications
- ⚠️ **Custom FibreFlow MCP** - Agent health monitoring

### Not Recommended for FibreFlow
- ❌ **JavaScript/TypeScript MCPs** - FibreFlow is Python-based
- ❌ **Write-access Database MCPs** - Security risk (use read-only)
- ❌ **Browser Extension MCPs** - Redundant with Playwright

---

## MCP vs. Native FibreFlow Agents

### When to Use MCP Server
- ✅ External tool integration (browsers, docs, GitHub)
- ✅ Standard protocols (HTTP, SQL, file systems)
- ✅ Language-agnostic operations
- ✅ Temporary, exploratory tasks

### When to Build FibreFlow Agent
- ✅ FibreFlow-specific domain logic
- ✅ Multi-step workflows
- ✅ Conversation history needed
- ✅ Orchestrator integration required

**Example**:
- **MCP**: Playwright for raw browser automation
- **Agent**: VPS Monitor with SSH, metrics, analysis

---

## Security Checklist

Before installing MCP servers:

- [ ] Review MCP server source code (GitHub)
- [ ] Use read-only database credentials
- [ ] Restrict filesystem access to specific directories
- [ ] Store tokens/credentials in `.env` (not settings file)
- [ ] Verify MCP package is from trusted source
- [ ] Test in development before production
- [ ] Monitor MCP server resource usage
- [ ] Disable unused MCPs
- [ ] Keep MCP packages updated

---

## Success Metrics

MCP integration is successful when:
- ✅ Context7 provides accurate, current documentation
- ✅ Playwright MCP can test production UI
- ✅ PostgreSQL MCP suggests valid optimizations
- ✅ No security issues or credential leaks
- ✅ Performance impact is minimal (<100ms per query)
- ✅ Sub-agents (especially @ui-tester) work with MCPs

---

## Next Steps

### Immediate (This Week)
1. ⬜ Add Context7 to `.claude/settings.local.json`
2. ⬜ Test Context7 with Python/FastAPI docs
3. ⬜ Add Playwright MCP for UI testing
4. ⬜ Test @ui-tester with Playwright integration

### Short-Term (Next 2 Weeks)
5. ⬜ Evaluate PostgreSQL MCP with read-only credentials
6. ⬜ Build custom FibreFlow MCP server (agent registry)
7. ⬜ Document MCP usage patterns

### Long-Term (Future)
8. ⬜ Explore additional Python development MCPs
9. ⬜ Create FibreFlow MCP server suite
10. ⬜ Share MCP configurations with team

---

## Resources

**Official MCP Documentation**:
- Model Context Protocol: https://modelcontextprotocol.io
- MCP Server Examples: https://github.com/modelcontextprotocol/servers
- Python SDK: https://github.com/modelcontextprotocol/python-sdk

**FibreFlow-Compatible MCPs**:
- Context7: https://github.com/upstash/context7
- Playwright MCP: https://github.com/executeautomation/mcp-playwright
- Postgres MCP Pro: https://www.npmjs.com/package/postgres-mcp-pro
- FastMCP: https://github.com/jlowin/fastmcp

**Tutorials**:
- Integrating MCP with FastAPI: https://medium.com/@ruchi.awasthi63/integrating-mcp-servers-with-fastapi-2c6d0c9a4749
- Playwright MCP Testing: https://testomat.io/blog/playwright-mcp-claude-code/

---

## Conclusion

MCP servers significantly extend Claude Code's capabilities for FibreFlow development. Start with Context7 (docs) and Playwright (testing) for immediate productivity gains, then expand to PostgreSQL and custom MCPs as needed.

**Priority**: Context7 > Playwright > PostgreSQL > Custom

**Timeline**: Week 3-4 for Phase 3 completion

**Status**: Configuration guide complete, ready for installation

---

**Last Updated**: 2025-11-26
**Phase**: 3 - MCP Server Integration
**Next**: Install and test MCPs with FibreFlow workflows
