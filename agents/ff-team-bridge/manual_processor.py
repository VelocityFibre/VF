#!/usr/bin/env python3
"""
WhatsApp to Claude Context Bridge - MINIMAL VERSION
Extracts important messages and creates a shared context file
"""

import json
import os
from datetime import datetime, timedelta
from pathlib import Path

# Configuration
CONTEXT_FILE = "/home/louisdup/Agents/claude/TEAM_CONTEXT.md"
TASKS_FILE = "/home/louisdup/Agents/claude/TEAM_TASKS.json"

class SimpleWABridge:
    """Dead simple WhatsApp to context bridge"""

    def __init__(self):
        # Explicit prefixes (case-insensitive)
        self.important_prefixes = [
            "TASK:",
            "TODO:",
            "DECIDED:",
            "DECISION:",
            "@CLAUDE",
            "IMPORTANT:",
            "BUG:",
            "FIXED:",
            "ISSUE:",
            "PROBLEM:",
            "URGENT:",
            "NOTE:"
        ]

        # Natural language patterns for task assignment
        self.task_patterns = [
            # "Louis will/should/can/must..."
            r"(louis|hein)\s+(will|should|can|must|needs to|has to)\s+(.+)",
            # "Can/Could Louis/Hein..."
            r"(can|could|would)\s+(louis|hein)\s+(.+)",
            # "I'll/I will..." (from identified sender)
            r"(i'll|i will|i'm going to|i am going to)\s+(.+)",
            # "@Louis/@Hein..."
            r"@(louis|hein)\s+(.+)",
            # "for Louis/Hein to..."
            r"for\s+(louis|hein)\s+to\s+(.+)"
        ]

    def is_important(self, message: str) -> bool:
        """Check if message should be saved - now with better detection"""
        import re

        message_upper = message.upper()

        # Check explicit prefixes
        if any(prefix in message_upper for prefix in self.important_prefixes):
            return True

        # Check for natural task language
        message_lower = message.lower()
        for pattern in self.task_patterns:
            if re.search(pattern, message_lower, re.IGNORECASE):
                return True

        # Check for question words with technical terms
        if '?' in message and any(term in message_lower for term in
            ['deploy', 'fix', 'bug', 'error', 'auth', 'database', 'api', 'production', 'staging']):
            return True

        return False

    def extract_tasks(self, message: str, sender: str = None) -> dict:
        """Extract task if present - now with better natural language understanding"""
        import re

        msg_lower = message.lower()
        msg_upper = message.upper()

        # Clean the message for better display
        clean_msg = message.strip()

        # Pattern 1: Explicit TASK:/TODO: with assignment
        if "TASK:" in msg_upper or "TODO:" in msg_upper:
            # Check if Louis or Hein is mentioned
            if re.search(r"@?(louis|for louis)", msg_lower):
                return {"assigned": "louis", "task": clean_msg}
            elif re.search(r"@?(hein|for hein)", msg_lower):
                return {"assigned": "hein", "task": clean_msg}
            else:
                return {"assigned": "unassigned", "task": clean_msg}

        # Pattern 2: Natural language - "Louis will/should/must..."
        match = re.search(r"(louis|hein)\s+(will|should|can|must|needs to|has to)\s+(.+)", msg_lower)
        if match:
            person = match.group(1)
            action = match.group(3).strip()
            return {"assigned": person, "task": f"{person.capitalize()} will {action}"}

        # Pattern 3: "Can/Could Louis/Hein..."
        match = re.search(r"(can|could|would)\s+(louis|hein)\s+(.+)", msg_lower)
        if match:
            person = match.group(2)
            action = match.group(3).strip()
            return {"assigned": person, "task": f"{person.capitalize()} to {action}"}

        # Pattern 4: "I'll/I will..." (use sender info)
        match = re.search(r"(i'll|i will|i'm going to|i am going to)\s+(.+)", msg_lower)
        if match and sender:
            action = match.group(2).strip()
            assigned_to = sender.lower() if sender.lower() in ['louis', 'hein'] else 'unassigned'
            return {"assigned": assigned_to, "task": f"{sender} will {action}"}

        # Pattern 5: "@Louis/@Hein [task]"
        match = re.search(r"@(louis|hein)\s+(.+)", msg_lower)
        if match:
            person = match.group(1)
            action = match.group(2).strip()
            return {"assigned": person, "task": f"@{person.capitalize()}: {action}"}

        # Pattern 6: "for Louis/Hein to..."
        match = re.search(r"for\s+(louis|hein)\s+to\s+(.+)", msg_lower)
        if match:
            person = match.group(1)
            action = match.group(2).strip()
            return {"assigned": person, "task": f"{person.capitalize()} to {action}"}

        # Pattern 7: Action verbs that imply tasks
        action_verbs = ['fix', 'update', 'deploy', 'check', 'implement', 'create', 'test', 'review']
        for verb in action_verbs:
            if verb in msg_lower and any(name in msg_lower for name in ['louis', 'hein']):
                if 'louis' in msg_lower:
                    return {"assigned": "louis", "task": clean_msg}
                elif 'hein' in msg_lower:
                    return {"assigned": "hein", "task": clean_msg}

        return None

    def update_context(self, messages: list):
        """Update the shared context file"""

        # Filter important messages
        important = [msg for msg in messages if self.is_important(msg['text'])]

        # Extract tasks (now with sender info for better assignment)
        tasks = []
        for msg in messages:  # Check ALL messages for tasks, not just "important"
            task = self.extract_tasks(msg['text'], sender=msg.get('sender'))
            if task:
                task['timestamp'] = msg['timestamp']
                task['from'] = msg['sender']
                tasks.append(task)

        # Generate context markdown
        context = f"""# FF App Team Context
Last Updated: {datetime.now().strftime('%Y-%m-%d %H:%M')}

## Recent Important Messages ({len(important)} messages)

"""

        for msg in important[-20:]:  # Last 20 important messages
            context += f"**{msg['sender']} ({msg['timestamp']}):**\n{msg['text']}\n\n"

        if tasks:
            context += f"\n## Extracted Tasks ({len(tasks)} tasks)\n\n"
            context += "### Louis\n"
            louis_tasks = [t for t in tasks if t['assigned'] == 'louis']
            for task in louis_tasks:
                context += f"- {task['task']}\n"

            context += "\n### Hein\n"
            hein_tasks = [t for t in tasks if t['assigned'] == 'hein']
            for task in hein_tasks:
                context += f"- {task['task']}\n"

            context += "\n### Unassigned\n"
            unassigned = [t for t in tasks if t['assigned'] == 'unassigned']
            for task in unassigned:
                context += f"- {task['task']}\n"

        # Write context file
        with open(CONTEXT_FILE, 'w') as f:
            f.write(context)

        # Write tasks JSON
        with open(TASKS_FILE, 'w') as f:
            json.dump({"tasks": tasks, "updated": datetime.now().isoformat()}, f, indent=2)

        print(f"✅ Updated context with {len(important)} messages and {len(tasks)} tasks")
        return len(important), len(tasks)

# Manual test function
def test_with_sample_messages():
    """Test with sample messages - now with improved detection"""
    bridge = SimpleWABridge()

    sample_messages = [
        {"sender": "Louis", "text": "TASK: Fix the auth bug in production", "timestamp": "10:30"},
        {"sender": "Hein", "text": "I'll check the deployment", "timestamp": "10:31"},
        {"sender": "Louis", "text": "How's it going?", "timestamp": "10:32"},
        {"sender": "Hein", "text": "DECIDED: Switch to Neon for auth", "timestamp": "10:33"},
        {"sender": "Louis", "text": "@claude can you help with the migration?", "timestamp": "10:34"},
        {"sender": "Hein", "text": "Louis will update the docs", "timestamp": "10:35"},
        {"sender": "Louis", "text": "BUG: The VPS is running out of memory", "timestamp": "10:36"}
    ]

    print("=" * 50)
    print("IMPROVED DETECTION TEST")
    print("=" * 50)

    # Test importance detection
    print("\n📊 IMPORTANCE DETECTION:")
    for msg in sample_messages:
        is_important = bridge.is_important(msg['text'])
        status = "✅ Important" if is_important else "❌ Ignored"
        print(f"{status}: {msg['text'][:50]}...")

    # Test task extraction
    print("\n📋 TASK EXTRACTION:")
    for msg in sample_messages:
        task = bridge.extract_tasks(msg['text'], msg['sender'])
        if task:
            print(f"✅ Task found: {task['assigned']:8} | {task['task'][:40]}...")

    # Run full update
    messages_processed, tasks_found = bridge.update_context(sample_messages)

    print("\n📈 RESULTS:")
    print(f"Important messages: {messages_processed} / {len(sample_messages)}")
    print(f"Tasks extracted: {tasks_found}")

    # Show task assignments
    with open(TASKS_FILE, 'r') as f:
        tasks_data = json.load(f)

    print("\n🎯 TASK ASSIGNMENTS:")
    for task in tasks_data['tasks']:
        print(f"  {task['assigned']:10} | {task['from']:8} | {task['task'][:35]}...")

if __name__ == "__main__":
    test_with_sample_messages()
    print(f"\n📄 Context file: {CONTEXT_FILE}")
    print(f"📝 Tasks file: {TASKS_FILE}")