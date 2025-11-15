"""
Knowledge Graph Builder module for Neo4j GraphRAG.
Handles document processing, entity extraction, and knowledge graph construction.
"""

import asyncio
from pathlib import Path
from typing import Optional, Dict, List, Any
from neo4j import Driver

from neo4j_graphrag.experimental.pipeline.kg_builder import SimpleKGPipeline
from neo4j_graphrag.experimental.components.schema import (
    SchemaBuilder,
    SchemaFromTextExtractor,
    NodeType,
    RelationshipType,
    PropertyType,
)
from neo4j_graphrag.experimental.components.text_splitters.fixed_size_splitter import (
    FixedSizeSplitter,
)
from neo4j_graphrag.experimental.components.resolver import (
    SinglePropertyExactMatchResolver,
    SpaCySemanticMatchResolver,
    FuzzyMatchResolver,
)
from neo4j_graphrag.llm import OpenAILLM, LLMInterface
from neo4j_graphrag.embeddings import OpenAIEmbeddings, Embedder


class KnowledgeGraphBuilder:
    """
    Main class for building knowledge graphs from unstructured data.
    """
    
    def __init__(
        self,
        driver: Driver,
        llm: LLMInterface,
        embedder: Embedder,
        neo4j_database: str = "neo4j",
        chunk_size: int = 4000,
        chunk_overlap: int = 200,
    ):
        """
        Initialize the Knowledge Graph Builder.
        
        Args:
            driver: Neo4j driver instance
            llm: LLM interface for entity extraction
            embedder: Embedder for creating chunk embeddings
            neo4j_database: Name of the Neo4j database
            chunk_size: Size of text chunks
            chunk_overlap: Overlap between chunks
        """
        self.driver = driver
        self.llm = llm
        self.embedder = embedder
        self.neo4j_database = neo4j_database
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.schema = None
    
    def define_schema(
        self,
        node_types: Optional[List[Dict[str, Any]]] = None,
        relationship_types: Optional[List[Dict[str, Any]]] = None,
        patterns: Optional[List[tuple]] = None,
    ) -> Dict[str, Any]:
        """
        Define a schema for the knowledge graph.
        
        Args:
            node_types: List of node type definitions
            relationship_types: List of relationship type definitions
            patterns: List of connection patterns (source, relation, target)
        
        Returns:
            Schema dictionary
        
        Example:
            node_types = [
                "Person",
                {"label": "Organization", "description": "A company or institution"},
                {
                    "label": "Location",
                    "properties": [
                        {"name": "name", "type": "STRING", "required": True},
                        {"name": "country", "type": "STRING"}
                    ]
                }
            ]
            relationship_types = [
                "WORKS_FOR",
                {"label": "LOCATED_IN", "description": "Physical location"}
            ]
            patterns = [
                ("Person", "WORKS_FOR", "Organization"),
                ("Organization", "LOCATED_IN", "Location")
            ]
        """
        self.schema = {
            "node_types": node_types or [],
            "relationship_types": relationship_types or [],
            "patterns": patterns or [],
        }
        return self.schema
    
    async def extract_schema_from_text(self, text: str) -> Dict[str, Any]:
        """
        Automatically extract schema from sample text using LLM.
        
        Args:
            text: Sample text to analyze
        
        Returns:
            Extracted schema dictionary
        """
        schema_extractor = SchemaFromTextExtractor(llm=self.llm)
        extracted_schema = await schema_extractor.run(text=text)
        
        # Save schema for later use
        self.schema = "EXTRACTED"
        
        # Optionally save to file
        extracted_schema.save("extracted_schema.json", overwrite=True)
        
        return extracted_schema
    
    async def build_from_pdf(
        self,
        file_path: Path,
        document_metadata: Optional[Dict[str, Any]] = None,
        perform_entity_resolution: bool = True,
        on_error: str = "IGNORE",
    ) -> Dict[str, Any]:
        """
        Build knowledge graph from PDF file.
        
        Args:
            file_path: Path to PDF file
            document_metadata: Metadata to attach to document node
            perform_entity_resolution: Whether to resolve duplicate entities
            on_error: Error handling strategy ("IGNORE" or "RAISE")
        
        Returns:
            Results dictionary with extraction statistics
        """
        # Create text splitter with custom settings
        text_splitter = FixedSizeSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap
        )
        
        # Initialize pipeline
        kg_builder = SimpleKGPipeline(
            llm=self.llm,
            driver=self.driver,
            embedder=self.embedder,
            from_pdf=True,
            text_splitter=text_splitter,
            schema=self.schema,
            perform_entity_resolution=perform_entity_resolution,
            neo4j_database=self.neo4j_database,
            on_error=on_error,
        )
        
        # Run pipeline
        result = await kg_builder.run_async(
            file_path=str(file_path),
            document_metadata=document_metadata or {}
        )
        
        return result
    
    async def build_from_text(
        self,
        text: str,
        document_metadata: Optional[Dict[str, Any]] = None,
        perform_entity_resolution: bool = True,
        on_error: str = "IGNORE",
    ) -> Dict[str, Any]:
        """
        Build knowledge graph from plain text.
        
        Args:
            text: Text content to process
            document_metadata: Metadata to attach to document node
            perform_entity_resolution: Whether to resolve duplicate entities
            on_error: Error handling strategy ("IGNORE" or "RAISE")
        
        Returns:
            Results dictionary with extraction statistics
        """
        # Create text splitter
        text_splitter = FixedSizeSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap
        )
        
        # Initialize pipeline
        kg_builder = SimpleKGPipeline(
            llm=self.llm,
            driver=self.driver,
            embedder=self.embedder,
            from_pdf=False,
            text_splitter=text_splitter,
            schema=self.schema,
            perform_entity_resolution=perform_entity_resolution,
            neo4j_database=self.neo4j_database,
            on_error=on_error,
        )
        
        # Run pipeline
        result = await kg_builder.run_async(
            text=text,
            document_metadata=document_metadata or {}
        )
        
        return result
    
    async def resolve_entities(
        self,
        resolver_type: str = "exact",
        filter_query: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Resolve duplicate entities in the knowledge graph.
        
        Args:
            resolver_type: Type of resolver ("exact", "semantic", "fuzzy")
            filter_query: Optional Cypher filter query
        
        Returns:
            Resolution results
        """
        if resolver_type == "exact":
            resolver = SinglePropertyExactMatchResolver(
                driver=self.driver,
                filter_query=filter_query
            )
        elif resolver_type == "semantic":
            resolver = SpaCySemanticMatchResolver(
                driver=self.driver,
                filter_query=filter_query
            )
        elif resolver_type == "fuzzy":
            resolver = FuzzyMatchResolver(
                driver=self.driver,
                filter_query=filter_query
            )
        else:
            raise ValueError(f"Unknown resolver type: {resolver_type}")
        
        result = await resolver.run()
        return result
    
    def close(self):
        """Close the Neo4j driver."""
        self.driver.close()


class SchemaManager:
    """
    Helper class for managing knowledge graph schemas.
    """
    
    @staticmethod
    def create_custom_schema(
        node_definitions: List[Dict[str, Any]],
        relationship_definitions: List[Dict[str, Any]],
        patterns: List[tuple],
    ) -> Dict[str, Any]:
        """
        Create a custom schema with detailed definitions.
        
        Args:
            node_definitions: Node type definitions
            relationship_definitions: Relationship type definitions
            patterns: Connection patterns
        
        Returns:
            Schema dictionary
        
        Example:
            nodes = [
                {
                    "label": "Person",
                    "properties": [
                        {"name": "name", "type": "STRING", "required": True},
                        {"name": "birth_date", "type": "DATE"}
                    ]
                },
                {
                    "label": "Company",
                    "description": "Business organization",
                    "properties": [
                        {"name": "name", "type": "STRING", "required": True},
                        {"name": "founded", "type": "INTEGER"}
                    ]
                }
            ]
            relationships = [
                {
                    "label": "WORKS_FOR",
                    "properties": [
                        {"name": "since", "type": "DATE"}
                    ]
                }
            ]
            patterns = [("Person", "WORKS_FOR", "Company")]
        """
        return {
            "node_types": node_definitions,
            "relationship_types": relationship_definitions,
            "patterns": patterns,
            "additional_node_types": False,  # Strict schema enforcement
            "additional_relationship_types": False,
            "additional_patterns": True,
        }
    
    @staticmethod
    async def extract_and_save_schema(
        llm: LLMInterface,
        sample_text: str,
        output_file: str = "schema.json"
    ) -> Any:
        """
        Extract schema from text and save to file.
        
        Args:
            llm: LLM interface
            sample_text: Text to analyze
            output_file: Output file path
        
        Returns:
            Extracted schema object
        """
        extractor = SchemaFromTextExtractor(llm=llm)
        schema = await extractor.run(text=sample_text)
        schema.save(output_file)
        return schema
    
    @staticmethod
    def load_schema_from_file(file_path: str) -> Any:
        """
        Load schema from JSON or YAML file.
        
        Args:
            file_path: Path to schema file
        
        Returns:
            Schema object
        """
        from neo4j_graphrag.experimental.components.schema import GraphSchema
        return GraphSchema.from_file(file_path)


# Example schema definitions for common use cases
EXAMPLE_SCHEMAS = {
    "academic": {
        "node_types": [
            {
                "label": "Person",
                "properties": [
                    {"name": "name", "type": "STRING", "required": True},
                    {"name": "email", "type": "STRING"}
                ]
            },
            {
                "label": "Publication",
                "properties": [
                    {"name": "title", "type": "STRING", "required": True},
                    {"name": "year", "type": "INTEGER"}
                ]
            },
            {"label": "Institution"},
            {"label": "ResearchField"}
        ],
        "relationship_types": [
            "AUTHORED",
            "AFFILIATED_WITH",
            "CITED_BY",
            "RELATED_TO"
        ],
        "patterns": [
            ("Person", "AUTHORED", "Publication"),
            ("Person", "AFFILIATED_WITH", "Institution"),
            ("Publication", "CITED_BY", "Publication"),
            ("Publication", "RELATED_TO", "ResearchField")
        ]
    },
    "business": {
        "node_types": [
            {"label": "Company"},
            {"label": "Person"},
            {"label": "Product"},
            {"label": "Location"}
        ],
        "relationship_types": [
            "WORKS_FOR",
            "CEO_OF",
            "PRODUCES",
            "LOCATED_IN",
            "PARTNERS_WITH"
        ],
        "patterns": [
            ("Person", "WORKS_FOR", "Company"),
            ("Person", "CEO_OF", "Company"),
            ("Company", "PRODUCES", "Product"),
            ("Company", "LOCATED_IN", "Location"),
            ("Company", "PARTNERS_WITH", "Company")
        ]
    }
}
