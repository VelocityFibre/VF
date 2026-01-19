---
id: ach-operations
name: ACH Operations
description: ACH file generation, validation, and parsing for automated bank transfers. Create NACHA-compliant ACH files, validate batches, and process payments.
triggers: [ach, nacha, bank, transfer, payment, direct deposit, wire, eft, banking]
estimated_tokens: 700
complexity: moderate
---

# ACH Operations Skill

## Overview

Generate, validate, and parse ACH (Automated Clearing House) files for bank transfers. Supports NACHA format, batch processing, and payment validation for contractor payments, payroll, and vendor disbursements.

## Capabilities

### File Generation
- Create NACHA-compliant ACH files
- Batch multiple transactions
- Support credit (deposits) and debit (withdrawals)
- Generate proper file headers, batch headers, and trailers

### Validation
- Validate routing numbers (ABA check digit)
- Verify account number formats
- Check transaction limits
- Validate batch totals and counts

### File Parsing
- Parse existing ACH files
- Extract transaction details
- Validate file integrity
- Generate payment reports

## ACH File Format (NACHA)

**Record Types**:
1. **File Header** - Identifies file creator and destination
2. **Batch Header** - Identifies company and transaction type
3. **Entry Detail** - Individual transaction records
4. **Batch Trailer** - Batch totals and counts
5. **File Trailer** - File totals and counts

**Key Fields**:
- Routing number (9 digits with check digit)
- Account number (up to 17 characters)
- Transaction amount (in cents, 10 digits)
- Transaction type (22=checking credit, 27=checking debit, etc.)

## Tools

### validate_routing_number
Validate bank routing number using ABA check digit algorithm.

**Usage**:
```bash
./scripts/validate_routing_number.py --routing 123456789
```

**Returns**: Valid/invalid with check digit validation

---

### generate_ach_file
Generate NACHA-compliant ACH file from payment data.

**Usage**:
```bash
./scripts/generate_ach_file.py \
  --input payments.json \
  --output contractor_payments.ach \
  --company-name "FibreFlow Inc" \
  --company-id "1234567890"
```

**Input Format** (payments.json):
```json
{
  "transactions": [
    {
      "routing_number": "123456789",
      "account_number": "9876543210",
      "amount": 1250.00,
      "type": "credit",
      "name": "John Contractor",
      "id": "CONT001"
    }
  ]
}
```

**Returns**: ACH file path and validation summary

---

### parse_ach_file
Parse existing ACH file and extract transaction details.

**Usage**:
```bash
./scripts/parse_ach_file.py --file incoming_payments.ach
```

**Returns**: JSON with parsed transactions, totals, and validation results

---

### validate_ach_file
Validate ACH file integrity and compliance.

**Usage**:
```bash
./scripts/validate_ach_file.py --file contractor_payments.ach
```

**Checks**:
- File structure (proper record types and order)
- Routing number validity
- Batch totals match detail records
- File totals match batch totals
- Field formats and lengths

**Returns**: Validation report with errors/warnings

---

### calculate_batch_total
Calculate totals for ACH batch from transaction list.

**Usage**:
```bash
./scripts/calculate_batch_total.py --input transactions.json
```

**Returns**: Entry count, total debits, total credits, hash total

---

### query_contractor_payments
Query database for pending contractor payments and format for ACH.

**Usage**:
```bash
./scripts/query_contractor_payments.py --status pending
```

**Returns**: Contractor payment data ready for ACH generation

---

## Workflow Examples

### Example 1: Generate Contractor Payments ACH File

```bash
# Step 1: Query pending payments from database
./scripts/query_contractor_payments.py --status pending > payments.json

# Step 2: Validate routing numbers
cat payments.json | jq -r '.transactions[].routing_number' | \
  while read routing; do
    ./scripts/validate_routing_number.py --routing $routing
  done

# Step 3: Generate ACH file
./scripts/generate_ach_file.py \
  --input payments.json \
  --output ach_$(date +%Y%m%d).ach \
  --company-name "FibreFlow Inc" \
  --company-id "1234567890"

# Step 4: Validate generated file
./scripts/validate_ach_file.py --file ach_$(date +%Y%m%d).ach
```

### Example 2: Parse Incoming ACH File

```bash
# Parse file
./scripts/parse_ach_file.py --file incoming_20251209.ach > parsed.json

# Extract payment details
cat parsed.json | jq '.transactions[] | {name, amount, account}'

# Validate file integrity
./scripts/validate_ach_file.py --file incoming_20251209.ach
```

### Example 3: Validate Before Sending

```bash
# Calculate batch totals
./scripts/calculate_batch_total.py --input payments.json

# Validate all routing numbers
./scripts/validate_routing_number.py --batch payments.json

# Generate and validate file
./scripts/generate_ach_file.py --input payments.json --output test.ach
./scripts/validate_ach_file.py --file test.ach
```

## Error Handling

All scripts return errors in JSON format:

```json
{
  "error": "Invalid routing number",
  "details": "Check digit validation failed",
  "routing_number": "123456780",
  "expected_check_digit": 9,
  "actual_check_digit": 0
}
```

**Common Errors**:
- **Invalid routing number**: Check digit doesn't match
- **Invalid amount**: Amount exceeds limits or wrong format
- **Batch total mismatch**: Sum of transactions doesn't match batch trailer
- **Missing required field**: Account number, routing number, or amount missing

## Database Integration

ACH operations integrate with Neon database for:
- Querying pending contractor payments
- Recording ACH file generation
- Tracking payment status
- Audit trail of transactions

**Connection**: Uses same connection pool as database-operations skill for optimal performance.

## Security & Compliance

**Security Measures**:
- ⚠️ Never log account numbers or routing numbers
- ⚠️ Encrypt ACH files at rest
- ⚠️ Validate all inputs before file generation
- ⚠️ Audit trail for all ACH operations

**Compliance**:
- ✅ NACHA format compliance
- ✅ Check digit validation (ABA algorithm)
- ✅ Field length and format validation
- ✅ Batch and file total reconciliation

**File Security**:
```bash
# Encrypt ACH file before transmission
gpg --encrypt --recipient bank@example.com contractor_payments.ach

# Set restrictive permissions
chmod 600 *.ach
```

## Performance

**With Connection Pooling**:
- Query payments: ~25ms
- Generate ACH file: ~50ms (1000 transactions)
- Validate file: ~30ms
- Parse file: ~40ms

**Batch Processing**:
- 1,000 transactions: ~50ms
- 10,000 transactions: ~200ms
- 100,000 transactions: ~1,500ms

## Limitations

- **Maximum file size**: 1 million transactions per file (NACHA limit)
- **Amount limit**: $999,999,999.99 per transaction
- **Batch limit**: 10,000 transactions per batch (recommended)
- **File format**: NACHA only (no international formats)

## When to Use This Skill

✅ **Use for**:
- Generating contractor payment files
- Validating ACH files before submission
- Parsing received ACH files
- Batch payment processing
- Payment automation

❌ **Don't use for**:
- Real-time payment processing (use bank API instead)
- International wire transfers (different format)
- Credit card transactions (different system)
- Manual one-off payments (use bank portal)

## Dependencies

```bash
# Python packages
pip install nacha  # ACH file generation library

# Environment variables
export NEON_DATABASE_URL="postgresql://..."  # For payment queries
export ACH_COMPANY_ID="1234567890"  # Your company ID
export ACH_COMPANY_NAME="FibreFlow Inc"  # Your company name
```

See `scripts/requirements.txt` for exact versions.

## Related Skills

- `database-operations` - Query payment data from Neon
- `contractor-management` - Contractor bank account information
- `financial-reporting` - Payment reconciliation and reporting

## References

- **NACHA Specification**: https://www.nacha.org/rules
- **ABA Routing Number**: https://www.aba.com/routing-number
- **ACH File Format Guide**: https://achdevguide.nacha.org/

## Notes

- ACH files process in batches (typically overnight)
- Same-day ACH available for urgent payments (extra fee)
- ACH transactions can be reversed within 2 business days
- Always test with bank's test environment first
