"""Business logic for index management."""

from __future__ import annotations

from typing import List, Dict, Any
from backend.app.repositories.neo4j_repository import Neo4jRepository


class IndexService:
    """Encapsulates index CRUD operations."""

    def __init__(self, repository: Neo4jRepository) -> None:
        self.repository = repository

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
