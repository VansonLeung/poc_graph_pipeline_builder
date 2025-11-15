"""
Script to manually create required indexes for Neo4j GraphRAG.
Run this if indexes are missing after building the knowledge graph.
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from config import Config
from utils import IndexManager, DatabaseUtils


def main():
    print("=" * 80)
    print("Neo4j GraphRAG - Index Creation")
    print("=" * 80)
    
    # Connect to Neo4j
    print("\n1. Connecting to Neo4j...")
    driver = Config.get_neo4j_driver()
    
    # Check database status
    print("\n2. Checking database status...")
    summary = DatabaseUtils.get_schema_summary(driver)
    total_nodes = sum(summary["nodes_per_label"].values())
    
    if total_nodes == 0:
        print("\n⚠️  Database is empty!")
        print("Run: uv run examples/example_kg_builder.py first")
        driver.close()
        return
    
    print(f"   ✓ Found {total_nodes:,} nodes in database")
    print(f"   Labels: {', '.join(summary['labels'])}")
    
    # Check for Chunk nodes
    chunk_count = summary["nodes_per_label"].get("Chunk", 0)
    if chunk_count == 0:
        print("\n⚠️  No 'Chunk' nodes found!")
        print("The knowledge graph builder creates 'Chunk' nodes with embeddings.")
        print("Your data might use different node labels.")
        print("\nAvailable node labels:")
        for label, count in summary["nodes_per_label"].items():
            print(f"  - {label}: {count:,} nodes")
        driver.close()
        return
    
    print(f"\n   ✓ Found {chunk_count:,} Chunk nodes")
    
    # Check existing indexes
    print("\n3. Checking existing indexes...")
    index_manager = IndexManager(driver)
    existing_indexes = index_manager.list_indexes()
    index_names = [idx.get("name") for idx in existing_indexes]
    
    print(f"   Existing indexes: {len(index_names)}")
    for idx_name in index_names:
        print(f"     - {idx_name}")
    
    # Create vector index if missing
    print("\n4. Creating vector index...")
    if Config.VECTOR_INDEX_NAME in index_names:
        print(f"   ℹ️  Vector index '{Config.VECTOR_INDEX_NAME}' already exists")
    else:
        try:
            index_manager.create_vector_index(
                index_name=Config.VECTOR_INDEX_NAME,
                label="Chunk",
                embedding_property="embedding",
                dimensions=Config.VECTOR_DIMENSIONS,
                similarity_fn="cosine",
            )
            print(f"   ✓ Created vector index '{Config.VECTOR_INDEX_NAME}'")
        except Exception as e:
            print(f"   ✗ Error creating vector index: {e}")
            print("\n   Common issues:")
            print("   - Chunk nodes don't have 'embedding' property yet")
            print("   - Run the knowledge graph builder to add embeddings")
    
    # Create fulltext index if missing
    print("\n5. Creating fulltext index...")
    if Config.FULLTEXT_INDEX_NAME in index_names:
        print(f"   ℹ️  Fulltext index '{Config.FULLTEXT_INDEX_NAME}' already exists")
    else:
        try:
            index_manager.create_fulltext_index(
                index_name=Config.FULLTEXT_INDEX_NAME,
                label="Chunk",
                text_properties=["text"],  # Note: parameter name in utils.py
            )
            print(f"   ✓ Created fulltext index '{Config.FULLTEXT_INDEX_NAME}'")
        except Exception as e:
            print(f"   ✗ Error creating fulltext index: {e}")
    
    # Verify index creation
    print("\n6. Verifying indexes...")
    updated_indexes = index_manager.list_indexes()
    updated_names = [idx.get("name") for idx in updated_indexes]
    
    vector_ok = Config.VECTOR_INDEX_NAME in updated_names
    fulltext_ok = Config.FULLTEXT_INDEX_NAME in updated_names
    
    print(f"   Vector index: {'✓' if vector_ok else '✗'}")
    print(f"   Fulltext index: {'✓' if fulltext_ok else '✗'}")
    
    # Close driver
    driver.close()
    
    print("\n" + "=" * 80)
    if vector_ok and fulltext_ok:
        print("✅ SUCCESS - All indexes created!")
        print("=" * 80)
        print("\nYou can now run:")
        print("  uv run examples/example_rag_query.py")
    else:
        print("⚠️  INCOMPLETE - Some indexes could not be created")
        print("=" * 80)
        print("\nTroubleshooting:")
        print("1. Make sure Chunk nodes have 'embedding' and 'text' properties")
        print("2. Re-run the knowledge graph builder:")
        print("   uv run examples/example_kg_builder.py")
        print("3. Check Neo4j logs for detailed error messages")
    print("=" * 80)


if __name__ == "__main__":
    main()
