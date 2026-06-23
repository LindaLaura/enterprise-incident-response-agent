"""
Document Processing Module

Handles loading, chunking, and preprocessing of documents for RAG.
"""

import os
from pathlib import Path
from typing import List, Dict, Any
import re


class DocumentChunk:
    """Represents a chunk of a document with metadata."""

    def __init__(self, content: str, metadata: Dict[str, Any]):
        self.content = content
        self.metadata = metadata

    def __repr__(self):
        return f"DocumentChunk(source={self.metadata.get('source')}, length={len(self.content)})"


class DocumentProcessor:
    """Processes documents into chunks for embedding."""

    def __init__(self, chunk_size: int = 500, chunk_overlap: int = 50):
        """
        Initialize document processor.

        Args:
            chunk_size: Target size of each chunk in characters
            chunk_overlap: Number of characters to overlap between chunks
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def load_text_file(self, file_path: Path) -> str:
        """
        Load content from a text file.

        Args:
            file_path: Path to text file

        Returns:
            File content as string
        """
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()

    def load_pdf_file(self, file_path: Path) -> str:
        """
        Load content from a PDF file.

        Args:
            file_path: Path to PDF file

        Returns:
            Extracted text content
        """
        try:
            from pypdf import PdfReader

            reader = PdfReader(file_path)
            text = []
            for page in reader.pages:
                text.append(page.extract_text())
            return '\n\n'.join(text)
        except ImportError:
            print(f"⚠️  pypdf not installed, skipping PDF: {file_path}")
            return ""
        except Exception as e:
            print(f"⚠️  Error reading PDF {file_path}: {e}")
            return ""

    def chunk_text(self, text: str, metadata: Dict[str, Any]) -> List[DocumentChunk]:
        """
        Split text into overlapping chunks.

        Args:
            text: Text to chunk
            metadata: Metadata to attach to each chunk

        Returns:
            List of DocumentChunk objects
        """
        if not text.strip():
            return []

        chunks = []
        start = 0

        while start < len(text):
            # Find end of chunk
            end = start + self.chunk_size

            # If not at end of text, try to break at sentence boundary
            if end < len(text):
                # Look for sentence endings near the target end
                search_start = max(start, end - 100)
                search_text = text[search_start:end + 100]

                # Find last sentence boundary
                sentence_endings = ['.', '!', '?', '\n\n']
                best_break = -1

                for ending in sentence_endings:
                    pos = search_text.rfind(ending)
                    if pos > len(search_text) // 2:  # In second half of search window
                        best_break = search_start + pos + 1
                        break

                if best_break > start:
                    end = best_break

            # Extract chunk
            chunk_text = text[start:end].strip()

            if chunk_text:
                # Create chunk with metadata
                chunk_metadata = metadata.copy()
                chunk_metadata['chunk_index'] = len(chunks)
                chunk_metadata['start_char'] = start
                chunk_metadata['end_char'] = end

                chunks.append(DocumentChunk(chunk_text, chunk_metadata))

            # Move to next chunk with overlap
            start = end - self.chunk_overlap

            # Ensure we make progress
            if start >= end:
                start = end

        return chunks

    def process_document(self, file_path: Path) -> List[DocumentChunk]:
        """
        Process a document file into chunks.

        Args:
            file_path: Path to document file

        Returns:
            List of DocumentChunk objects
        """
        # Load content based on file type
        if file_path.suffix.lower() == '.pdf':
            content = self.load_pdf_file(file_path)
        elif file_path.suffix.lower() in ['.txt', '.md']:
            content = self.load_text_file(file_path)
        else:
            print(f"⚠️  Unsupported file type: {file_path.suffix}")
            return []

        if not content:
            return []

        # Create base metadata
        metadata = {
            'source': str(file_path),
            'filename': file_path.name,
            'filetype': file_path.suffix.lower(),
            'doc_type': self._infer_doc_type(file_path)
        }

        # Chunk the document
        chunks = self.chunk_text(content, metadata)

        return chunks

    def process_directory(self, directory: Path) -> List[DocumentChunk]:
        """
        Process all documents in a directory.

        Args:
            directory: Path to directory

        Returns:
            List of all DocumentChunk objects from all documents
        """
        all_chunks = []

        # Find all supported files
        supported_extensions = ['.txt', '.md', '.pdf']
        files = []

        for ext in supported_extensions:
            files.extend(directory.glob(f'*{ext}'))

        print(f"📁 Found {len(files)} documents in {directory}")

        # Process each file
        for file_path in sorted(files):
            print(f"   Processing: {file_path.name}")
            chunks = self.process_document(file_path)
            all_chunks.extend(chunks)
            print(f"      → {len(chunks)} chunks")

        return all_chunks

    def _infer_doc_type(self, file_path: Path) -> str:
        """
        Infer document type from filename.

        Args:
            file_path: Path to file

        Returns:
            Document type string
        """
        name_lower = file_path.name.lower()

        if 'runbook' in name_lower:
            return 'runbook'
        elif 'troubleshoot' in name_lower or 'debug' in name_lower:
            return 'troubleshooting'
        elif 'incident' in name_lower:
            return 'incident_report'
        elif 'api' in name_lower or 'gateway' in name_lower:
            return 'api_documentation'
        elif 'database' in name_lower or 'db' in name_lower:
            return 'database_documentation'
        elif 'kubernetes' in name_lower or 'k8s' in name_lower:
            return 'kubernetes_documentation'
        else:
            return 'general'
