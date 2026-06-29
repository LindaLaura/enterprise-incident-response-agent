"""
RAG Retriever Module

Handles semantic search and retrieval of relevant documentation chunks.
"""

from typing import List, Dict, Any, Optional
from .chroma_db_manager import ChromaDBManager


class RAGRetriever:
    """Retrieves relevant documentation for incident analysis."""

    def __init__(self, chroma_manager: Optional[ChromaDBManager] = None):
        """
        Initialize RAG retriever.

        Args:
            chroma_manager: ChromaDB manager instance (creates new if None)
        """
        self.chroma = chroma_manager or ChromaDBManager()

    def retrieve(
        self,
        query: str,
        n_results: int = 3,
        doc_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Retrieve relevant documentation chunks.

        Args:
            query: Search query
            n_results: Number of chunks to retrieve
            doc_type: Optional document type filter

        Returns:
            List of dicts with 'content', 'metadata', 'relevance_score'
        """
        # Build metadata filter
        where_filter = None
        if doc_type:
            where_filter = {"doc_type": doc_type}

        # Search
        results = self.chroma.search(query, n_results=n_results, where=where_filter)

        # Format results
        retrieved_chunks = []
        for doc, meta, distance in zip(
            results['documents'],
            results['metadatas'],
            results['distances']
        ):
            retrieved_chunks.append({
                'content': doc,
                'metadata': meta,
                'relevance_score': 1 - distance  # Convert distance to similarity
            })

        return retrieved_chunks

    def format_context(
        self,
        chunks: List[Dict[str, Any]],
        max_chunks: Optional[int] = None
    ) -> str:
        """
        Format retrieved chunks into context string for prompts.

        Args:
            chunks: List of retrieved chunks
            max_chunks: Maximum number of chunks to include

        Returns:
            Formatted context string
        """
        if not chunks:
            return ""

        if max_chunks:
            chunks = chunks[:max_chunks]

        context_parts = ["\n--- Retrieved Documentation Context ---\n"]

        for i, chunk in enumerate(chunks, 1):
            meta = chunk['metadata']
            context_parts.append(
                f"\n[Document {i}] {meta.get('filename', 'Unknown')} "
                f"({meta.get('doc_type', 'general')})\n"
            )
            context_parts.append(chunk['content'])
            context_parts.append("\n")

        return "".join(context_parts)

    def retrieve_and_format(
        self,
        query: str,
        n_results: int = 3,
        doc_type: Optional[str] = None
    ) -> str:
        """
        Retrieve and format in one step.

        Args:
            query: Search query
            n_results: Number of chunks to retrieve
            doc_type: Optional document type filter

        Returns:
            Formatted context string
        """
        chunks = self.retrieve(query, n_results, doc_type)
        return self.format_context(chunks)

    def get_stats(self) -> Dict[str, Any]:
        """Get retriever statistics."""
        return self.chroma.get_stats()
