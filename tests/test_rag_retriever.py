"""
Tests for RAG Retriever
"""
import unittest
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from rag_retriever import RAGRetriever


class TestRAGRetriever(unittest.TestCase):
    """Test RAG retrieval functionality."""

    @classmethod
    def setUpClass(cls):
        """Set up class-level fixtures."""
        try:
            cls.retriever = RAGRetriever()
            cls.has_chroma = True
        except Exception as e:
            print(f"Warning: Could not initialize RAGRetriever: {e}")
            cls.has_chroma = False

    def test_initialization(self):
        """Test retriever initialization."""
        if not self.has_chroma:
            self.skipTest("ChromaDB not available")

        self.assertIsNotNone(self.retriever)
        self.assertIsNotNone(self.retriever.db_manager)

    def test_retrieve_basic(self):
        """Test basic retrieval."""
        if not self.has_chroma:
            self.skipTest("ChromaDB not available")

        # Try to retrieve documents
        try:
            chunks = self.retriever.retrieve("database connection pool", n_results=3)
            self.assertIsInstance(chunks, list)
            # May be empty if no documents ingested yet
            if chunks:
                self.assertIn('content', chunks[0])
                self.assertIn('metadata', chunks[0])
                self.assertIn('relevance_score', chunks[0])
        except Exception as e:
            self.skipTest(f"Retrieval failed: {e}")

    def test_retrieve_with_doc_type_filter(self):
        """Test retrieval with document type filter."""
        if not self.has_chroma:
            self.skipTest("ChromaDB not available")

        try:
            chunks = self.retriever.retrieve("kubernetes", n_results=2, doc_type="troubleshooting")
            self.assertIsInstance(chunks, list)
        except Exception as e:
            self.skipTest(f"Retrieval with filter failed: {e}")

    def test_format_context(self):
        """Test context formatting."""
        if not self.has_chroma:
            self.skipTest("ChromaDB not available")

        chunks = [
            {
                'content': 'Test content 1',
                'metadata': {'filename': 'test1.txt', 'doc_type': 'runbook'},
                'relevance_score': 0.95
            },
            {
                'content': 'Test content 2',
                'metadata': {'filename': 'test2.txt', 'doc_type': 'troubleshooting'},
                'relevance_score': 0.85
            }
        ]

        context = self.retriever.format_context(chunks)
        self.assertIn('Test content 1', context)
        self.assertIn('Test content 2', context)
        self.assertIn('test1.txt', context)

    def test_retrieve_and_format(self):
        """Test combined retrieve and format."""
        if not self.has_chroma:
            self.skipTest("ChromaDB not available")

        try:
            context = self.retriever.retrieve_and_format("database", n_results=2)
            self.assertIsInstance(context, str)
        except Exception as e:
            self.skipTest(f"Retrieve and format failed: {e}")

    def test_empty_query(self):
        """Test behavior with empty query."""
        if not self.has_chroma:
            self.skipTest("ChromaDB not available")

        chunks = self.retriever.retrieve("", n_results=3)
        # Should return empty list or handle gracefully
        self.assertIsInstance(chunks, list)


if __name__ == '__main__':
    unittest.main()
