#!/usr/bin/env python3
"""
Knowledge Graph - Cross-agent learning and relationship mapping
Enables agents to share learnings and understand concept relationships.
"""

import os
import json
import psycopg2
from psycopg2.extras import RealDictCursor
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime


class KnowledgeGraph:
    """
    Knowledge graph for storing and querying relationships between concepts.

    Enables cross-agent learning: when one agent learns something,
    all agents can benefit from that knowledge.
    """

    def __init__(self, neon_url: Optional[str] = None):
        """
        Initialize knowledge graph.

        Args:
            neon_url: Neon PostgreSQL connection string
        """
        self.neon_url = neon_url or os.environ.get("NEON_DATABASE_URL")
        if not self.neon_url:
            raise ValueError("NEON_DATABASE_URL required for knowledge graph")

        self.connection = None
        self._init_schema()

        print(f"✅ Knowledge Graph initialized")
        print(f"   Shared learning enabled")

    def _connect(self):
        """Connect to database."""
        if not self.connection or self.connection.closed:
            self.connection = psycopg2.connect(
                self.neon_url,
                cursor_factory=RealDictCursor
            )
        return self.connection

    def _init_schema(self):
        """Create database schema for knowledge graph."""
        schema_sql = """
        -- Knowledge nodes (concepts, entities, facts)
        CREATE TABLE IF NOT EXISTS knowledge_nodes (
            id SERIAL PRIMARY KEY,
            node_type VARCHAR(100) NOT NULL,  -- 'concept', 'entity', 'fact', 'skill'
            name VARCHAR(500) NOT NULL,
            description TEXT,
            confidence FLOAT DEFAULT 1.0,
            source_agent VARCHAR(255),  -- Which agent contributed this
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            metadata JSONB DEFAULT '{}'::jsonb,
            UNIQUE(node_type, name)
        );

        -- Knowledge edges (relationships between nodes)
        CREATE TABLE IF NOT EXISTS knowledge_edges (
            id SERIAL PRIMARY KEY,
            from_node_id INTEGER REFERENCES knowledge_nodes(id) ON DELETE CASCADE,
            to_node_id INTEGER REFERENCES knowledge_nodes(id) ON DELETE CASCADE,
            relationship_type VARCHAR(100) NOT NULL,  -- 'relates_to', 'causes', 'solves', etc.
            weight FLOAT DEFAULT 1.0,
            source_agent VARCHAR(255),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            metadata JSONB DEFAULT '{}'::jsonb,
            UNIQUE(from_node_id, to_node_id, relationship_type)
        );

        -- Agent contributions (track who contributed what)
        CREATE TABLE IF NOT EXISTS agent_contributions (
            id SERIAL PRIMARY KEY,
            agent_id VARCHAR(255) NOT NULL,
            contribution_type VARCHAR(100) NOT NULL,  -- 'node', 'edge', 'validation'
            node_id INTEGER REFERENCES knowledge_nodes(id) ON DELETE CASCADE,
            confidence FLOAT DEFAULT 1.0,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            metadata JSONB DEFAULT '{}'::jsonb
        );

        -- Indexes
        CREATE INDEX IF NOT EXISTS idx_nodes_type ON knowledge_nodes(node_type);
        CREATE INDEX IF NOT EXISTS idx_nodes_name ON knowledge_nodes(name);
        CREATE INDEX IF NOT EXISTS idx_edges_from ON knowledge_edges(from_node_id);
        CREATE INDEX IF NOT EXISTS idx_edges_to ON knowledge_edges(to_node_id);
        CREATE INDEX IF NOT EXISTS idx_edges_type ON knowledge_edges(relationship_type);
        CREATE INDEX IF NOT EXISTS idx_contributions_agent ON agent_contributions(agent_id);
        """

        try:
            conn = self._connect()
            with conn.cursor() as cursor:
                cursor.execute(schema_sql)
                conn.commit()
            print("   Schema initialized")
        except Exception as e:
            print(f"   Warning: Schema init failed: {e}")

    def add_knowledge(
        self,
        node_type: str,
        name: str,
        description: str,
        source_agent: str,
        confidence: float = 1.0,
        metadata: Optional[Dict] = None
    ) -> int:
        """
        Add a knowledge node.

        Args:
            node_type: Type of knowledge
            name: Name/identifier
            description: Description
            source_agent: Agent contributing this
            confidence: Confidence level (0-1)
            metadata: Additional data

        Returns:
            Node ID
        """
        conn = self._connect()

        try:
            with conn.cursor() as cursor:
                # Insert or update node
                cursor.execute("""
                    INSERT INTO knowledge_nodes
                    (node_type, name, description, confidence, source_agent, metadata)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    ON CONFLICT (node_type, name)
                    DO UPDATE SET
                        description = EXCLUDED.description,
                        confidence = GREATEST(knowledge_nodes.confidence, EXCLUDED.confidence),
                        updated_at = NOW(),
                        metadata = knowledge_nodes.metadata || EXCLUDED.metadata
                    RETURNING id
                """, (
                    node_type,
                    name,
                    description,
                    confidence,
                    source_agent,
                    json.dumps(metadata or {})
                ))

                node_id = cursor.fetchone()['id']

                # Track contribution
                cursor.execute("""
                    INSERT INTO agent_contributions
                    (agent_id, contribution_type, node_id, confidence)
                    VALUES (%s, %s, %s, %s)
                """, (source_agent, 'node', node_id, confidence))

                conn.commit()
                return node_id

        except Exception as e:
            conn.rollback()
            raise Exception(f"Failed to add knowledge: {e}")

    def add_relationship(
        self,
        from_node_id: int,
        to_node_id: int,
        relationship_type: str,
        source_agent: str,
        weight: float = 1.0,
        metadata: Optional[Dict] = None
    ) -> int:
        """
        Add a relationship between knowledge nodes.

        Args:
            from_node_id: Source node
            to_node_id: Target node
            relationship_type: Type of relationship
            source_agent: Agent contributing this
            weight: Relationship strength
            metadata: Additional data

        Returns:
            Edge ID
        """
        conn = self._connect()

        try:
            with conn.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO knowledge_edges
                    (from_node_id, to_node_id, relationship_type, weight, source_agent, metadata)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    ON CONFLICT (from_node_id, to_node_id, relationship_type)
                    DO UPDATE SET
                        weight = GREATEST(knowledge_edges.weight, EXCLUDED.weight),
                        metadata = knowledge_edges.metadata || EXCLUDED.metadata
                    RETURNING id
                """, (
                    from_node_id,
                    to_node_id,
                    relationship_type,
                    weight,
                    source_agent,
                    json.dumps(metadata or {})
                ))

                edge_id = cursor.fetchone()['id']
                conn.commit()
                return edge_id

        except Exception as e:
            conn.rollback()
            raise Exception(f"Failed to add relationship: {e}")

    def find_node(self, node_type: str, name: str) -> Optional[Dict[str, Any]]:
        """Find a knowledge node."""
        conn = self._connect()

        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT * FROM knowledge_nodes
                WHERE node_type = %s AND name = %s
            """, (node_type, name))

            result = cursor.fetchone()
            return dict(result) if result else None

    def get_related_knowledge(
        self,
        node_id: int,
        relationship_type: Optional[str] = None,
        max_depth: int = 2
    ) -> List[Dict[str, Any]]:
        """
        Get related knowledge nodes.

        Args:
            node_id: Starting node
            relationship_type: Filter by relationship type
            max_depth: How many hops to traverse

        Returns:
            Related nodes with relationship info
        """
        conn = self._connect()

        with conn.cursor() as cursor:
            if relationship_type:
                cursor.execute("""
                    SELECT
                        n.*,
                        e.relationship_type,
                        e.weight
                    FROM knowledge_edges e
                    JOIN knowledge_nodes n ON n.id = e.to_node_id
                    WHERE e.from_node_id = %s
                      AND e.relationship_type = %s
                    ORDER BY e.weight DESC
                """, (node_id, relationship_type))
            else:
                cursor.execute("""
                    SELECT
                        n.*,
                        e.relationship_type,
                        e.weight
                    FROM knowledge_edges e
                    JOIN knowledge_nodes n ON n.id = e.to_node_id
                    WHERE e.from_node_id = %s
                    ORDER BY e.weight DESC
                """, (node_id,))

            results = cursor.fetchall()
            return [dict(r) for r in results]

    def find_solution_path(
        self,
        problem_node_id: int,
        max_depth: int = 3
    ) -> List[Dict[str, Any]]:
        """
        Find solution paths from a problem node.

        Looks for 'solves' or 'fixes' relationships.
        """
        conn = self._connect()

        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT
                    n.*,
                    e.relationship_type,
                    e.weight
                FROM knowledge_edges e
                JOIN knowledge_nodes n ON n.id = e.to_node_id
                WHERE e.from_node_id = %s
                  AND e.relationship_type IN ('solves', 'fixes', 'resolves')
                ORDER BY e.weight DESC, n.confidence DESC
            """, (problem_node_id,))

            solutions = cursor.fetchall()
            return [dict(s) for s in solutions]

    def get_agent_knowledge(
        self,
        agent_id: str,
        limit: int = 20
    ) -> Dict[str, Any]:
        """
        Get all knowledge contributed by an agent.

        Args:
            agent_id: Agent identifier
            limit: Maximum results

        Returns:
            Agent's knowledge contributions
        """
        conn = self._connect()

        with conn.cursor() as cursor:
            # Get nodes
            cursor.execute("""
                SELECT n.*, ac.timestamp as contributed_at
                FROM knowledge_nodes n
                JOIN agent_contributions ac ON ac.node_id = n.id
                WHERE ac.agent_id = %s
                  AND ac.contribution_type = 'node'
                ORDER BY ac.timestamp DESC
                LIMIT %s
            """, (agent_id, limit))

            nodes = [dict(n) for n in cursor.fetchall()]

            # Get contribution stats
            cursor.execute("""
                SELECT
                    contribution_type,
                    COUNT(*) as count,
                    AVG(confidence) as avg_confidence
                FROM agent_contributions
                WHERE agent_id = %s
                GROUP BY contribution_type
            """, (agent_id,))

            stats = [dict(s) for s in cursor.fetchall()]

            return {
                "agent_id": agent_id,
                "contributions": nodes,
                "stats": stats
            }

    def learn_from_success(
        self,
        problem_description: str,
        solution_description: str,
        agent_id: str,
        confidence: float = 0.9
    ):
        """
        Record a successful problem-solution pair.

        This is how agents share learnings with each other.

        Args:
            problem_description: What the problem was
            solution_description: How it was solved
            agent_id: Agent that solved it
            confidence: Confidence in solution
        """
        # Add problem node
        problem_id = self.add_knowledge(
            node_type="problem",
            name=problem_description[:500],
            description=problem_description,
            source_agent=agent_id,
            confidence=confidence
        )

        # Add solution node
        solution_id = self.add_knowledge(
            node_type="solution",
            name=solution_description[:500],
            description=solution_description,
            source_agent=agent_id,
            confidence=confidence
        )

        # Link them
        self.add_relationship(
            from_node_id=problem_id,
            to_node_id=solution_id,
            relationship_type="solves",
            source_agent=agent_id,
            weight=confidence
        )

        print(f"   📚 {agent_id} shared knowledge with the team")

    def get_graph_stats(self) -> Dict[str, Any]:
        """Get knowledge graph statistics."""
        conn = self._connect()

        with conn.cursor() as cursor:
            # Node stats
            cursor.execute("""
                SELECT
                    node_type,
                    COUNT(*) as count,
                    AVG(confidence) as avg_confidence
                FROM knowledge_nodes
                GROUP BY node_type
            """)
            node_stats = [dict(s) for s in cursor.fetchall()]

            # Edge stats
            cursor.execute("""
                SELECT
                    relationship_type,
                    COUNT(*) as count,
                    AVG(weight) as avg_weight
                FROM knowledge_edges
                GROUP BY relationship_type
            """)
            edge_stats = [dict(s) for s in cursor.fetchall()]

            # Total counts
            cursor.execute("""
                SELECT
                    (SELECT COUNT(*) FROM knowledge_nodes) as total_nodes,
                    (SELECT COUNT(*) FROM knowledge_edges) as total_edges,
                    (SELECT COUNT(DISTINCT source_agent) FROM knowledge_nodes) as contributing_agents
            """)
            totals = dict(cursor.fetchone())

            return {
                "totals": totals,
                "by_node_type": node_stats,
                "by_relationship": edge_stats
            }

    def close(self):
        """Close database connection."""
        if self.connection and not self.connection.closed:
            self.connection.close()

    def __del__(self):
        """Cleanup."""
        self.close()


def main():
    """Demo knowledge graph system."""
    print("\n" + "="*70)
    print("KNOWLEDGE GRAPH - Cross-Agent Learning Demo")
    print("="*70 + "\n")

    try:
        kg = KnowledgeGraph()

        # Add sample knowledge
        print("📚 Adding sample knowledge...\n")

        # Neon agent learns something
        problem = "Database connection timeout"
        solution = "Increase connection pool size and add retry logic"

        kg.learn_from_success(
            problem_description=problem,
            solution_description=solution,
            agent_id="neon-agent",
            confidence=0.95
        )

        # VPS agent learns something
        kg.learn_from_success(
            problem_description="High CPU usage",
            solution_description="Identify and optimize resource-heavy processes",
            agent_id="vps-monitor",
            confidence=0.9
        )

        # Test retrieval
        print("\n" + "="*70)
        print("KNOWLEDGE RETRIEVAL")
        print("="*70 + "\n")

        # Find the problem
        problem_node = kg.find_node("problem", problem[:500])
        if problem_node:
            print(f"🔍 Found problem: {problem_node['name']}")
            print(f"   Confidence: {problem_node['confidence']:.1%}")
            print(f"   Source: {problem_node['source_agent']}\n")

            # Find solutions
            solutions = kg.find_solution_path(problem_node['id'])
            print(f"💡 Found {len(solutions)} solution(s):\n")
            for sol in solutions:
                print(f"   - {sol['name']}")
                print(f"     Confidence: {sol['confidence']:.1%}")
                print(f"     Weight: {sol['weight']:.1%}\n")

        # Get agent knowledge
        print("="*70)
        print("AGENT CONTRIBUTIONS")
        print("="*70 + "\n")

        for agent in ["neon-agent", "vps-monitor"]:
            knowledge = kg.get_agent_knowledge(agent)
            print(f"🤖 {agent}:")
            print(f"   Contributions: {len(knowledge['contributions'])}")
            for stat in knowledge['stats']:
                print(f"   {stat['contribution_type']}: {stat['count']}")
            print()

        # Get stats
        print("="*70)
        print("GRAPH STATISTICS")
        print("="*70)
        stats = kg.get_graph_stats()
        print(json.dumps(stats, indent=2, default=str))

        print("\n✅ Knowledge graph demo completed!")

    except Exception as e:
        print(f"❌ Error: {e}")
        print("   Make sure NEON_DATABASE_URL is set")


if __name__ == "__main__":
    main()
