#!/usr/bin/env python3
"""
FF Team Bridge Service
Connects WhatsApp FF App group to Claude context
"""

import asyncio
import json
import os
import sys
import time
import requests
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, List

# Add parent directories to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from message_processor import MessageProcessor
from claude_sync import ClaudeContextSync
from database import BridgeDatabase

# Configuration
WHATSAPP_SERVICE_URL = os.getenv("WHATSAPP_SERVICE_URL", "http://100.96.203.105:8081")
POLL_INTERVAL = int(os.getenv("BRIDGE_POLL_INTERVAL", "60"))  # seconds
GROUP_NAME_PATTERN = os.getenv("FF_GROUP_PATTERN", "FF")  # Pattern to find FF App group

# Logging setup
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bridge.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class FFTeamBridge:
    """Main bridge service that connects WhatsApp to Claude"""

    def __init__(self):
        self.group_id = None
        self.last_message_timestamp = None
        self.processor = MessageProcessor()
        self.claude_sync = ClaudeContextSync()
        self.database = BridgeDatabase()
        self.processed_message_ids = set()

    async def initialize(self):
        """Initialize the bridge service"""
        logger.info("Initializing FF Team Bridge...")

        # Find the FF App group
        self.group_id = await self._find_ff_group()
        if not self.group_id:
            logger.error("Could not find FF App group!")
            return False

        logger.info(f"Found FF App group: {self.group_id}")

        # Initialize database
        await self.database.initialize()

        # Load previously processed messages
        self.processed_message_ids = await self.database.get_processed_message_ids()
        logger.info(f"Loaded {len(self.processed_message_ids)} processed messages")

        return True

    async def _find_ff_group(self) -> str:
        """Find the FF App group ID"""
        try:
            response = requests.get(
                f"{WHATSAPP_SERVICE_URL}/api/groups",
                timeout=10
            )

            if response.status_code == 200:
                groups = response.json()
                for group in groups:
                    if GROUP_NAME_PATTERN in group.get('name', ''):
                        return group['id']

            logger.error(f"Failed to get groups: {response.status_code}")
            return None

        except Exception as e:
            logger.error(f"Error finding FF group: {e}")
            return None

    async def poll_messages(self):
        """Poll for new messages from the WhatsApp group"""
        if not self.group_id:
            logger.warning("No group ID set, skipping poll")
            return []

        try:
            # Get messages from the last hour (or since last poll)
            since = self.last_message_timestamp or (
                datetime.now() - timedelta(hours=1)
            ).isoformat()

            response = requests.get(
                f"{WHATSAPP_SERVICE_URL}/api/groups/{self.group_id}/messages",
                params={"since": since},
                timeout=10
            )

            if response.status_code == 200:
                messages = response.json()
                new_messages = []

                for msg in messages:
                    msg_id = msg.get('id')
                    if msg_id and msg_id not in self.processed_message_ids:
                        new_messages.append(msg)
                        self.processed_message_ids.add(msg_id)

                if new_messages:
                    logger.info(f"Found {len(new_messages)} new messages")
                    self.last_message_timestamp = datetime.now().isoformat()

                return new_messages

            logger.error(f"Failed to get messages: {response.status_code}")
            return []

        except Exception as e:
            logger.error(f"Error polling messages: {e}")
            return []

    async def process_messages(self, messages: List[Dict[str, Any]]):
        """Process new messages"""
        if not messages:
            return

        logger.info(f"Processing {len(messages)} messages...")

        for msg in messages:
            try:
                # Extract message details
                message_data = {
                    'id': msg.get('id'),
                    'group_id': self.group_id,
                    'sender': msg.get('sender', 'Unknown'),
                    'sender_phone': msg.get('phone', ''),
                    'text': msg.get('text', ''),
                    'timestamp': msg.get('timestamp', datetime.now().isoformat())
                }

                # Process the message
                extracted = await self.processor.process(message_data)

                # Store in database
                await self.database.store_message(message_data, extracted)

                # Log what we found
                if any(extracted.values()):
                    logger.info(f"Extracted from {message_data['sender']}: "
                              f"{len(extracted.get('tasks', []))} tasks, "
                              f"{len(extracted.get('decisions', []))} decisions")

            except Exception as e:
                logger.error(f"Error processing message: {e}")

        # Update Claude context after processing all messages
        await self.update_claude_context()

    async def update_claude_context(self):
        """Update the Claude context files"""
        try:
            # Get recent messages and extractions from database
            recent_data = await self.database.get_recent_context(hours=24)

            # Update context files
            await self.claude_sync.update_context(recent_data)

            logger.info("Claude context updated successfully")

        except Exception as e:
            logger.error(f"Error updating Claude context: {e}")

    async def run(self):
        """Main service loop"""
        logger.info("Starting FF Team Bridge service...")

        # Initialize
        if not await self.initialize():
            logger.error("Failed to initialize, exiting")
            return

        logger.info(f"Bridge service running, polling every {POLL_INTERVAL} seconds")

        while True:
            try:
                # Poll for new messages
                new_messages = await self.poll_messages()

                # Process them
                if new_messages:
                    await self.process_messages(new_messages)

                # Wait before next poll
                await asyncio.sleep(POLL_INTERVAL)

            except KeyboardInterrupt:
                logger.info("Shutting down bridge service...")
                break

            except Exception as e:
                logger.error(f"Error in main loop: {e}")
                await asyncio.sleep(POLL_INTERVAL)

    async def send_to_group(self, message: str):
        """Send a message to the FF App group"""
        if not self.group_id:
            logger.warning("No group ID set, cannot send message")
            return False

        try:
            response = requests.post(
                f"{WHATSAPP_SERVICE_URL}/api/send-group",
                json={
                    "group_id": self.group_id,
                    "message": message
                },
                timeout=30
            )

            if response.status_code == 200:
                logger.info("Message sent to group successfully")
                return True

            logger.error(f"Failed to send message: {response.status_code}")
            return False

        except Exception as e:
            logger.error(f"Error sending message: {e}")
            return False

def main():
    """Entry point"""
    bridge = FFTeamBridge()

    # Run the service
    asyncio.run(bridge.run())

if __name__ == "__main__":
    main()