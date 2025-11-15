# Fixes Applied to Neo4j GraphRAG Project

## Summary
This document details all fixes applied to make the Neo4j GraphRAG system work with local LLM models (qwen3-embed embeddings and Qwen3-4B-Instruct LLM).

## Date
2025-01-XX

---

## Issues Fixed

### 1. ✅ Custom Prompt Template Variable Names
**Problem**: Custom prompt templates used `{question}` placeholder but RagTemplate expects `{query_text}`
- **Error**: `KeyError: 'question'` when using custom templates
- **Files Modified**: `graphrag.py`
- **Fix**: Updated all 4 template methods in `CustomPromptTemplates` class:
  - `get_detailed_template()`
  - `get_conversational_template()`
  - `get_academic_template()`
  - `get_structured_template()`
- **Changes**: 
  - Changed `{question}` → `{query_text}` in template strings
  - Updated `expected_inputs` to `["context", "query_text"]`

### 2. ✅ Text2Cypher Retriever Parameters
**Problem**: Text2Cypher retriever doesn't accept `top_k` in `retriever_config`
- **Error**: `Text2CypherRetriever.get_search_results() got an unexpected keyword argument 'top_k'`
- **Files Modified**: 
  - `graphrag.py` - Added error handling with automatic retry
  - `examples/example_rag_query.py` - Removed retriever_config from Text2Cypher example
- **Fix**: 
  - Added try/catch in `GraphRAGPipeline.query()` and `query_async()` methods
  - Automatically retries with empty `retriever_config={}` if TypeError occurs
  - Graceful fallback for retrievers with different parameter requirements

### 3. ✅ RagResultModel Import Location
**Problem**: Import path was incorrect for RagResultModel
- **Error**: `ImportError: cannot import name 'RagResultModel' from 'neo4j_graphrag.types'`
- **Files Modified**: `graphrag.py`
- **Fix**: Changed import from `neo4j_graphrag.types` to `neo4j_graphrag.generation.types`

### 4. ✅ VectorCypherRetriever Invalid Parameter
**Problem**: VectorCypherRetriever doesn't accept `return_properties` parameter
- **Error**: `TypeError: VectorCypherRetriever.__init__() got an unexpected keyword argument 'return_properties'`
- **Files Modified**: `retrievers.py`
- **Fix**: Removed `return_properties` parameter from `get_vector_cypher_retriever()` initialization

### 5. ✅ Fulltext Index Parameter Name
**Problem**: Wrong parameter name when creating fulltext index
- **Error**: `TypeError: create_fulltext_index() got an unexpected keyword argument 'text_properties'`
- **Files Modified**: `utils.py`
- **Fix**: Changed `text_properties` → `node_properties` in `IndexManager.create_fulltext_index()`

### 6. ✅ Embedding Dimension Mismatch
**Problem**: Vector index created with 1536 dimensions but qwen3-embed produces 1024
- **Error**: `ValueError: dimension mismatch`
- **Files Modified**: 
  - `.env` - Set `VECTOR_DIMENSIONS=1024`
  - Created `fix_dimensions.py` utility
- **Fix**: 
  - Detected actual embedding dimensions from model
  - Dropped and recreated vector index with correct dimensions
  - Updated environment configuration

### 7. ✅ Missing Vector and Fulltext Indexes
**Problem**: Database had no indexes despite having Chunk nodes with embeddings
- **Files Modified**: Created `create_indexes.py` utility
- **Fix**: 
  - Created `document_embeddings` vector index (1024 dimensions)
  - Created `document_fulltext` fulltext index
  - Added validation to `example_rag_query.py`

### 8. ✅ APOC Plugin Not Installed
**Problem**: Neo4j database missing required APOC plugin
- **Error**: `There is no procedure with the name 'apoc.create.addLabels'`
- **Files Modified**: 
  - `setup_check.py` - Added APOC validation
  - Updated documentation
- **Fix**: Added instructions for installing APOC plugin in Neo4j

### 9. ✅ Virtual Environment Conflicts
**Problem**: Two virtual environments (venv/ and .venv/) causing import errors
- **Files Modified**: Created `IMPORTANT_README.txt`
- **Fix**: 
  - Documented the issue clearly
  - Recommended deleting venv/ directory
  - Emphasized using `uv run` or activating `.venv/`

### 10. ✅ Missing Default RagTemplate
**Problem**: GraphRAGPipeline required explicit prompt_template parameter
- **Files Modified**: `graphrag.py`
- **Fix**: Added automatic instantiation of default RagTemplate if none provided

---

## Configuration Changes

### Environment Variables (.env)
```bash
# LLM Provider Selection
LLM_PROVIDER=openai  # or anthropic, cohere, mistral, ollama, etc.
OPENAI_BASE_URL=http://localhost:18000/v1  # For local models
OPENAI_API_KEY=dummy  # Required but not used for local

# Embedding Configuration
VECTOR_DIMENSIONS=1024  # Must match embedding model output
```

### Local Model Setup
- **Embedding Model**: qwen3-embed (1024 dimensions)
- **LLM**: Qwen3-4B-Instruct-2507-4bit
- **API Endpoint**: http://localhost:18000/v1 (OpenAI-compatible)

---

## Testing Results

### All 8 Examples Working ✅

1. **Basic Vector Retrieval** - ✅ Working
2. **Vector Cypher Retrieval** - ✅ Working  
3. **Hybrid Retrieval** - ✅ Working
4. **Text2Cypher** - ✅ Working (with automatic parameter fallback)
5. **Custom Prompt Templates** - ✅ Working (all 4 templates)
6. **Filtered Search** - ✅ Working
7. **Batch Queries** - ✅ Working
8. **Query with Fallback** - ✅ Working

### Database State
- 118 nodes total
- 7 Chunk nodes with embeddings
- Vector index: `document_embeddings` (1024 dimensions)
- Fulltext index: `document_fulltext`

---

## Key Learnings

### 1. Template Variable Names
- RagTemplate expects specific variable names: `{query_text}`, `{context}`, `{examples}`
- Custom templates must use these exact names
- `expected_inputs` list must match template placeholders

### 2. Retriever Parameter Compatibility
- Different retrievers accept different parameters
- VectorRetriever: accepts `top_k`, `return_properties`
- VectorCypherRetriever: accepts `top_k` but NOT `return_properties`
- Text2CypherRetriever: doesn't accept `top_k` or other retriever_config params
- Hybrid retrievers: accept both vector and fulltext parameters

### 3. Embedding Dimensions
- Must match exactly between model output and vector index
- Check actual model output, don't assume standard dimensions
- OpenAI models: typically 1536
- Local models: varies (qwen3-embed: 1024)

### 4. Index Creation
- Vector index requires: name, dimensions, similarity metric
- Fulltext index requires: name, node label, text properties
- Both must be created before running queries

### 5. Virtual Environment Management
- Use uv for consistent dependency management
- Avoid mixing pip venv with uv's .venv
- Always activate correct environment before running scripts

---

## Utilities Created

### create_indexes.py
- Creates missing vector and fulltext indexes
- Validates database has Chunk nodes
- Configurable dimensions and index names

### fix_dimensions.py
- Detects embedding dimension mismatches
- Tests actual model output
- Drops and recreates indexes with correct dimensions

### IMPORTANT_README.txt
- Documents virtual environment conflict
- Provides clear instructions for resolution

---

## Future Improvements

1. Add automatic dimension detection in config
2. Add index existence checks before queries
3. Improve error messages for common issues
4. Add retriever parameter validation
5. Document all retriever parameter requirements
6. Add health check endpoint
7. Add comprehensive test suite

---

## Commands Reference

### Run Examples
```bash
# Using uv (recommended)
uv run python examples/example_kg_builder.py
uv run python examples/example_rag_query.py

# Using activated .venv
source .venv/bin/activate
python examples/example_kg_builder.py
python examples/example_rag_query.py
```

### Create Indexes
```bash
uv run python create_indexes.py
```

### Fix Dimensions
```bash
uv run python fix_dimensions.py
```

### Check Setup
```bash
uv run python setup_check.py
```

---

## Notes

- All fixes tested with Python 3.13.7
- Neo4j GraphRAG v1.10.1
- Local models via OpenAI-compatible API
- APOC plugin required for knowledge graph building
- Resource cleanup (driver.close()) implemented in all examples
