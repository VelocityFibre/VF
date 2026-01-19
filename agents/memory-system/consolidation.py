#!/usr/bin/env python3
"""
Memory Consolidation - Like human sleep, consolidates and optimizes memories
Compresses old data, extracts patterns, and maintains memory quality.
"""

import os
import json
import psycopg2
from psycopg2.extras import RealDictCursor
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from anthropic import Anthropic


class MemoryConsolidation:
    """
    Memory consolidation system - the AI equivalent of sleep.

    Functions:
    - Compress old conversations into summaries
    - Extract key patterns and learnings
    - Archive low-value data
    - Strengthen important memories
    """

    def __init__(
        self,
        neon_url: Optional[str] = None,
        anthropic_api_key: Optional[str] = None
    ):
        """
        Initialize memory consolidation system.

        Args:
            neon_url: Neon PostgreSQL connection string
            anthropic_api_key: Anthropic API key for summarization
        """
        self.neon_url = neon_url or os.environ.get("NEON_DATABASE_URL")
        if not self.neon_url:
            raise ValueError("NEON_DATABASE_URL required")

        self.connection = None

        # Anthropic for summarization
        api_key = anthropic_api_key or os.environ.get("ANTHROPIC_API_KEY")
        self.anthropic = Anthropic(api_key=api_key) if api_key else None

        self._init_schema()

        print(f"✅ Memory Consolidation initialized")
        print(f"   Summarization: {'Enabled' if self.anthropic else 'Disabled'}")

    def _connect(self):
        """Connect to database."""
        if not self.connection or self.connection.closed:
            self.connection = psycopg2.connect(
                self.neon_url,
                cursor_factory=RealDictCursor
            )
        return self.connection

    def _init_schema(self):
        """Create schema for consolidation tracking."""
        schema_sql = """
        -- Consolidated memories (archived summaries)
        CREATE TABLE IF NOT EXISTS consolidated_memories (
            id SERIAL PRIMARY KEY,
            memory_type VARCHAR(100) NOT NULL,  -- 'conversation', 'performance', 'knowledge'
            period_start TIMESTAMP NOT NULL,
            period_end TIMESTAMP NOT NULL,
            summary TEXT NOT NULL,
            key_points JSONB DEFAULT '[]'::jsonb,
            original_count INTEGER DEFAULT 0,
            compression_ratio FLOAT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            metadata JSONB DEFAULT '{}'::jsonb
        );

        -- Consolidation runs (track when consolidation happened)
        CREATE TABLE IF NOT EXISTS consolidation_runs (
            id SERIAL PRIMARY KEY,
            run_type VARCHAR(100) NOT NULL,
            records_processed INTEGER DEFAULT 0,
            records_archived INTEGER DEFAULT 0,
            records_deleted INTEGER DEFAULT 0,
            duration_seconds FLOAT,
            status VARCHAR(50) DEFAULT 'completed',
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            metadata JSONB DEFAULT '{}'::jsonb
        );

        -- Indexes
        CREATE INDEX IF NOT EXISTS idx_consolidated_type ON consolidated_memories(memory_type);
        CREATE INDEX IF NOT EXISTS idx_consolidated_period ON consolidated_memories(period_start, period_end);
        """

        try:
            conn = self._connect()
            with conn.cursor() as cursor:
                cursor.execute(schema_sql)
                conn.commit()
            print("   Schema initialized")
        except Exception as e:
            print(f"   Warning: Schema init failed: {e}")

    def consolidate_conversations(
        self,
        older_than_days: int = 30,
        summarize: bool = True
    ) -> Dict[str, Any]:
        """
        Consolidate old conversations into summaries.

        Args:
            older_than_days: Consolidate conversations older than this
            summarize: Whether to generate AI summaries

        Returns:
            Consolidation results
        """
        start_time = datetime.now()
        cutoff_date = datetime.now() - timedelta(days=older_than_days)

        conn = self._connect()

        # Find old conversations
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT c.*, COUNT(m.id) as message_count
                FROM conversations c
                LEFT JOIN messages m ON c.id = m.conversation_id
                WHERE c.created_at < %s
                  AND c.id NOT IN (
                      SELECT DISTINCT metadata->>'conversation_id'::integer
                      FROM consolidated_memories
                      WHERE memory_type = 'conversation'
                        AND metadata ? 'conversation_id'
                  )
                GROUP BY c.id
                HAVING COUNT(m.id) > 0
                LIMIT 100
            """, (cutoff_date,))

            old_conversations = cursor.fetchall()

        consolidated_count = 0
        total_messages = 0

        for conv in old_conversations:
            # Get messages
            with conn.cursor() as cursor:
                cursor.execute("""
                    SELECT role, content FROM messages
                    WHERE conversation_id = %s
                    ORDER BY timestamp
                """, (conv['id'],))

                messages = cursor.fetchall()

            if not messages:
                continue

            # Create summary
            if summarize and self.anthropic:
                summary = self._summarize_conversation([dict(m) for m in messages])
            else:
                summary = f"Conversation with {len(messages)} messages"

            # Extract key points
            key_points = self._extract_key_points([dict(m) for m in messages])

            # Store consolidated memory
            with conn.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO consolidated_memories
                    (memory_type, period_start, period_end, summary, key_points,
                     original_count, compression_ratio, metadata)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    'conversation',
                    conv['created_at'],
                    conv['updated_at'] or conv['created_at'],
                    summary,
                    json.dumps(key_points),
                    len(messages),
                    len(summary) / sum(len(m['content']) for m in messages),
                    json.dumps({
                        "conversation_id": conv['id'],
                        "user_id": conv['user_id'],
                        "session_id": conv['session_id']
                    })
                ))
                conn.commit()

            consolidated_count += 1
            total_messages += len(messages)

        # Record consolidation run
        duration = (datetime.now() - start_time).total_seconds()

        with conn.cursor() as cursor:
            cursor.execute("""
                INSERT INTO consolidation_runs
                (run_type, records_processed, records_archived, duration_seconds, metadata)
                VALUES (%s, %s, %s, %s, %s)
            """, (
                'conversation_consolidation',
                len(old_conversations),
                consolidated_count,
                duration,
                json.dumps({"older_than_days": older_than_days})
            ))
            conn.commit()

        return {
            "status": "completed",
            "conversations_consolidated": consolidated_count,
            "total_messages": total_messages,
            "duration_seconds": duration
        }

    def consolidate_performance_data(
        self,
        older_than_days: int = 60
    ) -> Dict[str, Any]:
        """
        Consolidate old performance metrics into aggregates.

        Args:
            older_than_days: Consolidate data older than this

        Returns:
            Consolidation results
        """
        start_time = datetime.now()
        cutoff_date = datetime.now() - timedelta(days=older_than_days)

        conn = self._connect()

        # Aggregate performance by agent and task type
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT
                    agent_id,
                    task_type,
                    COUNT(*) as total_attempts,
                    SUM(CASE WHEN success THEN 1 ELSE 0 END) as successes,
                    AVG(execution_time_ms) as avg_time,
                    MIN(timestamp) as period_start,
                    MAX(timestamp) as period_end
                FROM agent_performance
                WHERE timestamp < %s
                GROUP BY agent_id, task_type
                HAVING COUNT(*) >= 10
            """, (cutoff_date,))

            aggregates = cursor.fetchall()

        consolidated_count = 0

        for agg in aggregates:
            summary = f"Agent '{agg['agent_id']}' performed {agg['total_attempts']} {agg['task_type']} tasks with {agg['successes']/agg['total_attempts']*100:.1f}% success rate"

            key_points = {
                "agent_id": agg['agent_id'],
                "task_type": agg['task_type'],
                "success_rate": float(agg['successes']) / float(agg['total_attempts']),
                "avg_time_ms": float(agg['avg_time']) if agg['avg_time'] else 0
            }

            # Store consolidated memory
            with conn.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO consolidated_memories
                    (memory_type, period_start, period_end, summary, key_points, original_count, metadata)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT DO NOTHING
                """, (
                    'performance',
                    agg['period_start'],
                    agg['period_end'],
                    summary,
                    json.dumps(key_points),
                    agg['total_attempts'],
                    json.dumps({"agent_id": agg['agent_id'], "task_type": agg['task_type']})
                ))
                conn.commit()

            consolidated_count += 1

        duration = (datetime.now() - start_time).total_seconds()

        # Record run
        with conn.cursor() as cursor:
            cursor.execute("""
                INSERT INTO consolidation_runs
                (run_type, records_processed, records_archived, duration_seconds)
                VALUES (%s, %s, %s, %s)
            """, ('performance_consolidation', len(aggregates), consolidated_count, duration))
            conn.commit()

        return {
            "status": "completed",
            "aggregates_created": consolidated_count,
            "duration_seconds": duration
        }

    def archive_old_data(
        self,
        table_name: str,
        older_than_days: int,
        delete: bool = False
    ) -> int:
        """
        Archive or delete old data.

        Args:
            table_name: Table to archive from
            older_than_days: Archive data older than this
            delete: Whether to delete (vs just mark)

        Returns:
            Number of records affected
        """
        cutoff_date = datetime.now() - timedelta(days=older_than_days)
        conn = self._connect()

        if delete:
            with conn.cursor() as cursor:
                cursor.execute(f"""
                    DELETE FROM {table_name}
                    WHERE timestamp < %s
                """, (cutoff_date,))
                conn.commit()
                return cursor.rowcount
        else:
            # Just count for now (implement archiving logic as needed)
            with conn.cursor() as cursor:
                cursor.execute(f"""
                    SELECT COUNT(*) as count FROM {table_name}
                    WHERE timestamp < %s
                """, (cutoff_date,))
                result = cursor.fetchone()
                return result['count'] if result else 0

    def run_full_consolidation(
        self,
        conversation_days: int = 30,
        performance_days: int = 60
    ) -> Dict[str, Any]:
        """
        Run complete memory consolidation (like a full night's sleep).

        Args:
            conversation_days: Consolidate conversations older than this
            performance_days: Consolidate performance data older than this

        Returns:
            Complete consolidation results
        """
        print("\n💤 Starting memory consolidation (like sleep)...\n")

        start_time = datetime.now()

        # Consolidate conversations
        print("   📝 Consolidating conversations...")
        conv_result = self.consolidate_conversations(older_than_days=conversation_days)
        print(f"      ✓ {conv_result['conversations_consolidated']} conversations consolidated")

        # Consolidate performance data
        print("   📊 Consolidating performance data...")
        perf_result = self.consolidate_performance_data(older_than_days=performance_days)
        print(f"      ✓ {perf_result['aggregates_created']} performance aggregates created")

        duration = (datetime.now() - start_time).total_seconds()

        print(f"\n✅ Consolidation complete in {duration:.1f}s")

        return {
            "status": "completed",
            "duration_seconds": duration,
            "conversations": conv_result,
            "performance": perf_result
        }

    def get_consolidation_stats(self) -> Dict[str, Any]:
        """Get consolidation statistics."""
        conn = self._connect()

        with conn.cursor() as cursor:
            # Consolidated memories stats
            cursor.execute("""
                SELECT
                    memory_type,
                    COUNT(*) as count,
                    SUM(original_count) as total_original_records,
                    AVG(compression_ratio) as avg_compression
                FROM consolidated_memories
                GROUP BY memory_type
            """)
            memory_stats = [dict(s) for s in cursor.fetchall()]

            # Recent runs
            cursor.execute("""
                SELECT *
                FROM consolidation_runs
                ORDER BY timestamp DESC
                LIMIT 5
            """)
            recent_runs = [dict(r) for r in cursor.fetchall()]

            return {
                "consolidated_memories": memory_stats,
                "recent_runs": recent_runs
            }

    def _summarize_conversation(self, messages: List[Dict]) -> str:
        """Generate AI summary of conversation."""
        if not self.anthropic:
            return "Summary unavailable (no Anthropic API key)"

        # Format conversation
        conv_text = "\n".join([
            f"{msg['role']}: {msg['content']}"
            for msg in messages
        ])

        # Generate summary
        try:
            response = self.anthropic.messages.create(
                model="claude-3-haiku-20240307",
                max_tokens=200,
                messages=[{
                    "role": "user",
                    "content": f"Summarize this conversation in 2-3 sentences:\n\n{conv_text[:3000]}"
                }]
            )

            summary = response.content[0].text if response.content else "Summary failed"
            return summary

        except Exception as e:
            return f"Summary error: {str(e)}"

    def _extract_key_points(self, messages: List[Dict]) -> List[str]:
        """Extract key points from conversation."""
        # Simple extraction: first user query and key assistant responses
        user_queries = [m['content'][:100] for m in messages if m['role'] == 'user']
        return user_queries[:3]  # First 3 queries

    def close(self):
        """Close database connection."""
        if self.connection and not self.connection.closed:
            self.connection.close()

    def __del__(self):
        """Cleanup."""
        self.close()


def main():
    """Demo memory consolidation."""
    print("\n" + "="*70)
    print("MEMORY CONSOLIDATION - Sleep-like Memory Optimization Demo")
    print("="*70 + "\n")

    try:
        consolidator = MemoryConsolidation()

        # Run full consolidation
        results = consolidator.run_full_consolidation(
            conversation_days=7,  # Short for demo
            performance_days=14
        )

        print("\n" + "="*70)
        print("CONSOLIDATION RESULTS")
        print("="*70)
        print(json.dumps(results, indent=2, default=str))

        # Get stats
        print("\n" + "="*70)
        print("CONSOLIDATION STATISTICS")
        print("="*70)
        stats = consolidator.get_consolidation_stats()
        print(json.dumps(stats, indent=2, default=str))

        print("\n✅ Memory consolidation demo completed!")

    except Exception as e:
        print(f"❌ Error: {e}")
        print("   Make sure NEON_DATABASE_URL and ANTHROPIC_API_KEY are set")


if __name__ == "__main__":
    main()
