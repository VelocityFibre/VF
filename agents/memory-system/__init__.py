"""
Memory Systems for AI Agents

Complete memory architecture mimicking human cognition:
- Vector Memory (Qdrant): Episodic/semantic memory
- Persistent Memory (Neon): Long-term conversation storage
- Meta-Learning: Performance tracking and improvement
- Knowledge Graph: Cross-agent learning
- Consolidation: Sleep-like memory optimization
"""

from .vector_memory import VectorMemory, EmbeddingService
from .persistent_memory import PersistentMemory
from .meta_learner import MetaLearner
from .knowledge_graph import KnowledgeGraph
from .consolidation import MemoryConsolidation

__all__ = [
    'VectorMemory',
    'EmbeddingService',
    'PersistentMemory',
    'MetaLearner',
    'KnowledgeGraph',
    'MemoryConsolidation'
]
