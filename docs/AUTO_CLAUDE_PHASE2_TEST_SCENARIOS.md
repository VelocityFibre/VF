# Auto-Claude Phase 2 - Self-Healing Validation Test Scenarios

**Date**: 2025-12-22
**Phase**: Self-Healing Validation
**Purpose**: Test scenarios to validate the self-healing validation loop implementation

---

## Overview

These test scenarios validate that the enhanced `coding_agent.md` prompt correctly implements self-healing validation loops, automatically fixing common errors up to 10 times before requiring manual intervention.

---

## Test Scenario 1: Syntax Error (Should Self-Heal in 1-2 Attempts)

### Initial Implementation (Intentional Bug)

```python
# agents/test_agent/agent.py - Missing comma in tool definition

def define_tools(self) -> List[Dict[str, Any]]:
    return [
        {
            "name": "query_data"
            "description": "Query database",  # ← Missing comma after "query_data"
            "input_schema": {...}
        }
    ]
```

### Expected Self-Healing Behavior

**Attempt 1: Initial Validation**
```bash
$ ./venv/bin/python3 -c "from agents.test_agent.agent import TestAgent; ..."
SyntaxError: invalid syntax (agent.py, line 23)
```

**Attempt 2: Self-Healing Fix**
- **Analysis**: Syntax error - missing comma after string
- **Fix Strategy**: Add comma after "query_data"
- **Implementation**:
```python
{
    "name": "query_data",  # ← Added comma
    "description": "Query database",
    "input_schema": {...}
}
```
- **Re-validation**: ALL STEPS PASS ✅

**Result**: Feature validated successfully after 2 attempts

---

## Test Scenario 2: Import Error (Should Self-Heal in 1 Attempt)

### Initial Implementation (Intentional Bug)

```python
# agents/test_agent/agent.py - Missing import

import json
# Missing: from typing import List, Dict, Any

class TestAgent(BaseAgent):
    def define_tools(self) -> List[Dict[str, Any]]:  # ← List not imported
        return [...]
```

### Expected Self-Healing Behavior

**Attempt 1: Initial Validation**
```bash
NameError: name 'List' is not defined
```

**Attempt 2: Self-Healing Fix**
- **Analysis**: Import error - typing module not imported
- **Fix Strategy**: Add missing import
- **Implementation**:
```python
import json
from typing import List, Dict, Any  # ← Added
```
- **Re-validation**: ALL STEPS PASS ✅

**Result**: Feature validated successfully after 2 attempts

---

## Test Scenario 3: Logic Error (Should Self-Heal in 2-3 Attempts)

### Initial Implementation (Intentional Bug)

```python
# agents/test_agent/agent.py - Returning wrong type

def define_tools(self) -> List[Dict[str, Any]]:
    tools = [
        {"name": "query", "description": "Query data", ...}
    ]
    return tools[0]  # ← Returning dict instead of list
```

### Expected Self-Healing Behavior

**Attempt 1: Initial Validation**
```bash
AssertionError: define_tools must return list
```

**Attempt 2: Self-Healing Fix #1**
- **Analysis**: Returning single dict instead of list
- **Fix Strategy**: Return the tools list, not first element
- **Implementation**:
```python
return tools  # ← Changed from tools[0]
```
- **Re-validation**: ALL STEPS PASS ✅

**Result**: Feature validated successfully after 2 attempts

---

## Test Scenario 4: Type Mismatch (Should Self-Heal in 2-4 Attempts)

### Initial Implementation (Intentional Bug)

```python
# agents/test_agent/agent.py - None return value

def define_tools(self) -> List[Dict[str, Any]]:
    if not self.initialized:
        return None  # ← Returning None instead of empty list
    return self.tools
```

### Expected Self-Healing Behavior

**Attempt 1: Initial Validation**
```bash
TypeError: 'NoneType' object is not iterable
```

**Attempt 2: Self-Healing Fix #1**
- **Analysis**: Returning None when not initialized
- **Fix Strategy**: Return empty list instead of None
- **Implementation**:
```python
if not self.initialized:
    return []  # ← Changed from None
return self.tools
```
- **Re-validation**:
```bash
AssertionError: Must have at least one tool
```

**Attempt 3: Self-Healing Fix #2**
- **Analysis**: Empty list doesn't satisfy "at least one tool" requirement
- **Fix Strategy**: Remove early return, always return self.tools
- **Implementation**:
```python
return self.tools if hasattr(self, 'tools') else []
```
- **Re-validation**: ALL STEPS PASS ✅

**Result**: Feature validated successfully after 3 attempts

---

## Test Scenario 5: Test Assertion Failure (Should Self-Heal in 1-2 Attempts)

### Initial Implementation (Intentional Bug)

```python
# tests/test_agent.py - Wrong assertion value

@pytest.mark.unit
def test_define_tools(agent):
    tools = agent.define_tools()
    assert len(tools) == 5  # ← Wrong expected count (actual is 3)
```

### Expected Self-Healing Behavior

**Attempt 1: Initial Validation**
```bash
AssertionError: assert 3 == 5
```

**Attempt 2: Self-Healing Fix**
- **Analysis**: Test expects 5 tools but implementation has 3
- **Fix Strategy**: Either add 2 more tools OR fix assertion (context-dependent)
- **Implementation** (assuming 3 is correct):
```python
assert len(tools) == 3  # ← Fixed expected value
```
- **Re-validation**: ALL STEPS PASS ✅

**Result**: Feature validated successfully after 2 attempts

---

## Test Scenario 6: Complex Bug (Should Require Manual Intervention)

### Initial Implementation (Intentional Complex Bug)

```python
# agents/test_agent/agent.py - External dependency failure

def execute_tool(self, tool_name: str, tool_input: Dict) -> str:
    if tool_name == "query_database":
        # Assumes database connection exists
        result = self.db.query(tool_input["sql"])  # ← self.db not initialized
        return json.dumps(result)
```

### Expected Self-Healing Behavior

**Attempt 1-10**: Various fixes attempted
- Attempt 1: Add self.db initialization → Still fails (no DATABASE_URL)
- Attempt 2: Add DATABASE_URL check → Still fails (connection refused)
- Attempt 3-10: Try different connection strategies → All fail

**After 10 Attempts**: Manual intervention required

**Failure Report Generated**:
```markdown
## Validation Failure Report

**Feature**: #25 - Implement execute_tool() for database queries
**Category**: 3_tools
**Attempts**: 10 (max reached)

### Failing Validation Step

**Step 4**: Integration test for database query tool

**Error**:
```
ConnectionRefusedError: [Errno 111] Connection refused
```

### Fix Attempts Made

1. **Attempt 1**: Added self.db initialization → AttributeError: DATABASE_URL
2. **Attempt 2**: Added DATABASE_URL check → ConnectionRefusedError
3. **Attempt 3**: Changed to connection pool → ConnectionRefusedError
...
10. **Attempt 10**: Added retry logic → ConnectionRefusedError (max retries)

### Root Cause Analysis

The database integration test requires an actual PostgreSQL database connection. This cannot be fixed automatically because:
- External dependency (database server) must be running
- Environment variables must be configured
- Test may need mocking instead of real connection

Possible causes:
- Database server not running on test environment
- DATABASE_URL environment variable not set correctly
- Network/firewall blocking database connection
- Test should use mocked database instead of real connection

### Recommended Manual Fix

Option 1: Start database server
```bash
docker run -d -p 5432:5432 postgres:15
export DATABASE_URL=postgresql://localhost:5432/test
```

Option 2: Mock the database connection in tests
```python
@pytest.fixture
def mock_db(monkeypatch):
    mock = MagicMock()
    monkeypatch.setattr('agents.test_agent.agent.db', mock)
    return mock

@pytest.mark.integration
def test_execute_tool_with_mock(agent, mock_db):
    # Test with mocked database
```

### Files Involved

- agents/test_agent/agent.py (execute_tool method)
- tests/test_agent.py (integration test)
- .env (DATABASE_URL configuration)

---

**Status**: ❌ INCOMPLETE - Manual intervention required
**Preserved State**: All code changes committed to git for review
```

---

## Test Scenario 7: Edge Case - Infinite Loop Prevention

### Initial Implementation (Intentional Infinite Loop Risk)

```python
# Bug that could cause infinite loop if not careful

def define_tools(self):
    return self.get_tools()  # ← Calls another method

def get_tools(self):
    return self.define_tools()  # ← Circular reference!
```

### Expected Self-Healing Behavior

**Attempt 1**: Initial Validation
```bash
RecursionError: maximum recursion depth exceeded
```

**Attempt 2-10**: Various fixes attempted
- Each attempt hits same recursion error
- Self-healing detects repeated identical errors
- After 3 identical errors, should recognize pattern

**Smart Failure Detection**:
```
Pattern detected: Same error on 3 consecutive attempts
Error type: RecursionError
Recommendation: This likely requires structural refactoring, not simple fixes
```

**Result**: Manual intervention required after detecting repetition

---

## Success Metrics for Phase 2

### Target Metrics

| Metric | Target | Measurement Method |
|--------|--------|-------------------|
| **Completion Rate** | 90% (up from 70%) | Features with `"passes": true` / Total features |
| **First-Attempt Success** | >60% | Features passing on attempt 1 / Total features |
| **Avg Self-Healing Attempts** | <3 per feature | Sum of attempts / Features needing healing |
| **Manual Interventions** | <10% of features | Features with `"manual_review_needed": true` / Total |
| **Self-Healing Effectiveness** | >80% | Features healed / Features attempted |

### Tracking Implementation

**Enhanced feature_list.json**:
```json
{
  "id": 25,
  "category": "3_tools",
  "description": "Implement execute_tool() method",
  "validation_steps": [...],
  "passes": true,
  "validation_attempts": 3,  // ← NEW: Track attempts
  "self_healing_used": true,  // ← NEW: Flag if self-healing activated
  "manual_review_needed": false  // ← NEW: Flag if manual intervention required
}
```

**Aggregate Metrics** (in feature_list.json):
```json
{
  "total_features": 75,
  "completed": 68,
  "metrics": {
    "first_attempt_success": 45,  // 60% - MEETS TARGET
    "self_healing_used": 23,       // 31% needed healing
    "avg_attempts": 2.3,           // <3 - MEETS TARGET
    "manual_review_needed": 5,     // 7% - MEETS TARGET
    "completion_rate": 0.91        // 91% - EXCEEDS TARGET
  }
}
```

---

## Testing the Implementation

### Manual Testing Process

1. **Create Test Agent Spec**:
   ```bash
   nano harness/specs/test_selfhealing_spec.md
   ```
   - Define simple agent with 10 features
   - Intentionally introduce bugs from scenarios above

2. **Run Harness with Self-Healing Prompt**:
   ```bash
   ./harness/runner.py --agent test_selfhealing --model haiku
   ```

3. **Monitor Validation Attempts**:
   ```bash
   # Watch progress
   watch -n 10 'tail -50 harness/runs/latest/claude_progress.md'

   # Check metrics
   cat harness/runs/latest/feature_list.json | jq '.metrics'
   ```

4. **Validate Metrics**:
   - Count features that needed self-healing
   - Calculate average attempts per feature
   - Verify manual intervention rate < 10%
   - Confirm completion rate > 90%

### Automated Testing (Future Enhancement)

```python
# tests/test_self_healing_harness.py

@pytest.mark.integration
@pytest.mark.harness
def test_self_healing_syntax_errors():
    """Test that harness can heal syntax errors automatically."""
    # Create agent with intentional syntax errors
    # Run harness session
    # Assert: Feature passes after 1-2 attempts
    pass

@pytest.mark.integration
@pytest.mark.harness
def test_self_healing_import_errors():
    """Test that harness can heal import errors automatically."""
    # Create agent with missing imports
    # Run harness session
    # Assert: Feature passes after 1 attempt
    pass

@pytest.mark.integration
@pytest.mark.harness
def test_self_healing_max_attempts():
    """Test that harness stops after 10 attempts."""
    # Create agent with unfixable error (external dependency)
    # Run harness session
    # Assert: Stops at 10 attempts with failure report
    pass
```

---

## Expected Outcomes

### Before Phase 2 (Current Behavior)

```
100 features in feature_list.json
  ↓
First validation attempt: 70 pass, 30 fail
  ↓
Manual intervention needed: 30 features
  ↓
Final completion rate: 70%
Developer time: ~6 hours (30 features × 12 min each)
```

### After Phase 2 (With Self-Healing)

```
100 features in feature_list.json
  ↓
First validation attempt: 60 pass, 40 fail
  ↓
Self-healing: 30 features auto-fixed (2-3 attempts avg)
  ↓
Manual intervention needed: 10 features (complex bugs)
  ↓
Final completion rate: 90%
Developer time: ~2 hours (10 features × 12 min each)
```

**Benefit**: 4 hours saved (67% reduction in manual intervention time)

---

## Conclusion

Phase 2 self-healing validation adds significant value by:

1. **Reducing Manual Intervention**: 30 → 10 features (67% reduction)
2. **Increasing Completion Rate**: 70% → 90% (+20 percentage points)
3. **Faster Iterations**: Auto-fixes common errors without waiting for human
4. **Better Error Documentation**: Detailed reports for complex failures
5. **Learning Opportunity**: Track common error patterns for future improvements

The implementation is **prompt-only** (no code changes required), making it **low-risk** and **easy to rollback** if needed.

---

**Next Steps**:
1. Run real-world test with intentional bugs
2. Measure actual metrics vs targets
3. Refine prompt based on results
4. Proceed to Phase 3 (Parallel Execution) if Phase 2 meets targets

---

*Generated on 2025-12-22*
*Auto-Claude Integration - Phase 2*
