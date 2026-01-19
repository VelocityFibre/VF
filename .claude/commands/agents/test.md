---
description: Run tests for a specific agent
argument-hint: [agent-name]
---

# Agent Test Runner

Run pytest tests for the **$ARGUMENTS** agent with detailed output.

## Test Execution

Execute the following command:

```bash
./venv/bin/pytest tests/test_$ARGUMENTS.py -v --tb=short
```

## Analysis Requirements

After running tests:

1. **If tests pass**:
   - Report number of tests passed
   - Show execution time
   - Highlight any warnings
   - Confirm agent is production-ready

2. **If tests fail**:
   - Analyze each failure
   - Identify root cause
   - Suggest specific fixes with code examples
   - Prioritize by severity: 🔴 Critical, 🟡 Important, 🟢 Minor

3. **Coverage Analysis**:
   - Check test coverage for the agent
   - Identify untested code paths
   - Suggest additional test cases if needed

## Output Format

```markdown
## Test Results: $ARGUMENTS Agent

**Status**: ✅ PASSED / ❌ FAILED
**Tests**: X passed, Y failed, Z warnings
**Duration**: X.XXs

### Details
[Test output summary]

### Issues Found (if any)
🔴 [Critical issue with fix]
🟡 [Important issue with fix]

### Recommendations
- [Specific action items]
```

## Context

FibreFlow uses pytest with custom markers:
- `@pytest.mark.unit` - Fast, isolated tests
- `@pytest.mark.integration` - Slower, external resources
- `@pytest.mark.vps` - VPS Monitor agent tests
- `@pytest.mark.database` - Database agent tests
- `@pytest.mark.orchestrator` - Orchestrator tests

Test files follow pattern: `tests/test_{agent_name}.py`
