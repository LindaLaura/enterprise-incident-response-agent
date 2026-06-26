"""
Tests for Document Processor
"""
import unittest
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from document_processor import DocumentProcessor, DocumentChunk


class TestDocumentProcessor(unittest.TestCase):
    """Test document processing functionality."""

    def setUp(self):
        """Set up test fixtures."""
        self.processor = DocumentProcessor()

    def test_chunk_text_basic(self):
        """Test basic text chunking."""
        text = "A" * 600  # 600 characters
        chunks = self.processor.chunk_text(text, chunk_size=500, overlap=50)

        self.assertGreater(len(chunks), 1)
        self.assertLessEqual(len(chunks[0].content), 500)

    def test_chunk_text_with_overlap(self):
        """Test chunking with overlap."""
        text = "This is sentence one. This is sentence two. This is sentence three."
        chunks = self.processor.chunk_text(text, chunk_size=40, overlap=10)

        # Verify overlap exists
        if len(chunks) > 1:
            self.assertTrue(any(word in chunks[1].content for word in chunks[0].content.split()[-3:]))

    def test_chunk_text_short(self):
        """Test chunking with text shorter than chunk size."""
        text = "Short text"
        chunks = self.processor.chunk_text(text, chunk_size=500, overlap=50)

        self.assertEqual(len(chunks), 1)
        self.assertEqual(chunks[0].content, text)

    def test_document_chunk_metadata(self):
        """Test DocumentChunk metadata."""
        chunk = DocumentChunk(
            content="Test content",
            metadata={'filename': 'test.txt', 'chunk_index': 0}
        )

        self.assertEqual(chunk.content, "Test content")
        self.assertEqual(chunk.metadata['filename'], 'test.txt')
        self.assertEqual(chunk.metadata['chunk_index'], 0)

    def test_infer_doc_type(self):
        """Test document type inference."""
        self.assertEqual(self.processor._infer_doc_type("database_runbook.txt"), "runbook")
        self.assertEqual(self.processor._infer_doc_type("troubleshooting_guide.txt"), "troubleshooting")
        self.assertEqual(self.processor._infer_doc_type("incident_report.txt"), "incident_report")
        self.assertEqual(self.processor._infer_doc_type("random.txt"), "general")


class TestDocumentLoading(unittest.TestCase):
    """Test document loading from files."""

    def setUp(self):
        """Set up test fixtures."""
        self.processor = DocumentProcessor()
        self.test_dir = Path(__file__).parent.parent / 'docs'

    def test_load_txt_file(self):
        """Test loading .txt files."""
        if self.test_dir.exists():
            txt_files = list(self.test_dir.glob('*.txt'))
            if txt_files:
                chunks = self.processor.load_and_chunk_document(str(txt_files[0]))
                self.assertGreater(len(chunks), 0)
                self.assertIsInstance(chunks[0], DocumentChunk)


if __name__ == '__main__':
    unittest.main()
