# Claude Code Best Practices Guide

Based on comprehensive analysis of Claude Code workflows and common pitfalls to avoid.

## 🔐 Security & Secrets Management

### Critical Rules

**NEVER commit secrets to Git:**
```bash
# Create .gitignore if not exists
cat >> .gitignore << EOF
.env
.env.*
!.env.example
**/credentials.json
**/secrets.json
**/.keys/
*.pem
*.key
EOF
```

**Use environment variables consistently:**
```bash
# .env.example (safe to commit)
ANTHROPIC_API_KEY=your_key_here
CONVEX_DEPLOYMENT_URL=your_url_here
NEON_DATABASE_URL=your_db_url_here

# .env (NEVER commit)
ANTHROPIC_API_KEY=sk-ant-actual-key-here
```

**Audit claude.md before sharing:**
- Remove internal URLs, credentials, employee names
- Sanitize business-specific data
- Create `claude.local.md` for sensitive instructions (add to .gitignore)

### Settings Hierarchy for Secrets

```
.claude/settings.local.json   (personal, not in git)
.claude/settings.json          (project, can share)
~/.claude/settings.json        (global, personal)
```

---

## 🧠 Context Window Management

### The 60-70-85 Rule

**At 60% usage:**
- Consider manual compaction
- Review what's loaded (check file lists)
- Remove completed task references

**At 70% usage:**
- Strongly recommend compaction
- Use retention instructions (see below)
- Archive old conversation threads

**At 85% usage:**
- **STOP and compact before proceeding**
- Critical threshold - performance degrades rapidly
- Risk of important context being lost

### Smart Compaction Strategy

**Retention Template:**
```
Please compact the context and retain:
- Current architectural decisions for [active feature]
- Open bugs from bugs.md with workarounds
- User preferences: [style, workflow, tools]
- Active implementation approach for [feature X]
- Project constraints: [performance, security, etc.]

Discard:
- Completed tasks from progress.md
- Failed experimental code attempts
- Debugging output and stack traces
- Resolved issues and old discussion threads
```

### Proactive Context Optimization

**Structure files to minimize loading:**
```
# Instead of one huge file
reference-docs.md (5000 lines)

# Split strategically
reference-docs/
├── api-reference.md      (load when API work)
├── database-schema.md    (load when DB work)
├── ui-components.md      (load when UI work)
└── deployment.md         (load when deploying)
```

**Use progressive disclosure:**
- Keep claude.md lean - link to details
- Put reference docs in separate files
- Use skills for reusable workflows

---

## ✅ Error Handling & Validation

### Always Verify Critical Operations

**Before deploying:**
```bash
# Run tests
npm test
# Check build
npm run build
# Verify environment
npm run check-env
```

**After API changes:**
```python
# Test the actual endpoints
python test_api_integration.py

# Don't just trust the code looks right
# Make the API calls
```

**Validate agent outputs:**
```python
# Don't assume agents got it right
# Add validation layer
def validate_agent_response(response):
    required_fields = ['status', 'data', 'timestamp']
    if not all(field in response for field in required_fields):
        raise ValidationError(f"Missing required fields")
    return response
```

### Error Recovery Patterns

**Graceful degradation:**
```python
try:
    result = convex_agent.query(user_input)
except ConvexError:
    # Fallback to Neon
    result = neon_agent.query(user_input)
except Exception as e:
    # Log and return safe default
    log_error(e)
    result = {"error": "Service temporarily unavailable"}
```

**Retry with exponential backoff:**
```python
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10)
)
def call_external_api():
    # API call here
    pass
```

---

## 🚀 Progressive Implementation Path

### Phase 1: Foundation (Week 1)

**Goals:**
- Basic claude.md setup
- GitHub backup configured
- 1-2 essential skills created
- Environment organized

**Checklist:**
- [ ] Create project folder structure
- [ ] Write initial claude.md with project context
- [ ] Set up .gitignore and .env
- [ ] Initialize Git repo and push to GitHub
- [ ] Create first skill (e.g., testing workflow)
- [ ] Document your conventions in claude.md

### Phase 2: Expansion (Week 2-3)

**Goals:**
- First specialized subagent
- API integrations working
- Custom logging implemented
- Skills library growing

**Checklist:**
- [ ] Create first subagent in `.claude/agents/`
- [ ] Connect first external API (GitHub, Notion, etc.)
- [ ] Implement logging to track work
- [ ] Add 2-3 more skills for common workflows
- [ ] Set up MCP if needed (start with official ones)

### Phase 3: Optimization (Week 4+)

**Goals:**
- Multiple departments/teams
- Parallel execution workflows
- Full productivity tracking
- Custom commands for frequent tasks

**Checklist:**
- [ ] Organize agents into departments (folders)
- [ ] Create parallel execution workflows
- [ ] Implement productivity assessment
- [ ] Build custom commands for recurring tasks
- [ ] Refine context management strategy

---

## 🎯 Tool Selection Decision Tree

```
┌─────────────────────────────────────┐
│ What do you need to do?             │
└──────────────┬──────────────────────┘
               │
        ┌──────┴──────┐
        │  COMPLEXITY  │
        └──────┬───────┘
               │
    ┌──────────┼──────────┐
    │          │          │
  SIMPLE    MODERATE   COMPLEX
    │          │          │
    ▼          ▼          ▼
```

### Simple → Direct Prompt
**When:**
- One-off request
- Single file edit
- Quick question

**Example:** "Fix the typo in line 42 of app.py"

### Moderate → Skill
**When:**
- Reusable workflow
- Multi-step process
- Needs to work across projects
- Auto-invoke desired

**Example:** Testing workflow, commit conventions, code review checklist

### Complex → Subagent
**When:**
- Requires specialized context
- Multi-step reasoning needed
- Isolated context window beneficial
- Part of larger orchestrated workflow

**Example:** API design agent, database migration agent, security audit agent

### Manual Trigger → Custom Command
**When:**
- Want explicit control
- Recurring specific task
- Needs user input

**Example:** Weekly planning, deployment checklist, project initialization

### External Data → MCP or API
**When:**
- Real-time data needed
- External service integration
- Dynamic information

**Example:** GitHub data, Notion pages, database queries

---

## 📊 Performance Monitoring

### Track Agent Usage

**Create: `.claude/logs/agent-usage.json`**
```json
{
  "date": "2025-11-11",
  "agents_invoked": ["convex-agent", "neon-agent"],
  "success_rate": 0.95,
  "avg_execution_time_seconds": 4.2,
  "failures": [
    {
      "agent": "convex-agent",
      "error": "Connection timeout",
      "timestamp": "2025-11-11T10:30:00Z"
    }
  ]
}
```

**Monitor in claude.md:**
```markdown
## Performance Notes

### Agent Success Rates (Last 7 Days)
- convex-agent: 98% (2 timeouts)
- neon-agent: 95% (5 connection errors)
- orchestrator: 100%

### Average Response Times
- Simple queries: 2.1s
- Complex multi-step: 8.5s
- With external API: 12.3s

### Action Items
- [ ] Investigate Neon connection pool settings
- [ ] Add caching for frequently accessed Convex data
```

### Context Usage Patterns

**Track what gets loaded:**
```markdown
## Context Efficiency Log

### Session 2025-11-11
- Loaded: api-docs.md (never used)
- Loaded: database-schema.md (used 3x ✓)
- Loaded: deployment-guide.md (never used)

**Optimization:** Move api-docs references to separate skill
```

---

## 🎨 Skills Best Practices

### Progressive Disclosure Structure

**Good:**
```markdown
---
name: Database Migrations
description: Guides safe database schema changes with rollback plans
---

# Quick Reference
Common commands and patterns.

# When to Use
[Brief triggers]

# Detailed Workflows
See [migration-guide.md](migration-guide.md)

# Examples
See [examples/](examples/)
```

**Bad:**
```markdown
---
name: Database Migrations
description: Database stuff
---

[3000 lines of everything about databases...]
```

### Testing Your Skills

**Validation checklist:**
```bash
# 1. Is it triggered appropriately?
echo "Create a migration to add user preferences" | claude-code
# → Should invoke Database Migrations skill

# 2. Does it load the right linked files?
# Check Claude's reasoning - should only load what's needed

# 3. Does it improve outcomes?
# Compare before/after skill creation
```

---

## ⚠️ Common Pitfalls & Solutions

### Pitfall 1: Over-Engineering Too Early

**Symptom:** Spending weeks building agent infrastructure before doing real work

**Solution:** Start simple
```markdown
# Start with this:
claude.md + direct prompts

# Then add as needed:
→ One skill for your most common workflow
→ One subagent for most complex task
→ API integration when manual copy-paste becomes painful
```

### Pitfall 2: Context Pollution

**Symptom:** Every session starts slow, context at 80%+ immediately

**Solution:**
- Compact more frequently (don't wait for 92%)
- Split large reference files
- Use `.claudeignore` for non-essential files
- Keep completed tasks in archive/

### Pitfall 3: Agent Chaos

**Symptom:** 20 agents, unclear which does what, overlap everywhere

**Solution:**
```
# Good structure
agents/
├── data/           (database, API, ETL agents)
├── code/           (review, refactor, testing agents)
├── content/        (docs, comments, README agents)
└── ops/            (deployment, monitoring agents)

# Each with clear, non-overlapping responsibilities
```

### Pitfall 4: Skill Naming Ambiguity

**Bad names:**
- "Helper" (helper for what?)
- "Utils" (too vague)
- "Stuff" (useless)

**Good names:**
- "API Testing Workflow"
- "Database Migration Guide"
- "React Component Standards"

### Pitfall 5: No Validation Layer

**Problem:** Trusting agent outputs blindly

**Solution:**
```python
# Always validate critical operations
def deploy_with_safety():
    # Agent generates deployment plan
    plan = agent.chat("Create deployment plan")

    # YOU review
    print(plan)
    confirm = input("Execute? (yes/no): ")

    if confirm == "yes":
        execute(plan)
```

---

## 🔄 Maintenance Routines

### Daily
- Check context usage at session start
- Compact if > 60%
- Update progress.md or equivalent

### Weekly
- Review agent success rates
- Update skills that are frequently modified
- Archive old conversation sessions
- Check for failed API integrations

### Monthly
- Audit claude.md for outdated information
- Review and prune unused skills
- Update subagent instructions based on learnings
- Backup and version control check

---

## 📚 Documentation Standards

### Every Project Should Have

**Minimum:**
```
project/
├── .claude/
│   └── claude.md         (context & instructions)
├── .env.example          (required env vars)
├── .gitignore            (secrets excluded)
└── README.md             (human docs)
```

**Recommended:**
```
project/
├── .claude/
│   ├── claude.md
│   ├── agents/
│   ├── skills/
│   └── commands/
├── docs/
│   ├── ARCHITECTURE.md
│   ├── API.md
│   └── DEPLOYMENT.md
├── .env.example
├── .gitignore
└── README.md
```

### Claude.md Template

```markdown
# Project Name

## Context
Brief description of what this project does and why it exists.

## Architecture
High-level architecture overview (link to docs/ARCHITECTURE.md for details).

## Current Status
What's working, what's in progress, what's next.

## Conventions
- Code style preferences
- Testing approach
- Commit message format
- File naming

## Available Tools
- Skills: [list with brief descriptions]
- Agents: [list with specializations]
- MCPs: [list with purposes]

## Common Tasks
Links to skills/commands for frequent operations.

## External Resources
- Documentation: [URL]
- API Docs: [URL]
- Design System: [URL]
```

---

## 🎯 Success Metrics

Track these to know if your Claude Code setup is working:

### Efficiency Metrics
- **Context usage at session start** (should be < 30%)
- **Time to find information** (should decrease over time)
- **Repeat questions** (should decrease as claude.md improves)

### Quality Metrics
- **Failed agent executions** (should be < 5%)
- **Manual corrections needed** (should decrease)
- **Successful first-attempt solutions** (should increase)

### Organization Metrics
- **Number of contexts loaded unnecessarily** (minimize)
- **Skills reused across projects** (maximize)
- **Time spent on setup vs. real work** (10/90 ratio goal)

---

## 🚨 When to Ask for Help

### Red Flags

1. **Context constantly at 90%+** despite compaction
   - Review file structure
   - Check for circular references
   - Consider splitting project

2. **Agents frequently failing** in same way
   - Review agent instructions
   - Check tool permissions
   - Validate external integrations

3. **Spending more time managing than building**
   - Simplify setup
   - Remove unused agents/skills
   - Return to basics

### Getting Unblocked

```markdown
# Good help request format:
1. What I'm trying to do: [goal]
2. What I expected: [expected behavior]
3. What actually happened: [actual behavior]
4. What I've tried: [debugging steps]
5. Relevant context: [files, settings, versions]
```

---

## 🎓 Learning Path

### Beginner (Week 1-2)
- Master basic claude.md usage
- Create first 2-3 skills
- Set up GitHub backup
- Learn context management

### Intermediate (Week 3-6)
- Build first subagent
- Connect 1-2 external APIs
- Implement custom logging
- Create custom commands

### Advanced (Month 2+)
- Multi-agent orchestration
- Parallel execution patterns
- Custom MCP development
- Productivity analytics

---

## 📖 Additional Resources

### Official Documentation
- [Claude Code Docs](https://docs.claude.com/claude-code)
- [Skills Guide](https://docs.anthropic.com/skills)
- [MCP Protocol](https://github.com/anthropics/mcp)

### Your Project Docs
- `AGENT_SKILLS_GUIDE.md` - Detailed skills implementation
- `QUICK_START.md` - Getting started quickly
- `CONTEXT_ENGINEERING_GUIDE.md` - Advanced context management

### Community Resources
- [Anthropic Cookbook](https://github.com/anthropics/anthropic-cookbook)
- [MCP Servers Repository](https://github.com/modelcontextprotocol/servers)

---

**Remember:** Start simple, iterate based on actual needs, and let your setup evolve with your workflow. Don't build infrastructure for infrastructure's sake.
