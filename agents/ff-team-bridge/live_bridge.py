#!/usr/bin/env python3
"""
Live FF Team Bridge - Works in manual or auto mode
Manual: Watch incoming_messages.txt for pasted messages
Auto: Connect to WhatsApp service (when group ID is known)
"""

import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List

# Add parent directories to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from message_processor import MessageProcessor
from claude_sync import ClaudeContextSync

class LiveBridge:
    def __init__(self):
        self.processor = MessageProcessor()
        self.claude_sync = ClaudeContextSync()
        self.config = self._load_config()
        self.processed_messages = set()
        self.last_check = datetime.now()

    def _load_config(self):
        """Load configuration"""
        config_file = Path(__file__).parent / "config.json"
        if config_file.exists():
            with open(config_file, 'r') as f:
                return json.load(f)
        return {}

    def run_manual_mode(self):
        """Watch for messages in incoming_messages.txt"""

        watch_file = Path(self.config['manual_mode']['watch_file'])

        print("=" * 60)
        print("🚀 FF TEAM BRIDGE - MANUAL MODE")
        print("=" * 60)
        print(f"\n📝 Watching: {watch_file}")
        print("\n📌 HOW TO USE:")
        print("1. Copy messages from your FF app WhatsApp group")
        print("2. Paste them into incoming_messages.txt")
        print("3. This bridge will process them automatically")
        print("\n📍 Message formats that work:")
        print("  TASK: Update the deployment docs @louis")
        print("  TODO: Fix the auth bug @hein")
        print("  DECIDED: Deploy every Friday")
        print("  BUG: Memory leak in worker")
        print("  @claude how do we optimize this?")
        print("  Louis will check the tests")
        print("  Can Hein review the PR?")
        print("\n⏳ Checking for new messages every 10 seconds...")
        print("-" * 60)

        # Create watch file if it doesn't exist
        if not watch_file.exists():
            watch_file.write_text("# Paste WhatsApp messages here\n")

        while True:
            try:
                # Read the file
                content = watch_file.read_text()

                # Skip if empty or just header
                if not content or content.strip() == "# Paste WhatsApp messages here":
                    time.sleep(10)
                    continue

                # Process new messages
                lines = content.strip().split('\n')
                new_messages = []

                for line in lines:
                    line = line.strip()
                    if not line or line.startswith('#'):
                        continue

                    # Simple message ID based on content hash
                    msg_id = str(hash(line))

                    if msg_id not in self.processed_messages:
                        # Parse WhatsApp format: [date, time] sender: message
                        # Or just treat as message if no format
                        if '] ' in line and ': ' in line:
                            # WhatsApp format
                            parts = line.split('] ', 1)
                            if len(parts) == 2:
                                timestamp_part = parts[0].strip('[')
                                rest = parts[1]

                                if ': ' in rest:
                                    sender, text = rest.split(': ', 1)
                                else:
                                    sender = "Unknown"
                                    text = rest
                            else:
                                sender = "Unknown"
                                text = line
                        else:
                            # Direct message
                            sender = "Unknown"
                            text = line

                        message = {
                            'id': msg_id,
                            'sender': sender,
                            'text': text,
                            'timestamp': datetime.now().isoformat()
                        }

                        new_messages.append(message)
                        self.processed_messages.add(msg_id)

                if new_messages:
                    print(f"\n✨ Found {len(new_messages)} new messages!")

                    # Process each message
                    important_count = 0
                    tasks_extracted = []
                    decisions_extracted = []

                    for msg in new_messages:
                        result = self.processor.process_message(msg)

                        if result['is_important']:
                            important_count += 1
                            print(f"  ✅ {msg['sender']}: {msg['text'][:50]}...")

                            if result.get('tasks'):
                                tasks_extracted.extend(result['tasks'])
                            if result.get('decisions'):
                                decisions_extracted.extend(result['decisions'])

                    # Update context files
                    if important_count > 0:
                        context_data = {
                            'messages': new_messages,
                            'tasks': tasks_extracted,
                            'decisions': decisions_extracted
                        }

                        self.claude_sync.update_context(context_data)

                        print(f"\n📊 PROCESSED:")
                        print(f"  Important messages: {important_count}")
                        print(f"  Tasks extracted: {len(tasks_extracted)}")
                        print(f"  Decisions captured: {len(decisions_extracted)}")

                        if tasks_extracted:
                            print(f"\n📋 TASKS:")
                            for task in tasks_extracted:
                                print(f"    {task.get('assigned_to', 'unassigned'):10} | {task['description'][:50]}")

                        print(f"\n✅ Updated: {self.config['bridge_config']['context_file']}")

                    # Clear the file after processing
                    watch_file.write_text("# Paste WhatsApp messages here\n")
                    print("\n⏳ Watching for more messages...")

            except KeyboardInterrupt:
                print("\n\n👋 Bridge stopped")
                break
            except Exception as e:
                print(f"\n❌ Error: {e}")
                time.sleep(10)

            time.sleep(10)  # Check every 10 seconds

    def find_group_id(self):
        """Help find the WhatsApp group ID"""

        print("\n" + "=" * 60)
        print("🔍 FINDING YOUR FF APP GROUP ID")
        print("=" * 60)

        print("\n📱 Option 1: Check WhatsApp Web")
        print("1. Open web.whatsapp.com")
        print("2. Click on your FF app group")
        print("3. Click group info (top bar)")
        print("4. Look at the URL - it contains the group ID")
        print("   Example: https://web.whatsapp.com/#chat/E9GHI...")

        print("\n📱 Option 2: Export and Check")
        print("1. In WhatsApp mobile app, go to FF app group")
        print("2. Menu → More → Export chat (without media)")
        print("3. Send to yourself and check the header")

        print("\n📱 Option 3: Use WhatsApp Service (if accessible)")
        print("Run this on VF Server:")
        print("curl http://localhost:8081/groups | jq '.[] | select(.name | contains(\"FF\"))'")

        print("\n📝 Once you have the group ID:")
        print("1. Edit config.json")
        print("2. Replace 'PASTE_YOUR_GROUP_ID_HERE' with your actual group ID")
        print("3. Set manual_mode.enabled to false")
        print("4. Restart this bridge")

        print("\n" + "=" * 60)

if __name__ == "__main__":
    bridge = LiveBridge()

    if len(sys.argv) > 1 and sys.argv[1] == "find-group":
        bridge.find_group_id()
    else:
        # Check if group ID is configured
        config = bridge.config

        if config.get('whatsapp_config', {}).get('group_id') == 'PASTE_YOUR_GROUP_ID_HERE':
            print("\n⚠️ WhatsApp group ID not configured!")
            print("\nStarting in MANUAL MODE...")
            print("(Run './live_bridge.py find-group' for help finding your group ID)")
            print("")
            time.sleep(2)

        # Run in manual mode for now
        bridge.run_manual_mode()