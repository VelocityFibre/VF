#!/usr/bin/env python3
"""
Database operations for FF Team Bridge
Stores messages and extracted information in Neon PostgreSQL
"""

import os
import json
import logging
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime, timedelta
from typing import Dict, Any, List, Set, Optional

logger = logging.getLogger(__name__)

class BridgeDatabase:
    """Database interface for the bridge service"""

    def __init__(self):
        self.connection_string = os.getenv("NEON_DATABASE_URL")
        self.conn = None
        self.initialized = False

    async def initialize(self):
        """Initialize database connection and create tables if needed"""

        if not self.connection_string:
            logger.warning("No database URL configured, using in-memory storage only")
            self.initialized = False
            return False

        try:
            # Connect to database
            self.conn = psycopg2.connect(self.connection_string)

            # Create tables if they don't exist
            await self._create_tables()

            self.initialized = True
            logger.info("Database initialized successfully")
            return True

        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")
            self.initialized = False
            return False

    async def _create_tables(self):
        """Create necessary tables if they don't exist"""

        try:
            with self.conn.cursor() as cursor:
                # Developer communications table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS developer_communications (
                        id SERIAL PRIMARY KEY,
                        message_id VARCHAR(255) UNIQUE,
                        group_id VARCHAR(255),
                        sender_phone VARCHAR(50),
                        sender_name VARCHAR(100),
                        message_text TEXT,
                        message_type VARCHAR(50) DEFAULT 'text',
                        attachments JSONB,
                        timestamp TIMESTAMPTZ DEFAULT NOW(),
                        processed BOOLEAN DEFAULT FALSE,

                        -- Extracted metadata
                        contains_task BOOLEAN DEFAULT FALSE,
                        contains_decision BOOLEAN DEFAULT FALSE,
                        contains_bug BOOLEAN DEFAULT FALSE,
                        contains_question BOOLEAN DEFAULT FALSE,
                        is_important BOOLEAN DEFAULT FALSE,

                        -- Processing results
                        extracted_tasks JSONB,
                        extracted_decisions JSONB,
                        extracted_bugs JSONB,
                        extracted_questions JSONB,
                        code_references JSONB,

                        -- Claude sync
                        synced_to_claude BOOLEAN DEFAULT FALSE,
                        claude_context_id VARCHAR(255),

                        created_at TIMESTAMPTZ DEFAULT NOW(),
                        updated_at TIMESTAMPTZ DEFAULT NOW()
                    )
                """)

                # Create indexes
                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_group_timestamp
                    ON developer_communications(group_id, timestamp DESC)
                """)

                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_unprocessed
                    ON developer_communications(processed, timestamp)
                """)

                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_important
                    ON developer_communications(is_important, timestamp DESC)
                """)

                # Developer tasks table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS developer_tasks (
                        id SERIAL PRIMARY KEY,
                        message_id VARCHAR(255) REFERENCES developer_communications(message_id),
                        task_description TEXT,
                        assigned_to VARCHAR(100),
                        status VARCHAR(50) DEFAULT 'pending',
                        priority VARCHAR(20) DEFAULT 'normal',
                        created_by VARCHAR(100),
                        created_at TIMESTAMPTZ DEFAULT NOW(),
                        started_at TIMESTAMPTZ,
                        completed_at TIMESTAMPTZ,
                        claude_session_id VARCHAR(255),
                        notes TEXT,

                        INDEX idx_status_assigned (status, assigned_to)
                    )
                """)

                self.conn.commit()
                logger.info("Database tables created/verified")

        except Exception as e:
            logger.error(f"Error creating tables: {e}")
            if self.conn:
                self.conn.rollback()
            raise

    async def store_message(self, message: Dict[str, Any], extracted: Dict[str, Any]):
        """Store a message and its extracted information"""

        if not self.initialized:
            logger.warning("Database not initialized, skipping store")
            return False

        try:
            with self.conn.cursor() as cursor:
                # Insert or update the message
                cursor.execute("""
                    INSERT INTO developer_communications (
                        message_id, group_id, sender_phone, sender_name,
                        message_text, timestamp, processed,
                        contains_task, contains_decision, contains_bug,
                        contains_question, is_important,
                        extracted_tasks, extracted_decisions, extracted_bugs,
                        extracted_questions, code_references
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (message_id)
                    DO UPDATE SET
                        processed = TRUE,
                        updated_at = NOW(),
                        extracted_tasks = EXCLUDED.extracted_tasks,
                        extracted_decisions = EXCLUDED.extracted_decisions,
                        extracted_bugs = EXCLUDED.extracted_bugs,
                        extracted_questions = EXCLUDED.extracted_questions,
                        code_references = EXCLUDED.code_references
                """, (
                    message.get('id'),
                    message.get('group_id'),
                    message.get('sender_phone'),
                    message.get('sender'),
                    message.get('text'),
                    message.get('timestamp', datetime.now()),
                    True,  # processed
                    len(extracted.get('tasks', [])) > 0,
                    len(extracted.get('decisions', [])) > 0,
                    len(extracted.get('bugs', [])) > 0,
                    len(extracted.get('questions', [])) > 0,
                    extracted.get('is_important', False),
                    json.dumps(extracted.get('tasks', [])),
                    json.dumps(extracted.get('decisions', [])),
                    json.dumps(extracted.get('bugs', [])),
                    json.dumps(extracted.get('questions', [])),
                    json.dumps(extracted.get('code_references', []))
                ))

                # Store tasks in separate table
                for task in extracted.get('tasks', []):
                    cursor.execute("""
                        INSERT INTO developer_tasks (
                            message_id, task_description, assigned_to,
                            status, priority, created_by
                        ) VALUES (%s, %s, %s, %s, %s, %s)
                    """, (
                        message.get('id'),
                        task.get('description'),
                        task.get('assigned_to', 'unassigned'),
                        'pending',
                        'normal',
                        message.get('sender')
                    ))

                self.conn.commit()
                return True

        except Exception as e:
            logger.error(f"Error storing message: {e}")
            if self.conn:
                self.conn.rollback()
            return False

    async def get_processed_message_ids(self) -> Set[str]:
        """Get set of already processed message IDs"""

        if not self.initialized:
            return set()

        try:
            with self.conn.cursor() as cursor:
                cursor.execute("""
                    SELECT message_id
                    FROM developer_communications
                    WHERE message_id IS NOT NULL
                """)

                return {row[0] for row in cursor.fetchall()}

        except Exception as e:
            logger.error(f"Error getting processed messages: {e}")
            return set()

    async def get_recent_context(self, hours: int = 24) -> Dict[str, Any]:
        """Get recent context data for Claude sync"""

        if not self.initialized:
            return self._empty_context()

        try:
            since = datetime.now() - timedelta(hours=hours)

            with self.conn.cursor(cursor_factory=RealDictCursor) as cursor:
                # Get recent messages
                cursor.execute("""
                    SELECT
                        message_id as id,
                        sender_name as sender,
                        sender_phone,
                        message_text as text,
                        timestamp,
                        is_important,
                        extracted_tasks,
                        extracted_decisions,
                        extracted_bugs,
                        extracted_questions
                    FROM developer_communications
                    WHERE timestamp > %s
                    ORDER BY timestamp DESC
                    LIMIT 100
                """, (since,))

                messages = cursor.fetchall()

                # Get recent tasks
                cursor.execute("""
                    SELECT
                        task_description as description,
                        assigned_to,
                        status,
                        priority,
                        created_by as sender,
                        created_at as timestamp
                    FROM developer_tasks
                    WHERE created_at > %s
                    ORDER BY created_at DESC
                    LIMIT 50
                """, (since,))

                tasks = cursor.fetchall()

                # Aggregate extracted data
                all_decisions = []
                all_bugs = []
                all_questions = []

                for msg in messages:
                    if msg['extracted_decisions']:
                        all_decisions.extend(json.loads(msg['extracted_decisions']))
                    if msg['extracted_bugs']:
                        all_bugs.extend(json.loads(msg['extracted_bugs']))
                    if msg['extracted_questions']:
                        all_questions.extend(json.loads(msg['extracted_questions']))

                return {
                    'messages': messages,
                    'tasks': tasks,
                    'decisions': all_decisions,
                    'bugs': all_bugs,
                    'questions': all_questions
                }

        except Exception as e:
            logger.error(f"Error getting recent context: {e}")
            return self._empty_context()

    def _empty_context(self) -> Dict[str, Any]:
        """Return empty context structure"""
        return {
            'messages': [],
            'tasks': [],
            'decisions': [],
            'bugs': [],
            'questions': []
        }

    async def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()
            logger.info("Database connection closed")