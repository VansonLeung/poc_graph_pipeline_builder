"""Business logic for document management and KG ingestion."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Dict, Any, List, Optional

from backend.app.core.clients import EmbeddingClient
from backend.app.repositories.neo4j_repository import Neo4jRepository
from backend.app.services.graph_builder_support import GraphBuilderSupport
from kg_builder import EXAMPLE_SCHEMAS

logger = logging.getLogger(__name__)


class DocumentService:
    """Handles CRUD for RAG documents and orchestrates KG builder workflows."""

    def __init__(self, repository: Neo4jRepository, embedder: EmbeddingClient) -> None:
        self.repository = repository
        self.embedder = embedder
        self._graph_builder_support = GraphBuilderSupport(repository.driver)

    def list_documents(self, index_name: str) -> List[Dict[str, Any]]:
        return self.repository.list_documents(index_name)

    def get_document(self, index_name: str, doc_id: str) -> Dict[str, Any] | None:
        return self.repository.get_document(index_name, doc_id)

    def create_document(
        self,
        index_name: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None,
        embedding: Optional[List[float]] = None,
    ) -> Dict[str, Any]:
        metadata_copy = dict(metadata or {})
        build_graph = bool(metadata_copy.pop("build_kg", False))
        schema_key = metadata_copy.pop("schema_key", None)
        perform_entity_resolution = metadata_copy.pop("perform_entity_resolution", True)

        builder_stats = None
        if build_graph:
            try:
                builder_stats = self.build_graph_from_text(
                    text=content,
                    metadata=metadata_copy,
                    schema_key=schema_key,
                    perform_entity_resolution=perform_entity_resolution,
                )
                metadata_copy["graph_ingest_completed"] = True
                metadata_copy["graph_schema_key"] = schema_key or "default"
                if isinstance(builder_stats, dict):
                    metadata_copy["graph_ingest_summary"] = {
                        "nodes": builder_stats.get("nodes_created"),
                        "relationships": builder_stats.get("relationships_created"),
                        "chunks": builder_stats.get("chunks_processed") or builder_stats.get("chunks"),
                    }
            except Exception as exc:  # pragma: no cover - defensive logging
                logger.warning("Graph ingestion failed: %s", exc)

        embedding_vec = embedding or self.embedder.embed(content)
        return self.repository.create_document(index_name, content, metadata_copy, embedding_vec)

    def update_document(
        self,
        index_name: str,
        doc_id: str,
        content: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        embedding: Optional[List[float]] = None,
    ) -> Dict[str, Any] | None:
        metadata_copy = None
        if metadata is not None:
            metadata_copy = dict(metadata)
            build_graph = bool(metadata_copy.pop("build_kg", False))
            schema_key = metadata_copy.pop("schema_key", None)
            perform_entity_resolution = metadata_copy.pop("perform_entity_resolution", True)
            if build_graph and content:
                try:
                    builder_stats = self.build_graph_from_text(
                        text=content,
                        metadata=metadata_copy,
                        schema_key=schema_key,
                        perform_entity_resolution=perform_entity_resolution,
                    )
                    metadata_copy["graph_ingest_completed"] = True
                    metadata_copy["graph_schema_key"] = schema_key or "default"
                    if isinstance(builder_stats, dict):
                        metadata_copy["graph_ingest_summary"] = {
                            "nodes": builder_stats.get("nodes_created"),
                            "relationships": builder_stats.get("relationships_created"),
                            "chunks": builder_stats.get("chunks_processed") or builder_stats.get("chunks"),
                        }
                except Exception as exc:  # pragma: no cover - defensive logging
                    logger.warning("Graph ingestion during update failed: %s", exc)
        embedding_vec = embedding
        if embedding_vec is None and content is not None:
            embedding_vec = self.embedder.embed(content)
        payload_metadata = metadata_copy if metadata_copy is not None else metadata
        return self.repository.update_document(index_name, doc_id, content, payload_metadata, embedding_vec)

    def delete_document(self, index_name: str, doc_id: str) -> None:
        self.repository.delete_document(index_name, doc_id)

    # ------------------------------------------------------------------
    # Knowledge Graph builder helpers (example_kg_builder parity)

    def build_graph_from_text(
        self,
        text: str,
        metadata: Optional[Dict[str, Any]] = None,
        schema_key: Optional[str] = None,
        perform_entity_resolution: bool = True,
    ) -> Dict[str, Any]:
        """Ingest plain text into the knowledge graph using KnowledgeGraphBuilder."""
        builder = self._graph_builder_support.get_builder()
        self._prepare_schema(builder, schema_key, sample_text=text)
        return self._graph_builder_support.run(
            builder.build_from_text,
            text=text,
            document_metadata=metadata or {},
            perform_entity_resolution=perform_entity_resolution,
        )

    def build_graph_from_pdf(
        self,
        file_path: str | Path,
        metadata: Optional[Dict[str, Any]] = None,
        schema_key: Optional[str] = None,
        perform_entity_resolution: bool = True,
    ) -> Dict[str, Any]:
        """Ingest PDF documents similarly to example_kg_builder."""
        builder = self._graph_builder_support.get_builder()
        self._prepare_schema(builder, schema_key)
        pdf_path = Path(file_path)
        return self._graph_builder_support.run(
            builder.build_from_pdf,
            file_path=pdf_path,
            document_metadata=metadata or {},
            perform_entity_resolution=perform_entity_resolution,
        )

    def _prepare_schema(self, builder, schema_key: Optional[str], sample_text: Optional[str] = None) -> None:
        """Apply schema strategies inspired by example_kg_builder."""
        if not schema_key:
            return
        if schema_key == "auto":
            if not sample_text:
                raise ValueError("Sample text is required for automatic schema extraction")
            self._graph_builder_support.run(builder.extract_schema_from_text, sample_text)
            return
        preset = EXAMPLE_SCHEMAS.get(schema_key)
        if not preset:
            raise ValueError(f"Unknown schema preset: {schema_key}")
        builder.define_schema(
            node_types=preset["node_types"],
            relationship_types=preset["relationship_types"],
            patterns=preset["patterns"],
        )
