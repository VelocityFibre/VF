# Agent Skills Implementation Guide

## Overview

Agent Skills extend Claude's capabilities by packaging domain-specific expertise into composable, reusable resources. Skills use progressive disclosure to keep context lean while providing deep knowledge when needed.

## Core Concepts

### Progressive Disclosure (3 Levels)
1. **Metadata** (name + description) - Always loaded in system prompt
2. **SKILL.md body** - Loaded when skill is triggered
3. **Linked files** - Loaded only when specific context is needed

### Anatomy of a Skill

```
skill-name/
├── SKILL.md              # Core skill file with metadata
├── reference.md          # Additional context (optional)
├── examples.md           # Usage examples (optional)
├── scripts/              # Executable code (optional)
│   ├── tool1.py
│   └── tool2.sh
└── resources/            # Additional assets (optional)
    └── templates/
```

## Creating Your First Skill

### Step 1: Create Skill Directory

```bash
mkdir -p skills/context-engineering
cd skills/context-engineering
```

### Step 2: Write SKILL.md

```markdown
---
name: Context Engineering
description: Expert guidance on managing Claude's context window, compaction, and memory effectively
---

# Context Engineering Skill

## When to Use This Skill
- Context window approaching 60%+ usage
- Before starting major new features
- When planning long coding sessions
- Setting up new projects with Claude

## Core Capabilities

### Context Monitoring
Check context regularly with `/context` command.

**Warning Thresholds**:
- 60-70%: Recommend compaction
- 85%+: Strongly urge compaction before proceeding

### Proactive Compaction
Don't wait for auto-compact at 92%. Compact manually with retention instructions.

**Retention Template**:
See [compaction-guide.md](compaction-guide.md) for detailed instructions.

### Memory Management
Use `#` command to persist important instructions across sessions.

For detailed workflows, see [memory-workflows.md](memory-workflows.md).

### Structured Documentation
Maintain project state in persistent files outside context window.

See [structured-notes.md](structured-notes.md) for complete system.

## Quick Actions

When user mentions "context" or "compact":
1. Check current context usage
2. Recommend appropriate action based on threshold
3. Offer compaction with retention instructions if needed

## Related Files
- `compaction-guide.md` - Detailed compaction workflows
- `memory-workflows.md` - Memory tool best practices
- `structured-notes.md` - Note-taking system
```

### Step 3: Add Supporting Files

**skills/context-engineering/compaction-guide.md**:
```markdown
# Compaction Guide

## When to Compact
- Context > 60%: Recommend
- Context > 70%: Warn user
- Context > 85%: Strongly recommend before proceeding
- Before major features
- After completing milestones

## Retention Instructions Template

"Retain:
- All architectural decisions from recent work
- Current bugs and their workarounds
- User preferences for code style and workflow
- Current implementation approach for active features
- Project constraints and requirements

Discard:
- Completed tasks from progress.md
- Failed experimental code
- Debugging output
- Resolved issues"

## Process
1. Check context: `/context`
2. Run compact: `/compact`
3. Provide retention instructions
4. Verify new context usage
```

## Skill Design Best Practices

### 1. Start with Evaluation
- Identify specific capability gaps
- Test on representative tasks
- Observe where Claude struggles
- Build skills to address shortcomings

### 2. Structure for Scale

**Keep SKILL.md Lean**:
- Only essential instructions in main file
- Link to additional files for deep dives
- Use progressive disclosure

**Split Context Strategically**:
- Mutually exclusive contexts → separate files
- Rarely used together → keep paths separate
- Reduces token usage

**Code as Tools and Documentation**:
- Include executable scripts
- Scripts serve as both tools and reference
- Clearly indicate if Claude should execute or read

### 3. Think from Claude's Perspective

**Monitor Usage**:
- Watch which contexts Claude loads
- Note unexpected trajectories
- Observe overreliance on certain sections

**Optimize Metadata**:
- Name and description determine triggering
- Make them clear and specific
- Test different phrasings

### 4. Iterate with Claude

**Collaborative Development**:
- Ask Claude to capture successful approaches
- Request self-reflection on failures
- Let Claude suggest improvements
- Discover needed context organically

## Example Skills to Build

### 1. Testing Skill
```
skills/testing/
├── SKILL.md              # When/how to write tests
├── frameworks.md         # Jest, Vitest, Pytest guides
├── patterns.md           # Common testing patterns
└── scripts/
    └── run-coverage.sh
```

### 2. Git Workflow Skill
```
skills/git-workflow/
├── SKILL.md              # Commit conventions, PR process
├── commit-templates.md   # Semantic commit examples
├── branch-strategy.md    # Branching model
└── scripts/
    └── pre-commit.sh
```

### 3. API Development Skill
```
skills/api-development/
├── SKILL.md              # REST/GraphQL best practices
├── security.md           # Auth, validation, sanitization
├── documentation.md      # OpenAPI, examples
└── templates/
    └── endpoint-template.ts
```

### 4. Database Skill
```
skills/database/
├── SKILL.md              # Migration, query optimization
├── schemas.md            # Schema design patterns
├── migrations.md         # Migration best practices
└── scripts/
    ├── backup.sh
    └── migrate.py
```

## Skills vs MCP Servers

### Use Skills When:
- Teaching Claude complex workflows
- Providing organizational context
- Bundling procedural knowledge
- Context-heavy guidance needed

### Use MCP Servers When:
- Connecting to external tools/APIs
- Real-time data access required
- Integration with existing services
- Dynamic data sources

### Use Both When:
- MCP provides tools, Skill teaches workflows
- Example: MCP for database connection, Skill for schema design patterns

## Security Considerations

### Only Install Trusted Skills
- Audit all files before use
- Read bundled scripts carefully
- Check network connections
- Verify data handling

### Red Flags:
- Unclear code dependencies
- External network calls to unknown sources
- File system operations outside project
- Data exfiltration instructions
- Obfuscated code

### Best Practices:
- Review SKILL.md thoroughly
- Inspect all scripts
- Understand data flows
- Test in isolated environment first
- Monitor Claude's actions when using new skills

## Context Window Impact

### Before Skill Activation
```
[System Prompt] + [Skill Metadata Only] + [User Message]
```

### After Skill Triggered
```
[System Prompt] + [Skill Metadata] + [Full SKILL.md] + [Linked Files] + [User Message]
```

### Optimization
- Only triggered skill content loaded
- Other skills remain as metadata only
- Linked files loaded on-demand
- Scripts executed without loading into context

## Publishing and Sharing Skills

### Skill Repository Structure
```
my-skills/
├── README.md
├── context-engineering/
│   └── SKILL.md
├── testing/
│   └── SKILL.md
└── api-development/
    └── SKILL.md
```

### Documentation Template
```markdown
# Skill Name

## Description
[What this skill does]

## Installation
[How to install/activate]

## Usage
[When and how to use]

## Examples
[Real-world examples]

## Requirements
[Dependencies, prerequisites]

## Author
[Your info]

## License
[License info]
```

## Integration with Existing Setup

### With claude.md
```markdown
# In your claude.md

## Available Skills
- **Context Engineering**: Manages context, compaction, memory
- **Testing**: Guides test writing and coverage
- **Git Workflow**: Enforces commit and PR standards

## Skill Activation
Claude will automatically load skills when relevant to the current task.
```

### With Structured Notes
Skills complement your existing files:
- **claude.md**: Project-specific instructions
- **Skills**: Reusable, portable capabilities
- **progress.md**: Task tracking
- **Skills**: Domain expertise

## Testing Your Skills

### Manual Testing
1. Create skill in `skills/` directory
2. Ask Claude to perform task requiring skill
3. Observe if skill is triggered
4. Check which linked files are loaded
5. Verify outcomes

### Evaluation Checklist
- [ ] Skill triggers at appropriate times
- [ ] Metadata is clear and accurate
- [ ] SKILL.md provides sufficient guidance
- [ ] Linked files are discovered correctly
- [ ] Scripts execute successfully
- [ ] Context usage is optimized
- [ ] Task outcomes improve

## Advanced Patterns

### Multi-Language Support
```
skills/i18n/
├── SKILL.md
├── en/
│   └── strings.md
├── es/
│   └── strings.md
└── scripts/
    └── translate.py
```

### Conditional Loading
```markdown
# In SKILL.md

## Context Selection

For API testing, see [api-testing.md](api-testing.md)
For unit testing, see [unit-testing.md](unit-testing.md)
For e2e testing, see [e2e-testing.md](e2e-testing.md)
```

### Skill Composition
```markdown
# In advanced-skill/SKILL.md

This skill builds on:
- Context Engineering skill
- Testing skill
- Git Workflow skill

Make sure those are installed.
```

## Future Possibilities

### Agent-Created Skills
- Claude learns patterns during development
- Auto-generates SKILL.md from successful workflows
- Self-improves through iteration
- Codifies institutional knowledge

### Skill Marketplace
- Community-shared skills
- Version control
- Reviews and ratings
- Installation management

### Enhanced Discovery
- Automatic skill recommendation
- Usage analytics
- Performance metrics
- Smart activation

## Getting Started Checklist

- [ ] Understand progressive disclosure concept
- [ ] Identify capability gaps in current workflow
- [ ] Create first skill directory
- [ ] Write SKILL.md with metadata
- [ ] Test skill activation
- [ ] Add linked files as needed
- [ ] Include executable scripts
- [ ] Document and share
- [ ] Iterate based on usage

## Resources

- [Official Skills Documentation](https://docs.anthropic.com/claude/docs/skills)
- [Skills Cookbook](https://github.com/anthropics/anthropic-cookbook/tree/main/skills)
- Your existing `CONTEXT_ENGINEERING_GUIDE.md`
- Your existing `claude.md` setup

## Examples from This Project

Your current setup already follows Skills principles:

**Existing Structure** → **Skills Equivalent**:
- `claude.md` → Project-level skill
- `CONTEXT_ENGINEERING_GUIDE.md` → Linked reference file
- `progress.md`, `decisions.md`, `bugs.md` → External resources

**Next Step**: Formalize as official Skills for portability and reuse.
