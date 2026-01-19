# FF App Developer Group Integration Plan

## Overview
Transform the FF app WhatsApp group into a shared brain between Louis, Hein, and their Claude instances, enabling real-time context sharing, task distribution, and automated documentation.

## Phase 1: Group Listener Setup (Day 1)

### 1.1 Configure WhatsApp Service for Group Monitoring
```python
# Location: /opt/whatsapp-sender/config.json
{
  "monitored_groups": {
    "ff_app": {
      "group_id": "", # Will be populated after group join
      "participants": ["+27...", "+27..."], # Louis & Hein
      "listen_only": false,
      "process_messages": true,
      "store_history": true
    }
  }
}
```

### 1.2 Database Schema for Developer Communications
```sql
-- New table: developer_communications
CREATE TABLE developer_communications (
    id SERIAL PRIMARY KEY,
    message_id VARCHAR(255) UNIQUE,
    group_id VARCHAR(255),
    sender_phone VARCHAR(50),
    sender_name VARCHAR(100),
    message_text TEXT,
    message_type VARCHAR(50), -- 'text', 'code', 'image', 'document'
    attachments JSONB,
    timestamp TIMESTAMPTZ DEFAULT NOW(),
    processed BOOLEAN DEFAULT FALSE,

    -- Extracted metadata
    contains_task BOOLEAN DEFAULT FALSE,
    contains_decision BOOLEAN DEFAULT FALSE,
    contains_code BOOLEAN DEFAULT FALSE,
    contains_question BOOLEAN DEFAULT FALSE,

    -- Processing results
    extracted_tasks JSONB,
    extracted_decisions JSONB,
    code_references JSONB,
    ai_questions JSONB,

    -- Claude sync
    synced_to_claude BOOLEAN DEFAULT FALSE,
    claude_context_id VARCHAR(255),

    INDEX idx_group_timestamp (group_id, timestamp DESC),
    INDEX idx_unprocessed (processed, timestamp)
);

-- Task assignments table
CREATE TABLE developer_tasks (
    id SERIAL PRIMARY KEY,
    message_id VARCHAR(255) REFERENCES developer_communications(message_id),
    task_description TEXT,
    assigned_to VARCHAR(100), -- 'louis' or 'hein'
    status VARCHAR(50) DEFAULT 'pending', -- pending, in_progress, completed
    priority VARCHAR(20) DEFAULT 'normal',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    completed_at TIMESTAMPTZ,
    claude_session_id VARCHAR(255),

    INDEX idx_status_assigned (status, assigned_to)
);
```

## Phase 2: Message Processing Pipeline (Day 2)

### 2.1 Message Listener Service
```python
# Location: agents/wa_group_monitor/listener.py
import asyncio
from typing import Dict, Any
import re

class FFAppGroupListener:
    def __init__(self):
        self.group_id = None
        self.patterns = {
            'task': r'(?:TODO|TASK|@(?:louis|hein)):\s*(.+)',
            'decision': r'(?:DECIDED|DECISION|ADR):\s*(.+)',
            'code_ref': r'(?:file://|\.py|\.ts|\.tsx|function|class)\s*(\S+)',
            'question': r'(?:@claude|claude\?|AI\?|QUESTION):\s*(.+)',
            'assignment': r'(?:louis|hein)\s+(?:will|can|should|to)\s+(.+)'
        }

    async def process_message(self, message: Dict[str, Any]):
        """Extract actionable information from group messages"""

        text = message.get('text', '')
        sender = message.get('sender')

        extracted = {
            'tasks': self._extract_tasks(text),
            'decisions': self._extract_decisions(text),
            'code_refs': self._extract_code_references(text),
            'questions': self._extract_ai_questions(text),
            'assignments': self._extract_assignments(text, sender)
        }

        # Store in database
        await self._store_communication(message, extracted)

        # Trigger Claude sync if needed
        if any(extracted.values()):
            await self._sync_to_claude(message, extracted)

        return extracted
```

### 2.2 Context Synchronization
```python
# Location: agents/wa_group_monitor/claude_sync.py
class ClaudeContextSync:
    def __init__(self):
        self.context_file = "/home/louisdup/Agents/claude/FF_APP_CONTEXT.md"
        self.task_queue = "/home/louisdup/Agents/claude/FF_APP_TASKS.json"

    async def update_shared_context(self, messages: list):
        """Update shared context file for Claude"""

        context = {
            'last_updated': datetime.now().isoformat(),
            'recent_messages': messages[-20:],  # Last 20 messages
            'active_tasks': self._get_active_tasks(),
            'recent_decisions': self._get_recent_decisions(),
            'pending_questions': self._get_pending_questions()
        }

        # Generate markdown context
        markdown = self._generate_context_markdown(context)

        # Write to shared file
        with open(self.context_file, 'w') as f:
            f.write(markdown)

        # Update task queue
        await self._update_task_queue()
```

## Phase 3: Task Extraction & Assignment (Day 3)

### 3.1 Smart Task Parser
```python
# Location: agents/wa_group_monitor/task_parser.py
class TaskParser:
    def parse_conversation_for_tasks(self, messages: list) -> list:
        """
        Extract tasks from natural conversation

        Examples:
        - "Louis will handle the auth fix" → Task for Louis
        - "Hein can you check the deployment?" → Task for Hein
        - "We need to update the docs" → Unassigned task
        - "@claude implement the user dashboard" → AI task
        """

        tasks = []
        for msg in messages:
            # Check for explicit assignments
            if self._is_task_assignment(msg):
                tasks.append(self._create_task(msg))

            # Check for implicit work items
            if self._contains_work_item(msg):
                tasks.append(self._infer_task(msg))

        return tasks
```

### 3.2 Auto-Documentation Generator
```python
# Location: agents/wa_group_monitor/auto_doc.py
class AutoDocumentationGenerator:
    def generate_from_conversation(self, messages: list):
        """Generate documentation from WhatsApp discussions"""

        sections = {
            'decisions': self._extract_architectural_decisions(messages),
            'tasks': self._extract_task_list(messages),
            'issues': self._extract_discussed_issues(messages),
            'solutions': self._extract_proposed_solutions(messages)
        }

        # Update relevant docs
        self._update_operations_log(sections['decisions'])
        self._update_task_board(sections['tasks'])
        self._update_decision_log(sections['decisions'])
```

## Phase 4: Claude Integration (Day 4)

### 4.1 Claude Context Provider
```python
# Location: .claude/skills/ff-app-context/skill.py
class FFAppContextSkill:
    """Provide FF App group context to Claude"""

    def get_recent_context(self, hours: int = 24) -> str:
        """Get recent team discussions"""

        messages = self._fetch_recent_messages(hours)
        tasks = self._fetch_active_tasks()
        decisions = self._fetch_recent_decisions()

        return f"""
        ## Recent Team Discussion ({len(messages)} messages)
        {self._format_messages(messages)}

        ## Active Tasks
        Louis: {self._format_tasks(tasks['louis'])}
        Hein: {self._format_tasks(tasks['hein'])}

        ## Recent Decisions
        {self._format_decisions(decisions)}
        """

    def get_my_tasks(self, developer: str) -> list:
        """Get tasks assigned to specific developer"""
        return self._fetch_assigned_tasks(developer)
```

### 4.2 Claude Command Integration
```bash
# New Claude commands
/ff-context       # Show recent team discussion
/ff-tasks         # Show my assigned tasks
/ff-sync          # Force sync with WhatsApp group
/ff-report        # Generate team status report
```

## Phase 5: Real-time Dashboard (Day 5)

### 5.1 Team Coordination Dashboard
```typescript
// Location: app/wa-monitor/team-dashboard.tsx
export function TeamDashboard() {
  return (
    <div className="grid grid-cols-2 gap-4">
      {/* Live Message Feed */}
      <MessageFeed groupId="ff_app" />

      {/* Task Distribution */}
      <TaskBoard developers={['louis', 'hein']} />

      {/* Decision Log */}
      <DecisionLog autoUpdate={true} />

      {/* AI Questions Queue */}
      <AIQuestionsPanel />
    </div>
  );
}
```

## Implementation Steps

### Day 1: Foundation
```bash
# 1. Add group monitoring to WhatsApp service
ssh velo@100.96.203.105
cd /opt/whatsapp-sender
# Update config to monitor FF app group

# 2. Create database tables
psql $NEON_DATABASE_URL < create_developer_tables.sql

# 3. Test group message reception
curl http://100.96.203.105:8081/api/groups
```

### Day 2: Message Processing
```bash
# 1. Deploy message processor
cd agents/wa_group_monitor
python listener.py &

# 2. Test extraction patterns
python test_extraction.py

# 3. Verify database writes
psql -c "SELECT * FROM developer_communications ORDER BY timestamp DESC LIMIT 10"
```

### Day 3: Task System
```bash
# 1. Deploy task parser
python task_parser.py &

# 2. Test task assignment
echo "Louis will fix the auth bug" | python test_parser.py

# 3. Check task queue
cat FF_APP_TASKS.json | jq .
```

### Day 4: Claude Integration
```bash
# 1. Install FF app context skill
cp -r ff-app-context .claude/skills/

# 2. Update Claude settings
nano .claude/settings.local.json

# 3. Test context retrieval
claude "show me recent team discussions"
```

### Day 5: Dashboard
```bash
# 1. Deploy dashboard
npm run dev -- --port 3007

# 2. Access dashboard
open http://100.96.203.105:3007/team

# 3. Monitor real-time updates
```

## Benefits

### For Louis & Hein
- ✅ No more copy-pasting conversations to Claude
- ✅ Automatic task tracking and assignment
- ✅ Decisions automatically documented
- ✅ Both Claude instances stay in sync

### For Claude
- ✅ Full context of team discussions
- ✅ Knows who's working on what
- ✅ Can reference recent decisions
- ✅ Answers questions asynchronously

### For the Project
- ✅ Automatic documentation generation
- ✅ Clear task distribution
- ✅ Decision history preserved
- ✅ Reduced communication overhead

## Security Considerations

1. **Message Filtering**: Only process messages from Louis & Hein
2. **Data Retention**: Keep 30 days of messages, archive older
3. **Access Control**: Dashboard requires authentication
4. **Sensitive Data**: Auto-redact credentials and keys

## Monitoring & Alerts

```python
# Alert conditions
alerts = {
    'unassigned_task': "Task mentioned but not assigned for >2 hours",
    'blocked_question': "Question to Claude unanswered for >1 hour",
    'decision_conflict': "Conflicting decisions detected",
    'high_priority': "URGENT or CRITICAL mentioned"
}
```

## Success Metrics

- **Response Time**: Questions answered within 1 hour
- **Task Clarity**: 90% of tasks have clear assignee
- **Documentation**: All decisions captured automatically
- **Context Sync**: Claude has context within 5 minutes

## Next Steps

1. **Immediate** (Today):
   - Get FF app group ID from WhatsApp
   - Create database tables
   - Deploy basic listener

2. **Tomorrow**:
   - Implement message processing
   - Test task extraction
   - Deploy Claude sync

3. **This Week**:
   - Complete all 5 phases
   - Run for 1 week trial
   - Gather feedback and iterate

## Example Usage

### WhatsApp Conversation
```
Louis: We need to fix the auth bug in production
Hein: I'll take a look at the clerk integration
Louis: @claude can you analyze the error logs?
Hein: DECIDED: We'll use Neon for auth instead of Clerk
Louis: TODO: Update the deployment guide
```

### Automatic Extraction
```json
{
  "tasks": [
    {"description": "Fix auth bug in production", "assigned_to": null, "priority": "high"},
    {"description": "Look at clerk integration", "assigned_to": "hein"},
    {"description": "Update the deployment guide", "assigned_to": "louis"}
  ],
  "decisions": [
    {"description": "Use Neon for auth instead of Clerk", "made_by": "hein"}
  ],
  "ai_questions": [
    {"question": "analyze the error logs", "asked_by": "louis"}
  ]
}
```

### Claude Context Update
```markdown
# FF App Team Context
Last Updated: 2026-01-09 14:30

## Recent Discussion
- Auth bug reported in production (Louis)
- Hein investigating Clerk integration
- Decision: Switch to Neon for auth

## Active Tasks
**Louis**: Update deployment guide
**Hein**: Clerk integration investigation

## Pending AI Questions
- Analyze error logs (asked by Louis, 5 mins ago)
```

This integration will transform your WhatsApp group into a powerful coordination hub!