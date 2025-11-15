"""
Setup verification and quick start script.
Run this first to verify your environment is properly configured.
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from config import Config
from utils import SetupHelper, DatabaseUtils


def check_environment():
    """Check if environment is properly configured."""
    
    print("=" * 80)
    print("Neo4j GraphRAG - Environment Check")
    print("=" * 80)
    
    issues = []
    
    # Check Neo4j configuration
    print("\n1. Checking Neo4j Configuration...")
    print(f"   URI: {Config.NEO4J_URI}")
    print(f"   Username: {Config.NEO4J_USERNAME}")
    print(f"   Database: {Config.NEO4J_DATABASE}")
    
    # Test Neo4j connection
    print("\n2. Testing Neo4j Connection...")
    connection_successful = SetupHelper.verify_connection(
        uri=Config.NEO4J_URI,
        username=Config.NEO4J_USERNAME,
        password=Config.NEO4J_PASSWORD
    )
    
    if connection_successful:
        print("   ✓ Neo4j connection successful!")
        
        # Check APOC installation
        print("\n   Checking APOC plugin...")
        driver = Config.get_neo4j_driver()
        apoc_installed = SetupHelper.check_apoc_installed(driver)
        driver.close()
        
        if not apoc_installed:
            issues.append("APOC plugin not installed")
            print("\n   ⚠️  APOC plugin is REQUIRED for GraphRAG")
            print("\n   Install APOC:")
            print("   - Neo4j Desktop: Go to your database → Plugins → Install APOC")
            print("   - Neo4j Aura: APOC is pre-installed (restart if just created)")
            print("   - Docker: Use neo4j:latest or add NEO4J_PLUGINS=[\"apoc\"]")
            print("   - Manual: Download from https://neo4j.com/labs/apoc/")
            print("\n   After installing APOC, restart Neo4j and run this check again.")
    else:
        issues.append("Neo4j connection failed")
        print("   ✗ Neo4j connection failed")
        print("\n   Troubleshooting:")
        print("   - Make sure Neo4j is running")
        print("   - Check your .env file for correct credentials")
        print("   - Verify NEO4J_URI, NEO4J_USERNAME, and NEO4J_PASSWORD")
        print("\n   Example Docker command to run Neo4j with APOC:")
        print("docker run --name neo4j-container-1 \\ ")
        print("  -p 7474:7474 \\ ")
        print("  -p 7687:7687 \\ ")
        print("  -v $HOME/neo4j/container-1/data:/data \\ ")
        print("  -e NEO4J_AUTH=neo4j/password \\ ")
        print("  -e NEO4J_apoc_export_file_enabled=true \\ ")
        print("  -e NEO4J_apoc_import_file_enabled=true \\ ")
        print("  -e NEO4J_apoc_import_file_use__neo4j__config=true \\ ")
        print("  -e NEO4J_PLUGINS=\\[\\\"apoc\\\"\\] \\ ")
        print("  neo4j ")
    
    # Check LLM API Keys
    print("\n3. Checking LLM Configuration...")
    print(f"   Selected Provider: {Config.LLM_PROVIDER}")
    
    provider = Config.LLM_PROVIDER.lower()
    provider_configured = False
    
    if provider == "openai":
        if Config.OPENAI_API_KEY:
            print("   ✓ OpenAI API key configured")
            provider_configured = True
        else:
            print("   ✗ OpenAI API key missing")
    elif provider == "anthropic":
        if Config.ANTHROPIC_API_KEY:
            print("   ✓ Anthropic API key configured")
            provider_configured = True
        else:
            print("   ✗ Anthropic API key missing")
    elif provider == "cohere":
        if Config.CO_API_KEY:
            print("   ✓ Cohere API key configured")
            provider_configured = True
        else:
            print("   ✗ Cohere API key missing")
    elif provider == "mistral":
        if Config.MISTRAL_API_KEY:
            print("   ✓ MistralAI API key configured")
            provider_configured = True
        else:
            print("   ✗ MistralAI API key missing")
    elif provider == "azure_openai":
        if Config.AZURE_OPENAI_API_KEY and Config.AZURE_OPENAI_ENDPOINT:
            print("   ✓ Azure OpenAI configured")
            provider_configured = True
        else:
            print("   ✗ Azure OpenAI API key or endpoint missing")
    elif provider == "vertexai":
        if Config.GOOGLE_APPLICATION_CREDENTIALS and Config.GOOGLE_CLOUD_PROJECT:
            print("   ✓ VertexAI configured")
            provider_configured = True
        else:
            print("   ✗ VertexAI credentials or project missing")
    elif provider == "ollama":
        print("   ✓ Ollama selected (no API key needed)")
        provider_configured = True
    else:
        print(f"   ✗ Unknown provider: {provider}")
    
    if not provider_configured:
        issues.append(f"LLM provider '{Config.LLM_PROVIDER}' not properly configured")
        print(f"\n   To configure {Config.LLM_PROVIDER}:")
        if provider == "openai":
            print("   - Set OPENAI_API_KEY in your .env file")
        elif provider == "anthropic":
            print("   - Set ANTHROPIC_API_KEY in your .env file")
        elif provider == "cohere":
            print("   - Set CO_API_KEY in your .env file")
        elif provider == "mistral":
            print("   - Set MISTRAL_API_KEY in your .env file")
        elif provider == "azure_openai":
            print("   - Set AZURE_OPENAI_API_KEY and AZURE_OPENAI_ENDPOINT in your .env file")
        elif provider == "vertexai":
            print("   - Set GOOGLE_APPLICATION_CREDENTIALS and GOOGLE_CLOUD_PROJECT in your .env file")
        elif provider == "ollama":
            print("   - Make sure Ollama is running locally")
    
    # Check other available providers
    other_providers = []
    if Config.OPENAI_API_KEY and provider != "openai":
        other_providers.append("OpenAI")
    if Config.ANTHROPIC_API_KEY and provider != "anthropic":
        other_providers.append("Anthropic")
    if Config.CO_API_KEY and provider != "cohere":
        other_providers.append("Cohere")
    if Config.MISTRAL_API_KEY and provider != "mistral":
        other_providers.append("MistralAI")
    if Config.AZURE_OPENAI_API_KEY and provider != "azure_openai":
        other_providers.append("Azure OpenAI")
    
    if other_providers:
        print(f"   ℹ️  Other available providers: {', '.join(other_providers)}")
        print("      You can change LLM_PROVIDER in your .env file to switch providers")
    
    # Check Ollama (optional)
    print("\n4. Checking Ollama (optional local LLM)...")
    print(f"   Host: {Config.OLLAMA_HOST}")
    print("   ℹ️  Ollama is optional for running local models")
    
    # Summary
    print("\n" + "=" * 80)
    if issues:
        print("❌ SETUP INCOMPLETE")
        print("=" * 80)
        print("\nIssues found:")
        for issue in issues:
            print(f"  - {issue}")
        print("\nPlease fix the issues above before running the examples.")
        print("\nQuick fix:")
        print("1. Copy .env.example to .env")
        print("2. Edit .env and add your credentials:")
        print("   - NEO4J_PASSWORD=your_neo4j_password")
        print("   - OPENAI_API_KEY=your_openai_key")
        print("3. Make sure Neo4j is running")
        return False
    else:
        print("✅ SETUP COMPLETE")
        print("=" * 80)
        print("\nYour environment is properly configured!")
        print("\nNext steps:")
        print("1. Run: python examples/example_kg_builder.py")
        print("2. Then: python examples/example_rag_query.py")
        print("3. View your graph at: http://localhost:7474")
        return True


def check_database_status():
    """Check database status if connection is successful."""
    try:
        driver = Config.get_neo4j_driver()
        
        print("\n5. Checking Database Status...")
        
        # Get database info
        summary = DatabaseUtils.get_schema_summary(driver)
        
        total_nodes = sum(summary["nodes_per_label"].values())
        total_rels = sum(summary["relationships_per_type"].values())
        
        if total_nodes == 0:
            print("   ℹ️  Database is empty (ready for new data)")
        else:
            print(f"   ℹ️  Database contains:")
            print(f"      - {total_nodes:,} nodes")
            print(f"      - {total_rels:,} relationships")
            print(f"      - {summary['label_count']} node labels")
            print(f"      - {summary['relationship_type_count']} relationship types")
        
        driver.close()
        
    except Exception as e:
        print(f"   ⚠️  Could not check database status: {e}")


if __name__ == "__main__":
    print("\nThis script will verify your setup for Neo4j GraphRAG.\n")
    
    success = check_environment()
    
    if success:
        check_database_status()
    
    print("\n" + "=" * 80)
