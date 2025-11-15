# Neo4j GraphRAG System - Complete Implementation

A comprehensive implementation of Neo4j's GraphRAG Python package for building knowledge graphs from unstructured data and performing advanced retrieval-augmented generation (RAG) queries.

## 🎯 Features

### Knowledge Graph Construction
- **Multiple data sources**: PDF documents, plain text, and custom formats
- **Automatic schema extraction**: LLM-powered schema discovery from sample data
- **Custom schema definition**: Define node types, relationships, and patterns
- **Entity extraction**: LLM-based entity and relationship extraction
- **Entity resolution**: Merge duplicate entities using exact, semantic, or fuzzy matching
- **Lexical graph**: Automatic creation of document and chunk nodes with relationships

### Advanced Retrieval Strategies
- **Vector Retrieval**: Semantic similarity search using embeddings
- **Vector Cypher Retrieval**: Combine vector search with custom Cypher queries
- **Hybrid Retrieval**: Combine vector and fulltext search
- **Text2Cypher**: Natural language to Cypher query generation
- **External Vector DBs**: Support for Weaviate, Pinecone, and Qdrant
- **Pre-filtering**: Filter results by node properties

### RAG Pipeline
- **Multiple LLM providers**: OpenAI, Anthropic, Google Vertex AI, Cohere, MistralAI, Ollama
- **Custom prompt templates**: Tailor responses for different use cases
- **Multi-retriever support**: Combine multiple retrieval strategies
- **Batch processing**: Process multiple queries efficiently
- **Context control**: Return retrieved context with answers
- **Feedback mechanism**: Track and improve query quality

## 📋 Prerequisites

- Python 3.9 or higher
- Neo4j 5.18.1+ (or Neo4j Aura 5.18.0+)
- At least one LLM API key (OpenAI, Anthropic, etc.) or local Ollama installation

## 🚀 Installation

### 1. Clone or Download Project

```bash
cd poc_graph_pipeline_builder
```

### 2. Create Virtual Environment

```bash
python -m venv venv
source venv/bin/activate  # On macOS/Linux
# or
venv\Scripts\activate  # On Windows
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

**Note**: The requirements file includes all optional dependencies. For a minimal installation:

```bash
pip install neo4j-graphrag[openai,experimental]
```

### 4. Configure Environment Variables

Copy the example environment file:

```bash
cp .env.example .env
```

Edit `.env` with your settings:

```bash
# Neo4j Configuration
NEO4J_URI=bolt://localhost:7687
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=your_password

# LLM Provider Selection
LLM_PROVIDER=openai  # Options: openai, anthropic, cohere, mistral, azure_openai, vertexai, ollama

# OpenAI Configuration
OPENAI_API_KEY=your_api_key
OPENAI_BASE_URL=  # Optional: leave empty for default, set for custom endpoints

# Other LLM providers (uncomment as needed)
# ANTHROPIC_API_KEY=your_anthropic_key
# CO_API_KEY=your_cohere_key
# MISTRAL_API_KEY=your_mistral_key
# AZURE_OPENAI_API_KEY=your_azure_key
# AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
# GOOGLE_APPLICATION_CREDENTIALS=path/to/credentials.json
# GOOGLE_CLOUD_PROJECT=your_project_id
```

### 5. Set Up Neo4j

#### Option A: Local Neo4j

1. [Download Neo4j Desktop](https://neo4j.com/download/)
2. Create a new database
3. **Install APOC plugin** (Plugins tab → Install APOC)
4. Start the database
5. Note the bolt URI and credentials

#### Option B: Neo4j Aura (Cloud)

1. Sign up at [Neo4j Aura](https://neo4j.com/cloud/aura/)
2. Create a free instance (APOC pre-installed)
3. Download credentials
4. Use the provided URI in your `.env` file

## 🌐 Web Console (Backend + Frontend)

The project now bundles a FastAPI backend and a Vite/React (shadcn-inspired) frontend for managing indexes, documents, and RAG searches.

### Backend API

```bash
uv run uvicorn backend.app.main:app --reload --port 8000
```

The API is CORS-enabled (all origins, no credentials) and exposes:

- `GET /api/health` – health check
- CRUD routes under `/api/indexes`
- Document management under `/api/indexes/{name}/documents`
- `POST /api/search` – vector + keyword RAG search

### Frontend Client

```bash
cd frontend
npm install
npm run dev
```

Configure the backend origin via `VITE_API_BASE_URL` (defaults to `http://localhost:8000/api`). The client keeps credentials in `localStorage`, per the project requirements.

## 📖 Usage

### Quick Start: Build a Knowledge Graph

```python
import asyncio
from pathlib import Path
from config import Config
from kg_builder import KnowledgeGraphBuilder
from neo4j_graphrag.embeddings import OpenAIEmbeddings

async def build_kg():
    # Initialize
    driver = Config.get_neo4j_driver()
    llm = Config.get_llm()
    embedder = OpenAIEmbeddings(model="text-embedding-3-large")
    
    # Create builder
    kg_builder = KnowledgeGraphBuilder(
        driver=driver,
        llm=llm,
        embedder=embedder
    )
    
    # Build from text
    text = """
    Marie Curie was a physicist and chemist who conducted pioneering 
    research on radioactivity. She was the first woman to win a Nobel 
    Prize and remains the only person to win Nobel Prizes in two 
    scientific fields.
    """
    
    result = await kg_builder.build_from_text(text=text)
    kg_builder.close()
    
    print("Knowledge graph created!")

asyncio.run(build_kg())
```

### Quick Start: Query the Knowledge Graph

```python
from config import Config
from retrievers import GraphRetrieverManager
from graphrag import GraphRAGPipeline
from neo4j_graphrag.embeddings import OpenAIEmbeddings

# Initialize
driver = Config.get_neo4j_driver()
llm = Config.get_llm()
embedder = OpenAIEmbeddings(model="text-embedding-3-large")

# Create retriever
retriever_manager = GraphRetrieverManager(
    driver=driver,
    embedder=embedder
)
vector_retriever = retriever_manager.get_vector_retriever()

# Create RAG pipeline
rag = GraphRAGPipeline(
    retriever=vector_retriever,
    llm=llm
)

# Query
response = rag.query(
    question="Who was Marie Curie?",
    retriever_config={"top_k": 5}
)

print(response.answer)
driver.close()
```

## 🔧 Complete Examples

### 1. Run Knowledge Graph Builder Example

```bash
# Use uv to run with correct environment
uv run examples/example_kg_builder.py

# OR activate the virtual environment first
source .venv/bin/activate  # On macOS/Linux
python examples/example_kg_builder.py
```

**Important:** Always use `uv run` or activate `.venv` (not `venv`) to ensure correct dependencies.

This example demonstrates:
- Automatic schema extraction
- Predefined schema usage
- PDF processing
- Entity resolution
- Custom schema definition

### 2. Run RAG Query Example

```bash
uv run examples/example_rag_query.py
```

This example demonstrates:
- Vector retrieval
- Vector Cypher retrieval
- Hybrid retrieval
- Text2Cypher
- Custom prompt templates
- Filtered search
- Batch queries

## 📚 Detailed Documentation

### Knowledge Graph Builder

#### Define Custom Schema

```python
schema = kg_builder.define_schema(
    node_types=[
        "Person",
        {
            "label": "Organization",
            "description": "A company or institution",
            "properties": [
                {"name": "name", "type": "STRING", "required": True},
                {"name": "founded", "type": "INTEGER"}
            ]
        }
    ],
    relationship_types=[
        "WORKS_FOR",
        {"label": "FOUNDED", "properties": [{"name": "year", "type": "INTEGER"}]}
    ],
    patterns=[
        ("Person", "WORKS_FOR", "Organization"),
        ("Person", "FOUNDED", "Organization")
    ]
)
```

#### Extract Schema from Text

```python
sample_text = "Your sample text here..."
schema = await kg_builder.extract_schema_from_text(sample_text)
# Schema is automatically saved to 'extracted_schema.json'
```

#### Build from PDF

```python
result = await kg_builder.build_from_pdf(
    file_path=Path("document.pdf"),
    document_metadata={"source": "research_paper", "year": 2024},
    perform_entity_resolution=True
)
```

#### Entity Resolution

```python
# Exact match (same name)
await kg_builder.resolve_entities(resolver_type="exact")

# Semantic match (similar meaning)
await kg_builder.resolve_entities(resolver_type="semantic")

# Fuzzy match (similar strings)
await kg_builder.resolve_entities(resolver_type="fuzzy")
```

### Retrieval Strategies

#### Vector Retrieval

```python
retriever = retriever_manager.get_vector_retriever(
    return_properties=["text", "title"]
)
results = retriever.search(query_text="What is AI?", top_k=5)
```

#### Vector Cypher Retrieval

```python
retrieval_query = """
OPTIONAL MATCH (node)-[:HAS_ENTITY]->(entity)
RETURN node.text as text,
       collect(entity.name) as entities,
       score
"""

retriever = retriever_manager.get_vector_cypher_retriever(
    retrieval_query=retrieval_query
)
```

#### Hybrid Retrieval

```python
# Requires fulltext index
retriever = retriever_manager.get_hybrid_retriever()
results = retriever.search(query_text="machine learning", top_k=5)
```

#### Text2Cypher

```python
schema = """
Node properties:
Person {name: STRING}
Company {name: STRING}

Relationships:
(:Person)-[:WORKS_FOR]->(:Company)
"""

retriever = retriever_manager.get_text2cypher_retriever(
    llm=llm,
    neo4j_schema=schema
)
results = retriever.search(query_text="Who works for Google?")
```

#### Filtered Search

```python
filters = {
    "year": {"$gte": 2020},
    "category": {"$in": ["AI", "ML"]}
}

results = retriever_manager.search_with_filters(
    query_text="recent research",
    filters=filters,
    top_k=5
)
```

### Custom Prompt Templates

```python
from graphrag import CustomPromptTemplates

# Detailed responses
detailed_template = CustomPromptTemplates.get_detailed_template()

# Conversational responses
conversational_template = CustomPromptTemplates.get_conversational_template()

# Academic responses
academic_template = CustomPromptTemplates.get_academic_template()

# Structured responses
structured_template = CustomPromptTemplates.get_structured_template()

# Custom template
custom_template = CustomPromptTemplates.get_custom_template(
    template="""
    Context: {context}
    Question: {question}
    
    Provide a concise answer:
    """,
    expected_inputs=["context", "question"]
)

# Use with RAG
rag = GraphRAGPipeline(
    retriever=retriever,
    llm=llm,
    prompt_template=custom_template
)
```

### Utility Functions

#### Set Up Indexes

```python
from utils import SetupHelper

SetupHelper.setup_indexes(
    driver=driver,
    vector_index_name="document_embeddings",
    fulltext_index_name="document_fulltext",
    chunk_label="Chunk",
    dimensions=1536
)
```

#### Database Statistics

```python
from utils import DatabaseUtils

# Print schema summary
DatabaseUtils.print_schema_summary(driver)

# Get counts
node_count = DatabaseUtils.get_node_count(driver, label="Person")
rel_count = DatabaseUtils.get_relationship_count(driver, rel_type="WORKS_FOR")

# Get all labels and types
labels = DatabaseUtils.get_labels(driver)
rel_types = DatabaseUtils.get_relationship_types(driver)
```

## 🏗️ Project Structure

```
poc_graph_pipeline_builder/
├── config.py                    # Configuration and environment variables
├── kg_builder.py                # Knowledge graph construction
├── retrievers.py                # Retrieval strategies
├── graphrag.py                  # RAG pipeline
├── utils.py                     # Utility functions
├── requirements.txt             # Dependencies
├── .env.example                 # Example environment variables
├── .env                         # Your environment variables (create this)
├── .gitignore                   # Git ignore file
├── README.md                    # This file
└── examples/
    ├── example_kg_builder.py    # KG building examples
    └── example_rag_query.py     # Query examples
```

## 🔑 Supported LLM Providers

The system supports multiple LLM providers. Configure your preferred provider in the `.env` file:

```bash
# Choose your provider
LLM_PROVIDER=openai  # or: anthropic, cohere, mistral, azure_openai, vertexai, ollama

# Provider-specific settings
OPENAI_API_KEY=your_key
# or
ANTHROPIC_API_KEY=your_key
# etc.
```

Then use the configured LLM in your code:

```python
from config import Config

# Automatically uses the configured provider
llm = Config.get_llm()
```

### Manual Provider Configuration

If you need to manually configure providers:

#### OpenAI

```python
from neo4j_graphrag.llm import OpenAILLM
llm = OpenAILLM(
    model_name="gpt-4o",
    api_key="your-api-key",
    base_url="https://custom-endpoint.com"  # Optional custom base URL
)
```

#### Anthropic

```python
from neo4j_graphrag.llm import AnthropicLLM
llm = AnthropicLLM(
    model_name="claude-3-opus-20240229",
    api_key="your-api-key",
    model_params={"max_tokens": 1000}
)
```

#### Google Vertex AI

```python
from neo4j_graphrag.llm import VertexAILLM
llm = VertexAILLM(model_name="gemini-2.5-flash")
```

### Cohere

```python
from neo4j_graphrag.llm import CohereLLM
llm = CohereLLM(model_name="command-r")
```

### MistralAI

```python
from neo4j_graphrag.llm import MistralAILLM
llm = MistralAILLM(model_name="mistral-small-latest")
```

### Ollama (Local)

```python
from neo4j_graphrag.llm import OllamaLLM
llm = OllamaLLM(model_name="llama3:8b")
```

## 📊 Embeddings

### OpenAI

```python
from neo4j_graphrag.embeddings import OpenAIEmbeddings
embedder = OpenAIEmbeddings(model="text-embedding-3-large")
```

### Sentence Transformers

```python
from neo4j_graphrag.embeddings import SentenceTransformerEmbeddings
embedder = SentenceTransformerEmbeddings(model="all-MiniLM-L6-v2")
```

### Vertex AI

```python
from neo4j_graphrag.embeddings import VertexAIEmbeddings
embedder = VertexAIEmbeddings()
```

## 🐛 Troubleshooting

### Wrong Python Environment / Module Not Found

**Problem:** Getting "No module named X" errors or wrong Python version

**Solution:** Make sure you're using the correct virtual environment:

```bash
# Always use uv run for commands
uv run examples/example_kg_builder.py

# OR activate the correct venv first
source .venv/bin/activate  # NOT venv/bin/activate

# Check which Python you're using
which python3  # Should point to .venv/bin/python3
```

If `python3` points to the wrong location, deactivate all environments and use `uv run`.

### APOC Not Installed

**Problem:** Error about `apoc.create.addLabels` not found

**Solution:** Install APOC plugin:
- **Neo4j Desktop:** Database → Plugins → Install APOC
- **Neo4j Aura:** Pre-installed (restart instance if needed)
- **Docker:** Add `-e NEO4J_PLUGINS='["apoc"]'` to docker run

Run `uv run setup_check.py` to verify APOC is installed.

### Connection Issues

```python
from utils import SetupHelper

# Verify connection
SetupHelper.verify_connection(
    uri="bolt://localhost:7687",
    username="neo4j",
    password="password"
)
```

### Import Errors

If you see import errors for optional dependencies:

```bash
# For OpenAI
pip install "neo4j-graphrag[openai]"

# For all LLM providers
pip install "neo4j-graphrag[openai,anthropic,google,cohere,mistralai]"

# For NLP features
pip install "neo4j-graphrag[nlp,fuzzy-matching]"
```

### No Results from Queries

1. Ensure indexes are created:
```python
from utils import IndexManager
manager = IndexManager(driver)
indexes = manager.list_indexes()
print(indexes)
```

2. Check if data exists:
```python
from utils import DatabaseUtils
DatabaseUtils.print_schema_summary(driver)
```

## 📖 Additional Resources

- [Neo4j GraphRAG Python Documentation](https://neo4j.com/docs/neo4j-graphrag-python/current/)
- [Neo4j Documentation](https://neo4j.com/docs/)
- [Neo4j GraphAcademy](https://graphacademy.neo4j.com/)
- [Neo4j Community Forum](https://community.neo4j.com/)

## 🤝 Contributing

This is a proof-of-concept implementation. Feel free to extend and customize for your needs.

## 📄 License

This project uses the Neo4j GraphRAG Python package which is maintained by Neo4j.

## ⚠️ Notes

- Vector indexes use approximate nearest neighbor search (may not be exact)
- LLM-generated Cypher queries may fail if schema doesn't match
- Entity resolution can be time-consuming for large graphs
- Rate limiting is enabled by default for LLM and embedding calls

## 🎓 Learning Path

1. **Start with examples**: Run `example_kg_builder.py` and `example_rag_query.py`
2. **Experiment with schemas**: Try different node types and relationships
3. **Test retrieval strategies**: Compare vector, hybrid, and Text2Cypher
4. **Customize prompts**: Create templates for your use case
5. **Optimize performance**: Tune chunk sizes, top_k values, and filters

## 🚀 Next Steps

After building your first knowledge graph:

1. Visualize in Neo4j Browser: `http://localhost:7474`
2. Explore the graph: `MATCH (n) RETURN n LIMIT 50`
3. Query entities: `MATCH (e:__Entity__) RETURN e.name, labels(e)`
4. Check relationships: `MATCH ()-[r]->() RETURN type(r), count(r)`
5. Test RAG queries with your own questions

---

**Happy Graph Building! 🎉**
