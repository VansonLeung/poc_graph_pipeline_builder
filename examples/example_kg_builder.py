"""
Example: Building a Knowledge Graph from documents
"""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import Config
from kg_builder import KnowledgeGraphBuilder, EXAMPLE_SCHEMAS
from neo4j_graphrag.embeddings import OpenAIEmbeddings


async def main():
    """
    Example workflow for building a knowledge graph.
    """
    
    print("=" * 80)
    print("Neo4j GraphRAG - Knowledge Graph Builder Example")
    print("=" * 80)
    
    # Initialize Neo4j driver
    print("\n1. Connecting to Neo4j...")
    driver = Config.get_neo4j_driver()
    
    # Initialize LLM
    print("2. Initializing LLM...")
    llm = Config.get_llm()
    
    # Initialize Embedder
    print("3. Initializing Embedder...")
    embedder = OpenAIEmbeddings(
      model=Config.EMBEDDING_MODEL,
      base_url=Config.EMBEDDING_BASE_URL,
    )
    
    # Create Knowledge Graph Builder
    print("4. Creating Knowledge Graph Builder...")
    kg_builder = KnowledgeGraphBuilder(
        driver=driver,
        llm=llm,
        embedder=embedder,
        neo4j_database=Config.NEO4J_DATABASE,
        chunk_size=4000,
        chunk_overlap=200,
    )
    
    # Example 1: Build from text with automatic schema extraction
    print("\n" + "=" * 80)
    print("EXAMPLE 1: Build KG from text with automatic schema extraction")
    print("=" * 80)
    
    sample_text = """
    Dr. Jane Smith is a renowned researcher at Stanford University, specializing in 
    artificial intelligence and machine learning. She completed her Ph.D. at MIT in 
    2010 and has published over 50 papers in top-tier conferences. Her recent work 
    on neural networks has been cited extensively by the research community.
    
    In 2022, Dr. Smith founded AI Innovations Inc., a startup focused on applying 
    deep learning to healthcare diagnostics. The company is based in Palo Alto, 
    California, and has raised $10 million in Series A funding.
    
    Dr. Smith collaborates closely with Professor John Doe from Berkeley, who works 
    on computer vision and robotics. Together, they received the Best Paper Award 
    at NeurIPS 2023 for their groundbreaking work on transformer architectures.
    """
    
    print("\nExtracting schema from sample text...")
    schema = await kg_builder.extract_schema_from_text(sample_text)
    print(f"✓ Schema extracted and saved to 'extracted_schema.json'")
    
    print("\nBuilding knowledge graph from text...")
    result1 = await kg_builder.build_from_text(
        text=sample_text,
        document_metadata={
            "source": "example_text",
            "created_at": "2024-01-15",
        },
        perform_entity_resolution=True,
    )
    print(f"✓ Knowledge graph built successfully!")
    
    # Example 2: Build from text with predefined schema
    print("\n" + "=" * 80)
    print("EXAMPLE 2: Build KG with predefined business schema")
    print("=" * 80)
    
    # Use predefined business schema
    kg_builder.define_schema(
        node_types=EXAMPLE_SCHEMAS["business"]["node_types"],
        relationship_types=EXAMPLE_SCHEMAS["business"]["relationship_types"],
        patterns=EXAMPLE_SCHEMAS["business"]["patterns"],
    )
    
    business_text = """
    TechCorp is a global technology company headquartered in San Francisco, California.
    The company was founded in 2000 by Sarah Johnson, who currently serves as CEO.
    TechCorp develops software products for enterprise customers and has offices in 
    New York, London, and Tokyo.
    
    In 2023, TechCorp launched CloudPlatform, a cloud computing service that competes 
    with AWS and Azure. The product has gained significant market share in the healthcare 
    and finance sectors.
    
    Michael Chen serves as CTO and leads the engineering team of over 500 developers.
    He joined TechCorp in 2015 after working at Google for 10 years. Under his leadership,
    the company has filed 50+ patents in cloud computing and artificial intelligence.
    
    TechCorp has a strategic partnership with DataSystems Inc., a data analytics company
    based in Boston. Together, they provide integrated solutions to Fortune 500 companies.
    """
    
    print("\nBuilding knowledge graph with business schema...")
    result2 = await kg_builder.build_from_text(
        text=business_text,
        document_metadata={
            "source": "business_example",
            "topic": "technology companies",
        },
        perform_entity_resolution=True,
    )
    print(f"✓ Knowledge graph built successfully!")
    
    # Example 3: Build from PDF (if you have a PDF file)
    print("\n" + "=" * 80)
    print("EXAMPLE 3: Build KG from PDF file (optional)")
    print("=" * 80)
    
    pdf_path = Path("sample_document.pdf")
    if pdf_path.exists():
        print(f"\nProcessing PDF: {pdf_path}")
        
        # Use academic schema for research papers
        kg_builder.define_schema(
            node_types=EXAMPLE_SCHEMAS["academic"]["node_types"],
            relationship_types=EXAMPLE_SCHEMAS["academic"]["relationship_types"],
            patterns=EXAMPLE_SCHEMAS["academic"]["patterns"],
        )
        
        result3 = await kg_builder.build_from_pdf(
            file_path=pdf_path,
            document_metadata={
                "source": "sample_document.pdf",
                "document_type": "research_paper",
            },
            perform_entity_resolution=True,
        )
        print(f"✓ Knowledge graph from PDF built successfully!")
    else:
        print(f"\nℹ️  No PDF file found at {pdf_path}")
        print("   Place a PDF file named 'sample_document.pdf' in the project directory to test PDF processing")
    
    # Example 4: Entity Resolution
    print("\n" + "=" * 80)
    print("EXAMPLE 4: Entity Resolution")
    print("=" * 80)
    
    print("\nResolving duplicate entities...")
    
    # Try different resolution strategies
    print("\n  - Exact match resolution...")
    exact_result = await kg_builder.resolve_entities(resolver_type="exact")
    print("  ✓ Exact match resolution completed")
    
    print("\n  - Semantic match resolution (using spaCy)...")
    try:
        semantic_result = await kg_builder.resolve_entities(resolver_type="semantic")
        print("  ✓ Semantic match resolution completed")
    except Exception as e:
        print(f"  ⚠️  Semantic resolution requires spaCy: {e}")
    
    print("\n  - Fuzzy match resolution...")
    try:
        fuzzy_result = await kg_builder.resolve_entities(resolver_type="fuzzy")
        print("  ✓ Fuzzy match resolution completed")
    except Exception as e:
        print(f"  ⚠️  Fuzzy resolution requires rapidfuzz: {e}")
    
    # Example 5: Custom Schema Definition
    print("\n" + "=" * 80)
    print("EXAMPLE 5: Custom Schema Definition")
    print("=" * 80)
    
    custom_schema = kg_builder.define_schema(
        node_types=[
            "Person",
            {
                "label": "Technology",
                "description": "A technological innovation or tool",
                "properties": [
                    {"name": "name", "type": "STRING", "required": True},
                    {"name": "category", "type": "STRING"},
                    {"name": "year_introduced", "type": "INTEGER"},
                ]
            },
            {"label": "Application", "description": "Real-world application of technology"},
        ],
        relationship_types=[
            "INVENTED",
            "USED_IN",
            {"label": "EVOLVED_FROM", "description": "Technological evolution"},
        ],
        patterns=[
            ("Person", "INVENTED", "Technology"),
            ("Technology", "USED_IN", "Application"),
            ("Technology", "EVOLVED_FROM", "Technology"),
        ]
    )
    
    print("\n✓ Custom schema defined:")
    print(f"   - Node types: {len(custom_schema['node_types'])}")
    print(f"   - Relationship types: {len(custom_schema['relationship_types'])}")
    print(f"   - Patterns: {len(custom_schema['patterns'])}")
    
    tech_text = """
    Tim Berners-Lee invented the World Wide Web in 1989 while working at CERN.
    The web is used in countless applications including e-commerce, social media,
    and online education. The modern web evolved from earlier hypertext systems
    like Memex and Xanadu.
    
    Machine learning, pioneered by researchers like Geoffrey Hinton and Yann LeCun,
    is used in applications such as image recognition, natural language processing,
    and autonomous vehicles. Modern deep learning evolved from earlier neural network
    research in the 1980s.
    """
    
    print("\nBuilding knowledge graph with custom schema...")
    result4 = await kg_builder.build_from_text(
        text=tech_text,
        document_metadata={"source": "technology_history"},
        perform_entity_resolution=True,
    )
    print("✓ Knowledge graph with custom schema built successfully!")
    
    # Cleanup
    print("\n" + "=" * 80)
    print("Cleanup")
    print("=" * 80)
    kg_builder.close()
    driver.close()  # Close the driver we created at the start
    print("✓ Neo4j driver closed")
    
    print("\n" + "=" * 80)
    print("Examples completed successfully!")
    print("=" * 80)
    print("\nNext steps:")
    print("1. Open Neo4j Browser at http://localhost:7474")
    print("2. Run: MATCH (n) RETURN n LIMIT 50 to view your knowledge graph")
    print("3. Run example_rag_query.py to query the knowledge graph")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(main())
