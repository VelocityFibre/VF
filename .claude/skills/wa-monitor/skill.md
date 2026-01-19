---
name: wa-monitor
version: 1.0.0
description: WA Monitor (Foto Reviews) - Automated DR quality evaluation with VLM
author: Claude
tags: [wa-monitor, foto-reviews, vlm, evaluation, whatsapp]
requires: [neon-database, vf-server]
async: true
context_fork: true
hooks:
  pre_tool_use: "echo '[WA-Monitor] Starting DR evaluation at $(date)' >> /tmp/wa_monitor_ops.log"
  post_tool_use: "echo '[WA-Monitor] Completed operation at $(date) - VLM evaluation logged' >> /tmp/wa_monitor_ops.log"
---

# WA Monitor (Foto Reviews) Skill

Automated Drop Record (DR) quality evaluation using Vision Language Model (VLM) with human-in-the-loop review and WhatsApp feedback delivery.

## Overview

The WA Monitor system evaluates fiber installation photos using AI, generates quality scores and feedback, allows human review, and sends approved feedback to contractors via WhatsApp.

## Key Components

### 1. VLM Service
- **Model**: Qwen/Qwen3-VL-8B-Instruct
- **Port**: 8100
- **Context**: 16384 tokens
- **Location**: VF Server (100.96.203.105)

### 2. Database
- **Table**: `foto_ai_reviews` (NOT `foto_evaluations`)
- **Connection**: Neon PostgreSQL
- **Records**: 27+ evaluations

### 3. WhatsApp Service
- **Port**: 8081
- **Phone**: +27 71 155 8396 (must be paired)
- **Technology**: Go + whatsmeow

## API Endpoints

### List Pending Reviews
```bash
GET http://100.96.203.105:3005/api/foto-reviews/pending?limit=10
```

### Get Review Details
```bash
GET http://100.96.203.105:3005/api/foto-reviews/DR1733758
```

### Trigger Evaluation
```bash
POST http://100.96.203.105:3005/api/foto/evaluate
Body: {"dr_number": "DR1234567"}
```

### Send Feedback
```bash
POST http://100.96.203.105:3005/api/foto/feedback
Body: {"dr_number": "DR1234567", "phone_number": "+27711558396"}
```

## Quick Commands

### Check System Status
```bash
# VLM Service
curl http://100.96.203.105:8100/health

# WhatsApp Service
curl http://100.96.203.105:8081/health

# Pending Reviews
curl "http://100.96.203.105:3005/api/foto-reviews/pending?limit=5" | jq '.data.total'
```

### Restart Services
```bash
# SSH to server
ssh louis@100.96.203.105

# Restart Next.js
pkill -f "next-server"
cd /home/louis/apps/fibreflow.OLD_20251217
PORT=3005 NODE_ENV=production npm run start > /tmp/next.log 2>&1 &

# Restart VLM (if needed)
cd ~/vlm-service
./restart_vlm_server.sh
```

## Database Queries

### Get Pending Evaluations
```sql
SELECT dr_number, overall_status, average_score, evaluation_date
FROM foto_ai_reviews
WHERE feedback_sent = false
ORDER BY evaluation_date DESC;
```

### Update Feedback Status
```sql
UPDATE foto_ai_reviews
SET feedback_sent = true, feedback_sent_at = NOW()
WHERE dr_number = 'DR1733758';
```

## Common Issues

### SQL Error
**Problem**: "This function can only be called as a tagged-template"
**Solution**: Use `` sql`SELECT...` `` not `sql('SELECT...', params)`

### Table Not Found
**Problem**: "relation foto_evaluations does not exist"
**Solution**: Use `foto_ai_reviews` table name

### WhatsApp Not Sending
**Problem**: Phone not paired
**Solution**:
```bash
ssh louis@100.96.203.105
curl http://localhost:8081/qr
# Scan with phone +27 71 155 8396
```

## Testing Workflow

```bash
# 1. Trigger evaluation for test DR
curl -X POST http://100.96.203.105:3005/api/foto/evaluate \
  -H "Content-Type: application/json" \
  -d '{"dr_number":"DRTEST999"}'

# 2. Wait 20-30 seconds for VLM processing

# 3. Check it's in pending list
curl "http://100.96.203.105:3005/api/foto-reviews/pending?limit=1" | jq '.data.reviews[0].dr_number'

# 4. View details
curl "http://100.96.203.105:3005/api/foto-reviews/DRTEST999" | jq '.data.average_score'

# 5. Send feedback (after human review)
curl -X POST http://100.96.203.105:3005/api/foto/feedback \
  -H "Content-Type: application/json" \
  -d '{"dr_number":"DRTEST999","phone_number":"+27711558396"}'
```

## Performance Metrics

- **VLM Evaluation**: 15-30 seconds per DR
- **Database Query**: 500-1200ms
- **Current Pending**: 27 evaluations
- **Score Range**: 1.5-9.2 out of 10

## Related Skills

- `neon-database` - Database operations
- `vf-server` - Server management
- `database-operations` - SQL queries

## Documentation

- Full module docs: `/home/louisdup/Agents/claude/WA_MONITOR_MODULE_DOCUMENTATION.md`
- Setup guide: `/home/louisdup/Agents/claude/WA_MONITOR_SETUP.md`
- Status: `/home/louisdup/Agents/claude/FINAL_WORKING_STATUS.md`