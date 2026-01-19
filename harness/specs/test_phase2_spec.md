# Test Agent for Phase 2 Self-Healing Validation

**Agent Name**: TestPhase2
**Type**: Test Agent
**Purpose**: Validate Phase 2 self-healing validation loop implementation

---

## Purpose

This is a minimal test agent designed to validate the Auto-Claude Phase 2 self-healing validation enhancements. It contains intentionally simple features that will have bugs introduced to test the self-healing loop.

---

## Capabilities

1. **Data Storage** - Store and retrieve simple key-value data
2. **Data Validation** - Validate data types and values
3. **Data Transformation** - Transform data between formats

---

## Tools

### 1. store_data

Store a key-value pair in memory.

**Parameters**:
- `key` (string, required) - The key to store
- `value` (string, required) - The value to store

**Returns**:
```json
{
  "status": "success",
  "key": "example",
  "message": "Data stored successfully"
}
```

### 2. retrieve_data

Retrieve a value by key.

**Parameters**:
- `key` (string, required) - The key to retrieve

**Returns**:
```json
{
  "status": "success",
  "key": "example",
  "value": "stored_value"
}
```

**OR** (if key not found):
```json
{
  "status": "error",
  "message": "Key not found"
}
```

### 3. validate_data

Validate that data meets criteria.

**Parameters**:
- `value` (string, required) - The value to validate
- `criteria` (string, required) - The validation criteria ("email", "phone", "number")

**Returns**:
```json
{
  "status": "success",
  "valid": true,
  "criteria": "email"
}
```

---

## Success Criteria

**Agent is complete when**:
- ✅ All 3 tools implemented
- ✅ BaseAgent inheritance working
- ✅ System prompt defined
- ✅ All tests passing
- ✅ Basic documentation complete
- ✅ Demo script functional

**Total Features**: ~10 features (small test agent)

**Expected Bugs** (for Phase 2 testing):
- 2 syntax errors (missing commas, colons)
- 2 import errors (missing typing imports)
- 2 logic errors (wrong return types)
- 1 type error (None handling)
- 3 features should pass first attempt

**Target Metrics**:
- Completion rate: 100% (all bugs should self-heal)
- Self-healing effectiveness: 70% (7/10 features need healing)
- Avg attempts: 2.0 (syntax/import = 1-2, logic = 2-3)
- Manual interventions: 0 (all bugs are fixable)

---

## Integration

**Orchestrator Triggers**: test, phase2, validation, self-healing, test_agent

**Environment Variables**: None (test agent, no external dependencies)

**Dependencies**: None (pure Python, no external services)

---

*Test Agent for Auto-Claude Phase 2 Validation*
*2025-12-22*
