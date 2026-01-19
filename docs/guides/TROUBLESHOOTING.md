# Claude Code Troubleshooting Guide

Quick solutions to common issues you'll encounter with Claude Code.

---

## 🔐 Authentication & API Issues

### "Authentication failed" or "API key invalid"

**Symptoms:**
- Can't connect to Claude
- 401 Unauthorized errors
- "Invalid API key" messages

**Solutions:**
```bash
# 1. Verify API key is set
echo $ANTHROPIC_API_KEY
# or
cat .env | grep ANTHROPIC_API_KEY

# 2. Check for extra spaces/newlines
# Bad:
ANTHROPIC_API_KEY="sk-ant-xxx
"
# Good:
ANTHROPIC_API_KEY="sk-ant-xxx"

# 3. Re-export if using shell
export ANTHROPIC_API_KEY="your-key-here"

# 4. Verify key is valid on Anthropic Console
# Go to: https://console.anthropic.com/settings/keys
```

### "Rate limit exceeded"

**Temporary solution:**
```python
import time
from tenacity import retry, wait_exponential

@retry(wait=wait_exponential(multiplier=1, min=4, max=60))
def call_claude():
    # Your API call here
    pass
```

**Long-term solution:**
- Upgrade API tier
- Implement request queue
- Add caching for repeated queries

---

## 🧠 Context Window Problems

### Context immediately full (80%+ at start)

**Diagnosis:**
```bash
# Check what's being loaded
ls -lh .claude/
# Look for large files

# Check file sizes in project
du -sh * | sort -h
```

**Solutions:**

**1. Split large files:**
```bash
# Instead of one 5MB reference doc
reference.md

# Create
reference/
├── api.md
├── database.md
├── ui.md
└── deployment.md
```

**2. Use .claudeignore:**
```bash
# Create .claudeignore
cat > .claudeignore << EOF
node_modules/
dist/
build/
*.log
test-results/
coverage/
.git/
EOF
```

**3. Archive old conversations:**
```bash
mkdir -p .claude/archive/2025-11/
mv .claude/conversations/old-* .claude/archive/2025-11/
```

### "Context too long" errors mid-session

**Quick fix:**
1. `/compact` with retention instructions
2. Save important points to files
3. Start new session with saved context

**Retention template:**
```
Compact and retain:
- Architecture decisions: [list key decisions]
- Active bugs: [list from bugs.md]
- Current task context: [what we're doing now]
- User preferences: [how I like things done]

Discard:
- Completed tasks
- Failed attempts
- Debug output
- Old discussions
```

### Performance degrading (slow responses)

**Symptoms:**
- Responses taking 30s+
- Partial responses
- Timeouts

**Solutions:**
1. Check context usage: `/context`
2. If > 70%, compact immediately
3. Close unnecessary files
4. Restart Claude Code session

---

## 🤖 Agent & Subagent Issues

### Agent not being invoked automatically

**Check agent metadata:**
```markdown
---
name: Database Agent
description: Handles all database queries, migrations, and schema design
# ^ Make this SPECIFIC - Claude uses it to decide when to invoke
---
```

**Test invocation:**
```bash
# Try explicit request
"Use the Database Agent to design a schema for user preferences"

# If it works explicitly but not automatically, improve description
```

**Verify agent location:**
```bash
# Agents should be in:
.claude/agents/        # Project-specific
~/.claude/agents/      # Global

# Check they're discoverable
ls -la .claude/agents/
```

### Agent fails with "Tool not found"

**Verify tool permissions:**
```json
// In .claude/settings.json
{
  "allowed_tools": [
    "read_file",
    "write_file",
    "bash"
  ]
}
```

**Check agent has access:**
```markdown
---
name: Database Agent
description: Database operations
allowed_tools: ["read_file", "bash"]  # ← Add this
---
```

### Agents conflicting (multiple agents triggered)

**Solution: Clarify boundaries**

**Bad:**
```markdown
# Agent 1
description: Handles database operations

# Agent 2
description: Manages data operations
# ^ These overlap!
```

**Good:**
```markdown
# Agent 1
description: Handles database schema design, migrations, and SQL queries

# Agent 2
description: Handles data validation, transformation, and ETL pipelines
# ^ Clear separation
```

---

## 🎯 Skills Issues

### Skill not triggering automatically

**1. Check skill location:**
```bash
# Should be in:
.claude/skills/         # Project
~/.claude/skills/       # Global

# Verify structure:
.claude/skills/my-skill/
└── SKILL.md            # Must be named SKILL.md
```

**2. Improve metadata:**
```markdown
---
name: API Testing
description: Automatically triggered when testing APIs, validating responses, or checking endpoints
# ^ Add keywords that match usage
---
```

**3. Manual invocation:**
```bash
# Force usage to test
"Use the API Testing skill to validate this endpoint"
```

### Skill loading unnecessary files

**Use conditional references:**
```markdown
# Bad (loads everything):
See [all-the-things.md](all-the-things.md)

# Good (loads on-demand):
For REST API testing, see [rest.md](rest.md)
For GraphQL testing, see [graphql.md](graphql.md)
For authentication testing, see [auth.md](auth.md)
```

### Skills interfering with each other

**Check for overlap:**
```bash
# List all skills
ls .claude/skills/

# Review descriptions
grep -r "description:" .claude/skills/*/SKILL.md
```

**Ensure distinct purposes:**
- One skill = One specific workflow
- No overlapping domains
- Clear trigger conditions

---

## 🔌 API & MCP Integration Issues

### API calls failing

**Debug checklist:**
```python
# 1. Test API directly (without Claude)
import requests
response = requests.get("https://api.example.com/test")
print(response.status_code, response.text)

# 2. Check environment variables
import os
print(os.getenv("API_KEY"))  # Should not be None

# 3. Verify API endpoint
print(f"Calling: {API_BASE_URL}/endpoint")  # Check for typos

# 4. Check authentication
headers = {"Authorization": f"Bearer {API_KEY}"}
print(headers)  # Verify format
```

**Common fixes:**
```python
# Fix 1: Missing env vars
# Load from .env explicitly
from dotenv import load_dotenv
load_dotenv()

# Fix 2: Wrong URL format
# Bad:
url = f"{BASE_URL}/endpoint"  # BASE_URL might have trailing /
# Good:
url = f"{BASE_URL.rstrip('/')}/endpoint"

# Fix 3: Timeout
response = requests.get(url, timeout=30)  # Add explicit timeout
```

### MCP server not connecting

**1. Check MCP status:**
```bash
# If using CLI
claude-code mcp status

# Should show connected servers
```

**2. Verify installation:**
```bash
# Check MCP config
cat ~/.config/claude/mcp_servers.json

# Should contain your server config
```

**3. Test MCP independently:**
```bash
# Try the MCP directly (without Claude Code)
# Example for GitHub MCP:
curl -X POST http://localhost:3000/mcp/github/repos
```

**4. Reinstall if needed:**
```bash
# Remove and reinstall
claude-code mcp uninstall github-mcp
claude-code mcp install github-mcp
```

### "Connection timeout" with external services

**Quick fixes:**
```python
# 1. Increase timeout
requests.get(url, timeout=60)  # Default is often too short

# 2. Add retries
from tenacity import retry, stop_after_attempt

@retry(stop=stop_after_attempt(3))
def fetch_data():
    return requests.get(url, timeout=30)

# 3. Check network
import socket
try:
    socket.create_connection(("api.example.com", 443), timeout=5)
    print("Network OK")
except OSError:
    print("Network issue")
```

---

## 📁 File & Project Structure Issues

### Claude can't find files

**Check file paths:**
```bash
# Claude uses absolute paths from project root
# Bad:
Read: ../other-project/file.md

# Good:
Read: /home/user/projects/main/docs/file.md
```

**Verify project root:**
```bash
# Claude should start from project root
cd /path/to/your/project
claude-code  # Launch from here
```

**Use relative paths consistently:**
```markdown
# In claude.md
Reference documentation: [API Docs](./docs/api.md)
Database schema: [Schema](./docs/database.md)
# ^ Start with ./ for clarity
```

### "Permission denied" errors

**Check file permissions:**
```bash
# See what's wrong
ls -la file.txt

# Fix read permissions
chmod +r file.txt

# Fix write permissions
chmod +w file.txt

# Fix execute permissions (scripts)
chmod +x script.sh
```

**Check directory permissions:**
```bash
# Can't create files in directory
chmod +w directory/

# Can't read directory contents
chmod +r directory/
```

### Git conflicts with .claude/ files

**Recommended .gitignore:**
```bash
# Add to .gitignore
.claude/conversations/
.claude/cache/
.claude/.settings.local.json
.claude/logs/

# Keep in git:
.claude/claude.md
.claude/agents/
.claude/skills/
.claude/commands/
```

---

## 🐛 Execution & Runtime Errors

### "Command not found" in bash tool

**Solutions:**
```bash
# 1. Use full path
/usr/bin/python3 script.py
# Instead of: python3 script.py

# 2. Check PATH
echo $PATH

# 3. Activate venv if needed
source venv/bin/activate && python script.py
```

### Python import errors

**Fix 1: Virtual environment not activated**
```bash
# Activate first
source venv/bin/activate

# Then run
python script.py
```

**Fix 2: Missing dependencies**
```bash
# Install missing package
pip install package-name

# Or from requirements
pip install -r requirements.txt
```

**Fix 3: PYTHONPATH issues**
```bash
# Add project to path
export PYTHONPATH="${PYTHONPATH}:/path/to/project"

# Or in code:
import sys
sys.path.insert(0, '/path/to/project')
```

### Database connection failures

**Diagnosis:**
```python
# Test connection separately
import psycopg2  # or your DB library

try:
    conn = psycopg2.connect(DATABASE_URL)
    print("Connection successful")
except Exception as e:
    print(f"Connection failed: {e}")
```

**Common fixes:**
```python
# Fix 1: Connection pool exhausted
# Use connection pooling
from psycopg2 import pool
connection_pool = pool.SimpleConnectionPool(1, 20, DATABASE_URL)

# Fix 2: Timeout too short
conn = psycopg2.connect(DATABASE_URL, connect_timeout=10)

# Fix 3: SSL required
conn = psycopg2.connect(DATABASE_URL, sslmode='require')
```

---

## 🔄 Parallel Execution Issues

### Agents stepping on each other

**Symptom:** Two agents editing same file simultaneously

**Solution: Use file locks**
```python
import fcntl

def safe_file_operation():
    with open('shared.txt', 'r+') as f:
        fcntl.flock(f.fileno(), fcntl.LOCK_EX)
        try:
            # Your operation
            data = f.read()
            # Process...
            f.write(new_data)
        finally:
            fcntl.flock(f.fileno(), fcntl.LOCK_UN)
```

**Solution: Separate concerns**
```markdown
# Agent 1: Database writes
description: Handles all database INSERT, UPDATE, DELETE operations

# Agent 2: Database reads
description: Handles all database SELECT queries and reports
# ^ Can run in parallel safely
```

### Race conditions in workflows

**Add synchronization:**
```python
import threading

lock = threading.Lock()

def critical_section():
    with lock:
        # Only one agent at a time
        perform_operation()
```

**Use message queues:**
```python
from queue import Queue

task_queue = Queue()

# Agent 1 adds tasks
task_queue.put(task)

# Agent 2 processes
task = task_queue.get()
```

---

## 💾 Memory & Performance Issues

### Claude Code using too much RAM

**Check usage:**
```bash
# On Linux
ps aux | grep claude-code

# On macOS
top -pid $(pgrep claude-code)
```

**Solutions:**
1. Restart Claude Code session
2. Close unused projects
3. Compact context more frequently
4. Reduce parallel agents

### Slow response times

**Diagnosis checklist:**
- [ ] Context > 70%? → Compact
- [ ] Large files in context? → Split them
- [ ] Many agents loaded? → Reduce
- [ ] External API slow? → Add caching
- [ ] Network issues? → Check connection

**Add caching:**
```python
from functools import lru_cache

@lru_cache(maxsize=100)
def expensive_operation(param):
    # Cached result
    return result
```

---

## 🎨 UI & Display Issues

### Output formatting broken

**Check terminal:**
```bash
# Verify terminal supports formatting
echo $TERM

# Should be: xterm-256color or similar
```

**Fix color issues:**
```bash
# Enable colors explicitly
export CLICOLOR=1
export TERM=xterm-256color
```

### Long outputs truncated

**Solution:**
```bash
# Redirect to file for review
claude-code > output.log 2>&1

# Or use less
claude-code | less
```

---

## 🚨 Emergency Recovery

### Everything is broken

**Nuclear option - start fresh:**
```bash
# 1. Backup current state
cp -r .claude/ .claude.backup/

# 2. Remove config
rm -rf .claude/

# 3. Reinitialize
claude-code init

# 4. Restore what you need
cp .claude.backup/claude.md .claude/
cp -r .claude.backup/skills/ .claude/
```

### Lost important context

**Check conversation history:**
```bash
# Find recent sessions
ls -lt .claude/conversations/

# Read the one you need
cat .claude/conversations/session-2025-11-11.json
```

**Check Git history:**
```bash
# See recent changes
git log --oneline --since="2 days ago"

# Recover deleted file
git checkout HEAD~1 -- file.md
```

### Corrupted settings

**Reset to defaults:**
```bash
# Remove corrupted file
rm .claude/settings.json

# Claude Code will regenerate on next start
```

---

## 📞 Getting Help

### Before asking for help, collect:

```markdown
1. **What I tried to do:**
   [Clear description]

2. **Expected result:**
   [What should have happened]

3. **Actual result:**
   [What actually happened]

4. **Error messages:**
   ```
   [Full error text]
   ```

5. **Environment:**
   - Claude Code version: [version]
   - OS: [Linux/macOS/Windows]
   - Python version: [if relevant]
   - Node version: [if relevant]

6. **Relevant files:**
   - claude.md
   - settings.json
   - [any other config]

7. **What I've tried:**
   - [List debugging steps]
```

### Useful diagnostic commands

```bash
# System info
uname -a

# Claude Code version
claude-code --version

# Check environment
env | grep -E "(ANTHROPIC|CLAUDE|API)"

# Check file structure
tree -L 2 .claude/

# Check logs
tail -n 100 .claude/logs/latest.log
```

---

## 🎓 Prevention > Cure

**Daily habits to avoid issues:**
- Check context at session start
- Compact before major work
- Commit to Git regularly
- Test integrations in isolation
- Review agent logs weekly

**Weekly maintenance:**
- Audit claude.md for accuracy
- Clean up unused skills/agents
- Update dependencies
- Check disk space
- Review error logs

**Monthly review:**
- Evaluate agent effectiveness
- Refactor project structure
- Update documentation
- Security audit (API keys, permissions)
- Backup important data

---

**Remember:** Most issues are fixable with simple restarts, permission fixes, or clarifying instructions. Start with the simple solutions before diving deep.
