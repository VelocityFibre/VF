#!/usr/bin/env python3
"""
Vector Memory System - Semantic/Episodic Memory using Qdrant
Enables the agent to remember and recall similar past experiences.
"""

import os
import json
import hashlib
from typing import List, Dict, Any, Optional
from datetime import datetime
from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance, VectorParams, PointStruct,
    Filter, FieldCondition, MatchValue
)
from anthropic import Anthropic


class VectorMemory:
    """
    Semantic/Episodic memory system using Qdrant vector database.

    This is the AI equivalent of the hippocampus - stores experiences
    and enables "I've seen something like this before" reasoning.
    """

    def __init__(
        self,
        collection_name: str = "agent_memory",
        qdrant_url: Optional[str] = None,
        qdrant_api_key: Optional[str] = None,
        embedding_model: str = "voyage-2"
    ):
        """
        Initialize vector memory system.

        Args:
            collection_name: Qdrant collection name
            qdrant_url: Qdrant server URL (defaults to localhost)
            qdrant_api_key: Qdrant API key (for cloud)
            embedding_model: Model to use for embeddings
        """
        # Initialize Qdrant client
        self.qdrant_url = qdrant_url or os.environ.get("QDRANT_URL", "http://localhost:6333")
        self.qdrant_api_key = qdrant_api_key or os.environ.get("QDRANT_API_KEY")

        self.client = QdrantClient(
            url=self.qdrant_url,
            api_key=self.qdrant_api_key
        )

        self.collection_name = collection_name
        self.embedding_model = embedding_model
        self.embedding_dim = 1024  # Voyage-2 dimension

        # Initialize Anthropic for embeddings (alternative to Voyage)
        anthropic_key = os.environ.get("ANTHROPIC_API_KEY")
        self.anthropic = Anthropic(api_key=anthropic_key) if anthropic_key else None

        # Create collection if it doesn't exist
        self._init_collection()

        print(f"✅ Vector Memory initialized")
        print(f"   Collection: {collection_name}")
        print(f"   Qdrant: {self.qdrant_url}")
        print(f"   Embedding: {embedding_model}")

    def _init_collection(self):
        """Create Qdrant collection if it doesn't exist."""
        try:
            collections = self.client.get_collections().collections
            exists = any(c.name == self.collection_name for c in collections)

            if not exists:
                self.client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=VectorParams(
                        size=self.embedding_dim,
                        distance=Distance.COSINE
                    )
                )
                print(f"   Created new collection: {self.collection_name}")
            else:
                print(f"   Using existing collection: {self.collection_name}")
        except Exception as e:
            print(f"   Warning: Could not verify collection: {e}")

    def _create_embedding(self, text: str) -> List[float]:
        """
        Create embedding vector for text.

        Uses simple approach: convert text to fixed-size hash-based vector.
        For production, use Voyage AI, OpenAI, or Anthropic embeddings.
        """
        # Simple hash-based embedding for demo
        # In production, replace with proper embedding API
        import numpy as np

        # Create deterministic embedding from text hash
        text_hash = hashlib.sha256(text.encode()).digest()

        # Expand to embedding dimension using numpy
        np.random.seed(int.from_bytes(text_hash[:4], 'big'))
        embedding = np.random.randn(self.embedding_dim)

        # Normalize
        embedding = embedding / np.linalg.norm(embedding)

        return embedding.tolist()

    def store_interaction(
        self,
        query: str,
        response: str,
        agent_id: str,
        metadata: Optional[Dict[str, Any]] = None,
        success: bool = True
    ) -> str:
        """
        Store an interaction in vector memory.

        Args:
            query: User's query
            response: Agent's response
            agent_id: Which agent handled this
            metadata: Additional metadata
            success: Whether interaction was successful

        Returns:
            Unique ID of stored memory
        """
        # Create combined text for embedding
        combined_text = f"Query: {query}\nResponse: {response}"

        # Generate embedding
        embedding = self._create_embedding(combined_text)

        # Create unique ID
        memory_id = hashlib.md5(
            f"{query}{datetime.now().isoformat()}".encode()
        ).hexdigest()

        # Prepare payload
        payload = {
            "query": query,
            "response": response,
            "agent_id": agent_id,
            "timestamp": datetime.now().isoformat(),
            "success": success,
            "metadata": metadata or {}
        }

        # Store in Qdrant
        self.client.upsert(
            collection_name=self.collection_name,
            points=[
                PointStruct(
                    id=memory_id,
                    vector=embedding,
                    payload=payload
                )
            ]
        )

        return memory_id

    def recall_similar(
        self,
        query: str,
        limit: int = 5,
        agent_id: Optional[str] = None,
        min_score: float = 0.7
    ) -> List[Dict[str, Any]]:
        """
        Find similar past interactions.

        This is the "I've seen something like this before" functionality.

        Args:
            query: Current query to find similar past queries for
            limit: Maximum number of results
            agent_id: Filter by specific agent
            min_score: Minimum similarity score (0-1)

        Returns:
            List of similar past interactions with scores
        """
        # Generate query embedding
        query_embedding = self._create_embedding(query)

        # Build filter if agent_id specified
        query_filter = None
        if agent_id:
            query_filter = Filter(
                must=[
                    FieldCondition(
                        key="agent_id",
                        match=MatchValue(value=agent_id)
                    )
                ]
            )

        # Search for similar vectors
        try:
            results = self.client.search(
                collection_name=self.collection_name,
                query_vector=query_embedding,
                limit=limit,
                query_filter=query_filter,
                score_threshold=min_score
            )

            # Format results
            similar_memories = []
            for result in results:
                memory = {
                    "score": result.score,
                    "query": result.payload.get("query"),
                    "response": result.payload.get("response"),
                    "agent_id": result.payload.get("agent_id"),
                    "timestamp": result.payload.get("timestamp"),
                    "success": result.payload.get("success"),
                    "metadata": result.payload.get("metadata", {})
                }
                similar_memories.append(memory)

            return similar_memories

        except Exception as e:
            print(f"   Error searching memories: {e}")
            return []

    def get_conversation_context(
        self,
        current_query: str,
        user_id: Optional[str] = None,
        limit: int = 3
    ) -> str:
        """
        Get relevant context from past conversations.

        Returns formatted string to inject into agent context.
        """
        similar = self.recall_similar(current_query, limit=limit)

        if not similar:
            return ""

        context = "\n## Relevant Past Experiences:\n\n"
        for i, memory in enumerate(similar, 1):
            context += f"### Similar Case {i} (similarity: {memory['score']:.2f}):\n"
            context += f"**Past Query:** {memory['query']}\n"
            context += f"**Solution:** {memory['response'][:200]}...\n"
            context += f"**Outcome:** {'✅ Success' if memory['success'] else '❌ Failed'}\n\n"

        return context

    def get_stats(self) -> Dict[str, Any]:
        """Get memory statistics."""
        try:
            collection_info = self.client.get_collection(self.collection_name)
            return {
                "total_memories": collection_info.points_count,
                "collection": self.collection_name,
                "embedding_dim": self.embedding_dim
            }
        except Exception as e:
            return {"error": str(e)}


class EmbeddingService:
    """
    Service for creating embeddings using various providers.
    Supports Voyage AI, OpenAI, and Anthropic.
    """

    def __init__(self, provider: str = "simple"):
        """
        Initialize embedding service.

        Args:
            provider: 'simple', 'voyage', 'openai', or 'anthropic'
        """
        self.provider = provider

        if provider == "voyage":
            try:
                import voyageai
                self.client = voyageai.Client(api_key=os.environ.get("VOYAGE_API_KEY"))
                self.embed_model = "voyage-2"
                self.dim = 1024
            except ImportError:
                raise ImportError("Install voyageai: pip install voyageai")

        elif provider == "openai":
            try:
                import openai
                self.client = openai.OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
                self.embed_model = "text-embedding-3-small"
                self.dim = 1536
            except ImportError:
                raise ImportError("Install openai: pip install openai")

        elif provider == "anthropic":
            # Anthropic doesn't have embeddings API yet
            # This is a placeholder for when they do
            self.client = None
            self.dim = 1024

        else:  # simple
            self.client = None
            self.dim = 1024

    def embed(self, text: str) -> List[float]:
        """Create embedding for text."""
        if self.provider == "voyage":
            result = self.client.embed([text], model=self.embed_model)
            return result.embeddings[0]

        elif self.provider == "openai":
            result = self.client.embeddings.create(
                input=[text],
                model=self.embed_model
            )
            return result.data[0].embedding

        else:  # simple fallback
            import numpy as np
            text_hash = hashlib.sha256(text.encode()).digest()
            np.random.seed(int.from_bytes(text_hash[:4], 'big'))
            embedding = np.random.randn(self.dim)
            return (embedding / np.linalg.norm(embedding)).tolist()


def main():
    """Demo vector memory system."""
    print("\n" + "="*70)
    print("VECTOR MEMORY SYSTEM - Semantic/Episodic Memory Demo")
    print("="*70 + "\n")

    # Initialize memory
    memory = VectorMemory()

    # Store some sample interactions
    print("📝 Storing sample interactions...\n")

    interactions = [
        {
            "query": "How do I connect to the database?",
            "response": "Use the connection string from NEON_DATABASE_URL environment variable",
            "agent_id": "neon-agent",
            "success": True
        },
        {
            "query": "Database connection failing",
            "response": "Check your connection string format and ensure the database is running",
            "agent_id": "neon-agent",
            "success": True
        },
        {
            "query": "What contractors are in the system?",
            "response": "Query the contractors table using SELECT * FROM contractors",
            "agent_id": "database-agent",
            "success": True
        },
        {
            "query": "VPS server CPU usage high",
            "response": "Check running processes with 'top' and identify resource-heavy processes",
            "agent_id": "vps-monitor",
            "success": True
        }
    ]

    for interaction in interactions:
        memory_id = memory.store_interaction(**interaction)
        print(f"✓ Stored: {interaction['query'][:50]}... (ID: {memory_id[:8]})")

    # Test recall
    print("\n" + "="*70)
    print("TESTING SEMANTIC RECALL")
    print("="*70 + "\n")

    test_queries = [
        "Can't connect to database",
        "Show me all contractors",
        "Server running slow"
    ]

    for test_query in test_queries:
        print(f"🔍 Query: \"{test_query}\"\n")
        similar = memory.recall_similar(test_query, limit=2)

        if similar:
            print(f"   Found {len(similar)} similar past cases:\n")
            for i, mem in enumerate(similar, 1):
                print(f"   {i}. Score: {mem['score']:.2f}")
                print(f"      Past: {mem['query']}")
                print(f"      Solution: {mem['response'][:60]}...")
                print(f"      Agent: {mem['agent_id']}\n")
        else:
            print("   No similar cases found\n")

    # Show stats
    print("="*70)
    print("MEMORY STATISTICS")
    print("="*70)
    stats = memory.get_stats()
    print(json.dumps(stats, indent=2))

    print("\n✅ Vector Memory demo completed!")


if __name__ == "__main__":
    main()
