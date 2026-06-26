# Tests for Enterprise Incident Response Agent

This directory contains comprehensive tests for all major components of the incident response system.

## Test Structure

```
tests/
├── __init__.py                    # Package initialization
├── README.md                      # This file
├── test_runner.py                 # Test runner script
├── test_document_processor.py     # Document processing tests
├── test_memory_manager.py         # Memory system tests
├── test_rag_retriever.py          # RAG retrieval tests
└── test_integration.py            # End-to-end integration tests
```

## Running Tests

### Run All Tests

```bash
# From project root
python tests/test_runner.py

# Or using unittest directly
python -m unittest discover tests

# Or run individual test files
python -m unittest tests.test_memory_manager
```

### Run Specific Test Module

```bash
python tests/test_runner.py tests.test_memory_manager
```

### Run Specific Test Class

```bash
python -m unittest tests.test_memory_manager.TestMemoryManager
```

### Run Specific Test Method

```bash
python -m unittest tests.test_memory_manager.TestMemoryManager.test_save_incident
```

## Test Coverage

### 1. Document Processor Tests (`test_document_processor.py`)

**Coverage:**
- ✅ Basic text chunking with size limits
- ✅ Chunking with overlap
- ✅ Handling short text (less than chunk size)
- ✅ DocumentChunk metadata structure
- ✅ Document type inference (runbook, troubleshooting, etc.)
- ✅ Loading .txt files from disk

**Key Tests:**
- `test_chunk_text_basic()` - Validates chunking logic
- `test_chunk_text_with_overlap()` - Ensures overlap works correctly
- `test_infer_doc_type()` - Tests filename-based type detection

---

### 2. Memory Manager Tests (`test_memory_manager.py`)

**Coverage:**
- ✅ Initialization and directory creation
- ✅ Saving incidents to long-term memory
- ✅ Retrieving similar incidents by keywords
- ✅ Short-term memory operations
- ✅ Memory persistence across sessions
- ✅ Statistics retrieval
- ✅ Events by severity structure validation

**Key Tests:**
- `test_save_incident()` - Validates incident storage
- `test_get_similar_incidents()` - Tests keyword-based search
- `test_memory_persistence()` - Ensures data persists to disk
- `test_events_by_severity_structure()` - Validates new schema

**Features Tested:**
- Incident ID, timestamp, severity tracking
- Service-level event tracking with timestamps
- Root cause and recommendation storage
- Similarity search by keywords

---

### 3. RAG Retriever Tests (`test_rag_retriever.py`)

**Coverage:**
- ✅ RAGRetriever initialization
- ✅ Basic semantic search
- ✅ Document type filtering
- ✅ Context formatting for prompts
- ✅ Combined retrieve-and-format operations
- ✅ Empty query handling

**Key Tests:**
- `test_retrieve_basic()` - Tests document retrieval
- `test_retrieve_with_doc_type_filter()` - Validates filtering
- `test_format_context()` - Ensures proper context formatting

**Note:** These tests may skip if ChromaDB is not initialized or no documents are ingested.

---

### 4. Integration Tests (`test_integration.py`)

**Coverage:**
- ✅ Sample log file existence and format
- ✅ Memory directory structure validation
- ✅ ChromaDB directory existence
- ✅ Documentation directory structure
- ✅ Environment configuration files
- ✅ .gitignore completeness
- ✅ JSON schema validation

**Key Tests:**
- `test_sample_logs_exist()` - Validates log files are present
- `test_memory_directory_structure()` - Checks memory JSON structure
- `test_events_by_severity_schema()` - Validates new schema format
- `test_incident_report_structure()` - Tests complete report structure

**JSON Schema Validation:**
Tests the complete incident report structure including:
- incident_id, incident_timestamp
- events_by_severity with service names
- severity, status, affected_services
- metadata (model_provider, rag_enabled, memory_enabled, generated_at)

---

## Test Requirements

```bash
# Install test dependencies (already in requirements.txt)
pip install -r requirements.txt
```

**Required for all tests:**
- Python 3.8+
- unittest (built-in)

**Required for specific tests:**
- ChromaDB (for RAG tests)
- Sample logs in `sample_logs/`
- Documentation in `docs/`

---

## Test Data

### Sample Log Files

The tests expect these log files in `sample_logs/`:
- `db_failure.txt` - Database connection pool failure
- `api_failure.txt` - API gateway circuit breaker incident
- `deployment_failure.txt` - Kubernetes deployment failure

### Documentation Files

The tests expect documentation files in `docs/`:
- `database_runbook.txt`
- `kubernetes_troubleshooting.txt`
- `api_gateway_incidents.txt`

---

## Expected Test Output

```bash
$ python tests/test_runner.py

================================================================================
Running All Tests
================================================================================
test_chunk_text_basic (tests.test_document_processor.TestDocumentProcessor) ... ok
test_chunk_text_short (tests.test_document_processor.TestDocumentProcessor) ... ok
test_chunk_text_with_overlap (tests.test_document_processor.TestDocumentProcessor) ... ok
test_document_chunk_metadata (tests.test_document_processor.TestDocumentProcessor) ... ok
test_infer_doc_type (tests.test_document_processor.TestDocumentProcessor) ... ok
test_load_txt_file (tests.test_document_processor.TestDocumentLoading) ... ok
test_initialization (tests.test_memory_manager.TestMemoryManager) ... ok
test_save_incident (tests.test_memory_manager.TestMemoryManager) ... ok
test_get_similar_incidents (tests.test_memory_manager.TestMemoryManager) ... ok
test_short_term_memory (tests.test_memory_manager.TestMemoryManager) ... ok
test_memory_persistence (tests.test_memory_manager.TestMemoryManager) ... ok
test_get_stats (tests.test_memory_manager.TestMemoryManager) ... ok
test_events_by_severity_structure (tests.test_memory_manager.TestMemoryManager) ... ok
...

----------------------------------------------------------------------
Ran XX tests in X.XXXs

OK
```

---

## Continuous Integration

To integrate with CI/CD:

```yaml
# .github/workflows/test.yml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.9'
      - name: Install dependencies
        run: pip install -r requirements.txt
      - name: Run tests
        run: python tests/test_runner.py
```

---

## Troubleshooting

**ChromaDB tests are skipped:**
- Run `python src/ingest_docs.py` to ingest documents first
- Ensure ChromaDB is properly installed: `pip install chromadb`

**Memory tests create temp files:**
- Tests use `tempfile.mkdtemp()` and clean up automatically
- No manual cleanup needed

**Integration tests fail:**
- Verify sample_logs/ directory exists with log files
- Verify docs/ directory has documentation files
- Check .env.example exists with required variables

---

## Adding New Tests

To add a new test file:

1. Create `test_<module_name>.py` in `tests/` directory
2. Import unittest and the module to test
3. Create test class inheriting from `unittest.TestCase`
4. Add test methods starting with `test_`
5. Run with `python tests/test_runner.py`

Example:
```python
import unittest
from your_module import YourClass

class TestYourClass(unittest.TestCase):
    def setUp(self):
        """Set up test fixtures."""
        self.instance = YourClass()
    
    def test_your_feature(self):
        """Test your feature."""
        result = self.instance.your_method()
        self.assertEqual(result, expected_value)

if __name__ == '__main__':
    unittest.main()
```

---

## Test Coverage Goals

- **Unit Tests:** 80%+ coverage of core logic
- **Integration Tests:** All major workflows tested
- **Edge Cases:** Boundary conditions and error handling
- **Regression Tests:** Known bugs have test cases

Run tests before committing code changes!
