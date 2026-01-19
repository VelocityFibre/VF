#!/usr/bin/env python3
"""
Persistent Conversation Memory - Cross-session memory storage
Stores conversations in Neon + creates embeddings for semantic search.
"""

import os
import json
import psycopg2
from psycopg2.extras import RealDictCursor
from typing import List, Dict, Any, Optional
from datetime import datetime
from .vector_memory import VectorMemory


class PersistentMemory:
    """
    Persistent memory layer that stores conversations across sessions.

    Combines:
    - Neon PostgreSQL for structured conversation storage
    - Qdrant for semantic search of past conversations
    """

    def __init__(
        self,
        neon_url: Optional[str] = None,
        vector_memory: Optional[VectorMemory] = None
    ):
        """
        Initialize persistent memory.

        Args:
            neon_url: Neon PostgreSQL connection string
            vector_memory: VectorMemory instance for semantic search
        """
        # Database connection
        self.neon_url = neon_url or os.environ.get("NEON_DATABASE_URL")
        if not self.neon_url:
            raise ValueError("NEON_DATABASE_URL required for persistent memory")

        self.connection = None

        # Vector memory for semantic search
        self.vector_memory = vector_memory or VectorMemory(
            collection_name="conversation_memory"
        )

        # Initialize database schema
        self._init_schema()

        print(f"✅ Persistent Memory initialized")
        print(f"   Database: Neon PostgreSQL")
        print(f"   Semantic Search: Enabled")

    def _connect(self):
        """Connect to database."""
        if not self.connection or self.connection.closed:
            self.connection = psycopg2.connect(
                self.neon_url,
                cursor_factory=RealDictCursor
            )
        return self.connection

    def _init_schema(self):
        """Create database schema for conversation storage."""
        schema_sql = """
        -- Conversations table
        CREATE TABLE IF NOT EXISTS conversations (
            id SERIAL PRIMARY KEY,
            user_id VARCHAR(255) NOT NULL,
            session_id VARCHAR(255) NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            summary TEXT,
            metadata JSONB DEFAULT '{}'::jsonb
        );

        -- Messages table
        CREATE TABLE IF NOT EXISTS messages (
            id SERIAL PRIMARY KEY,
            conversation_id INTEGER REFERENCES conversations(id) ON DELETE CASCADE,
            role VARCHAR(50) NOT NULL,  -- 'user' or 'assistant'
            content TEXT NOT NULL,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            metadata JSONB DEFAULT '{}'::jsonb
        );

        -- Agent actions table (for tracking which agents were used)
        CREATE TABLE IF NOT EXISTS agent_actions (
            id SERIAL PRIMARY KEY,
            conversation_id INTEGER REFERENCES conversations(id) ON DELETE CASCADE,
            agent_id VARCHAR(255) NOT NULL,
            action_type VARCHAR(100) NOT NULL,  -- 'query', 'tool_use', etc.
            input_data JSONB,
            output_data JSONB,
            success BOOLEAN DEFAULT true,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        -- Indexes for performance
        CREATE INDEX IF NOT EXISTS idx_conversations_user_id ON conversations(user_id);
        CREATE INDEX IF NOT EXISTS idx_conversations_session_id ON conversations(session_id);
        CREATE INDEX IF NOT EXISTS idx_messages_conversation_id ON messages(conversation_id);
        CREATE INDEX IF NOT EXISTS idx_agent_actions_conversation_id ON agent_actions(conversation_id);
        """

        try:
            conn = self._connect()
            with conn.cursor() as cursor:
                cursor.execute(schema_sql)
                conn.commit()
            print("   Schema initialized")
        except Exception as e:
            print(f"   Warning: Schema init failed: {e}")

    def save_conversation(
        self,
        user_id: str,
        session_id: str,
        messages: List[Dict[str, Any]],
        summary: Optional[str] = None,
        metadata: Optional[Dict] = None
    ) -> int:
        """
        Save a conversation to persistent storage.

        Args:
            user_id: User identifier
            session_id: Session identifier
            messages: List of message dicts with 'role' and 'content'
            summary: Optional conversation summary
            metadata: Additional metadata

        Returns:
            Conversation ID
        """
        conn = self._connect()

        try:
            with conn.cursor() as cursor:
                # Insert conversation
                cursor.execute("""
                    INSERT INTO conversations (user_id, session_id, summary, metadata)
                    VALUES (%s, %s, %s, %s)
                    RETURNING id
                """, (user_id, session_id, summary, json.dumps(metadata or {})))

                conversation_id = cursor.fetchone()['id']

                # Insert messages
                for msg in messages:
                    cursor.execute("""
                        INSERT INTO messages (conversation_id, role, content, metadata)
                        VALUES (%s, %s, %s, %s)
                    """, (
                        conversation_id,
                        msg.get('role', 'user'),
                        msg.get('content', ''),
                        json.dumps(msg.get('metadata', {}))
                    ))

                conn.commit()

                # Store in vector memory for semantic search
                if summary:
                    self.vector_memory.store_interaction(
                        query=summary,
                        response=self._extract_main_response(messages),
                        agent_id="conversation",
                        metadata={
                            "user_id": user_id,
                            "session_id": session_id,
                            "conversation_id": conversation_id,
                            "message_count": len(messages)
                        }
                    )

                return conversation_id

        except Exception as e:
            conn.rollback()
            raise Exception(f"Failed to save conversation: {e}")

    def load_conversation(self, conversation_id: int) -> Dict[str, Any]:
        """
        Load a conversation by ID.

        Args:
            conversation_id: Conversation ID

        Returns:
            Conversation data with messages
        """
        conn = self._connect()

        with conn.cursor() as cursor:
            # Get conversation
            cursor.execute("""
                SELECT * FROM conversations WHERE id = %s
            """, (conversation_id,))
            conversation = cursor.fetchone()

            if not conversation:
                return None

            # Get messages
            cursor.execute("""
                SELECT * FROM messages
                WHERE conversation_id = %s
                ORDER BY timestamp ASC
            """, (conversation_id,))
            messages = cursor.fetchall()

            return {
                "id": conversation['id'],
                "user_id": conversation['user_id'],
                "session_id": conversation['session_id'],
                "summary": conversation['summary'],
                "created_at": conversation['created_at'].isoformat(),
                "metadata": conversation['metadata'],
                "messages": [dict(msg) for msg in messages]
            }

    def get_user_conversations(
        self,
        user_id: str,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Get recent conversations for a user.

        Args:
            user_id: User identifier
            limit: Maximum number of conversations

        Returns:
            List of conversation summaries
        """
        conn = self._connect()

        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT
                    c.id,
                    c.session_id,
                    c.summary,
                    c.created_at,
                    c.metadata,
                    COUNT(m.id) as message_count
                FROM conversations c
                LEFT JOIN messages m ON c.id = m.conversation_id
                WHERE c.user_id = %s
                GROUP BY c.id
                ORDER BY c.created_at DESC
                LIMIT %s
            """, (user_id, limit))

            conversations = cursor.fetchall()
            return [dict(conv) for conv in conversations]

    def track_agent_action(
        self,
        conversation_id: int,
        agent_id: str,
        action_type: str,
        input_data: Optional[Dict] = None,
        output_data: Optional[Dict] = None,
        success: bool = True
    ):
        """
        Track an agent action within a conversation.

        Args:
            conversation_id: Conversation ID
            agent_id: Agent identifier
            action_type: Type of action
            input_data: Input data
            output_data: Output data
            success: Whether action succeeded
        """
        conn = self._connect()

        try:
            with conn.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO agent_actions
                    (conversation_id, agent_id, action_type, input_data, output_data, success)
                    VALUES (%s, %s, %s, %s, %s, %s)
                """, (
                    conversation_id,
                    agent_id,
                    action_type,
                    json.dumps(input_data or {}),
                    json.dumps(output_data or {}),
                    success
                ))
                conn.commit()
        except Exception as e:
            conn.rollback()
            print(f"   Warning: Failed to track action: {e}")

    def find_similar_conversations(
        self,
        query: str,
        user_id: Optional[str] = None,
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Find similar past conversations using semantic search.

        Args:
            query: Search query
            user_id: Optional user filter
            limit: Maximum results

        Returns:
            Similar conversations with similarity scores
        """
        # Use vector memory to find similar
        similar = self.vector_memory.recall_similar(
            query=query,
            limit=limit * 2  # Get more, then filter
        )

        # Filter by user_id if specified
        if user_id:
            similar = [
                s for s in similar
                if s.get('metadata', {}).get('user_id') == user_id
            ]

        # Load full conversation data
        results = []
        for mem in similar[:limit]:
            conv_id = mem.get('metadata', {}).get('conversation_id')
            if conv_id:
                conv = self.load_conversation(conv_id)
                if conv:
                    conv['similarity_score'] = mem['score']
                    results.append(conv)

        return results

    def get_conversation_stats(self, user_id: Optional[str] = None) -> Dict[str, Any]:
        """Get conversation statistics."""
        conn = self._connect()

        with conn.cursor() as cursor:
            if user_id:
                cursor.execute("""
                    SELECT
                        COUNT(DISTINCT c.id) as total_conversations,
                        COUNT(m.id) as total_messages,
                        COUNT(DISTINCT c.session_id) as total_sessions
                    FROM conversations c
                    LEFT JOIN messages m ON c.id = m.conversation_id
                    WHERE c.user_id = %s
                """, (user_id,))
            else:
                cursor.execute("""
                    SELECT
                        COUNT(DISTINCT c.id) as total_conversations,
                        COUNT(m.id) as total_messages,
                        COUNT(DISTINCT c.user_id) as total_users,
                        COUNT(DISTINCT c.session_id) as total_sessions
                    FROM conversations c
                    LEFT JOIN messages m ON c.id = m.conversation_id
                """)

            stats = cursor.fetchone()
            return dict(stats) if stats else {}

    def _extract_main_response(self, messages: List[Dict]) -> str:
        """Extract main assistant response from messages."""
        assistant_msgs = [
            m.get('content', '')
            for m in messages
            if m.get('role') == 'assistant'
        ]
        return ' '.join(assistant_msgs)[:500]  # First 500 chars

    def _generate_summary(self, messages: List[Dict]) -> str:
        """Generate a summary from messages (simple version)."""
        # Simple summary: first user message + first assistant response
        user_msg = next(
            (m.get('content') for m in messages if m.get('role') == 'user'),
            ""
        )
        assistant_msg = next(
            (m.get('content') for m in messages if m.get('role') == 'assistant'),
            ""
        )
        return f"{user_msg[:100]}... -> {assistant_msg[:100]}..."

    def close(self):
        """Close database connection."""
        if self.connection and not self.connection.closed:
            self.connection.close()

    def __del__(self):
        """Cleanup."""
        self.close()


def main():
    """Demo persistent memory system."""
    print("\n" + "="*70)
    print("PERSISTENT MEMORY SYSTEM - Cross-session Storage Demo")
    print("="*70 + "\n")

    try:
        memory = PersistentMemory()

        # Save a sample conversation
        print("💾 Saving sample conversation...\n")

        sample_messages = [
            {"role": "user", "content": "How do I query the database?"},
            {"role": "assistant", "content": "You can use the Neon agent to query the PostgreSQL database. Use SQL queries like SELECT * FROM contractors."},
            {"role": "user", "content": "Show me all active contractors"},
            {"role": "assistant", "content": "Here are the active contractors: [list of contractors]"}
        ]

        conv_id = memory.save_conversation(
            user_id="demo_user",
            session_id="session_001",
            messages=sample_messages,
            summary="Database query help",
            metadata={"topic": "database"}
        )

        print(f"✓ Saved conversation ID: {conv_id}\n")

        # Load it back
        print("📖 Loading conversation...\n")
        loaded = memory.load_conversation(conv_id)
        print(f"   Messages: {len(loaded['messages'])}")
        print(f"   Summary: {loaded['summary']}")

        # Get stats
        print("\n" + "="*70)
        print("STATISTICS")
        print("="*70)
        stats = memory.get_conversation_stats()
        print(json.dumps(stats, indent=2))

        print("\n✅ Persistent memory demo completed!")

    except Exception as e:
        print(f"❌ Error: {e}")
        print("   Make sure NEON_DATABASE_URL is set and Qdrant is running")


if __name__ == "__main__":
    main()
