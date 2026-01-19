#!/bin/bash
# /tdd spec <feature-name>
# Creates a test specification for a new feature

FEATURE_NAME="$1"

if [ -z "$FEATURE_NAME" ]; then
    echo "❌ Usage: /tdd spec <feature-name>"
    echo "Example: /tdd spec contractor-approval"
    exit 1
fi

SPEC_FILE="tests/specs/${FEATURE_NAME}.spec.md"

# Create specs directory if it doesn't exist
mkdir -p tests/specs

# Check if spec already exists
if [ -f "$SPEC_FILE" ]; then
    echo "⚠️  Spec already exists: $SPEC_FILE"
    echo "Opening in editor..."
    ${EDITOR:-nano} "$SPEC_FILE"
    exit 0
fi

# Create spec from template
cat > "$SPEC_FILE" << 'EOF'
# Feature: [Feature Name]

**Author**: [Your Name]
**Date**: [YYYY-MM-DD]
**Module**: [Module name from .claude/modules/_index.yaml]
**Isolation Level**: [fully_isolated / mostly_isolated / tightly_coupled]

---

## Overview

Brief description of the feature and its purpose.

## Requirements

- [ ] Requirement 1
- [ ] Requirement 2
- [ ] Requirement 3

## Test Cases

### Unit Tests

| ID | Description | Input | Expected Output | Priority |
|----|-------------|-------|-----------------|----------|
| U1 | Test case 1 | {...} | {...} | High |
| U2 | Test case 2 | {...} | {...} | Medium |

### Integration Tests

| ID | Description | Setup | Steps | Expected | Priority |
|----|-------------|-------|-------|----------|----------|
| I1 | Test case 1 | Setup DB | 1. Do X<br>2. Do Y | Result | High |

### E2E Tests (if applicable)

| ID | User Flow | Steps | Expected Outcome | Priority |
|----|-----------|-------|------------------|----------|
| E1 | User creates X | 1. Login<br>2. Navigate<br>3. Submit | X is created | High |

## Edge Cases

- Edge case 1: Description and how to handle
- Edge case 2: Description and how to handle

## Database Changes

### New Tables
```sql
-- If creating new tables
CREATE TABLE example (...);
```

### Table Modifications
```sql
-- If modifying existing tables
ALTER TABLE existing ADD COLUMN new_field TEXT;
```

### Migrations Required
- [ ] Migration script created
- [ ] Migration tested locally
- [ ] Rollback script prepared

## API Changes

### New Endpoints
| Endpoint | Method | Purpose | Auth |
|----------|--------|---------|------|
| /api/new | POST | Create | Yes |

### Modified Endpoints
List any changes to existing endpoints

## Dependencies

### External
- Service/library and why it's needed

### Internal Modules
- Module name and how it's used

## Acceptance Criteria

- [ ] All unit tests pass
- [ ] All integration tests pass
- [ ] E2E tests pass (if tightly coupled)
- [ ] Code coverage >80%
- [ ] No linting errors
- [ ] Type check passes
- [ ] Documentation updated
- [ ] Module profile updated (`.claude/modules/{module}.md`)

## Testing Strategy

### Mock Requirements
- What needs to be mocked and why

### Test Data
- Sample data needed for tests

### Performance Criteria
- Expected response times
- Load requirements

## Rollback Plan

How to revert changes if deployment fails:
```bash
# Rollback steps
```

---

**Generated with** [Claude Code](https://claude.com/claude-code)
EOF

echo "✅ Created test spec: $SPEC_FILE"
echo ""
echo "Next steps:"
echo "1. Fill in the spec: ${EDITOR:-nano} $SPEC_FILE"
echo "2. Generate tests: /tdd generate $SPEC_FILE"
echo "3. Run tests: /tdd validate"
echo ""
