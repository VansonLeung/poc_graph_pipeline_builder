"""
Retriever module for Neo4j GraphRAG.
Implements various retrieval strategies for querying the knowledge graph.
"""

from typing import Optional, Dict, List, Any
from neo4j import Driver

from neo4j_graphrag.retrievers import (
    VectorRetriever,
    VectorCypherRetriever,
    HybridRetriever,
    HybridCypherRetriever,
    Text2CypherRetriever,
    WeaviateNeo4jRetriever,
    PineconeNeo4jRetriever,
    QdrantNeo4jRetriever,
)
from neo4j_graphrag.embeddings import Embedder
from neo4j_graphrag.llm import LLMInterface
from neo4j_graphrag.types import RetrieverResultItem
import neo4j


class GraphRetrieverManager:
    """
    Manager class for different retrieval strategies.
    """
    
    def __init__(
        self,
        driver: Driver,
        embedder: Embedder,
        vector_index_name: str = "document_embeddings",
        fulltext_index_name: str = "document_fulltext",
    ):
        """
        Initialize the retriever manager.
        
        Args:
            driver: Neo4j driver instance
            embedder: Embedder for converting text to vectors
            vector_index_name: Name of the vector index
            fulltext_index_name: Name of the fulltext index
        """
        self.driver = driver
        self.embedder = embedder
        self.vector_index_name = vector_index_name
        self.fulltext_index_name = fulltext_index_name
    
    def get_vector_retriever(
        self,
        return_properties: Optional[List[str]] = None,
    ) -> VectorRetriever:
        """
        Create a basic vector retriever.
        
        Args:
            return_properties: List of node properties to return
        
        Returns:
            VectorRetriever instance
        
        Example usage:
            retriever = manager.get_vector_retriever(
                return_properties=["title", "content"]
            )
            results = retriever.search(query_text="What is GraphRAG?", top_k=5)
        """
        return VectorRetriever(
            driver=self.driver,
            index_name=self.vector_index_name,
            embedder=self.embedder,
            return_properties=return_properties,
        )
    
    def get_vector_cypher_retriever(
        self,
        retrieval_query: str,
        result_formatter: Optional[callable] = None,
    ) -> VectorCypherRetriever:
        """
        Create a vector retriever with custom Cypher query.
        
        Args:
            retrieval_query: Cypher query to execute after vector search
            result_formatter: Function to format results
        
        Returns:
            VectorCypherRetriever instance
        
        Example usage:
            retrieval_query = '''
            MATCH (node)-[:HAS_ENTITY]->(entity)
            RETURN node.text as text, 
                   collect(entity.name) as entities,
                   score
            '''
            
            def formatter(record):
                return RetrieverResultItem(
                    content=f"Text: {record['text']}, Entities: {record['entities']}",
                    metadata={"score": record["score"]}
                )
            
            retriever = manager.get_vector_cypher_retriever(
                retrieval_query=retrieval_query,
                result_formatter=formatter
            )
        """
        return VectorCypherRetriever(
            driver=self.driver,
            index_name=self.vector_index_name,
            embedder=self.embedder,
            retrieval_query=retrieval_query,
            result_formatter=result_formatter,
        )
    
    def get_hybrid_retriever(
        self,
        return_properties: Optional[List[str]] = None,
    ) -> HybridRetriever:
        """
        Create a hybrid retriever (vector + fulltext).
        
        Args:
            return_properties: List of node properties to return
        
        Returns:
            HybridRetriever instance
        
        Example usage:
            retriever = manager.get_hybrid_retriever()
            results = retriever.search(
                query_text="machine learning applications",
                top_k=5
            )
        """
        return HybridRetriever(
            driver=self.driver,
            vector_index_name=self.vector_index_name,
            fulltext_index_name=self.fulltext_index_name,
            embedder=self.embedder,
            return_properties=return_properties,
        )
    
    def get_hybrid_cypher_retriever(
        self,
        retrieval_query: str,
        result_formatter: Optional[callable] = None,
    ) -> HybridCypherRetriever:
        """
        Create a hybrid retriever with custom Cypher query.
        
        Args:
            retrieval_query: Cypher query to execute after hybrid search
            result_formatter: Function to format results
        
        Returns:
            HybridCypherRetriever instance
        """
        return HybridCypherRetriever(
            driver=self.driver,
            vector_index_name=self.vector_index_name,
            fulltext_index_name=self.fulltext_index_name,
            embedder=self.embedder,
            retrieval_query=retrieval_query,
            result_formatter=result_formatter,
        )
    
    def get_text2cypher_retriever(
        self,
        llm: LLMInterface,
        neo4j_schema: Optional[str] = None,
        examples: Optional[List[str]] = None,
    ) -> Text2CypherRetriever:
        """
        Create a Text2Cypher retriever that generates Cypher queries from natural language.
        
        Args:
            llm: LLM interface for query generation
            neo4j_schema: Optional Neo4j schema description
            examples: Optional list of example queries
        
        Returns:
            Text2CypherRetriever instance
        
        Example usage:
            schema = '''
            Node properties:
            Person {name: STRING, age: INTEGER}
            Company {name: STRING, industry: STRING}
            
            Relationships:
            (:Person)-[:WORKS_FOR]->(:Company)
            (:Person)-[:KNOWS]->(:Person)
            '''
            
            examples = [
                "USER: 'Find all people' QUERY: MATCH (p:Person) RETURN p.name",
                "USER: 'Who works for Acme?' QUERY: MATCH (p:Person)-[:WORKS_FOR]->(c:Company {name: 'Acme'}) RETURN p.name"
            ]
            
            retriever = manager.get_text2cypher_retriever(
                llm=llm,
                neo4j_schema=schema,
                examples=examples
            )
            
            results = retriever.search(query_text="Who are the employees of Google?")
        """
        return Text2CypherRetriever(
            driver=self.driver,
            llm=llm,
            neo4j_schema=neo4j_schema,
            examples=examples,
        )
    
    def search_with_filters(
        self,
        query_text: str,
        filters: Dict[str, Any],
        top_k: int = 5,
        retriever_type: str = "vector",
    ) -> Any:
        """
        Search with pre-filters applied.
        
        Args:
            query_text: Query text
            filters: Filter dictionary
            top_k: Number of results to return
            retriever_type: Type of retriever to use
        
        Returns:
            Search results
        
        Example filters:
            # Equal
            filters = {"year": 2023}
            
            # Greater than or equal
            filters = {"year": {"$gte": 2020}}
            
            # Between
            filters = {"year": {"$between": [2020, 2023]}}
            
            # In list
            filters = {"category": {"$in": ["AI", "ML", "DL"]}}
            
            # Like (case-sensitive)
            filters = {"title": {"$like": "Neural"}}
            
            # Multiple conditions (AND)
            filters = {
                "year": {"$gte": 2020},
                "category": {"$in": ["AI", "ML"]}
            }
            
            # OR conditions
            filters = {
                "$or": [
                    {"category": "AI"},
                    {"category": "ML"}
                ]
            }
        """
        if retriever_type == "vector":
            retriever = self.get_vector_retriever()
        elif retriever_type == "hybrid":
            retriever = self.get_hybrid_retriever()
        else:
            raise ValueError(f"Unsupported retriever type: {retriever_type}")
        
        return retriever.search(
            query_text=query_text,
            top_k=top_k,
            filters=filters
        )


class ExternalVectorRetrieverManager:
    """
    Manager for external vector database retrievers.
    """
    
    @staticmethod
    def get_weaviate_retriever(
        driver: Driver,
        weaviate_client: Any,
        embedder: Embedder,
        collection: str,
        id_property_external: str = "neo4j_id",
        id_property_neo4j: str = "id",
        return_properties: Optional[List[str]] = None,
        retrieval_query: Optional[str] = None,
    ) -> WeaviateNeo4jRetriever:
        """
        Create a Weaviate retriever.
        
        Args:
            driver: Neo4j driver
            weaviate_client: Weaviate client instance
            embedder: Embedder
            collection: Weaviate collection name
            id_property_external: Property name in Weaviate
            id_property_neo4j: Property name in Neo4j
            return_properties: Properties to return
            retrieval_query: Optional Cypher query
        
        Returns:
            WeaviateNeo4jRetriever instance
        """
        return WeaviateNeo4jRetriever(
            driver=driver,
            client=weaviate_client,
            embedder=embedder,
            collection=collection,
            id_property_external=id_property_external,
            id_property_neo4j=id_property_neo4j,
            return_properties=return_properties,
            retrieval_query=retrieval_query,
        )
    
    @staticmethod
    def get_pinecone_retriever(
        driver: Driver,
        pinecone_client: Any,
        embedder: Embedder,
        index_name: str,
        id_property_neo4j: str = "id",
        return_properties: Optional[List[str]] = None,
        retrieval_query: Optional[str] = None,
    ) -> PineconeNeo4jRetriever:
        """
        Create a Pinecone retriever.
        
        Args:
            driver: Neo4j driver
            pinecone_client: Pinecone client instance
            embedder: Embedder
            index_name: Pinecone index name
            id_property_neo4j: Property name in Neo4j
            return_properties: Properties to return
            retrieval_query: Optional Cypher query
        
        Returns:
            PineconeNeo4jRetriever instance
        """
        return PineconeNeo4jRetriever(
            driver=driver,
            client=pinecone_client,
            embedder=embedder,
            index_name=index_name,
            id_property_neo4j=id_property_neo4j,
            return_properties=return_properties,
            retrieval_query=retrieval_query,
        )
    
    @staticmethod
    def get_qdrant_retriever(
        driver: Driver,
        qdrant_client: Any,
        embedder: Embedder,
        collection_name: str,
        using: str = "my-vector",
        id_property_external: str = "neo4j_id",
        id_property_neo4j: str = "id",
        return_properties: Optional[List[str]] = None,
        retrieval_query: Optional[str] = None,
    ) -> QdrantNeo4jRetriever:
        """
        Create a Qdrant retriever.
        
        Args:
            driver: Neo4j driver
            qdrant_client: Qdrant client instance
            embedder: Embedder
            collection_name: Qdrant collection name
            using: Vector name in Qdrant
            id_property_external: Property name in Qdrant
            id_property_neo4j: Property name in Neo4j
            return_properties: Properties to return
            retrieval_query: Optional Cypher query
        
        Returns:
            QdrantNeo4jRetriever instance
        """
        return QdrantNeo4jRetriever(
            driver=driver,
            client=qdrant_client,
            embedder=embedder,
            collection_name=collection_name,
            using=using,
            id_property_external=id_property_external,
            id_property_neo4j=id_property_neo4j,
            return_properties=return_properties,
            retrieval_query=retrieval_query,
        )


# Common retrieval query templates
RETRIEVAL_QUERY_TEMPLATES = {
    "entity_context": """
        OPTIONAL MATCH (node)-[:HAS_ENTITY]->(entity:__Entity__)
        RETURN node.text as text,
               node.index as chunk_index,
               collect(DISTINCT entity.name) as entities,
               score
    """,
    
    "document_context": """
        MATCH (node)-[:FROM_DOCUMENT]->(doc:Document)
        RETURN node.text as text,
               doc.path as document_path,
               node.index as chunk_index,
               score
    """,
    
    "full_context": """
        OPTIONAL MATCH (node)-[:HAS_ENTITY]->(entity:__Entity__)
        OPTIONAL MATCH (node)-[:FROM_DOCUMENT]->(doc:Document)
        OPTIONAL MATCH (node)-[:NEXT_CHUNK]->(next:Chunk)
        RETURN node.text as text,
               doc.path as document_path,
               node.index as chunk_index,
               collect(DISTINCT entity.name) as entities,
               next.text as next_chunk_text,
               score
    """,
    
    "neighbor_chunks": """
        OPTIONAL MATCH (prev:Chunk)-[:NEXT_CHUNK]->(node)
        OPTIONAL MATCH (node)-[:NEXT_CHUNK]->(next:Chunk)
        RETURN prev.text as previous_chunk,
               node.text as current_chunk,
               next.text as next_chunk,
               score
    """,
}


def create_result_formatter(fields: List[str]) -> callable:
    """
    Create a result formatter function.
    
    Args:
        fields: List of field names to include in content
    
    Returns:
        Formatter function
    
    Example:
        formatter = create_result_formatter(["text", "entities", "document_path"])
        
        # This creates a formatter that generates content like:
        # "Text: ..., Entities: [...], Document: ..."
    """
    def formatter(record: neo4j.Record) -> RetrieverResultItem:
        content_parts = []
        metadata = {"score": record.get("score")}
        
        for field in fields:
            value = record.get(field)
            if value is not None:
                content_parts.append(f"{field}: {value}")
                metadata[field] = value
        
        content = ", ".join(content_parts)
        
        return RetrieverResultItem(
            content=content,
            metadata=metadata
        )
    
    return formatter
