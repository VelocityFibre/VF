#!/usr/bin/env python3
"""
Superior Agent Brain - Complete AI cognition system
Integrates all memory systems for human-like intelligence.

This is the "complete brain" - combining all cognitive components:
- LLM (CPU): Claude Sonnet for processing
- Context Window (RAM): 200K token working memory
- Vector Memory (Episodic): Qdrant for semantic recall
- Persistent Memory (Long-term): Neon for conversation storage
- Meta-Learning (Neuroplasticity): Performance improvement
- Knowledge Graph (Shared Learning): Cross-agent knowledge
- Memory Consolidation (Sleep): Data optimization
- Orchestrator (Executive Function): Task routing
- Specialized Agents (Brain Regions): Domain experts
"""

import os
import sys
import json
from typing import Dict, List, Any, Optional
from datetime import datetime
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from memory import (
    VectorMemory,
    PersistentMemory,
    MetaLearner,
    KnowledgeGraph,
    MemoryConsolidation
)
from orchestrator.orchestrator import AgentOrchestrator
from anthropic import Anthropic


class SuperiorAgentBrain:
    """
    The complete AI agent brain with human-like cognitive architecture.

    Components map to human brain functions:
    - LLM: Cortex (processing)
    - Context: Working memory (RAM)
    - Vector DB: Hippocampus (episodic memory)
    - Persistent DB: Long-term memory
    - Meta-Learner: Neuroplasticity
    - Knowledge Graph: Semantic network
    - Consolidation: Sleep consolidation
    - Orchestrator: Prefrontal cortex
    """

    def __init__(
        self,
        model: str = "claude-sonnet-4-5-20250929",
        enable_vector_memory: bool = True,
        enable_persistent_memory: bool = True,
        enable_meta_learning: bool = True,
        enable_knowledge_graph: bool = True,
        enable_orchestration: bool = True
    ):
        """
        Initialize the superior agent brain.

        Args:
            model: Claude model to use (the "CPU")
            enable_vector_memory: Enable semantic/episodic memory
            enable_persistent_memory: Enable cross-session storage
            enable_meta_learning: Enable performance tracking
            enable_knowledge_graph: Enable shared learning
            enable_orchestration: Enable task routing
        """
        print("\n" + "="*70)
        print("🧠 INITIALIZING SUPERIOR AGENT BRAIN")
        print("="*70 + "\n")

        # 1. CPU (Processing Unit)
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY required")

        self.client = Anthropic(api_key=api_key)
        self.model = model
        self.max_tokens = 8192
        print(f"✅ CPU: {model}")

        # 2. RAM (Working Memory / Context Window)
        self.conversation_history: List[Dict[str, Any]] = []
        self.context_limit = 200000  # tokens
        print(f"✅ RAM: {self.context_limit:,} token context window")

        # 3. Long-term Memory Systems
        self.vector_memory = None
        self.persistent_memory = None
        self.meta_learner = None
        self.knowledge_graph = None
        self.consolidator = None

        # Vector Memory (Episodic/Semantic - Hippocampus)
        if enable_vector_memory:
            try:
                self.vector_memory = VectorMemory(collection_name="superior_agent_memory")
                print(f"✅ Episodic Memory: Qdrant vector database")
            except Exception as e:
                print(f"⚠️  Episodic Memory: Disabled ({e})")

        # Persistent Memory (Long-term Storage)
        if enable_persistent_memory:
            try:
                self.persistent_memory = PersistentMemory(
                    vector_memory=self.vector_memory
                )
                print(f"✅ Long-term Memory: Neon PostgreSQL + Vector search")
            except Exception as e:
                print(f"⚠️  Long-term Memory: Disabled ({e})")

        # Meta-Learning (Neuroplasticity)
        if enable_meta_learning:
            try:
                self.meta_learner = MetaLearner()
                print(f"✅ Meta-Learning: Performance tracking enabled")
            except Exception as e:
                print(f"⚠️  Meta-Learning: Disabled ({e})")

        # Knowledge Graph (Shared Intelligence)
        if enable_knowledge_graph:
            try:
                self.knowledge_graph = KnowledgeGraph()
                print(f"✅ Knowledge Graph: Cross-agent learning enabled")
            except Exception as e:
                print(f"⚠️  Knowledge Graph: Disabled ({e})")

        # Memory Consolidation (Sleep)
        try:
            self.consolidator = MemoryConsolidation()
            print(f"✅ Memory Consolidation: Optimization system ready")
        except Exception as e:
            print(f"⚠️  Memory Consolidation: Disabled ({e})")

        # 4. Executive Function (Orchestrator)
        self.orchestrator = None
        if enable_orchestration:
            try:
                self.orchestrator = AgentOrchestrator()
                agent_count = len(self.orchestrator.list_agents())
                print(f"✅ Orchestrator: {agent_count} specialized agents available")
            except Exception as e:
                print(f"⚠️  Orchestrator: Disabled ({e})")

        # Session tracking
        self.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.user_id = "default_user"

        print(f"\n{'='*70}")
        print(f"🎯 Brain Status: OPERATIONAL")
        print(f"   Session ID: {self.session_id}")
        print(f"={'='*70}\n")

    def process_query(
        self,
        query: str,
        user_id: Optional[str] = None,
        use_memory: bool = True
    ) -> Dict[str, Any]:
        """
        Process a query through the complete cognitive pipeline.

        This is the full "thinking" process:
        1. Recall similar past experiences (episodic memory)
        2. Route to specialized agent (executive function)
        3. Process with context (working memory)
        4. Learn from outcome (meta-learning)
        5. Share knowledge (knowledge graph)

        Args:
            query: User's query
            user_id: User identifier
            use_memory: Whether to use memory systems

        Returns:
            Response with metadata
        """
        start_time = datetime.now()
        user_id = user_id or self.user_id

        print(f"\n{'─'*70}")
        print(f"💭 Processing: \"{query}\"")
        print(f"{'─'*70}\n")

        # 1. RECALL - Check episodic memory for similar experiences
        similar_experiences = []
        if use_memory and self.vector_memory:
            print("🔍 Searching episodic memory...")
            similar_experiences = self.vector_memory.recall_similar(
                query=query,
                limit=3,
                min_score=0.7
            )

            if similar_experiences:
                print(f"   Found {len(similar_experiences)} similar past experience(s)")
            else:
                print(f"   No similar experiences found (new territory)")

        # 2. ROUTE - Determine best agent for task
        selected_agent = None
        routing_confidence = 0.0

        if self.orchestrator:
            print("\n🎯 Routing to specialist...")
            routing = self.orchestrator.route_task(query, auto_select=True)

            if routing['status'] == 'routed':
                selected_agent = routing['agent']['agent_id']
                routing_confidence = routing['agent']['confidence']
                print(f"   → {routing['agent']['agent_name']} (confidence: {routing_confidence})")
            else:
                print(f"   → General processing (no specialist match)")

        # 3. PROCESS - Generate response
        print("\n🧠 Processing with cognitive pipeline...\n")

        # Build context from memories
        context_additions = []

        if similar_experiences:
            context_additions.append("## Past Experiences:\n")
            for i, exp in enumerate(similar_experiences, 1):
                context_additions.append(
                    f"{i}. Similar query (similarity: {exp['score']:.2f}):\n"
                    f"   Q: {exp['query']}\n"
                    f"   A: {exp['response'][:200]}...\n"
                )

        # Combine query with context
        enhanced_query = query
        if context_additions:
            enhanced_query = "\n".join(context_additions) + "\n\n" + query

        # Add to conversation history
        self.conversation_history.append({
            "role": "user",
            "content": enhanced_query
        })

        # Generate response
        response = self.client.messages.create(
            model=self.model,
            max_tokens=self.max_tokens,
            messages=self.conversation_history
        )

        # Extract response text
        response_text = ""
        if response.content:
            response_text = " ".join([
                block.text for block in response.content
                if hasattr(block, 'text')
            ])

        # Add to history
        self.conversation_history.append({
            "role": "assistant",
            "content": response_text
        })

        execution_time = (datetime.now() - start_time).total_seconds()

        # 4. LEARN - Track performance
        if self.meta_learner and selected_agent:
            self.meta_learner.track_outcome(
                agent_id=selected_agent or "general",
                task_type="query_response",
                query=query,
                success=True,  # Could add validation logic
                execution_time_ms=int(execution_time * 1000)
            )

        # 5. REMEMBER - Store in long-term memory
        if use_memory and self.vector_memory:
            self.vector_memory.store_interaction(
                query=query,
                response=response_text,
                agent_id=selected_agent or "general",
                success=True
            )

        # 6. SHARE - Add to knowledge graph if significant
        # (Could add logic to determine if worth sharing)

        print(f"\n✅ Response generated in {execution_time:.2f}s")

        return {
            "response": response_text,
            "metadata": {
                "execution_time_seconds": execution_time,
                "selected_agent": selected_agent,
                "routing_confidence": routing_confidence,
                "similar_experiences_found": len(similar_experiences),
                "session_id": self.session_id,
                "timestamp": datetime.now().isoformat()
            }
        }

    def chat(self, message: str, user_id: Optional[str] = None) -> str:
        """
        Simple chat interface.

        Args:
            message: User message
            user_id: User identifier

        Returns:
            Response text
        """
        result = self.process_query(message, user_id=user_id)
        return result["response"]

    def save_session(self, summary: Optional[str] = None):
        """
        Save current session to persistent memory.

        Args:
            summary: Optional session summary
        """
        if not self.persistent_memory:
            print("⚠️  Persistent memory not enabled")
            return

        if not summary:
            summary = f"Session {self.session_id}"

        try:
            conv_id = self.persistent_memory.save_conversation(
                user_id=self.user_id,
                session_id=self.session_id,
                messages=self.conversation_history,
                summary=summary
            )
            print(f"💾 Session saved (ID: {conv_id})")
        except Exception as e:
            print(f"⚠️  Failed to save session: {e}")

    def sleep(self, conversation_days: int = 30, performance_days: int = 60):
        """
        Run memory consolidation (like sleep).

        Args:
            conversation_days: Consolidate conversations older than this
            performance_days: Consolidate performance data older than this
        """
        if not self.consolidator:
            print("⚠️  Memory consolidation not enabled")
            return

        print("\n💤 Entering sleep mode (memory consolidation)...")
        results = self.consolidator.run_full_consolidation(
            conversation_days=conversation_days,
            performance_days=performance_days
        )

        return results

    def get_brain_status(self) -> Dict[str, Any]:
        """Get complete brain status and statistics."""
        status = {
            "session_id": self.session_id,
            "model": self.model,
            "conversation_length": len(self.conversation_history),
            "components": {
                "vector_memory": self.vector_memory is not None,
                "persistent_memory": self.persistent_memory is not None,
                "meta_learner": self.meta_learner is not None,
                "knowledge_graph": self.knowledge_graph is not None,
                "orchestrator": self.orchestrator is not None,
                "consolidator": self.consolidator is not None
            }
        }

        # Add stats from each component
        if self.vector_memory:
            status["vector_memory_stats"] = self.vector_memory.get_stats()

        if self.meta_learner:
            status["performance_summary"] = self.meta_learner.get_performance_summary()

        if self.knowledge_graph:
            status["knowledge_stats"] = self.knowledge_graph.get_graph_stats()

        if self.orchestrator:
            status["agent_stats"] = self.orchestrator.get_agent_stats()

        return status

    def reset_conversation(self):
        """Clear working memory (reset conversation)."""
        self.conversation_history = []
        print("🔄 Working memory cleared")

    def close(self):
        """Shutdown brain and close all connections."""
        print("\n🔌 Shutting down brain components...")

        if self.persistent_memory:
            self.persistent_memory.close()

        if self.meta_learner:
            self.meta_learner.close()

        if self.knowledge_graph:
            self.knowledge_graph.close()

        if self.consolidator:
            self.consolidator.close()

        print("✅ Shutdown complete")


def main():
    """Demo the superior agent brain."""
    print("\n" + "="*70)
    print("SUPERIOR AGENT BRAIN - Complete Cognitive System Demo")
    print("="*70)

    # Initialize brain
    brain = SuperiorAgentBrain(
        enable_vector_memory=True,
        enable_persistent_memory=True,
        enable_meta_learning=True,
        enable_knowledge_graph=True,
        enable_orchestration=True
    )

    # Test queries
    test_queries = [
        "What contractors do we have in the system?",
        "How many active projects are there?",
        "What's the status of the VPS servers?",
    ]

    print("\n" + "="*70)
    print("TESTING COGNITIVE PIPELINE")
    print("="*70)

    for i, query in enumerate(test_queries, 1):
        print(f"\n{'═'*70}")
        print(f"Test {i}/{len(test_queries)}")
        print(f"{'═'*70}")

        result = brain.process_query(query)

        print(f"\n📤 Response:")
        print(f"{result['response'][:300]}...")

        print(f"\n📊 Metadata:")
        print(f"   Time: {result['metadata']['execution_time_seconds']:.2f}s")
        print(f"   Agent: {result['metadata']['selected_agent'] or 'general'}")
        print(f"   Similar experiences: {result['metadata']['similar_experiences_found']}")

    # Save session
    print(f"\n{'='*70}")
    brain.save_session(summary="Demo session testing cognitive pipeline")

    # Get brain status
    print(f"\n{'='*70}")
    print("BRAIN STATUS")
    print(f"{'='*70}")
    status = brain.get_brain_status()
    print(json.dumps(status, indent=2, default=str))

    # Cleanup
    brain.close()

    print(f"\n{'='*70}")
    print("✅ SUPERIOR AGENT BRAIN DEMO COMPLETED")
    print(f"{'='*70}\n")


if __name__ == "__main__":
    main()
