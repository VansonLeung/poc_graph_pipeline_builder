"""Search service implementing lightweight RAG."""

from __future__ import annotations

from typing import Dict, Any, List, Optional

from backend.app.core.clients import EmbeddingClient, ChatClient
from backend.app.repositories.neo4j_repository import Neo4jRepository

DEFAULT_SYSTEM_PROMPT = (
    "You are a helpful assistant. Use only the provided context to answer. "
    "If the context is insufficient, say you don't know."
)


class SearchService:
    """Combines vector search with LLM generation."""

    def __init__(
        self,
        repository: Neo4jRepository,
        embedder: EmbeddingClient,
        llm: ChatClient,
    ) -> None:
        self.repository = repository
        self.embedder = embedder
        self.llm = llm

    def rag_search(
        self,
        index_name: str,
        query: str,
        keywords: Optional[List[str]] = None,
        top_k: int = 5,
    ) -> Dict[str, Any]:
        embedding = self.embedder.embed(query)
        chunks = self.repository.vector_search(
            index_name=index_name,
            embedding=embedding,
            top_k=top_k,
            keywords=keywords,
        )
        context = self._build_context(chunks)
        user_prompt = self._build_prompt(context, query)
        answer = self.llm.complete(DEFAULT_SYSTEM_PROMPT, user_prompt) if context else (
            "I don't have enough information to answer this question."
        )
        return {"answer": answer, "chunks": chunks}

    @staticmethod
    def _build_context(chunks: List[Dict[str, Any]]) -> str:
        sections = []
        for idx, chunk in enumerate(chunks, start=1):
            metadata_str = "" if not chunk.get("metadata") else f"Metadata: {chunk['metadata']}\n"
            sections.append(
                f"Chunk {idx}:\n{metadata_str}{chunk.get('content', '')}\n"
            )
        return "\n".join(sections)

    @staticmethod
    def _build_prompt(context: str, question: str) -> str:
        return (
            "Context from the knowledge base:\n"
            f"{context}\n\n"
            f"Question: {question}\n"
            "Answer using only the context above."
        )
