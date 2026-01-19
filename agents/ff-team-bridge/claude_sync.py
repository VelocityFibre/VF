#!/usr/bin/env python3
"""
Claude Context Synchronization
Updates context files that both Claude instances read
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List

logger = logging.getLogger(__name__)

class ClaudeContextSync:
    """Manages Claude context file updates"""

    def __init__(self):
        # Context file paths
        self.context_file = Path("/home/louisdup/Agents/claude/TEAM_CONTEXT.md")
        self.tasks_file = Path("/home/louisdup/Agents/claude/TEAM_TASKS.json")
        self.decisions_file = Path("/home/louisdup/Agents/claude/TEAM_DECISIONS.json")

        # Ensure files exist
        self._ensure_files_exist()

    def _ensure_files_exist(self):
        """Ensure all context files exist"""
        if not self.context_file.exists():
            self.context_file.write_text(self._default_context())

        if not self.tasks_file.exists():
            self.tasks_file.write_text(json.dumps({"tasks": [], "updated": ""}, indent=2))

        if not self.decisions_file.exists():
            self.decisions_file.write_text(json.dumps({"decisions": [], "updated": ""}, indent=2))

    async def update_context(self, data: Dict[str, Any]):
        """Update all context files with new data"""

        try:
            # Update markdown context
            await self._update_markdown_context(data)

            # Update JSON files
            await self._update_tasks_json(data.get('tasks', []))
            await self._update_decisions_json(data.get('decisions', []))

            logger.info("Context files updated successfully")
            return True

        except Exception as e:
            logger.error(f"Error updating context: {e}")
            return False

    async def _update_markdown_context(self, data: Dict[str, Any]):
        """Update the main markdown context file"""

        messages = data.get('messages', [])
        tasks = data.get('tasks', [])
        decisions = data.get('decisions', [])
        bugs = data.get('bugs', [])
        questions = data.get('questions', [])

        # Build the markdown content
        content = f"""# FF App Team Context

**Last Updated:** {datetime.now().strftime('%Y-%m-%d %H:%M')}
**Developers:** Louis & Hein
**Purpose:** Single source of truth for team decisions, tasks, and context

---

## 📌 How to Use This File

1. **Both Claudes:** Read this file with "check TEAM_CONTEXT.md" for updates
2. **Prefixes:** Use TASK:, DECIDED:, BUG:, @claude for important items
3. **Natural Language:** "Louis will X" or "Hein should Y" creates tasks

---

## 🎯 Current Focus

{self._get_current_focus(data)}

---

## 💬 Recent Important Messages ({len(messages)} total)

"""

        # Add recent messages
        for msg in messages[-20:]:  # Last 20 messages
            if msg.get('is_important'):
                content += f"**{msg.get('sender', 'Unknown')} ({msg.get('timestamp', '')}):**\n"
                content += f"{msg.get('text', '')}\n\n"

        # Add active tasks
        content += f"\n## 📋 Active Tasks ({len(tasks)} total)\n\n"

        # Group tasks by assignee
        louis_tasks = [t for t in tasks if t.get('assigned_to') == 'louis' and t.get('status') != 'completed']
        hein_tasks = [t for t in tasks if t.get('assigned_to') == 'hein' and t.get('status') != 'completed']
        unassigned = [t for t in tasks if t.get('assigned_to') == 'unassigned' and t.get('status') != 'completed']

        if louis_tasks:
            content += "### Louis\n"
            for task in louis_tasks[:10]:
                status = "✅" if task.get('status') == 'completed' else "⏳" if task.get('status') == 'in_progress' else "📌"
                content += f"- {status} {task.get('description', 'No description')}\n"
            content += "\n"

        if hein_tasks:
            content += "### Hein\n"
            for task in hein_tasks[:10]:
                status = "✅" if task.get('status') == 'completed' else "⏳" if task.get('status') == 'in_progress' else "📌"
                content += f"- {status} {task.get('description', 'No description')}\n"
            content += "\n"

        if unassigned:
            content += "### Unassigned\n"
            for task in unassigned[:10]:
                content += f"- 🔴 {task.get('description', 'No description')}\n"
            content += "\n"

        # Add recent decisions
        if decisions:
            content += f"\n## 🎯 Recent Decisions ({len(decisions)} total)\n\n"
            for decision in decisions[-10:]:
                content += f"- **{decision.get('made_by', 'Team')}:** {decision.get('description', '')}\n"
            content += "\n"

        # Add bugs/issues
        if bugs:
            content += f"\n## 🐛 Known Issues ({len(bugs)} total)\n\n"
            for bug in bugs[-10:]:
                severity = "🔴" if bug.get('severity') == 'high' else "🟡"
                content += f"- {severity} {bug.get('description', '')}\n"
            content += "\n"

        # Add questions for Claude
        if questions:
            claude_questions = [q for q in questions if q.get('for') == 'claude']
            if claude_questions:
                content += f"\n## 💡 Questions for Claude ({len(claude_questions)} pending)\n\n"
                for q in claude_questions[-5:]:
                    content += f"- {q.get('question', '')}\n"
                content += "\n"

        # Add update log
        content += f"""
---

## 🔄 Update Log

- {datetime.now().strftime('%Y-%m-%d %H:%M')}: Automatic sync from WhatsApp
- Messages processed: {len(messages)}
- Tasks extracted: {len(tasks)}
- Decisions captured: {len(decisions)}

---

## Quick Command Reference

### For WhatsApp
```
TASK: [description] @louis/@hein
DECIDED: [decision]
BUG: [issue description]
@claude: [question]
```

### For Claude
```
/ff-context - Show this context
/ff-tasks - Show my tasks
/ff-sync - Force sync with WhatsApp
```
"""

        # Write the file
        self.context_file.write_text(content)
        logger.debug(f"Updated context file: {len(content)} characters")

    async def _update_tasks_json(self, tasks: List[Dict[str, Any]]):
        """Update the tasks JSON file"""

        # Load existing tasks
        try:
            with open(self.tasks_file, 'r') as f:
                existing_data = json.load(f)
                existing_tasks = existing_data.get('tasks', [])
        except:
            existing_tasks = []

        # Merge tasks (avoid duplicates based on description)
        existing_descriptions = {t.get('description', '').lower() for t in existing_tasks}

        for task in tasks:
            if task.get('description', '').lower() not in existing_descriptions:
                existing_tasks.append(task)

        # Keep only recent tasks (last 100)
        existing_tasks = existing_tasks[-100:]

        # Save updated tasks
        tasks_data = {
            "tasks": existing_tasks,
            "updated": datetime.now().isoformat(),
            "summary": {
                "total": len(existing_tasks),
                "louis": len([t for t in existing_tasks if t.get('assigned_to') == 'louis']),
                "hein": len([t for t in existing_tasks if t.get('assigned_to') == 'hein']),
                "unassigned": len([t for t in existing_tasks if t.get('assigned_to') == 'unassigned'])
            }
        }

        with open(self.tasks_file, 'w') as f:
            json.dump(tasks_data, f, indent=2)

        logger.debug(f"Updated tasks file: {len(existing_tasks)} tasks")

    async def _update_decisions_json(self, decisions: List[Dict[str, Any]]):
        """Update the decisions JSON file"""

        # Load existing decisions
        try:
            with open(self.decisions_file, 'r') as f:
                existing_data = json.load(f)
                existing_decisions = existing_data.get('decisions', [])
        except:
            existing_decisions = []

        # Merge decisions (avoid duplicates)
        existing_descriptions = {d.get('description', '').lower() for d in existing_decisions}

        for decision in decisions:
            if decision.get('description', '').lower() not in existing_descriptions:
                existing_decisions.append(decision)

        # Keep only recent decisions (last 50)
        existing_decisions = existing_decisions[-50:]

        # Save updated decisions
        decisions_data = {
            "decisions": existing_decisions,
            "updated": datetime.now().isoformat(),
            "count": len(existing_decisions)
        }

        with open(self.decisions_file, 'w') as f:
            json.dump(decisions_data, f, indent=2)

        logger.debug(f"Updated decisions file: {len(existing_decisions)} decisions")

    def _get_current_focus(self, data: Dict[str, Any]) -> str:
        """Generate a summary of current focus based on recent data"""

        tasks = data.get('tasks', [])
        recent_tasks = [t for t in tasks if t.get('status') != 'completed']

        if not recent_tasks:
            return "- No active tasks at the moment"

        # Find most common keywords
        keywords = {}
        for task in recent_tasks:
            desc = task.get('description', '').lower()
            for word in ['auth', 'deployment', 'bug', 'api', 'database', 'ui', 'test']:
                if word in desc:
                    keywords[word] = keywords.get(word, 0) + 1

        if keywords:
            top_focus = max(keywords, key=keywords.get)
            return f"- Primary focus: {top_focus.capitalize()} related work\n- {len(recent_tasks)} active tasks"
        else:
            return f"- {len(recent_tasks)} active tasks"

    def _default_context(self) -> str:
        """Default context file content"""
        return f"""# FF App Team Context

**Last Updated:** {datetime.now().strftime('%Y-%m-%d %H:%M')} (Initialized)
**Status:** Waiting for first sync...

---

## Setup Instructions

1. Ensure WhatsApp service is connected to FF App group
2. Start the bridge service: `python bridge_service.py`
3. Send a test message: "TASK: Test the bridge @claude"
4. Check this file updates automatically

---

## No data yet

The bridge will populate this file with team discussions once connected.
"""