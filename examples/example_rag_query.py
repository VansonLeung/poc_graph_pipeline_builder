"""
Example: Querying the Knowledge Graph with GraphRAG
"""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import Config
from retrievers import GraphRetrieverManager, RETRIEVAL_QUERY_TEMPLATES, create_result_formatter
from graphrag import GraphRAGPipeline, CustomPromptTemplates, MultiRetrieverRAG
from utils import DatabaseUtils, IndexManager
from neo4j_graphrag.embeddings import OpenAIEmbeddings


def main():
    """
    Example workflow for querying a knowledge graph with GraphRAG.
    """
    
    print("=" * 80)
    print("Neo4j GraphRAG - Query Example")
    print("=" * 80)
    
    # Initialize Neo4j driver
    print("\n1. Connecting to Neo4j...")
    driver = Config.get_neo4j_driver()
    
    # Check if database has data
    print("\n2. Checking database status...")
    summary = DatabaseUtils.get_schema_summary(driver)
    total_nodes = sum(summary["nodes_per_label"].values())
    
    if total_nodes == 0:
        print("\n⚠️  WARNING: Your database is empty!")
        print("\nYou need to build a knowledge graph first:")
        print("  1. Run: uv run examples/example_kg_builder.py")
        print("  2. Then come back and run this query example")
        print("\nExiting...")
        driver.close()
        return
    
    print(f"   ✓ Found {total_nodes:,} nodes in database")
    
    # Check if indexes exist
    index_manager = IndexManager(driver)
    indexes = index_manager.list_indexes()
    index_names = [idx.get("name") for idx in indexes]
    
    if Config.VECTOR_INDEX_NAME not in index_names:
        print(f"\n⚠️  WARNING: Vector index '{Config.VECTOR_INDEX_NAME}' not found!")
        print("\nThe knowledge graph builder should have created this index.")
        print("Run: uv run examples/example_kg_builder.py")
        print("\nExiting...")
        driver.close()
        return
    
    print(f"   ✓ Vector index '{Config.VECTOR_INDEX_NAME}' exists")
    
    # Initialize LLM
    print("\n3. Initializing LLM...")
    llm = Config.get_llm()
    
    # Initialize Embedder
    print("4. Initializing Embedder...")
    embedder = OpenAIEmbeddings(model=Config.EMBEDDING_MODEL)
    
    # Create Retriever Manager
    print("5. Creating Retriever Manager...")
    retriever_manager = GraphRetrieverManager(
        driver=driver,
        embedder=embedder,
        vector_index_name=Config.VECTOR_INDEX_NAME,
        fulltext_index_name=Config.FULLTEXT_INDEX_NAME,
    )
    
    # Example 1: Basic Vector Retrieval
    print("\n" + "=" * 80)
    print("EXAMPLE 1: Basic Vector Retrieval")
    print("=" * 80)
    
    vector_retriever = retriever_manager.get_vector_retriever(
        return_properties=["text", "index"]
    )
    
    rag_pipeline = GraphRAGPipeline(
        retriever=vector_retriever,
        llm=llm,
    )
    
    question1 = "What is artificial intelligence?"
    print(f"\nQuestion: {question1}")
    print("-" * 80)
    
    response1 = rag_pipeline.query(
        question=question1,
        retriever_config={"top_k": 5},
        return_context=True,
    )
    
    print(f"\nAnswer:\n{response1.answer}")
    
    if response1.retriever_result:
        print(f"\nRetrieved {len(response1.retriever_result.items)} chunks")
    
    # Example 2: Vector Cypher Retrieval with Entity Context
    print("\n" + "=" * 80)
    print("EXAMPLE 2: Vector Cypher Retrieval with Entity Context")
    print("=" * 80)
    
    formatter = create_result_formatter(["text", "entities", "chunk_index"])
    
    vector_cypher_retriever = retriever_manager.get_vector_cypher_retriever(
        retrieval_query=RETRIEVAL_QUERY_TEMPLATES["entity_context"],
        result_formatter=formatter,
    )
    
    rag_pipeline2 = GraphRAGPipeline(
        retriever=vector_cypher_retriever,
        llm=llm,
    )
    
    question2 = "Who are the key people in AI research?"
    print(f"\nQuestion: {question2}")
    print("-" * 80)
    
    response2 = rag_pipeline2.query(
        question=question2,
        retriever_config={"top_k": 5},
        return_context=True,
    )
    
    print(f"\nAnswer:\n{response2.answer}")
    
    # Example 3: Hybrid Retrieval (Vector + Fulltext)
    print("\n" + "=" * 80)
    print("EXAMPLE 3: Hybrid Retrieval (Vector + Fulltext)")
    print("=" * 80)
    
    try:
        hybrid_retriever = retriever_manager.get_hybrid_retriever()
        
        rag_pipeline3 = GraphRAGPipeline(
            retriever=hybrid_retriever,
            llm=llm,
        )
        
        question3 = "machine learning applications in healthcare"
        print(f"\nQuestion: {question3}")
        print("-" * 80)
        
        response3 = rag_pipeline3.query(
            question=question3,
            retriever_config={"top_k": 5},
        )
        
        print(f"\nAnswer:\n{response3.answer}")
    except Exception as e:
        print(f"\n⚠️  Hybrid retrieval requires fulltext index: {e}")
        print("   Create fulltext index first using utils.create_fulltext_index()")
    
    # Example 4: Text2Cypher - Natural Language to Cypher
    print("\n" + "=" * 80)
    print("EXAMPLE 4: Text2Cypher - Natural Language to Cypher")
    print("=" * 80)
    
    # Define Neo4j schema for Text2Cypher
    neo4j_schema = """
    Node properties:
    Person {name: STRING}
    Organization {name: STRING}
    Technology {name: STRING, category: STRING}
    Location {name: STRING, country: STRING}
    
    Relationship properties:
    WORKS_FOR {since: DATE}
    FOUNDED {year: INTEGER}
    LOCATED_IN {}
    
    Relationships:
    (:Person)-[:WORKS_FOR]->(:Organization)
    (:Person)-[:FOUNDED]->(:Organization)
    (:Organization)-[:LOCATED_IN]->(:Location)
    (:Person)-[:INVENTED]->(:Technology)
    """
    
    examples = [
        "USER: 'Find all people' QUERY: MATCH (p:Person) RETURN p.name",
        "USER: 'Which companies are in California?' QUERY: MATCH (o:Organization)-[:LOCATED_IN]->(l:Location {name: 'California'}) RETURN o.name",
    ]
    
    text2cypher_retriever = retriever_manager.get_text2cypher_retriever(
        llm=llm,
        neo4j_schema=neo4j_schema,
        examples=examples,
    )
    
    rag_pipeline4 = GraphRAGPipeline(
        retriever=text2cypher_retriever,
        llm=llm,
    )
    
    question4 = "Who founded TechCorp?"
    print(f"\nQuestion: {question4}")
    print("-" * 80)
    
    try:
        response4 = rag_pipeline4.query(
            question=question4,
            # Text2Cypher doesn't use retriever_config like other retrievers
        )
        print(f"\nAnswer:\n{response4.answer}")
    except Exception as e:
        print(f"\n⚠️  Text2Cypher query failed: {e}")
        print("   This is expected if the knowledge graph doesn't contain relevant data")
    
    # Example 5: Custom Prompt Templates
    print("\n" + "=" * 80)
    print("EXAMPLE 5: Custom Prompt Templates")
    print("=" * 80)
    
    # Detailed template
    detailed_template = CustomPromptTemplates.get_detailed_template()
    rag_detailed = GraphRAGPipeline(
        retriever=vector_retriever,
        llm=llm,
        prompt_template=detailed_template,
    )
    
    question5 = "What are the main applications of machine learning?"
    print(f"\nQuestion: {question5}")
    print("Using: Detailed Template")
    print("-" * 80)
    
    response5 = rag_detailed.query(question=question5)
    print(f"\nAnswer:\n{response5.answer}")
    
    # Conversational template
    conversational_template = CustomPromptTemplates.get_conversational_template()
    rag_conversational = GraphRAGPipeline(
        retriever=vector_retriever,
        llm=llm,
        prompt_template=conversational_template,
    )
    
    print(f"\nSame question with Conversational Template:")
    print("-" * 80)
    response5b = rag_conversational.query(question=question5)
    print(f"\nAnswer:\n{response5b.answer}")
    
    # Example 6: Filtered Search
    print("\n" + "=" * 80)
    print("EXAMPLE 6: Filtered Search")
    print("=" * 80)
    
    # Search with filters
    filters = {
        "source": "business_example",  # Only search in business documents
    }
    
    question6 = "Tell me about technology companies"
    print(f"\nQuestion: {question6}")
    print(f"Filters: {filters}")
    print("-" * 80)
    
    response6 = rag_pipeline.query(
        question=question6,
        retriever_config={"top_k": 3, "filters": filters},
    )
    print(f"\nAnswer:\n{response6.answer}")
    
    # Example 7: Batch Queries
    print("\n" + "=" * 80)
    print("EXAMPLE 7: Batch Queries")
    print("=" * 80)
    
    questions = [
        "What is deep learning?",
        "Who invented the World Wide Web?",
        "What are neural networks used for?",
    ]
    
    print("\nProcessing multiple questions...")
    responses = rag_pipeline.batch_query(questions, retriever_config={"top_k": 3})
    
    for i, (q, r) in enumerate(zip(questions, responses), 1):
        print(f"\nQ{i}: {q}")
        print(f"A{i}: {r.answer[:200]}...")  # First 200 chars
    
    # Example 8: Query with Fallback
    print("\n" + "=" * 80)
    print("EXAMPLE 8: Query with Fallback Message")
    print("=" * 80)
    
    question8 = "What is quantum computing?"  # Might not be in the KG
    print(f"\nQuestion: {question8}")
    print("-" * 80)
    
    response8 = rag_pipeline.query(
        question=question8,
        retriever_config={"top_k": 3},
        response_fallback="I don't have information about that topic in the knowledge graph.",
    )
    print(f"\nAnswer:\n{response8.answer}")
    
    # Cleanup
    print("\n" + "=" * 80)
    print("Cleanup")
    print("=" * 80)
    driver.close()
    print("✓ Neo4j driver closed")
    
    print("\n" + "=" * 80)
    print("Query examples completed successfully!")
    print("=" * 80)
    print("\nKey Takeaways:")
    print("1. Different retrievers work better for different use cases")
    print("2. Vector retrieval: semantic similarity")
    print("3. Hybrid retrieval: combines semantic + keyword matching")
    print("4. Text2Cypher: precise queries using graph structure")
    print("5. Custom prompts: tailor responses to your needs")
    print("=" * 80)


if __name__ == "__main__":
    main()
