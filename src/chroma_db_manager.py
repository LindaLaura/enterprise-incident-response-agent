"""
ChromaDB Manager with OpenAI Embeddings

Manages vector database operations using OpenAI embeddings.
"""

import os
from pathlib import Path
from typing import List, Dict, Any, Optional
import chromadb
from chromadb.config import Settings
from openai import OpenAI
from .document_processor import DocumentChunk


class ChromaDBManager:
    """Manages ChromaDB operations with OpenAI embeddings."""

    def __init__(self, db_path: str = "./chroma_db", collection_name: str = "incident_docs"):
        """
        Initialize ChromaDB manager.

        Args:
            db_path: Path to ChromaDB storage
            collection_name: Name of the collection
        """
        self.db_path = Path(db_path)
        self.db_path.mkdir(parents=True, exist_ok=True)
        self.collection_name = collection_name

        # Initialize ChromaDB
        self.client = chromadb.PersistentClient(
            path=str(self.db_path),
            settings=Settings(
                anonymized_telemetry=False,
                allow_reset=True
            )
        )

        # Initialize OpenAI client
        api_key = os.getenv("OPENAI_API_KEY")
        base_url = os.getenv("OPENAI_BASE_URL")

        if not api_key:
            raise ValueError("OPENAI_API_KEY not found in environment")

        client_kwargs = {"api_key": api_key}
        if base_url:
            client_kwargs["base_url"] = base_url

        self.openai_client = OpenAI(**client_kwargs)

        # Use ChromaDB's built-in embeddings instead of OpenAI (proxy doesn't support embedding models)
        self.use_openai_embeddings = False
        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"}
        )

    def _test_openai_embeddings(self) -> bool:
        """Test if OpenAI embeddings are available."""
        try:
            response = self.openai_client.embeddings.create(
                model="text-embedding-3-small",
                input="test"
            )
            return True
        except Exception:
            return False

    def generate_embedding(self, text: str) -> List[float]:
        """
        Generate embedding for text.

        Args:
            text: Text to embed

        Returns:
            Embedding vector
        """
        if not self.use_openai_embeddings:
            return None  # ChromaDB will handle it

        response = self.openai_client.embeddings.create(
            model="text-embedding-3-small",
            input=text
        )
        return response.data[0].embedding

    def add_chunks(self, chunks: List[DocumentChunk]) -> List[str]:
        """
        Add document chunks to the collection.

        Args:
            chunks: List of DocumentChunk objects

        Returns:
            List of chunk IDs
        """
        if not chunks:
            return []

        documents = [chunk.content for chunk in chunks]
        metadatas = [chunk.metadata for chunk in chunks]
        ids = [f"{chunk.metadata['filename']}_{i}" for i, chunk in enumerate(chunks)]

        if self.use_openai_embeddings:
            # Generate embeddings
            print(f"   Generating embeddings for {len(chunks)} chunks...")
            embeddings = [self.generate_embedding(doc) for doc in documents]

            self.collection.add(
                documents=documents,
                embeddings=embeddings,
                metadatas=metadatas,
                ids=ids
            )
        else:
            # Let ChromaDB handle embeddings
            self.collection.add(
                documents=documents,
                metadatas=metadatas,
                ids=ids
            )

        return ids

    def search(
        self,
        query: str,
        n_results: int = 3,
        where: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Semantic search for relevant chunks.

        Args:
            query: Search query
            n_results: Number of results to return
            where: Optional metadata filter

        Returns:
            Dict with documents, metadatas, distances, ids
        """
        if self.use_openai_embeddings:
            query_embedding = self.generate_embedding(query)
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=n_results,
                where=where
            )
        else:
            results = self.collection.query(
                query_texts=[query],
                n_results=n_results,
                where=where
            )

        return {
            'documents': results['documents'][0] if results['documents'] else [],
            'metadatas': results['metadatas'][0] if results['metadatas'] else [],
            'distances': results['distances'][0] if results['distances'] else [],
            'ids': results['ids'][0] if results['ids'] else []
        }

    def get_stats(self) -> Dict[str, Any]:
        """Get collection statistics."""
        return {
            'total_chunks': self.collection.count(),
            'collection_name': self.collection_name,
            'db_path': str(self.db_path),
            'embedding_type': 'openai' if self.use_openai_embeddings else 'local'
        }

    def reset_collection(self):
        """Reset the collection."""
        try:
            self.client.delete_collection(name=self.collection_name)
        except:
            pass

        # Recreate with same settings
        self.__init__(str(self.db_path), self.collection_name)
