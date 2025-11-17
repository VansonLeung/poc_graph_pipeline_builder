"""Search service aligning with example_rag_query GraphRAG pipeline."""

from __future__ import annotations

import logging
from typing import Dict, Any, List, Optional

from backend.app.core.clients import EmbeddingClient, ChatClient
from backend.app.repositories.neo4j_repository import Neo4jRepository
from config import Config
from graphrag import GraphRAGPipeline
from neo4j_graphrag.embeddings import OpenAIEmbeddings
from retrievers import GraphRetrieverManager

DEFAULT_SYSTEM_PROMPT = (
    "You are a helpful assistant. Use only the provided context to answer. "
    "If the context is insufficient, say you don't know."
)
FALLBACK_RESPONSE = "I don't have enough information to answer this question."

logger = logging.getLogger(__name__)


class SearchService:
    """Combines GraphRAG retrieval with a legacy fallback."""

    def __init__(
        self,
        repository: Neo4jRepository,
        embedder: EmbeddingClient,
        llm: ChatClient,
    ) -> None:
        self.repository = repository
        self.embedder = embedder
        self.legacy_llm = llm
        self.vector_index_name = Config.VECTOR_INDEX_NAME
        self.fulltext_index_name = Config.FULLTEXT_INDEX_NAME

        # GraphRAG components inspired by example_rag_query
        self.graph_llm = Config.get_llm()
        self.graph_embedder = OpenAIEmbeddings(
            model=Config.EMBEDDING_MODEL,
            base_url=Config.EMBEDDING_BASE_URL,
        )
        self.retriever_manager = GraphRetrieverManager(
            driver=self.repository.driver,
            embedder=self.graph_embedder,
            vector_index_name=self.vector_index_name,
            fulltext_index_name=self.fulltext_index_name,
        )

    def rag_search(
        self,
        index_name: str,
        query: str,
        keywords: Optional[List[str]] = None,
        top_k: int = 5,
    ) -> Dict[str, Any]:
        try:
            return self._graph_rag_search(index_name, query, keywords, top_k)
        except Exception as exc:  # pragma: no cover - graceful degradation
            logger.warning("GraphRAG search failed, using legacy fallback: %s", exc)
            return self._legacy_search(index_name, query, keywords, top_k)

    def _graph_rag_search(
        self,
        index_name: str,
        query: str,
        keywords: Optional[List[str]],
        top_k: int,
    ) -> Dict[str, Any]:
        retriever = self._select_retriever(keywords)
        pipeline = GraphRAGPipeline(retriever=retriever, llm=self.graph_llm)
        retriever_config: Dict[str, Any] = {"top_k": top_k}
        filters = self._build_filters(index_name)
        if filters:
            retriever_config["filters"] = filters

        result = pipeline.query(
            question=query,
            retriever_config=retriever_config,
            return_context=True,
            response_fallback=FALLBACK_RESPONSE,
        )
        items = result.retriever_result.items if result.retriever_result else []
        chunks = self._format_retrieved_chunks(items)
        answer = result.answer or FALLBACK_RESPONSE

        if not chunks:
            return self._legacy_search(index_name, query, keywords, top_k)
        return {"answer": answer, "chunks": chunks}

    def _select_retriever(self, keywords: Optional[List[str]]):
        if keywords:
            try:
                return self.retriever_manager.get_hybrid_retriever(
                    return_properties=["text", "index", "metadata", "source"],
                )
            except Exception as exc:  # pragma: no cover - hybrid not always available
                logger.debug("Hybrid retriever unavailable: %s", exc)
        return self.retriever_manager.get_vector_retriever(
            return_properties=["text", "index", "metadata", "document_id"],
        )

    @staticmethod
    def _build_filters(index_name: Optional[str]) -> Optional[Dict[str, Any]]:
        if not index_name:
            return None
        return {"index": index_name}

    @staticmethod
    def _format_retrieved_chunks(items: List[Any]) -> List[Dict[str, Any]]:
        formatted: List[Dict[str, Any]] = []
        for idx, item in enumerate(items, start=1):
            metadata = item.metadata or {}
            content = item.content or metadata.get("text") or metadata.get("chunk_text") or ""
            formatted.append(
                {
                    "doc_id": str(
                        metadata.get("doc_id")
                        or metadata.get("document_id")
                        or metadata.get("chunk_id")
                        or f"chunk_{idx}"
                    ),
                    "content": content,
                    "metadata": metadata,
                    "score": float(getattr(item, "score", metadata.get("score", 0.0))),
                }
            )
        return formatted

    # Legacy vector search -------------------------------------------------
    def _legacy_search(
        self,
        index_name: str,
        query: str,
        keywords: Optional[List[str]],
        top_k: int,
    ) -> Dict[str, Any]:
        try:
            embedding = self.embedder.embed(query)
        except Exception as exc:
            logger.warning("Legacy embedder failed, returning fallback: %s", exc)
            return {"answer": FALLBACK_RESPONSE, "chunks": self._document_chunks_fallback(index_name, top_k)}

        try:
            chunks = self.repository.vector_search(
                index_name=index_name,
                embedding=embedding,
                top_k=top_k,
                keywords=keywords,
            )
        except Exception as exc:
            logger.warning("Vector search failed, returning fallback: %s", exc)
            return {"answer": FALLBACK_RESPONSE, "chunks": self._document_chunks_fallback(index_name, top_k)}

        if not chunks:
            chunks = self._document_chunks_fallback(index_name, top_k)

        context = self._build_context(chunks)
        if not context:
            return {"answer": FALLBACK_RESPONSE, "chunks": chunks}

        user_prompt = self._build_prompt(context, query)
        try:
            answer = self.legacy_llm.complete(DEFAULT_SYSTEM_PROMPT, user_prompt)
        except Exception as exc:
            logger.warning("Legacy LLM failed, returning fallback: %s", exc)
            answer = FALLBACK_RESPONSE
        return {"answer": answer, "chunks": chunks}

    def _document_chunks_fallback(self, index_name: str, top_k: int) -> List[Dict[str, Any]]:
        """Return deterministic chunks built from stored documents or a synthetic placeholder."""
        documents = self.repository.list_documents(index_name)[:top_k]
        if documents:
            return [
                {
                    "doc_id": doc["doc_id"],
                    "content": doc.get("content", ""),
                    "metadata": doc.get("metadata", {}),
                    "score": 0.0,
                }
                for doc in documents
            ]
        return [
            {
                "doc_id": "fallback",
                "content": "No matching documents were found, but the system is operational.",
                "metadata": {"index_name": index_name},
                "score": 0.0,
            }
        ]

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
