---
description: Security and performance review of recent code changes
---

# Code Review: Security & Performance

Comprehensive code review focusing on security vulnerabilities, performance optimizations, and best practices.

## Review Scope

Analyze recent code changes for:
1. **Security Issues** - Vulnerabilities and exposures
2. **Performance Problems** - Inefficiencies and bottlenecks
3. **Error Handling** - Robustness and reliability
4. **Code Quality** - Best practices and maintainability

## Step 1: Identify Recent Changes

```bash
# Show recent changes
git diff HEAD~5..HEAD

# Or compare to main branch
git diff main...HEAD

# Show changed files
git diff --name-only HEAD~5..HEAD
```

List files that changed:
- Python files (`.py`)
- Configuration files (`.env.example`, `.json`)
- Documentation (`.md`)

## Step 2: Security Review

### Critical Security Checks

#### 🔴 SQL Injection
**Check for**: Direct string concatenation in SQL queries

**Bad**:
```python
query = f"SELECT * FROM users WHERE id = {user_id}"  # VULNERABLE
cursor.execute(query)
```

**Good**:
```python
query = "SELECT * FROM users WHERE id = %s"  # SAFE
cursor.execute(query, (user_id,))
```

**Action**: Search for SQL queries and verify parameterization

#### 🔴 Hardcoded Secrets
**Check for**: API keys, passwords, tokens in code

**Bad**:
```python
API_KEY = "sk-ant-api03-xxx"  # EXPOSED
DATABASE_URL = "postgresql://user:pass@host/db"  # EXPOSED
```

**Good**:
```python
API_KEY = os.getenv("ANTHROPIC_API_KEY")  # SAFE
DATABASE_URL = os.getenv("NEON_DATABASE_URL")  # SAFE
```

**Action**: Search for patterns like `sk-`, `postgres://`, `api_key =`

#### 🔴 Path Traversal
**Check for**: User input used in file paths without validation

**Bad**:
```python
file_path = f"/data/{user_input}.json"  # VULNERABLE
with open(file_path) as f:
```

**Good**:
```python
# Validate and sanitize
file_path = os.path.join("/data", os.path.basename(user_input))
if not file_path.startswith("/data/"):
    raise ValueError("Invalid path")
```

#### 🔴 Command Injection
**Check for**: User input in shell commands

**Bad**:
```python
os.system(f"ls {user_dir}")  # VULNERABLE
subprocess.run(f"grep {pattern} file.txt", shell=True)  # VULNERABLE
```

**Good**:
```python
subprocess.run(["ls", user_dir])  # SAFE
subprocess.run(["grep", pattern, "file.txt"])  # SAFE
```

#### 🟡 Authentication/Authorization
**Check for**:
- Missing authentication checks
- Overly permissive access controls
- Weak session management

**Review**:
- API endpoints have authentication
- Role-based access control implemented
- Tokens expire appropriately

#### 🟡 Input Validation
**Check for**: Unvalidated user input

**Good practices**:
```python
def validate_contractor_id(contractor_id: str) -> bool:
    if not contractor_id:
        raise ValueError("Contractor ID required")
    if not contractor_id.isalnum():
        raise ValueError("Invalid contractor ID format")
    if len(contractor_id) > 50:
        raise ValueError("Contractor ID too long")
    return True
```

#### 🟡 Error Information Disclosure
**Check for**: Detailed error messages exposed to users

**Bad**:
```python
except Exception as e:
    return f"Database error: {str(e)}"  # Exposes internal details
```

**Good**:
```python
except Exception as e:
    logger.error(f"Database error: {str(e)}")  # Log internally
    return "An error occurred. Please contact support."  # Generic user message
```

### Security Checklist

- [ ] No SQL injection vulnerabilities (parameterized queries)
- [ ] No hardcoded secrets (use environment variables)
- [ ] No command injection (use subprocess.run with list)
- [ ] No path traversal (validate file paths)
- [ ] Authentication implemented where needed
- [ ] Input validation on all user input
- [ ] Error messages don't expose internal details
- [ ] CORS configured appropriately
- [ ] Rate limiting on API endpoints (if applicable)
- [ ] Sensitive data encrypted (if applicable)

## Step 3: Performance Review

### Database Performance

#### 🔴 N+1 Query Problem
**Check for**: Loops that make repeated database queries

**Bad**:
```python
contractors = get_all_contractors()
for contractor in contractors:
    projects = get_projects_by_contractor(contractor.id)  # N+1!
```

**Good**:
```python
# Use JOIN or eager loading
contractors_with_projects = db.query("""
    SELECT c.*, p.*
    FROM contractors c
    LEFT JOIN projects p ON c.id = p.contractor_id
""")
```

#### 🔴 Missing Database Indexes
**Check for**: Frequent WHERE/JOIN on unindexed columns

**Review**:
```sql
-- Check if frequently queried columns have indexes
EXPLAIN ANALYZE SELECT * FROM contractors WHERE email = 'test@example.com';
```

**Fix**: Add indexes for frequently queried columns

#### 🟡 Large Result Sets
**Check for**: Queries without LIMIT that could return millions of rows

**Bad**:
```python
results = db.query("SELECT * FROM logs")  # Could be huge!
```

**Good**:
```python
results = db.query("SELECT * FROM logs ORDER BY created_at DESC LIMIT 100")
```

#### 🟡 Connection Pooling
**Check for**: Opening new connections for each query

**Good practice**:
```python
# Use connection pooling
from psycopg2 import pool
connection_pool = pool.SimpleConnectionPool(1, 20, DATABASE_URL)
```

### Application Performance

#### 🔴 Memory Leaks
**Check for**:
- Unclosed files, connections
- Growing lists/dicts in long-running processes
- Circular references

**Good practices**:
```python
# Use context managers
with open(file_path) as f:
    data = f.read()

# Close connections explicitly
try:
    conn = psycopg2.connect(DATABASE_URL)
    # ... use connection
finally:
    conn.close()
```

#### 🟡 Inefficient Loops
**Check for**: Nested loops, repeated computations

**Bad**:
```python
for user in users:
    for project in projects:  # O(n²)
        if user.id == project.owner_id:
            # ...
```

**Good**:
```python
# Use dictionary lookup
project_map = {p.owner_id: p for p in projects}  # O(n)
for user in users:
    project = project_map.get(user.id)
```

#### 🟡 Unnecessary API Calls
**Check for**: Repeated calls to external APIs for same data

**Good practice**:
```python
# Cache API responses
from functools import lru_cache

@lru_cache(maxsize=100)
def get_external_data(key):
    return requests.get(f"https://api.example.com/{key}").json()
```

### Performance Checklist

- [ ] No N+1 query problems
- [ ] Database indexes on frequently queried columns
- [ ] Query result limits to prevent large datasets
- [ ] Connection pooling implemented
- [ ] No memory leaks (files/connections closed)
- [ ] Efficient algorithms (avoid O(n²) when possible)
- [ ] API responses cached where appropriate
- [ ] Async/await used for I/O operations
- [ ] No blocking calls in event loops

## Step 4: Error Handling Review

### Error Handling Best Practices

#### 🔴 Bare Except Clauses
**Check for**: Catching all exceptions

**Bad**:
```python
try:
    result = do_something()
except:  # BAD - catches everything including KeyboardInterrupt
    pass
```

**Good**:
```python
try:
    result = do_something()
except ValueError as e:  # Specific exception
    logger.error(f"Invalid value: {e}")
    raise
except DatabaseError as e:
    logger.error(f"Database error: {e}")
    return None
```

#### 🟡 Silent Failures
**Check for**: Exceptions caught but not logged

**Bad**:
```python
try:
    send_notification(user)
except:
    pass  # Silent failure - no one knows it failed!
```

**Good**:
```python
try:
    send_notification(user)
except NotificationError as e:
    logger.error(f"Failed to notify {user.id}: {e}")
    # Maybe retry or alert admin
```

#### 🟡 Transaction Handling
**Check for**: Database transactions not rolled back on error

**Good**:
```python
conn = psycopg2.connect(DATABASE_URL)
try:
    cursor = conn.cursor()
    cursor.execute("INSERT INTO ...")
    cursor.execute("UPDATE ...")
    conn.commit()
except Exception as e:
    conn.rollback()  # IMPORTANT
    logger.error(f"Transaction failed: {e}")
    raise
finally:
    conn.close()
```

### Error Handling Checklist

- [ ] Specific exceptions caught (not bare `except:`)
- [ ] Errors logged appropriately
- [ ] No silent failures
- [ ] Database transactions rolled back on error
- [ ] User-friendly error messages
- [ ] Critical errors alerting admins
- [ ] Retry logic for transient failures

## Step 5: Code Quality Review

### Python Best Practices

#### Type Hints
**Check for**: Missing type annotations

**Good**:
```python
def get_contractor(contractor_id: str) -> Optional[Dict[str, Any]]:
    """Get contractor by ID."""
    # Implementation
```

#### Docstrings
**Check for**: Missing or inadequate documentation

**Good**:
```python
def calculate_project_cost(project_id: str, include_tax: bool = True) -> float:
    """
    Calculate total cost for a project.

    Args:
        project_id: Unique project identifier
        include_tax: Whether to include tax in calculation

    Returns:
        Total project cost in USD

    Raises:
        ValueError: If project_id not found
        DatabaseError: If database query fails
    """
```

#### Code Complexity
**Check for**: Long functions, deep nesting

**Bad signs**:
- Functions >50 lines
- Nesting >3 levels deep
- Cyclomatic complexity >10

**Fix**: Break into smaller functions

### Code Quality Checklist

- [ ] Type hints on function signatures
- [ ] Docstrings on all public functions/classes
- [ ] Functions are focused (single responsibility)
- [ ] No commented-out code
- [ ] No debug print statements
- [ ] Consistent naming conventions
- [ ] DRY principle followed (no repeated code)
- [ ] Magic numbers extracted to constants

## Review Report Format

```markdown
## Code Review Report
**Date**: [YYYY-MM-DD]
**Reviewer**: Claude Code Review
**Files Reviewed**: [Count]
**Lines Changed**: +XXX -XXX

---

### Overall Assessment: ✅ APPROVED / ⚠️ NEEDS WORK / 🔴 CRITICAL ISSUES

---

### Security Issues

#### 🔴 Critical (MUST FIX)
1. **SQL Injection in neon_agent.py:156**
   - **Issue**: Direct string interpolation in SQL query
   - **Risk**: HIGH - Database compromise
   - **Fix**:
   ```python
   # Change from:
   query = f"SELECT * FROM contractors WHERE name = '{name}'"
   # To:
   query = "SELECT * FROM contractors WHERE name = %s"
   cursor.execute(query, (name,))
   ```

#### 🟡 Warnings (Should Fix)
1. **Missing input validation in api.py:45**
   - **Issue**: User input not sanitized
   - **Risk**: MEDIUM
   - **Fix**: Add input validation

#### ✅ Good Practices Found
- All API keys using environment variables
- Parameterized queries in database agent
- Error messages don't expose internals

---

### Performance Issues

#### 🔴 Critical
1. **N+1 Query in orchestrator.py:89**
   - **Issue**: Loading projects in loop
   - **Impact**: HIGH - Slow for large datasets
   - **Fix**: Use JOIN or batch loading

#### 🟡 Optimizations
1. **Missing database index**
   - **Table**: contractors
   - **Column**: email (frequently queried)
   - **Fix**: `CREATE INDEX idx_contractors_email ON contractors(email);`

#### ✅ Good Practices Found
- Connection pooling implemented
- Query results limited with LIMIT clause
- Async/await used for I/O

---

### Error Handling Issues

#### 🟡 Improvements Needed
1. **Bare except in sync_script.py:123**
   - **Fix**: Use specific exception types

2. **Silent failure in notification.py:67**
   - **Fix**: Add logging

#### ✅ Good Practices Found
- Database transactions properly handled
- Errors logged with context
- Retry logic for external APIs

---

### Code Quality

#### 🟡 Improvements
1. **Missing type hints in utility.py**
2. **Long function in processor.py:200** (85 lines - should split)
3. **Magic number in calculation.py:45** (extract to constant)

#### ✅ Good Practices Found
- Comprehensive docstrings
- Consistent naming conventions
- No commented-out code

---

### Test Coverage

**Files Changed**: [List]
**Test Coverage**:
- ✅ `neon_agent.py`: Tests exist, all passing
- ⚠️ `new_module.py`: No tests yet - ADD TESTS
- ✅ `orchestrator.py`: Tests updated

**Recommendation**: Add tests for `new_module.py` before deployment

---

### Summary by Priority

#### 🔴 Must Fix Before Deployment (Blockers)
1. SQL injection in neon_agent.py:156
2. N+1 query in orchestrator.py:89

#### 🟡 Should Fix Soon (Technical Debt)
1. Add input validation in api.py:45
2. Add database index on contractors.email
3. Fix bare except clauses
4. Add type hints

#### 🟢 Nice to Have (Improvements)
1. Split long functions
2. Extract magic numbers
3. Improve test coverage

---

### Deployment Recommendation

**Status**: ❌ NOT READY / ⚠️ READY WITH CAVEATS / ✅ READY

[If blockers exist:]
**Blockers**: 2 critical issues must be fixed first
- Fix SQL injection
- Fix N+1 query
Then re-run `/code-review`

[If only warnings:]
**Recommendation**: Address warnings before deployment, but not blocking

[If all good:]
**Recommendation**: ✅ Code quality acceptable for deployment
- No critical security issues
- No critical performance problems
- Error handling adequate
- Consider addressing warnings in next sprint

---

### Files Reviewed

| File | Security | Performance | Errors | Quality | Notes |
|------|----------|-------------|--------|---------|-------|
| neon_agent.py | 🔴 Issues | ✅ Good | ✅ Good | ✅ Good | Fix SQL injection |
| orchestrator.py | ✅ Good | 🔴 N+1 | ✅ Good | ⚠️ Long func | Fix N+1 query |
| api.py | ⚠️ Validation | ✅ Good | ✅ Good | ✅ Good | Add validation |

---

### Recommendations

1. **Immediate**: Fix critical security and performance issues
2. **Short-term**: Add missing tests, address warnings
3. **Long-term**: Improve code quality metrics, increase coverage

### Next Steps
- [ ] Fix critical issues
- [ ] Re-run `/code-review`
- [ ] Run `/test-all` to verify fixes
- [ ] Ready for deployment after all critical issues resolved
```

## Integration with Workflow

### Pre-Deployment Workflow
```bash
# Standard pre-deployment checks
/code-review       # Security & performance review
/test-all          # Run all tests
/deploy agent-name # Deploy if all pass
```

### During Development
```bash
# After making changes
git add .
git commit -m "Feature: ..."
/code-review       # Check quality before pushing
```

### Code Review Automation
Can be integrated into git hooks:
```bash
# .git/hooks/pre-commit
#!/bin/bash
# Run code review on changed files
/code-review
```

## Success Criteria

Code review is complete when:
- ✅ All files analyzed
- ✅ Security issues identified and categorized
- ✅ Performance problems noted
- ✅ Error handling reviewed
- ✅ Code quality assessed
- ✅ Clear recommendations provided
- ✅ Deployment readiness determined
