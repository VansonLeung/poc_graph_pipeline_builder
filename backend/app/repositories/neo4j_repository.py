"""Neo4j repository helpers for indexes, documents and search."""

from __future__ import annotations

import json
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import uuid4

from neo4j import Driver
from neo4j.graph import Node


class Neo4jRepository:
    """Low-level data access helper for Neo4j."""

    INDEX_LABEL = "RAGIndex"
    DOCUMENT_LABEL = "RAGDocument"

    def __init__(self, driver: Driver, vector_index_name: str) -> None:
        self.driver = driver
        self.vector_index_name = vector_index_name
        self._ensure_constraints()

    def _ensure_constraints(self) -> None:
        with self.driver.session() as session:
            session.run(
                f"""
                CREATE CONSTRAINT IF NOT EXISTS
                FOR (index:{self.INDEX_LABEL})
                REQUIRE index.name IS UNIQUE
                """
            )
            session.run(
                f"""
                CREATE CONSTRAINT IF NOT EXISTS
                FOR (doc:{self.DOCUMENT_LABEL})
                REQUIRE doc.doc_id IS UNIQUE
                """
            )

    # Index operations -----------------------------------------------------
    def list_indexes(self) -> List[Dict[str, Any]]:
        query = (
            f"MATCH (i:{self.INDEX_LABEL}) "
            "RETURN i ORDER BY i.name"
        )
        with self.driver.session() as session:
            records = session.run(query)
            return [record["i"] for record in records]

    def get_index(self, name: str) -> Optional[Dict[str, Any]]:
        query = (
            f"MATCH (i:{self.INDEX_LABEL} {{name: $name}}) "
            "RETURN i"
        )
        with self.driver.session() as session:
            record = session.run(query, name=name).single()
            return record["i"] if record else None

    def upsert_index(self, data: Dict[str, Any]) -> Dict[str, Any]:
        now = datetime.utcnow().isoformat()
        query = (
            f"MERGE (i:{self.INDEX_LABEL} {{name: $name}}) "
            "ON CREATE SET i.created_at = $now "
            "SET i.description = $description, "
            "    i.vector_index_name = $vector_index_name, "
            "    i.dimension = $dimension, "
            "    i.updated_at = $now "
            "RETURN i"
        )
        params = {
            "name": data["name"],
            "description": data.get("description"),
            "vector_index_name": data.get("vector_index_name", self.vector_index_name),
            "dimension": data.get("dimension"),
            "now": now,
        }
        with self.driver.session() as session:
            record = session.run(query, **params).single()
            return record["i"]

    def delete_index(self, name: str) -> None:
        with self.driver.session() as session:
            session.run(
                f"MATCH (d:{self.DOCUMENT_LABEL} {{index_name: $name}}) DETACH DELETE d",
                name=name,
            )
            session.run(
                f"MATCH (i:{self.INDEX_LABEL} {{name: $name}}) DETACH DELETE i",
                name=name,
            )

    # Document operations --------------------------------------------------
    def list_documents(self, index_name: str) -> List[Dict[str, Any]]:
        query = (
            f"MATCH (i:{self.INDEX_LABEL} {{name: $index_name}})-[:HAS_DOCUMENT]->(d:{self.DOCUMENT_LABEL}) "
            "RETURN d ORDER BY d.updated_at DESC"
        )
        with self.driver.session() as session:
            records = session.run(query, index_name=index_name)
            return [self._node_to_dict(record["d"]) for record in records]

    def get_document(self, index_name: str, doc_id: str) -> Optional[Dict[str, Any]]:
        query = (
            f"MATCH (i:{self.INDEX_LABEL} {{name: $index_name}})-[:HAS_DOCUMENT]->(d:{self.DOCUMENT_LABEL} {{doc_id: $doc_id}}) "
            "RETURN d"
        )
        with self.driver.session() as session:
            record = session.run(query, index_name=index_name, doc_id=doc_id).single()
            return self._node_to_dict(record["d"]) if record else None

    def create_document(
        self,
        index_name: str,
        content: str,
        metadata: Dict[str, Any],
        embedding: List[float],
    ) -> Dict[str, Any]:
        doc_id = str(uuid4())
        now = datetime.utcnow().isoformat()
        metadata_json = json.dumps(metadata or {})
        document_payload = {
            "doc_id": doc_id,
            "index_name": index_name,
            "content": content,
            "metadata_json": metadata_json,
            "embedding": embedding,
            "created_at": now,
            "updated_at": now,
        }
        query = (
            f"MATCH (i:{self.INDEX_LABEL} {{name: $index_name}}) "
            f"CREATE (i)-[:HAS_DOCUMENT]->(d:{self.DOCUMENT_LABEL}) "
            "SET d = $payload "
            "RETURN d"
        )
        with self.driver.session() as session:
            record = session.run(query, payload=document_payload, index_name=index_name).single()
            if not record:
                raise ValueError(f"Index {index_name} not found")
            return self._node_to_dict(record["d"])

    def update_document(
        self,
        index_name: str,
        doc_id: str,
        content: Optional[str],
        metadata: Optional[Dict[str, Any]],
        embedding: Optional[List[float]],
    ) -> Optional[Dict[str, Any]]:
        assignments = ["d.updated_at = $now"]
        params: Dict[str, Any] = {
            "index_name": index_name,
            "doc_id": doc_id,
            "now": datetime.utcnow().isoformat(),
        }
        if content is not None:
            assignments.append("d.content = $content")
            params["content"] = content
        if metadata is not None:
            assignments.append("d.metadata_json = $metadata_json")
            params["metadata_json"] = json.dumps(metadata)
        if embedding is not None:
            assignments.append("d.embedding = $embedding")
            params["embedding"] = embedding
        if len(assignments) == 1:  # Only updated_at
            set_clause = "SET " + assignments[0]
        else:
            set_clause = "SET " + ", ".join(assignments)
        query = (
            f"MATCH (i:{self.INDEX_LABEL} {{name: $index_name}})-[:HAS_DOCUMENT]->(d:{self.DOCUMENT_LABEL} {{doc_id: $doc_id}}) "
            f"{set_clause} RETURN d"
        )
        with self.driver.session() as session:
            record = session.run(query, **params).single()
            return self._node_to_dict(record["d"]) if record else None

    def delete_document(self, index_name: str, doc_id: str) -> None:
        query = (
            f"MATCH (i:{self.INDEX_LABEL} {{name: $index_name}})-[:HAS_DOCUMENT]->(d:{self.DOCUMENT_LABEL} {{doc_id: $doc_id}}) "
            "DETACH DELETE d"
        )
        with self.driver.session() as session:
            session.run(query, index_name=index_name, doc_id=doc_id)

    def vector_search(
        self,
        index_name: str,
        embedding: List[float],
        top_k: int,
        keywords: Optional[List[str]] = None,
    ) -> List[Dict[str, Any]]:
        multiplier = max(3, top_k * 2)
        query = (
            "CALL db.index.vector.queryNodes($vector_index_name, $limit, $embedding) "
            "YIELD node, score "
            "WITH node, score "
            "WHERE node.index_name = $index_name "
            "  AND ($keywords IS NULL OR size($keywords) = 0 OR any(keyword IN $keywords "
            "      WHERE toLower(node.content) CONTAINS toLower(keyword))) "
            "RETURN node.doc_id AS doc_id, node.content AS content, node.metadata_json AS metadata_json, score "
            "ORDER BY score DESC LIMIT $top_k"
        )
        params = {
            "vector_index_name": self.vector_index_name,
            "limit": multiplier,
            "embedding": embedding,
            "index_name": index_name,
            "keywords": keywords,
            "top_k": top_k,
        }
        with self.driver.session() as session:
            result = session.run(query, **params)
            chunks = []
            for record in result:
                metadata_json = record.get("metadata_json")
                metadata = json.loads(metadata_json) if metadata_json else {}
                chunks.append(
                    {
                        "doc_id": record["doc_id"],
                        "content": record["content"],
                        "metadata": metadata,
                        "score": record["score"],
                    }
                )
            return chunks

    # ------------------------------------------------------------------
    # ------------------------------------------------------------------
    @staticmethod
    def _node_to_dict(node: Node) -> Dict[str, Any]:
        data = dict(node)
        metadata_json = data.pop("metadata_json", None)
        if metadata_json:
            try:
                data["metadata"] = json.loads(metadata_json)
            except json.JSONDecodeError:
                data["metadata"] = {}
        else:
            data["metadata"] = {}
        return data
