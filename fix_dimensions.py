"""
Fix embedding dimension mismatch by recreating the vector index.
Run this if you get a dimension mismatch error.
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from config import Config
from utils import IndexManager
from neo4j_graphrag.embeddings import OpenAIEmbeddings


def main():
    print("=" * 80)
    print("Fix Embedding Dimension Mismatch")
    print("=" * 80)
    
    # Connect
    driver = Config.get_neo4j_driver()
    index_manager = IndexManager(driver)
    
    # Get actual embedding dimensions from the model
    print("\n1. Testing embedding model...")
    print(f"   Model: {Config.EMBEDDING_MODEL}")
    print(f"   Base URL: {Config.EMBEDDING_BASE_URL or 'default'}")
    
    try:
        embedder = OpenAIEmbeddings(
            model=Config.EMBEDDING_MODEL,
            base_url=Config.EMBEDDING_BASE_URL,
        )
        test_embedding = embedder.embed_query("test")
        actual_dimensions = len(test_embedding)
        print(f"   ✓ Actual dimensions: {actual_dimensions}")
    except Exception as e:
        print(f"   ✗ Error: {e}")
        print("\nMake sure your embedding service is running!")
        driver.close()
        return
    
    # Check configured dimensions
    print(f"\n2. Configured dimensions in .env: {Config.VECTOR_DIMENSIONS}")
    
    if actual_dimensions == Config.VECTOR_DIMENSIONS:
        print("   ✓ Dimensions match!")
        driver.close()
        return
    
    print(f"\n⚠️  MISMATCH: Model produces {actual_dimensions} but index expects {Config.VECTOR_DIMENSIONS}")
    
    # Drop and recreate index
    print(f"\n3. Recreating vector index with correct dimensions...")
    print(f"   Dropping index '{Config.VECTOR_INDEX_NAME}'...")
    
    try:
        index_manager.drop_index(Config.VECTOR_INDEX_NAME)
        print("   ✓ Index dropped")
    except Exception as e:
        print(f"   Note: {e}")
    
    print(f"   Creating new index with {actual_dimensions} dimensions...")
    try:
        index_manager.create_vector_index(
            index_name=Config.VECTOR_INDEX_NAME,
            label="Chunk",
            embedding_property="embedding",
            dimensions=actual_dimensions,
            similarity_fn="cosine",
        )
        print("   ✓ Index recreated")
    except Exception as e:
        print(f"   ✗ Error: {e}")
        driver.close()
        return
    
    # Update .env reminder
    print("\n4. Update your .env file:")
    print(f"   Change: VECTOR_DIMENSIONS={Config.VECTOR_DIMENSIONS}")
    print(f"   To:     VECTOR_DIMENSIONS={actual_dimensions}")
    
    driver.close()
    
    print("\n" + "=" * 80)
    print("✅ Index recreated with correct dimensions!")
    print("=" * 80)
    print("\nIMPORTANT: The embeddings in existing Chunk nodes still have wrong dimensions.")
    print("You need to rebuild the knowledge graph to regenerate embeddings:")
    print("  uv run examples/example_kg_builder.py")
    print("\nOr update VECTOR_DIMENSIONS in .env and use a model with 1536 dimensions.")
    print("=" * 80)


if __name__ == "__main__":
    main()
