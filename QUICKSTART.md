# Quick Start Guide

## ⚡ Fast Setup (5 minutes)

### Step 1: Install Dependencies ✅ DONE

You've already completed this step:
```bash
uv venv
uv pip install -r requirements.txt
```

### Step 2: Set Up Neo4j Database

You have **two options**:

#### Option A: Neo4j Desktop (Recommended for local development)

1. **Download**: [https://neo4j.com/download/](https://neo4j.com/download/)
2. **Install** Neo4j Desktop
3. **Create a new project** and database
4. **IMPORTANT: Install APOC plugin**:
   - Select your database
   - Go to the "Plugins" tab
   - Click "Install" next to APOC
5. **Start** the database
6. **Note the password** you set

#### Option B: Neo4j Aura (Free cloud database)

1. **Sign up**: [https://neo4j.com/cloud/aura/](https://neo4j.com/cloud/aura/)
2. **Create a free instance** (APOC is pre-installed ✓)
3. **Download credentials** (you'll get a password file)
4. **Copy the connection URI** (looks like `neo4j+s://xxxxx.databases.neo4j.io`)

### Step 3: Configure Environment Variables

1. **Create your .env file**:
   ```bash
   cp .env.example .env
   ```

2. **Edit .env** with your credentials:
   ```bash
   # For Local Neo4j Desktop
   NEO4J_URI=bolt://localhost:7687
   NEO4J_USERNAME=neo4j
   NEO4J_PASSWORD=your_password_here
   
   # For Neo4j Aura
   NEO4J_URI=neo4j+s://xxxxx.databases.neo4j.io
   NEO4J_USERNAME=neo4j
   NEO4J_PASSWORD=your_aura_password_here
   
   # LLM Provider (choose one: openai, anthropic, cohere, mistral, azure_openai, ollama, vertexai)
   LLM_PROVIDER=openai
   
   # OpenAI (required if using openai provider)
   OPENAI_API_KEY=sk-your_key_here
   OPENAI_BASE_URL=  # Optional: leave empty for default, or set custom endpoint
   ```

3. **Get an OpenAI API Key** (if you don't have one):
   - Go to: [https://platform.openai.com/api-keys](https://platform.openai.com/api-keys)
   - Create a new API key
   - Copy and paste it into your .env file

### Step 4: Verify Setup

```bash
uv run setup_check.py
```

You should see:
```
✅ SETUP COMPLETE
```

### Step 5: Build Your First Knowledge Graph

```bash
uv run examples/example_kg_builder.py
```

This will:
- Extract entities from sample text
- Build a knowledge graph in Neo4j
- Create embeddings for semantic search
- Resolve duplicate entities

### Step 6: Query Your Knowledge Graph

**Important:** Make sure you ran Step 5 first to build the knowledge graph!

```bash
uv run examples/example_rag_query.py
```

This will demonstrate:
- Vector similarity search
- Graph traversal queries
- Hybrid retrieval
- Natural language to Cypher

### Step 7: Visualize Your Graph

1. Open Neo4j Browser: **http://localhost:7474** (or your Aura URL)
2. Run this query:
   ```cypher
   MATCH (n) RETURN n LIMIT 50
   ```
3. Explore your knowledge graph!

## 🎯 What You Need

### Minimum Requirements:
- ✅ Python 3.9+ (you have 3.13.7 ✓)
- ✅ Dependencies installed (done ✓)
- ⚠️ **Neo4j database** (need to start)
- ⚠️ **OpenAI API key** (need to add)

### Optional but Recommended:
- Neo4j Desktop (easier than Docker)
- OpenAI API key with credits
- Or use Ollama for local LLM (free but requires setup)

## 🆘 Troubleshooting

### "Wrong Python environment" / "No module named..."
**Problem**: Using wrong virtual environment

**Solution**:
```bash
# ALWAYS use uv run:
uv run examples/example_kg_builder.py

# Check your Python:
which python3  # Should be in .venv, NOT venv
```

### "APOC procedure not found"
**Problem**: APOC plugin not installed

**Solution**:
- **Neo4j Desktop**: Database → Plugins → Install APOC → Restart
- **Neo4j Aura**: Already installed (restart instance if needed)
- Run `uv run setup_check.py` to verify

### "Connection refused" Error
**Problem**: Neo4j is not running

**Solution**:
- If using Neo4j Desktop: Start your database
- If using Docker: `docker start neo4j`
- If using Aura: Check your connection URI

### "OpenAI API key required" Error
**Problem**: No API key in .env file

**Solution**:
1. Get a key from [platform.openai.com](https://platform.openai.com/api-keys)
2. Add it to .env: `OPENAI_API_KEY=sk-...`

### Alternative: Use Ollama (Free, Local)

If you don't want to use OpenAI, you can use Ollama:

1. **Install Ollama**: [https://ollama.ai/](https://ollama.ai/)
2. **Pull a model**: `ollama pull llama3`
3. **Update examples** to use OllamaLLM instead of OpenAILLM

## 📚 Next Steps

Once everything is working:

1. **Read the full README.md** for detailed documentation
2. **Experiment with your own data**:
   - Replace sample text with your content
   - Try PDF documents
   - Create custom schemas
3. **Customize for your use case**:
   - Modify prompt templates
   - Adjust chunk sizes
   - Try different retrieval strategies

## 💡 Quick Test Without Setup

If you just want to see the code structure without running:

```bash
# View the project structure
tree -L 2

# Read the main modules
cat config.py
cat kg_builder.py
cat retrievers.py
cat graphrag.py
```

## 🎓 Learning Resources

- [Neo4j GraphRAG Docs](https://neo4j.com/docs/neo4j-graphrag-python/current/)
- [Neo4j GraphAcademy](https://graphacademy.neo4j.com/) (Free courses)
- [Cypher Query Language](https://neo4j.com/docs/cypher-manual/current/)

---

**Need Help?**
- Neo4j Community Forum: [community.neo4j.com](https://community.neo4j.com/)
- Discord: [discord.gg/neo4j](https://discord.gg/neo4j)
