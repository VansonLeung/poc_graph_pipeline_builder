"""
Utility functions for Neo4j GraphRAG system.
Includes index management, data loading, and visualization helpers.
"""

from typing import Optional, List, Dict, Any
from pathlib import Path
import json

from neo4j import Driver, GraphDatabase
from neo4j_graphrag.indexes import (
    create_vector_index,
    create_fulltext_index,
    upsert_vector,
    upsert_vectors,
    drop_index_if_exists,
)
from neo4j_graphrag.types import EntityType


class IndexManager:
    """
    Manager for Neo4j indexes (vector and fulltext).
    """
    
    def __init__(self, driver: Driver):
        """
        Initialize the index manager.
        
        Args:
            driver: Neo4j driver instance
        """
        self.driver = driver
    
    def create_vector_index(
        self,
        index_name: str,
        label: str,
        embedding_property: str,
        dimensions: int = 1536,
        similarity_fn: str = "cosine",
    ) -> None:
        """
        Create a vector index.
        
        Args:
            index_name: Name of the index
            label: Node label to index
            embedding_property: Property containing embeddings
            dimensions: Vector dimensions
            similarity_fn: Similarity function ("cosine", "euclidean")
        
        Example:
            manager.create_vector_index(
                index_name="chunk_embeddings",
                label="Chunk",
                embedding_property="embedding",
                dimensions=1536,
                similarity_fn="cosine"
            )
        """
        print(f"Creating vector index '{index_name}'...")
        create_vector_index(
            self.driver,
            index_name,
            label=label,
            embedding_property=embedding_property,
            dimensions=dimensions,
            similarity_fn=similarity_fn,
        )
        print(f"✓ Vector index '{index_name}' created successfully")
    
    def create_fulltext_index(
        self,
        index_name: str,
        label: str,
        text_properties: List[str],
    ) -> None:
        """
        Create a fulltext index.
        
        Args:
            index_name: Name of the index
            label: Node label to index
            text_properties: List of text properties to index
        
        Example:
            manager.create_fulltext_index(
                index_name="chunk_fulltext",
                label="Chunk",
                text_properties=["text"]
            )
        """
        print(f"Creating fulltext index '{index_name}'...")
        create_fulltext_index(
            self.driver,
            index_name,
            label=label,
            node_properties=text_properties,
        )
        print(f"✓ Fulltext index '{index_name}' created successfully")
    
    def drop_index(self, index_name: str) -> None:
        """
        Drop an index if it exists.
        
        Args:
            index_name: Name of the index to drop
        """
        print(f"Dropping index '{index_name}'...")
        drop_index_if_exists(self.driver, index_name)
        print(f"✓ Index '{index_name}' dropped")
    
    def list_indexes(self) -> List[Dict[str, Any]]:
        """
        List all indexes in the database.
        
        Returns:
            List of index information dictionaries
        """
        with self.driver.session() as session:
            result = session.run("SHOW INDEXES")
            indexes = [dict(record) for record in result]
        
        return indexes
    
    def upsert_embeddings(
        self,
        ids: List[str],
        embeddings: List[List[float]],
        embedding_property: str = "embedding",
        entity_type: EntityType = EntityType.NODE,
    ) -> None:
        """
        Upsert embeddings for nodes or relationships.
        
        Args:
            ids: List of node/relationship IDs
            embeddings: List of embedding vectors
            embedding_property: Property name for embeddings
            entity_type: NODE or RELATIONSHIP
        """
        upsert_vectors(
            self.driver,
            ids=ids,
            embedding_property=embedding_property,
            embeddings=embeddings,
            entity_type=entity_type,
        )


class DatabaseUtils:
    """
    Utility functions for database operations.
    """
    
    @staticmethod
    def get_node_count(driver: Driver, label: Optional[str] = None) -> int:
        """
        Get count of nodes, optionally filtered by label.
        
        Args:
            driver: Neo4j driver
            label: Optional node label filter
        
        Returns:
            Node count
        """
        with driver.session() as session:
            if label:
                query = f"MATCH (n:{label}) RETURN count(n) as count"
            else:
                query = "MATCH (n) RETURN count(n) as count"
            
            result = session.run(query)
            return result.single()["count"]
    
    @staticmethod
    def get_relationship_count(driver: Driver, rel_type: Optional[str] = None) -> int:
        """
        Get count of relationships, optionally filtered by type.
        
        Args:
            driver: Neo4j driver
            rel_type: Optional relationship type filter
        
        Returns:
            Relationship count
        """
        with driver.session() as session:
            if rel_type:
                query = f"MATCH ()-[r:{rel_type}]->() RETURN count(r) as count"
            else:
                query = "MATCH ()-[r]->() RETURN count(r) as count"
            
            result = session.run(query)
            return result.single()["count"]
    
    @staticmethod
    def get_labels(driver: Driver) -> List[str]:
        """
        Get all node labels in the database.
        
        Args:
            driver: Neo4j driver
        
        Returns:
            List of labels
        """
        with driver.session() as session:
            result = session.run("CALL db.labels()")
            return [record["label"] for record in result]
    
    @staticmethod
    def get_relationship_types(driver: Driver) -> List[str]:
        """
        Get all relationship types in the database.
        
        Args:
            driver: Neo4j driver
        
        Returns:
            List of relationship types
        """
        with driver.session() as session:
            result = session.run("CALL db.relationshipTypes()")
            return [record["relationshipType"] for record in result]
    
    @staticmethod
    def clear_database(driver: Driver, confirm: bool = False) -> None:
        """
        Clear all data from the database.
        
        Args:
            driver: Neo4j driver
            confirm: Must be True to actually clear the database
        
        Warning:
            This will delete ALL data in the database!
        """
        if not confirm:
            raise ValueError("Must set confirm=True to clear database")
        
        with driver.session() as session:
            # Delete in batches to avoid memory issues
            while True:
                result = session.run(
                    "MATCH (n) WITH n LIMIT 10000 DETACH DELETE n RETURN count(n) as deleted"
                )
                deleted = result.single()["deleted"]
                if deleted == 0:
                    break
        
        print("✓ Database cleared")
    
    @staticmethod
    def get_schema_summary(driver: Driver) -> Dict[str, Any]:
        """
        Get a summary of the database schema.
        
        Args:
            driver: Neo4j driver
        
        Returns:
            Schema summary dictionary
        """
        labels = DatabaseUtils.get_labels(driver)
        rel_types = DatabaseUtils.get_relationship_types(driver)
        
        summary = {
            "labels": labels,
            "label_count": len(labels),
            "relationship_types": rel_types,
            "relationship_type_count": len(rel_types),
            "nodes_per_label": {},
            "relationships_per_type": {},
        }
        
        # Get counts per label
        for label in labels:
            count = DatabaseUtils.get_node_count(driver, label)
            summary["nodes_per_label"][label] = count
        
        # Get counts per relationship type
        for rel_type in rel_types:
            count = DatabaseUtils.get_relationship_count(driver, rel_type)
            summary["relationships_per_type"][rel_type] = count
        
        return summary
    
    @staticmethod
    def print_schema_summary(driver: Driver) -> None:
        """
        Print a formatted schema summary.
        
        Args:
            driver: Neo4j driver
        """
        summary = DatabaseUtils.get_schema_summary(driver)
        
        print("\n" + "=" * 80)
        print("DATABASE SCHEMA SUMMARY")
        print("=" * 80)
        
        print(f"\nNode Labels ({summary['label_count']}):")
        for label, count in summary["nodes_per_label"].items():
            print(f"  - {label}: {count:,} nodes")
        
        print(f"\nRelationship Types ({summary['relationship_type_count']}):")
        for rel_type, count in summary["relationships_per_type"].items():
            print(f"  - {rel_type}: {count:,} relationships")
        
        total_nodes = sum(summary["nodes_per_label"].values())
        total_rels = sum(summary["relationships_per_type"].values())
        
        print(f"\nTotal: {total_nodes:,} nodes, {total_rels:,} relationships")
        print("=" * 80)


class DataLoader:
    """
    Helper for loading data from various sources.
    """
    
    @staticmethod
    def load_text_file(file_path: Path) -> str:
        """
        Load text from a file.
        
        Args:
            file_path: Path to text file
        
        Returns:
            File content as string
        """
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    
    @staticmethod
    def load_json_file(file_path: Path) -> Any:
        """
        Load JSON from a file.
        
        Args:
            file_path: Path to JSON file
        
        Returns:
            Parsed JSON data
        """
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    @staticmethod
    def load_multiple_files(
        directory: Path,
        extensions: List[str] = ['.txt', '.md'],
    ) -> List[Dict[str, Any]]:
        """
        Load multiple text files from a directory.
        
        Args:
            directory: Directory path
            extensions: List of file extensions to include
        
        Returns:
            List of dictionaries with 'path' and 'content' keys
        """
        files = []
        for ext in extensions:
            for file_path in directory.glob(f"*{ext}"):
                content = DataLoader.load_text_file(file_path)
                files.append({
                    "path": str(file_path),
                    "content": content,
                    "filename": file_path.name,
                })
        
        return files


class QueryHelper:
    """
    Helper functions for common Cypher queries.
    """
    
    @staticmethod
    def find_shortest_path(
        driver: Driver,
        start_label: str,
        start_property: str,
        start_value: str,
        end_label: str,
        end_property: str,
        end_value: str,
    ) -> List[Any]:
        """
        Find shortest path between two nodes.
        
        Args:
            driver: Neo4j driver
            start_label: Label of start node
            start_property: Property to match on start node
            start_value: Value to match
            end_label: Label of end node
            end_property: Property to match on end node
            end_value: Value to match
        
        Returns:
            List of paths
        """
        query = f"""
        MATCH (start:{start_label} {{{start_property}: $start_value}}),
              (end:{end_label} {{{end_property}: $end_value}}),
              path = shortestPath((start)-[*]-(end))
        RETURN path
        """
        
        with driver.session() as session:
            result = session.run(
                query,
                start_value=start_value,
                end_value=end_value
            )
            return [record["path"] for record in result]
    
    @staticmethod
    def get_neighbors(
        driver: Driver,
        label: str,
        property_name: str,
        property_value: str,
        depth: int = 1,
    ) -> List[Dict[str, Any]]:
        """
        Get neighboring nodes up to a certain depth.
        
        Args:
            driver: Neo4j driver
            label: Node label
            property_name: Property to match
            property_value: Value to match
            depth: Traversal depth
        
        Returns:
            List of neighbor nodes
        """
        query = f"""
        MATCH (n:{label} {{{property_name}: $value}})
        CALL apoc.path.subgraphNodes(n, {{
            maxLevel: $depth
        }})
        YIELD node
        RETURN node
        """
        
        with driver.session() as session:
            result = session.run(
                query,
                value=property_value,
                depth=depth
            )
            return [dict(record["node"]) for record in result]


class SetupHelper:
    """
    Helper functions for initial setup.
    """
    
    @staticmethod
    def setup_indexes(
        driver: Driver,
        vector_index_name: str = "document_embeddings",
        fulltext_index_name: str = "document_fulltext",
        chunk_label: str = "Chunk",
        dimensions: int = 1536,
    ) -> None:
        """
        Set up all necessary indexes.
        
        Args:
            driver: Neo4j driver
            vector_index_name: Name for vector index
            fulltext_index_name: Name for fulltext index
            chunk_label: Label for chunk nodes
            dimensions: Vector dimensions
        """
        manager = IndexManager(driver)
        
        print("\nSetting up indexes...")
        print("-" * 80)
        
        # Create vector index
        manager.create_vector_index(
            index_name=vector_index_name,
            label=chunk_label,
            embedding_property="embedding",
            dimensions=dimensions,
            similarity_fn="cosine",
        )
        
        # Create fulltext index
        manager.create_fulltext_index(
            index_name=fulltext_index_name,
            label=chunk_label,
            text_properties=["text"],
        )
        
        print("\n✓ All indexes created successfully!")
    
    @staticmethod
    def verify_connection(
        uri: str,
        username: str,
        password: str,
    ) -> bool:
        """
        Verify Neo4j connection.
        
        Args:
            uri: Neo4j URI
            username: Username
            password: Password
        
        Returns:
            True if connection successful
        """
        try:
            driver = GraphDatabase.driver(uri, auth=(username, password))
            with driver.session() as session:
                result = session.run("RETURN 1 as test")
                result.single()
            driver.close()
            print("✓ Neo4j connection successful!")
            return True
        except Exception as e:
            print(f"✗ Neo4j connection failed: {e}")
            return False
    
    @staticmethod
    def check_apoc_installed(driver: Driver) -> bool:
        """
        Check if APOC plugin is installed.
        
        Args:
            driver: Neo4j driver
        
        Returns:
            True if APOC is installed
        """
        try:
            with driver.session() as session:
                result = session.run("RETURN apoc.version() as version")
                version = result.single()["version"]
                print(f"✓ APOC installed (version {version})")
                return True
        except Exception:
            print("✗ APOC not installed")
            return False
