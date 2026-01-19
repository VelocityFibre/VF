# Context Engineering Implementation Guide

This guide shows you how to implement the context engineering techniques from Anthropic's paper to maximize Claude Code's effectiveness.

---

## 1. Compaction Strategy

### When to Compact
- **Don't wait for auto-compact** (triggers at ~92% context usage)
- **Manually compact at 60-70%** context usage
- **Before starting major new features**
- **After completing significant milestones**

### How to Compact
```bash
# Check current context usage
/context

# Manual compaction with custom instructions
/compact

# Optional: Add retention instructions when prompted
"Remember all architectural decisions, current bugs, and the user's preference for TypeScript over JavaScript"
```

### Best Practices
- Monitor context with `/context` command regularly
- Compact proactively, not reactively
- Specify what to retain in compaction instructions
- Use compaction as a natural breakpoint between work sessions

---

## 2. Memory Tool Usage

### Save Important Instructions
Use the `#` command to persist instructions across sessions:

```bash
# Example memory commands
# Always check context before new tasks
# Use TypeScript for all new components
# Follow the project's established naming conventions
```

### What to Save in Memory
- **Coding preferences** (style, patterns, libraries)
- **Project constraints** (framework versions, compatibility requirements)
- **Workflow rules** (testing requirements, commit conventions)
- **User preferences** (verbosity level, explanation style)

### Memory Types
- **Project Memory**: Shared across all sessions in this project
- **Session Memory**: Temporary, cleared after session ends
- **Global Memory**: Applies to all Claude Code sessions

---

## 3. claude.md File Structure

### Location
Place `claude.md` in your project root directory.

### Recommended Sections

```markdown
# Project Name

## Overview
Brief description of what the project does and its purpose.

## Tech Stack
- Frontend: React 18, TypeScript, Tailwind CSS
- Backend: Node.js, Express, PostgreSQL
- Testing: Jest, React Testing Library

## Architecture
High-level architecture decisions and patterns used.

## Development Guidelines
### Code Style
- Use functional components with hooks
- Prefer named exports over default exports
- Keep components under 200 lines

### Testing Requirements
- Write unit tests for all utilities
- Integration tests for API endpoints
- Minimum 80% code coverage

### Naming Conventions
- Components: PascalCase
- Utilities: camelCase
- Constants: UPPER_SNAKE_CASE

## Key Features
List of main features and their locations in codebase.

## Known Issues
Current bugs and workarounds.

## Next Steps
Planned features and improvements.
```

---

## 4. Structured Note-Taking

### File System
Create these files in your project root or `.claude/` directory:

#### `progress.md`
```markdown
# Project Progress

## Completed
- [x] Initial project setup
- [x] Authentication system
- [x] User dashboard

## In Progress
- [ ] Payment integration (70% complete)

## Next Steps
- [ ] Email notification system
- [ ] Admin panel
- [ ] Performance optimization
```

#### `decisions.md`
```markdown
# Architectural Decisions

## 2025-10-21: Chose PostgreSQL over MongoDB
**Reason**: Need for complex relational queries and ACID compliance.
**Impact**: Required migration scripts, better data integrity.

## 2025-10-15: Implemented JWT authentication
**Reason**: Stateless auth for microservices architecture.
**Impact**: Added refresh token logic, 7-day expiration.
```

#### `bugs.md`
```markdown
# Known Bugs and Issues

## Active Bugs
### Bug #1: Login timeout on slow connections
- **Severity**: Medium
- **Reproduction**: Login on 3G connection
- **Workaround**: Increase timeout to 10s
- **Status**: Investigating

## Resolved Bugs
### Bug #5: Memory leak in WebSocket connection
- **Resolution**: Added proper cleanup in useEffect
- **Resolved**: 2025-10-18
- **Commit**: abc123f
```

### Automate Updates
Add to memory or claude.md:
```markdown
## Instructions for Claude
- Update progress.md after completing each task
- Document all architectural decisions in decisions.md
- Log bugs in bugs.md when discovered
- Reference past decisions before making new ones
```

---

## 5. Sub-Agent Architecture

### When to Use
- **Complex projects** with distinct domains (frontend, backend, database)
- **Large refactoring** across multiple systems
- **Specialized tasks** requiring different expertise

### Implementation Options

#### Option 1: Use Existing Framework
- [Claude Multi-Agent Framework](https://github.com/example/claude-agents)
- Install and configure with your agents

#### Option 2: Custom Agent Setup
Define agents in your claude.md:

```markdown
## Agent Architecture

### Lead Agent (Coordinator)
- Analyzes user requests
- Delegates to specialist agents
- Combines results

### Frontend Agent
- Tools: React, CSS, UI libraries
- Focus: Component design, user experience
- Context: Frontend codebase only

### Backend Agent
- Tools: Node.js, database, APIs
- Focus: Server logic, data models
- Context: Backend codebase only

### DevOps Agent
- Tools: Docker, CI/CD, deployment
- Focus: Infrastructure, deployment
- Context: Config files, scripts
```

### Trade-offs
**Pros**:
- Isolated contexts per domain
- Specialized expertise
- Better for large projects

**Cons**:
- More complex coordination
- Slower for simple tasks
- Requires careful setup

---

## Quick Start Checklist

- [ ] Create `claude.md` in project root
- [ ] Set up structured note files (`progress.md`, `decisions.md`, `bugs.md`)
- [ ] Save common instructions to memory using `#` command
- [ ] Set context monitoring habit (check at `/context` regularly)
- [ ] Establish compaction schedule (at 60-70% context)
- [ ] (Optional) Design sub-agent architecture for complex projects

---

## Example Workflow

### Starting a New Session
1. Claude reads `claude.md` automatically
2. Check `/context` to see available space
3. Review `progress.md` for last known state
4. Begin work with full project context

### During Development
1. Claude updates `progress.md` after each task
2. Documents decisions in `decisions.md`
3. Logs bugs in `bugs.md`
4. Monitors context usage

### Before Major Changes
1. Run `/compact` with retention instructions
2. Update `claude.md` with new guidelines
3. Review `decisions.md` for consistency
4. Clear completed items from `progress.md`

---

## Context Usage Tips

### High Context Consumption
- Long conversations with many tool calls
- Large file reads
- Multiple MCP servers active

### Reduce Context
- Use file references instead of reading full files
- Compact proactively
- Use structured notes for persistence
- Enable context editing (auto-enabled in Sonnet 4.5)

### Optimal Context
- Keep context at 40-60% during active development
- Reserve space for tool outputs and responses
- Compact before starting new features
- Use memory for long-term storage, context for short-term work

---

## Advanced Techniques

### Custom Compaction Instructions Template
```
Retain:
- All architectural decisions from the past 3 tasks
- Current bugs and their workarounds
- User preferences for code style
- The current implementation approach for [feature name]

Discard:
- Exploratory code that was not used
- Failed attempts and debugging output
- Completed tasks from progress.md
```

### Memory Instruction Template
```
# Project-Specific Rules
- Always run tests before marking tasks complete
- Update progress.md after each completed task
- Check context usage before starting new features
- Document breaking changes in decisions.md
- Use semantic commit messages
```

### Periodic Maintenance
- **Weekly**: Review and update claude.md
- **After major features**: Update decisions.md
- **When bugs fixed**: Move from bugs.md to resolved section
- **Monthly**: Archive old progress entries

---

## Measuring Success

You'll know context engineering is working when:
- ✅ Claude rarely auto-compacts unexpectedly
- ✅ New sessions start with full project understanding
- ✅ Less repetition of instructions across sessions
- ✅ Better consistency in code patterns
- ✅ Fewer hallucinations and context loss
- ✅ Faster task completion with better quality

---

## Resources

- [Anthropic's Context Engineering Paper](https://www.anthropic.com/research/context-engineering)
- [Claude Code Documentation](https://docs.claude.com/claude-code)
- [Multi-Agent Frameworks](https://github.com/search?q=claude+multi+agent)
