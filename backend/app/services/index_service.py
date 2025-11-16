"""Business logic for index management and KG schema orchestration."""

from __future__ import annotations

from typing import List, Dict, Any, Optional

from backend.app.repositories.neo4j_repository import Neo4jRepository
from backend.app.services.graph_builder_support import GraphBuilderSupport
from kg_builder import EXAMPLE_SCHEMAS


class IndexService:
    """Encapsulates index CRUD operations and schema workflows."""

    def __init__(self, repository: Neo4jRepository) -> None:
        self.repository = repository
        self._graph_builder_support = GraphBuilderSupport(repository.driver)

    def list_indexes(self) -> List[Dict[str, Any]]:
        return self.repository.list_indexes()

    def get_index(self, name: str) -> Dict[str, Any] | None:
        return self.repository.get_index(name)

    def create_index(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        return self.repository.upsert_index(payload)

    def update_index(self, name: str, payload: Dict[str, Any]) -> Dict[str, Any] | None:
        data = {"name": name, **payload}
        return self.repository.upsert_index(data)

    def delete_index(self, name: str) -> None:
        self.repository.delete_index(name)

    # ------------------------------------------------------------------
    # Knowledge graph schema helpers (align with example_kg_builder)

    def extract_schema_from_text(self, sample_text: str) -> Dict[str, Any]:
        """Extract a schema from example text using the builder pipeline."""
        builder = self._graph_builder_support.get_builder()
        return self._graph_builder_support.run(builder.extract_schema_from_text, sample_text)

    def apply_schema_preset(self, preset_name: str) -> Dict[str, Any]:
        """Apply one of the EXAMPLE_SCHEMAS presets to the builder."""
        schema = self._get_schema_preset(preset_name)
        builder = self._graph_builder_support.get_builder()
        builder.define_schema(
            node_types=schema["node_types"],
            relationship_types=schema["relationship_types"],
            patterns=schema["patterns"],
        )
        return schema

    def define_custom_schema(
        self,
        node_types: List[Dict[str, Any]],
        relationship_types: List[Dict[str, Any]],
        patterns: List[tuple],
    ) -> Dict[str, Any]:
        """Define a tailored schema for specialized indexes."""
        builder = self._graph_builder_support.get_builder()
        return builder.define_schema(
            node_types=node_types,
            relationship_types=relationship_types,
            patterns=patterns,
        )

    def resolve_entities(
        self,
        resolver_type: str = "exact",
        filter_query: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Trigger entity resolution routines just like example_kg_builder."""
        builder = self._graph_builder_support.get_builder()
        return self._graph_builder_support.run(
            builder.resolve_entities,
            resolver_type=resolver_type,
            filter_query=filter_query,
        )

    @staticmethod
    def _get_schema_preset(preset_name: str) -> Dict[str, Any]:
        if preset_name not in EXAMPLE_SCHEMAS:
            raise ValueError(f"Unknown schema preset: {preset_name}")
        return EXAMPLE_SCHEMAS[preset_name]
