"""Business logic for document management."""

from __future__ import annotations

from typing import Dict, Any, List, Optional

from backend.app.core.clients import EmbeddingClient
from backend.app.repositories.neo4j_repository import Neo4jRepository


class DocumentService:
    """Handles CRUD for RAG documents."""

    def __init__(self, repository: Neo4jRepository, embedder: EmbeddingClient) -> None:
        self.repository = repository
        self.embedder = embedder

    def list_documents(self, index_name: str) -> List[Dict[str, Any]]:
        return self.repository.list_documents(index_name)

    def get_document(self, index_name: str, doc_id: str) -> Dict[str, Any] | None:
        return self.repository.get_document(index_name, doc_id)

    def create_document(
        self,
        index_name: str,
        content: str,
        metadata: Dict[str, Any],
        embedding: Optional[List[float]] = None,
    ) -> Dict[str, Any]:
        embedding_vec = embedding or self.embedder.embed(content)
        return self.repository.create_document(index_name, content, metadata, embedding_vec)

    def update_document(
        self,
        index_name: str,
        doc_id: str,
        content: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        embedding: Optional[List[float]] = None,
    ) -> Dict[str, Any] | None:
        embedding_vec = embedding
        if embedding_vec is None and content is not None:
            embedding_vec = self.embedder.embed(content)
        return self.repository.update_document(index_name, doc_id, content, metadata, embedding_vec)

    def delete_document(self, index_name: str, doc_id: str) -> None:
        self.repository.delete_document(index_name, doc_id)
