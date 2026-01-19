# ACH Operations Skill - Implementation Guide

**Based on**: Skills-based architecture validated 2025-12-09
**Reference**: `database-operations` skill (23ms, 84% context savings)
**Status**: Template created, ready for implementation

## Why Build as a Skill (Not an Agent)

### Performance Comparison

| Approach | Context | Speed | Integration | Maintenance |
|----------|---------|-------|-------------|-------------|
| **Skill** | 930 tokens | 23ms | Native | Easy |
| **Agent** | 4,500 tokens | 500ms | Manual | Medium |

**Verdict**: Skills approach is 95% faster with 80% less context.

## What's Already Created

✅ `skill.md` - Complete progressive disclosure format
✅ `scripts/validate_routing_number.py` - Example implementation
✅ `IMPLEMENTATION_GUIDE.md` - This file

## What Needs to Be Built

### Priority 1: Core Tools (2-3 hours)

1. **`generate_ach_file.py`** - Most important
   - Input: Payment data (JSON)
   - Output: NACHA-compliant ACH file
   - Complexity: Moderate (NACHA format has strict rules)

2. **`validate_ach_file.py`** - Essential for safety
   - Input: ACH file path
   - Output: Validation report
   - Complexity: Moderate (many validation rules)

3. **`parse_ach_file.py`** - Useful for incoming files
   - Input: ACH file path
   - Output: Parsed transactions (JSON)
   - Complexity: Moderate (parsing fixed-width format)

### Priority 2: Database Integration (1-2 hours)

4. **`query_contractor_payments.py`** - Database queries
   - Uses same connection pool as `database-operations` skill
   - Query pending payments from Neon
   - Format for ACH generation

5. **`ach_utils.py`** - Shared utilities
   - Connection pooling (copy from `db_utils.py`)
   - Common validation functions
   - Error handling helpers

### Priority 3: Helper Tools (1 hour)

6. **`calculate_batch_total.py`** - Batch calculations
7. **Test harness** - `test_ach_skill.sh`
8. **`requirements.txt`** - Dependencies list

**Total effort**: 4-6 hours for complete implementation

## Implementation Steps

### Step 1: Set Up Dependencies (15 min)

```bash
cd .claude/skills/ach-operations/scripts

# Create requirements.txt
cat > requirements.txt << 'EOF'
nacha==0.6.0           # ACH file generation
python-dotenv==1.0.0   # Environment variables
psycopg2-binary==2.9.9 # Database connection
EOF

# Install
pip install -r requirements.txt
```

### Step 2: Copy Connection Pooling (5 min)

```bash
# Copy db_utils.py as template
cp ../../database-operations/scripts/db_utils.py ./ach_utils.py

# Customize for ACH operations (add ACH-specific helpers)
```

### Step 3: Implement Core Tools (2-3 hours)

**Use this pattern** (from `validate_routing_number.py`):

```python
#!/usr/bin/env python3
"""
Tool description.
"""

import sys
import json
import argparse


def main_function(params):
    """Core logic here."""
    try:
        # Do the work
        result = {"success": True, "data": ...}
        return result
    except Exception as e:
        return {"success": False, "error": str(e)}


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(description="...")
    parser.add_argument("--param", required=True)
    args = parser.parse_args()

    result = main_function(args.param)
    print(json.dumps(result, indent=2))

    sys.exit(0 if result.get("success") else 1)


if __name__ == "__main__":
    main()
```

**Key principles**:
- ✅ JSON input/output
- ✅ Clear error messages
- ✅ Argparse for CLI
- ✅ Exit codes (0=success, 1=error)
- ✅ Self-contained (can run standalone)

### Step 4: Test Each Tool (30 min)

```bash
# Test validate_routing_number
./validate_routing_number.py --routing 123456789

# Test generate_ach_file (after implementing)
./generate_ach_file.py --input test_payments.json --output test.ach

# Test validate_ach_file
./validate_ach_file.py --file test.ach
```

### Step 5: Integration Test (30 min)

Create `test_ach_skill.sh`:

```bash
#!/bin/bash
echo "=== Testing ACH Operations Skill ==="

# Test 1: Validate routing number
echo "Test 1: Valid routing number"
./validate_routing_number.py --routing 011000015  # Federal Reserve

# Test 2: Invalid routing number
echo "Test 2: Invalid routing number"
./validate_routing_number.py --routing 123456789 || true

# Test 3: Generate ACH file
echo "Test 3: Generate ACH file"
cat > test_payments.json << 'EOF'
{
  "transactions": [
    {
      "routing_number": "011000015",
      "account_number": "1234567890",
      "amount": 100.00,
      "type": "credit",
      "name": "Test Contractor",
      "id": "TEST001"
    }
  ]
}
EOF
./generate_ach_file.py --input test_payments.json --output test.ach

# Test 4: Validate generated file
echo "Test 4: Validate ACH file"
./validate_ach_file.py --file test.ach

echo "=== Tests Complete ==="
```

## ACH File Generation Implementation

### Using `nacha` Library

The `nacha` Python library handles NACHA format complexity:

```python
from nacha import ACHFile, Batch, Entry

# Create file
ach_file = ACHFile(
    immediate_destination='012345678',  # Bank routing
    immediate_origin='1234567890',      # Your company ID
    file_creation_date='251209',        # YYMMDD
    file_creation_time='1200',          # HHMM
    immediate_destination_name='Bank Name',
    immediate_origin_name='Your Company'
)

# Create batch
batch = Batch(
    service_class_code='200',  # Mixed debits/credits
    company_name='FibreFlow Inc',
    company_identification='1234567890',
    standard_entry_class_code='PPD',  # Prearranged payments
    company_entry_description='CONTRACTOR',
    effective_entry_date='251210'  # YYMMDD
)

# Add entry (transaction)
entry = Entry(
    transaction_code='22',  # Checking credit
    receiving_dfi_identification='12345678',  # Bank routing (first 8 digits)
    check_digit='9',  # Routing check digit
    dfi_account_number='9876543210',
    amount=125000,  # In cents ($1,250.00)
    individual_identification_number='CONT001',
    individual_name='John Contractor',
    discretionary_data='',
    addenda_record_indicator='0'
)

batch.add_entry(entry)
ach_file.add_batch(batch)

# Generate file content
file_content = ach_file.render()

# Write to file
with open('contractor_payments.ach', 'w') as f:
    f.write(file_content)
```

### Key NACHA Concepts

**Transaction Codes**:
- `22` - Checking account credit (deposit)
- `27` - Checking account debit (withdrawal)
- `32` - Savings account credit
- `37` - Savings account debit

**SEC Codes** (Standard Entry Class):
- `PPD` - Prearranged Payment and Deposit (consumer)
- `CCD` - Corporate Credit or Debit (business)
- `CTX` - Corporate Trade Exchange (with invoice data)
- `WEB` - Internet-initiated entry

**File Structure**:
```
File Header (1 record)
  Batch Header (1 record)
    Entry Detail (N records)
    [Optional Addenda (N records)]
  Batch Trailer (1 record)
File Trailer (1 record)
```

## Database Integration Pattern

```python
# In query_contractor_payments.py

from ach_utils import get_connection_pool

def query_pending_payments():
    """Query pending contractor payments."""
    pool = get_connection_pool()
    conn = pool.getconn()

    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT
                    c.id,
                    c.name,
                    c.bank_routing_number,
                    c.bank_account_number,
                    p.amount,
                    p.payment_id
                FROM contractors c
                JOIN pending_payments p ON c.id = p.contractor_id
                WHERE p.status = 'pending'
                AND p.payment_method = 'ACH'
                AND c.bank_routing_number IS NOT NULL
            """)

            results = cur.fetchall()

            # Format for ACH generation
            transactions = []
            for row in results:
                transactions.append({
                    "routing_number": row['bank_routing_number'],
                    "account_number": row['bank_account_number'],
                    "amount": float(row['amount']),
                    "type": "credit",
                    "name": row['name'],
                    "id": row['payment_id']
                })

            return {"transactions": transactions}

    finally:
        pool.putconn(conn)
```

## Performance Expectations

With connection pooling (like `database-operations` skill):

| Operation | Time | Notes |
|-----------|------|-------|
| Query payments | ~25ms | With connection pooling |
| Validate routing | ~1ms | Pure Python calculation |
| Generate ACH file | ~50ms | 1,000 transactions |
| Validate file | ~30ms | Full integrity check |
| Parse file | ~40ms | Extract all transactions |

**Session of 10 operations**: ~250ms total (0.25 seconds)

## Testing Strategy

### Unit Tests (Optional but Recommended)

```python
# tests/test_ach_operations.py

def test_validate_routing_number():
    """Test routing number validation."""
    # Valid: Federal Reserve Bank of New York
    result = validate_routing_number("021000021")
    assert result["valid"] == True

    # Invalid: wrong check digit
    result = validate_routing_number("021000020")
    assert result["valid"] == False

def test_generate_ach_file():
    """Test ACH file generation."""
    payments = {
        "transactions": [{
            "routing_number": "021000021",
            "account_number": "1234567890",
            "amount": 100.00,
            "type": "credit",
            "name": "Test",
            "id": "TEST001"
        }]
    }

    result = generate_ach_file(payments, "test.ach")
    assert result["success"] == True
    assert os.path.exists("test.ach")
```

### Integration Tests

```bash
# End-to-end workflow test
./query_contractor_payments.py --status pending > payments.json
./generate_ach_file.py --input payments.json --output test.ach
./validate_ach_file.py --file test.ach
# Should all succeed
```

## Security Considerations

### Sensitive Data Handling

```python
# DON'T log sensitive data
logger.info(f"Processing payment for {account_number}")  # ❌ BAD

# DO log safely
logger.info(f"Processing payment for account ending in {account_number[-4:]}")  # ✅ GOOD
```

### File Permissions

```bash
# ACH files should be readable only by owner
chmod 600 *.ach

# Scripts should be executable
chmod +x scripts/*.py
```

### Encryption

```bash
# Encrypt before transmission
gpg --encrypt --recipient bank@example.com contractor_payments.ach

# Bank will decrypt with their private key
```

## Deployment Checklist

Before using in production:

- [ ] All 8 tools implemented and tested
- [ ] Connection pooling working (query tool < 50ms)
- [ ] Routing number validation tested (valid and invalid)
- [ ] ACH file generation tested with real data
- [ ] File validation catches all error types
- [ ] Database queries return correct contractor data
- [ ] Test harness passes all tests
- [ ] Documentation complete (skill.md accurate)
- [ ] Security review (no logging of sensitive data)
- [ ] Bank test environment validated

## Common Issues & Solutions

### Issue: Routing Number Validation Fails

**Symptom**: Valid routing numbers marked as invalid

**Solution**: Ensure using correct ABA check digit algorithm:
```python
checksum = 3*(D1+D4+D7) + 7*(D2+D5+D8) + 1*(D3+D6+D9)
check_digit = (10 - (checksum % 10)) % 10
```

### Issue: ACH File Rejected by Bank

**Symptom**: Bank returns error on file submission

**Common causes**:
1. Incorrect company ID or routing number
2. Batch totals don't match entry details
3. Missing or incorrect record counts
4. Invalid SEC code for transaction type
5. Effective date is past or too far in future

**Solution**: Use `validate_ach_file.py` before submission

### Issue: Slow Performance

**Symptom**: Queries take >1 second

**Solution**: Add connection pooling (copy from `db_utils.py`)

## Next Steps

### Phase 1: MVP (4 hours)
1. Implement `generate_ach_file.py`
2. Implement `validate_ach_file.py`
3. Implement `query_contractor_payments.py`
4. Test end-to-end workflow

### Phase 2: Complete (2 hours)
5. Implement remaining tools
6. Add comprehensive testing
7. Document all edge cases

### Phase 3: Production (1 hour)
8. Bank test environment validation
9. Security review
10. Team training

**Total**: 7 hours to production-ready ACH skill

## Resources

- **NACHA Rules**: https://www.nacha.org/rules
- **ACH Format Guide**: https://achdevguide.nacha.org/
- **Python `nacha` library**: https://pypi.org/project/nacha/
- **ABA Routing Numbers**: https://www.routingnumbers.info/

## Questions?

This implementation follows the exact pattern from `database-operations` skill which achieved:
- ✅ 23ms execution (99% faster than unoptimized)
- ✅ 930 tokens context (84% less than agent approach)
- ✅ Native Claude Code integration
- ✅ Production-ready with full testing

Apply the same patterns and you'll get the same results.
