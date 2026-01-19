# FibreFlow Custom Commands - Quick Reference

**Quick access guide for all Claude Code custom commands**

---

## Agent Development

### `/agent-test [agent-name]`
Test a specific agent with detailed analysis
```
/agent-test vps_monitor
/agent-test neon_database
```

### `/agent-new [name] [capabilities]`
Create a new agent following FibreFlow patterns
```
/agent-new email-notifier "Send email notifications to clients and contractors"
/agent-new reporting "Generate business intelligence reports from Neon database"
```

### `/agent-document [agent-name]`
Generate or update agent documentation
```
/agent-document vps_monitor
/agent-document neon_database
```

---

## Database Operations

### `/db-query [natural-language-query]`
Query Neon PostgreSQL in natural language
```
/db-query "List all active contractors with their email addresses"
/db-query "Show project completion rates by contractor"
/db-query "Calculate total BOQ value for project Solar-City-Phase-2"
```

### `/db-sync`
Sync Neon data to Convex backend
```
/db-sync
```

---

## Deployment & Monitoring

### `/vps-health`
Check VPS health metrics
```
/vps-health
```

### `/deploy [agent-name or 'all']`
Deploy to production with validation
```
/deploy brain-api
/deploy vps_monitor
/deploy all
```

---

## Testing & Quality

### `/test-all`
Run complete test suite
```
/test-all
```

### `/code-review`
Security and performance review
```
/code-review
```

### `/eval [content]`
Validate external content against sources of truth
```
/eval [paste transcript or article here]
```

---

## Common Workflows

### New Feature Development
```bash
# 1. Write code
# 2. Review it
/code-review

# 3. Test it
/test-all

# 4. Deploy it
/vps-health
/deploy feature-name
```

### New Agent Creation
```bash
# 1. Create agent
/agent-new my-agent "Agent description and capabilities"

# 2. [Implement tools and logic in generated files]

# 3. Document it
/agent-document my-agent

# 4. Test it
/agent-test my-agent

# 5. Review and deploy
/code-review
/deploy my-agent
```

### Database Queries
```bash
# Quick queries
/db-query "Your natural language question"

# After Neon changes, sync to Convex
/db-sync
```

### Pre-Deployment Checklist
```bash
/code-review      # Security & performance
/test-all         # All tests passing?
/vps-health       # VPS ready?
/deploy all       # Deploy with validation
```

---

## Tips

- **Commands save tokens**: Each command saves ~60 words per invocation
- **Commands are context-aware**: They understand FibreFlow architecture
- **Commands include validation**: Built-in safety checks and error handling
- **Commands are educational**: They explain what they do and why

---

## Command Arguments

| Command | Arguments | Optional? |
|---------|-----------|-----------|
| `/agent-test` | agent-name | No |
| `/agent-new` | name capabilities | No |
| `/agent-document` | agent-name | No |
| `/db-query` | natural-language-query | No |
| `/db-sync` | none | - |
| `/vps-health` | none | - |
| `/deploy` | agent-name or 'all' | No |
| `/test-all` | none | - |
| `/code-review` | none | - |
| `/eval` | content to evaluate | No |

---

## Getting Help

Each command includes:
- Detailed instructions
- Error handling guidance
- Output format specifications
- Troubleshooting tips
- Success criteria

Just invoke the command and it will guide you through the process!

---

## What's Next?

**Phase 2**: Sub-agents for automated code review, test generation, and documentation
**Phase 3**: MCP server integrations for enhanced capabilities

See `CLAUDE_CODE_OPTIMIZATION_ROADMAP.md` for full plan.

---

**Quick Access**: Type `/` in Claude Code to see all available commands!
