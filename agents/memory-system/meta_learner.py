#!/usr/bin/env python3
"""
Meta-Learning Layer - Tracks and learns from agent performance
Enables continuous improvement by learning what works best.
"""

import os
import json
import psycopg2
from psycopg2.extras import RealDictCursor
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from collections import defaultdict


class MetaLearner:
    """
    Meta-learning system that tracks agent performance and learns patterns.

    Equivalent to human neuroplasticity - getting better at tasks through repetition.
    """

    def __init__(self, neon_url: Optional[str] = None):
        """
        Initialize meta-learner.

        Args:
            neon_url: Neon PostgreSQL connection string
        """
        self.neon_url = neon_url or os.environ.get("NEON_DATABASE_URL")
        if not self.neon_url:
            raise ValueError("NEON_DATABASE_URL required for meta-learning")

        self.connection = None
        self._init_schema()

        print(f"✅ Meta-Learner initialized")
        print(f"   Tracking: Agent performance, success patterns")

    def _connect(self):
        """Connect to database."""
        if not self.connection or self.connection.closed:
            self.connection = psycopg2.connect(
                self.neon_url,
                cursor_factory=RealDictCursor
            )
        return self.connection

    def _init_schema(self):
        """Create database schema for meta-learning."""
        schema_sql = """
        -- Agent performance tracking
        CREATE TABLE IF NOT EXISTS agent_performance (
            id SERIAL PRIMARY KEY,
            agent_id VARCHAR(255) NOT NULL,
            task_type VARCHAR(255) NOT NULL,
            query_pattern VARCHAR(500),
            success BOOLEAN NOT NULL,
            execution_time_ms INTEGER,
            error_message TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            metadata JSONB DEFAULT '{}'::jsonb
        );

        -- Agent routing decisions
        CREATE TABLE IF NOT EXISTS routing_history (
            id SERIAL PRIMARY KEY,
            query TEXT NOT NULL,
            selected_agent VARCHAR(255) NOT NULL,
            confidence_score FLOAT,
            alternative_agents JSONB,
            success BOOLEAN,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        -- Learning insights (accumulated knowledge)
        CREATE TABLE IF NOT EXISTS learning_insights (
            id SERIAL PRIMARY KEY,
            insight_type VARCHAR(100) NOT NULL,  -- 'pattern', 'rule', 'preference'
            content TEXT NOT NULL,
            confidence FLOAT DEFAULT 0.5,
            evidence_count INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            metadata JSONB DEFAULT '{}'::jsonb
        );

        -- Indexes
        CREATE INDEX IF NOT EXISTS idx_agent_perf_agent_id ON agent_performance(agent_id);
        CREATE INDEX IF NOT EXISTS idx_agent_perf_task_type ON agent_performance(task_type);
        CREATE INDEX IF NOT EXISTS idx_routing_agent ON routing_history(selected_agent);
        CREATE INDEX IF NOT EXISTS idx_insights_type ON learning_insights(insight_type);
        """

        try:
            conn = self._connect()
            with conn.cursor() as cursor:
                cursor.execute(schema_sql)
                conn.commit()
            print("   Schema initialized")
        except Exception as e:
            print(f"   Warning: Schema init failed: {e}")

    def track_outcome(
        self,
        agent_id: str,
        task_type: str,
        query: str,
        success: bool,
        execution_time_ms: Optional[int] = None,
        error_message: Optional[str] = None,
        metadata: Optional[Dict] = None
    ):
        """
        Track the outcome of an agent action.

        Args:
            agent_id: Which agent was used
            task_type: Type of task (e.g., 'database_query', 'vps_monitor')
            query: The user's query
            success: Whether it succeeded
            execution_time_ms: How long it took
            error_message: Error if failed
            metadata: Additional data
        """
        conn = self._connect()

        try:
            with conn.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO agent_performance
                    (agent_id, task_type, query_pattern, success, execution_time_ms, error_message, metadata)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                """, (
                    agent_id,
                    task_type,
                    query[:500],  # Truncate long queries
                    success,
                    execution_time_ms,
                    error_message,
                    json.dumps(metadata or {})
                ))
                conn.commit()

            # Extract learning insights
            self._extract_insights(agent_id, task_type, success)

        except Exception as e:
            conn.rollback()
            print(f"   Warning: Failed to track outcome: {e}")

    def track_routing(
        self,
        query: str,
        selected_agent: str,
        confidence_score: float,
        alternatives: Optional[List[str]] = None,
        success: Optional[bool] = None
    ):
        """
        Track a routing decision.

        Args:
            query: User query
            selected_agent: Which agent was selected
            confidence_score: Routing confidence
            alternatives: Other agents considered
            success: Whether routing was successful
        """
        conn = self._connect()

        try:
            with conn.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO routing_history
                    (query, selected_agent, confidence_score, alternative_agents, success)
                    VALUES (%s, %s, %s, %s, %s)
                """, (
                    query,
                    selected_agent,
                    confidence_score,
                    json.dumps(alternatives or []),
                    success
                ))
                conn.commit()
        except Exception as e:
            conn.rollback()
            print(f"   Warning: Failed to track routing: {e}")

    def get_agent_success_rate(
        self,
        agent_id: str,
        task_type: Optional[str] = None,
        days: int = 30
    ) -> Dict[str, Any]:
        """
        Get success rate for an agent.

        Args:
            agent_id: Agent identifier
            task_type: Optional task type filter
            days: Look back period

        Returns:
            Success rate and statistics
        """
        conn = self._connect()

        cutoff_date = datetime.now() - timedelta(days=days)

        with conn.cursor() as cursor:
            if task_type:
                cursor.execute("""
                    SELECT
                        COUNT(*) as total_attempts,
                        SUM(CASE WHEN success THEN 1 ELSE 0 END) as successes,
                        AVG(execution_time_ms) as avg_execution_time,
                        AVG(CASE WHEN success THEN 1.0 ELSE 0.0 END) as success_rate
                    FROM agent_performance
                    WHERE agent_id = %s
                      AND task_type = %s
                      AND timestamp > %s
                """, (agent_id, task_type, cutoff_date))
            else:
                cursor.execute("""
                    SELECT
                        COUNT(*) as total_attempts,
                        SUM(CASE WHEN success THEN 1 ELSE 0 END) as successes,
                        AVG(execution_time_ms) as avg_execution_time,
                        AVG(CASE WHEN success THEN 1.0 ELSE 0.0 END) as success_rate
                    FROM agent_performance
                    WHERE agent_id = %s
                      AND timestamp > %s
                """, (agent_id, cutoff_date))

            result = cursor.fetchone()
            return dict(result) if result else {}

    def get_best_agent_for_task(self, task_type: str) -> Dict[str, Any]:
        """
        Determine which agent performs best for a task type.

        Args:
            task_type: Task type

        Returns:
            Best agent recommendation with statistics
        """
        conn = self._connect()

        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT
                    agent_id,
                    COUNT(*) as attempts,
                    AVG(CASE WHEN success THEN 1.0 ELSE 0.0 END) as success_rate,
                    AVG(execution_time_ms) as avg_time
                FROM agent_performance
                WHERE task_type = %s
                  AND timestamp > NOW() - INTERVAL '30 days'
                GROUP BY agent_id
                HAVING COUNT(*) >= 3  -- At least 3 attempts
                ORDER BY success_rate DESC, avg_time ASC
                LIMIT 1
            """, (task_type,))

            result = cursor.fetchone()
            return dict(result) if result else None

    def get_learning_insights(
        self,
        insight_type: Optional[str] = None,
        min_confidence: float = 0.7,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Get accumulated learning insights.

        Args:
            insight_type: Filter by type
            min_confidence: Minimum confidence threshold
            limit: Maximum results

        Returns:
            List of insights
        """
        conn = self._connect()

        with conn.cursor() as cursor:
            if insight_type:
                cursor.execute("""
                    SELECT * FROM learning_insights
                    WHERE insight_type = %s
                      AND confidence >= %s
                    ORDER BY confidence DESC, evidence_count DESC
                    LIMIT %s
                """, (insight_type, min_confidence, limit))
            else:
                cursor.execute("""
                    SELECT * FROM learning_insights
                    WHERE confidence >= %s
                    ORDER BY confidence DESC, evidence_count DESC
                    LIMIT %s
                """, (min_confidence, limit))

            insights = cursor.fetchall()
            return [dict(i) for i in insights]

    def _extract_insights(self, agent_id: str, task_type: str, success: bool):
        """
        Extract learning insights from patterns.

        This is the "neuroplasticity" - learning what works.
        """
        conn = self._connect()

        # Calculate recent success rate for this combination
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT
                    COUNT(*) as attempts,
                    AVG(CASE WHEN success THEN 1.0 ELSE 0.0 END) as success_rate
                FROM agent_performance
                WHERE agent_id = %s
                  AND task_type = %s
                  AND timestamp > NOW() - INTERVAL '7 days'
            """, (agent_id, task_type))

            stats = cursor.fetchone()

            if stats and stats['attempts'] >= 5:  # Need enough data
                success_rate = float(stats['success_rate'])

                insight_content = f"Agent '{agent_id}' has {success_rate:.1%} success rate for '{task_type}' tasks"

                # Check if insight exists
                cursor.execute("""
                    SELECT id, confidence, evidence_count
                    FROM learning_insights
                    WHERE content = %s
                """, (insight_content,))

                existing = cursor.fetchone()

                if existing:
                    # Update existing insight
                    new_evidence = existing['evidence_count'] + 1
                    new_confidence = min(0.99, existing['confidence'] * 0.9 + success_rate * 0.1)

                    cursor.execute("""
                        UPDATE learning_insights
                        SET confidence = %s,
                            evidence_count = %s,
                            updated_at = NOW()
                        WHERE id = %s
                    """, (new_confidence, new_evidence, existing['id']))
                else:
                    # Create new insight
                    cursor.execute("""
                        INSERT INTO learning_insights
                        (insight_type, content, confidence, evidence_count, metadata)
                        VALUES (%s, %s, %s, %s, %s)
                    """, (
                        'pattern',
                        insight_content,
                        success_rate,
                        int(stats['attempts']),
                        json.dumps({"agent_id": agent_id, "task_type": task_type})
                    ))

                conn.commit()

    def get_performance_summary(self, days: int = 7) -> Dict[str, Any]:
        """Get overall performance summary."""
        conn = self._connect()

        cutoff_date = datetime.now() - timedelta(days=days)

        with conn.cursor() as cursor:
            # Overall stats
            cursor.execute("""
                SELECT
                    COUNT(*) as total_actions,
                    AVG(CASE WHEN success THEN 1.0 ELSE 0.0 END) as overall_success_rate,
                    COUNT(DISTINCT agent_id) as agents_used,
                    COUNT(DISTINCT task_type) as task_types
                FROM agent_performance
                WHERE timestamp > %s
            """, (cutoff_date,))
            overall = dict(cursor.fetchone())

            # Per-agent stats
            cursor.execute("""
                SELECT
                    agent_id,
                    COUNT(*) as actions,
                    AVG(CASE WHEN success THEN 1.0 ELSE 0.0 END) as success_rate,
                    AVG(execution_time_ms) as avg_time_ms
                FROM agent_performance
                WHERE timestamp > %s
                GROUP BY agent_id
                ORDER BY actions DESC
            """, (cutoff_date,))
            per_agent = [dict(row) for row in cursor.fetchall()]

            # Top insights
            cursor.execute("""
                SELECT content, confidence, evidence_count
                FROM learning_insights
                ORDER BY confidence DESC, evidence_count DESC
                LIMIT 5
            """)
            top_insights = [dict(row) for row in cursor.fetchall()]

            return {
                "period_days": days,
                "overall": overall,
                "per_agent": per_agent,
                "top_insights": top_insights
            }

    def close(self):
        """Close database connection."""
        if self.connection and not self.connection.closed:
            self.connection.close()

    def __del__(self):
        """Cleanup."""
        self.close()


def main():
    """Demo meta-learning system."""
    print("\n" + "="*70)
    print("META-LEARNING SYSTEM - Performance Tracking Demo")
    print("="*70 + "\n")

    try:
        learner = MetaLearner()

        # Track some sample outcomes
        print("📊 Tracking sample outcomes...\n")

        sample_outcomes = [
            {"agent_id": "neon-agent", "task_type": "database_query", "query": "List contractors", "success": True, "execution_time_ms": 150},
            {"agent_id": "neon-agent", "task_type": "database_query", "query": "Show projects", "success": True, "execution_time_ms": 120},
            {"agent_id": "vps-monitor", "task_type": "system_check", "query": "CPU usage", "success": True, "execution_time_ms": 50},
            {"agent_id": "convex-agent", "task_type": "realtime_query", "query": "Active tasks", "success": True, "execution_time_ms": 80},
        ]

        for outcome in sample_outcomes:
            learner.track_outcome(**outcome)
            print(f"✓ Tracked: {outcome['agent_id']} - {outcome['task_type']}")

        # Get success rates
        print("\n" + "="*70)
        print("AGENT SUCCESS RATES")
        print("="*70 + "\n")

        for agent in ["neon-agent", "vps-monitor", "convex-agent"]:
            stats = learner.get_agent_success_rate(agent)
            if stats.get('total_attempts', 0) > 0:
                print(f"🤖 {agent}:")
                print(f"   Success Rate: {stats.get('success_rate', 0):.1%}")
                print(f"   Total Attempts: {stats.get('total_attempts', 0)}")
                print(f"   Avg Time: {stats.get('avg_execution_time', 0):.0f}ms\n")

        # Get insights
        print("="*70)
        print("LEARNING INSIGHTS")
        print("="*70 + "\n")

        insights = learner.get_learning_insights(min_confidence=0.0)
        for insight in insights:
            print(f"💡 {insight['content']}")
            print(f"   Confidence: {insight['confidence']:.1%}")
            print(f"   Evidence: {insight['evidence_count']} observations\n")

        # Get summary
        print("="*70)
        print("PERFORMANCE SUMMARY")
        print("="*70)
        summary = learner.get_performance_summary()
        print(json.dumps(summary, indent=2, default=str))

        print("\n✅ Meta-learning demo completed!")

    except Exception as e:
        print(f"❌ Error: {e}")
        print("   Make sure NEON_DATABASE_URL is set")


if __name__ == "__main__":
    main()
