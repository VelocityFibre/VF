# FF Team Bridge Module

## Overview

WhatsApp-to-Claude bridge for the FF App developer group. Creates a shared consciousness between Louis, Hein, and their Claude instances by monitoring WhatsApp group messages and extracting actionable information.

## Architecture

```
FF App WhatsApp Group
        ↓
  WA Monitor Service
        ↓
  Message Processor
        ↓
   ┌────────┴────────┐
   │                 │
Database        Context Files
   │                 │
   └────────┬────────┘
            │
      Both Claudes
```

## Quick Start

### 1. Get Group ID

First, identify your FF App group:

```bash
# SSH to server with WhatsApp service
ssh root@72.60.17.245  # or wherever service is running

# Get list of groups
curl http://localhost:8081/api/groups | jq '.[].name'

# Find your FF App group ID
curl http://localhost:8081/api/groups | jq '.[] | select(.name | contains("FF"))'
```

### 2. Configure Monitoring

Edit `/opt/whatsapp-sender/config.json`:

```json
{
  "monitored_groups": {
    "ff_app": {
      "group_id": "[YOUR_GROUP_ID]",
      "participants": ["+27...", "+27..."],
      "process_messages": true
    }
  }
}
```

### 3. Start Bridge Service

```bash
cd /home/louisdup/Agents/claude/agents/ff-team-bridge
./venv/bin/python bridge_service.py &
```

### 4. Test

Send a test message to the group:
```
TASK: Test the WhatsApp bridge
```

Check if it was captured:
```bash
cat /home/louisdup/Agents/claude/TEAM_CONTEXT.md
```

## Files

- `bridge_service.py` - Main service that listens to WhatsApp
- `message_processor.py` - Extracts tasks, decisions, etc.
- `claude_sync.py` - Updates context files for Claude
- `database.py` - Database operations
- `config.yaml` - Configuration

## Context Files

- `/home/louisdup/Agents/claude/TEAM_CONTEXT.md` - Human-readable context
- `/home/louisdup/Agents/claude/TEAM_TASKS.json` - Machine-readable tasks

## Message Patterns

### Recognized Prefixes
- `TASK:` or `TODO:` - Creates a task
- `DECIDED:` or `DECISION:` - Documents a decision
- `BUG:` or `ISSUE:` - Reports a problem
- `@claude` - Question for AI
- `FIXED:` - Documents a fix

### Natural Language
- "Louis will [action]" → Task for Louis
- "Hein should [action]" → Task for Hein
- "Can you [action]?" → Question/request
- "@Louis [action]" → Direct assignment

## Database Schema

```sql
-- developer_communications table
- message_id: Unique WhatsApp message ID
- group_id: WhatsApp group ID
- sender_phone: Sender's phone number
- message_text: Message content
- timestamp: When received
- processed: Processing status
- extracted_tasks: JSON of extracted tasks
- extracted_decisions: JSON of decisions

-- developer_tasks table
- task_description: What needs to be done
- assigned_to: louis/hein/unassigned
- status: pending/in_progress/completed
- created_at: When created
- claude_session_id: Which Claude session created it
```

## Integration with Claude

Both Claude instances should read the context file on startup:

```bash
# In your Claude prompt
"Check TEAM_CONTEXT.md for recent team discussions"
```

Or use the skill:
```bash
# Returns recent context
/ff-context

# Returns your tasks
/ff-tasks
```

## Manual Usage (Without Full Integration)

### Option 1: Copy-Paste Method
1. Export WhatsApp chat
2. Save to `chat.txt`
3. Run: `python process_chat.py chat.txt`
4. Context updates automatically

### Option 2: Daily Summary
```bash
# Run daily to update context
python daily_summary.py
```

## Troubleshooting

### Bridge Not Receiving Messages
1. Check WhatsApp service is running: `curl http://localhost:8081/health`
2. Check phone is paired: `curl http://localhost:8081/api/status`
3. Check group ID is correct: `curl http://localhost:8081/api/groups`

### Tasks Not Being Extracted
1. Check patterns in `message_processor.py`
2. Test with explicit prefix: "TASK: test task"
3. Check logs: `tail -f bridge.log`

### Context Not Updating
1. Check file permissions: `ls -la TEAM_CONTEXT.md`
2. Check service is running: `ps aux | grep bridge_service`
3. Force update: `python claude_sync.py --force`

## Benefits

- **No more copy-paste** - Context automatically shared
- **Task tracking** - Never lose track of who's doing what
- **Decision history** - All decisions documented
- **Shared memory** - Both Claudes know the same context

## Future Enhancements

- [ ] Real-time dashboard
- [ ] Task completion tracking
- [ ] Auto-assign based on expertise
- [ ] Meeting summaries
- [ ] Sprint planning integration