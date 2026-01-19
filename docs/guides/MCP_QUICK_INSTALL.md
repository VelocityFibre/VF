# MCP Servers - Quick Installation Guide

**Get FibreFlow powered up with MCP servers in 5 minutes**

---

## Step 1: Choose Your MCPs

**Essential** (Start Here):
- ✅ **Context7** - Documentation lookup
- ✅ **Playwright MCP** - UI testing

**Optional** (Add Later):
- ⚠️ **PostgreSQL MCP** - Database access (requires setup)
- ⚠️ **Python REPL** - Code execution
- ⚠️ **GitHub MCP** - Repository management

---

## Step 2: Quick Install (Recommended)

### Option A: Add Essential MCPs Only

Edit `.claude/settings.local.json` and add this `mcpServers` section:

```json
{
  "permissions": {
    // ... your existing permissions ...
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
    }
  }
}
```

### Option B: Copy Full Configuration

Copy from `.claude/mcp-config-example.json` and paste into `.claude/settings.local.json`.

Enable/disable MCPs by adding/removing the `"disabled": true` line.

---

## Step 3: Restart Claude Code

Close and reopen Claude Code to load the MCP servers.

---

## Step 4: Test MCPs

### Test Context7
```
Use context7 to fetch latest FastAPI middleware documentation
```

Expected: Returns current FastAPI docs with code examples

### Test Playwright
```
@ui-tester Test the production interface at http://72.60.17.245
```

Expected: Navigates to site and generates test report

---

## Step 5: Add PostgreSQL MCP (Optional)

**Security First**: Create read-only database user

```sql
-- Connect to Neon database
CREATE USER mcp_readonly WITH PASSWORD 'generate_secure_password_here';
GRANT CONNECT ON DATABASE your_database TO mcp_readonly;
GRANT USAGE ON SCHEMA public TO mcp_readonly;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO mcp_readonly;
```

Then add to `.env`:
```bash
MCP_DATABASE_URL=postgresql://mcp_readonly:password@host/database
```

Update settings.local.json:
```json
{
  "postgres-mcp": {
    "command": "npx",
    "args": ["-y", "postgres-mcp-pro"],
    "env": {
      "DATABASE_URI": "${MCP_DATABASE_URL}"
    }
  }
}
```

---

## Troubleshooting

### MCPs not loading?
1. Check `.claude/settings.local.json` syntax (valid JSON)
2. Restart Claude Code
3. Check Claude Code logs for errors

### Context7 timeout?
- Network issue - check internet connection
- Try again in a few seconds

### Playwright not working?
- Requires Node.js and npm installed
- Run: `npx @executeautomation/playwright-mcp-server` manually to test

---

## Usage Examples

### Documentation Lookup
```
Use context7 for PostgreSQL JSON query examples
Use context7 to show FastAPI dependency injection patterns
```

### UI Testing
```
@ui-tester Run all UI tests
@ui-tester Test chat functionality
Navigate to http://72.60.17.245 and take screenshot
```

### Database Analysis (if configured)
```
Use postgres-mcp to analyze contractor table performance
Get EXPLAIN plan for project queries
```

---

## Full Documentation

For detailed information, see `MCP_SERVERS_GUIDE.md`

---

## Quick Reference

**Priority**: Install Context7 first (easiest, most useful)

**Recommendation**:
1. Week 1: Context7 only
2. Week 2: Add Playwright MCP
3. Week 3: Evaluate PostgreSQL MCP need
4. As needed: Add others

**Status**: Ready to install anytime!
