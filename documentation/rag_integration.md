# RAG Integration Documentation

## Overview

The Enterprise Incident Response Agent now includes Retrieval-Augmented Generation (RAG) capabilities powered by ChromaDB. This enhances incident analysis by retrieving relevant historical incident data and best practices during the analysis process.

## Architecture

```
┌─────────────────────┐
│   Incident Logs     │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ Step 1: Extract     │
│ Key Information     │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────────────────────┐
│ Step 2: Analyze Root Cause          │
│  ┌──────────────────────────────┐   │
│  │  1. Semantic Search          │   │
│  │  2. Retrieve Historical      │   │
│  │     Incidents (Top 2)        │   │
│  │  3. Augment Context          │   │
│  └──────────────────────────────┘   │
│                 ↓                    │
│  ChromaDB Knowledge Base             │
└──────────┬───────────────────────────┘
           │
           ▼
┌─────────────────────────────────────┐
│ Step 3: Generate Recommendations    │
│  ┌──────────────────────────────┐   │
│  │  1. Semantic Search          │   │
│  │  2. Retrieve Best Practices  │   │
│  │  3. Augment Context          │   │
│  └──────────────────────────────┘   │
│                 ↓                    │
│  ChromaDB Knowledge Base             │
└──────────┬───────────────────────────┘
           │
           ▼
┌─────────────────────┐
│ Step 4: Structure   │
│ JSON Report         │
└─────────────────────┘
```

## Components

### 1. ChromaDB Manager (`chroma_manager.py`)

Handles all vector database operations:
- **PersistentClient**: Stores embeddings locally in `./chroma_db`
- **Collection**: `incident_docs` collection for historical data
- **Embeddings**: Local `all-MiniLM-L6-v2` model (no API calls needed)
- **Operations**: Add documents, batch ingestion, semantic search

### 2. Document Ingestion (`ingest_documents.py`)

Populates the knowledge base with:
- Database connection pool exhaustion incidents
- API gateway/external service outages
- Kubernetes deployment failures
- Memory leak incidents
- Rate limiting best practices
- Database query performance issues

### 3. RAG-Enhanced Analysis Chain (`incident_chain.py`)

Integrates retrieval into analysis:
- **Root Cause Analysis**: Retrieves 2 most relevant historical incidents
- **Recommendations**: Retrieves 2 most relevant best practice documents
- **Context Augmentation**: Appends retrieved documents to prompts

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Ingest Knowledge Base

```bash
python src/ingest_documents.py
```

Expected output:
```
✅ Successfully added 6 documents!
📊 Final collection stats:
   - Total documents: 6
   - Collection name: incident_docs
```

### 3. Configure Environment

Add to your `.env` file:
```bash
USE_RAG=true  # Enable RAG (default: true)
```

## Usage

### Run with RAG Enabled (Default)

```bash
python src/main.py sample_logs/db_failure.txt
```

Output will show:
```
📚 RAG enabled: 6 documents in knowledge base
```

### Run without RAG

```bash
# Temporarily disable RAG
USE_RAG=false python src/main.py sample_logs/db_failure.txt
```

## Knowledge Base Structure

Each document in the knowledge base includes:

**Document Fields:**
- Full text content with causes, indicators, best practices, and solutions

**Metadata Fields:**
- `incident_type`: database, api, deployment, performance
- `category`: connection_pool, external_service, kubernetes, memory_leak, etc.
- `severity`: critical, high, medium, low
- `technology`: postgresql, rest_api, k8s, jvm, sql, general

## Semantic Search Examples

```python
from chroma_manager import ChromaManager

chroma = ChromaManager()

# Search for database issues
results = chroma.search("database connection pool exhausted", n_results=2)

# Filter by incident type
results = chroma.search(
    "deployment failure",
    n_results=3,
    where={"incident_type": "deployment"}
)
```

## RAG Enhancement Details

### Step 2: Root Cause Analysis

When analyzing root causes, the system:
1. Takes extracted incident information
2. Performs semantic search: `chroma.search(extracted_info, n_results=2)`
3. Retrieves top 2 most similar historical incidents
4. Appends to prompt as "Historical Context from Knowledge Base"
5. LLM analyzes with enriched context

### Step 3: Recommendations

When generating recommendations, the system:
1. Takes root cause analysis
2. Adds keywords: "best practices solutions remediation"
3. Performs semantic search
4. Retrieves top 2 relevant best practice documents
5. Appends to prompt as "Best Practices from Knowledge Base"
6. LLM generates recommendations with proven solutions

## Benefits

✅ **Consistency**: Recommendations based on proven solutions
✅ **Speed**: Faster analysis with relevant context
✅ **Quality**: Better root cause identification
✅ **Learning**: System improves as knowledge base grows
✅ **Offline**: No external API calls for embeddings

## Extending the Knowledge Base

### Add Custom Documents

```python
from chroma_manager import ChromaManager

chroma = ChromaManager()

# Add a new incident document
chroma.add_document(
    document="""
    Your incident description and learnings...
    """,
    metadata={
        "incident_type": "custom",
        "category": "my_category",
        "severity": "high",
        "technology": "my_tech"
    }
)
```

### Batch Import

```python
documents = [doc1, doc2, doc3]
metadatas = [meta1, meta2, meta3]

chroma.add_documents_batch(documents, metadatas)
```

### Reset Collection

```bash
rm -rf chroma_db
python src/ingest_documents.py
```

## Storage

- **Location**: `./chroma_db/` directory
- **Persistence**: Automatically persisted on disk
- **Size**: Grows with number of documents (~KB per document)
- **Backup**: Copy entire `chroma_db/` directory

## Performance

- **Embedding Generation**: ~50ms per document (local)
- **Search Query**: ~10-20ms
- **Collection Size**: 6 documents (expandable to thousands)
- **Memory Usage**: Minimal (~100MB for model + collection)

## Troubleshooting

### "Collection already exists" Error

```bash
rm -rf chroma_db
python src/ingest_documents.py
```

### RAG Not Working

Check output for:
```
📚 RAG enabled: X documents in knowledge base
```

If you see:
```
⚠️ RAG initialization failed
```

Verify ChromaDB installation:
```bash
pip install chromadb>=1.3.5
```

### No Results from Search

Ensure knowledge base is populated:
```python
from chroma_manager import ChromaManager
chroma = ChromaManager()
print(chroma.get_collection_stats())
```

Should show:
```
{'total_documents': 6, 'collection_name': 'incident_docs', ...}
```

## Future Enhancements

- [ ] Automatic document chunking for large texts
- [ ] Metadata filtering in search queries
- [ ] Hybrid search (semantic + keyword)
- [ ] User feedback loop for improving retrieval
- [ ] Real-time incident ingestion after resolution
- [ ] Multi-language support
- [ ] Document versioning
