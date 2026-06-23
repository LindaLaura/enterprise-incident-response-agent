"""
Document Ingestion Script

Loads documents from docs/ folder, chunks them, generates embeddings,
and stores them in ChromaDB.
"""

import sys
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
BASE_DIR = Path(__file__).resolve().parent.parent
ENV_FILE = BASE_DIR / ".env"
if ENV_FILE.exists():
    load_dotenv(ENV_FILE, override=True)
else:
    load_dotenv(override=True)

from document_processor import DocumentProcessor
from chroma_db_manager import ChromaDBManager


def ingest_documents(docs_dir: Path, reset: bool = False):
    """
    Ingest documents from directory into ChromaDB.

    Args:
        docs_dir: Path to documents directory
        reset: Whether to reset existing collection
    """
    print("=" * 60)
    print("📚 Document Ingestion for RAG System")
    print("=" * 60)
    print()

    # Initialize components
    print("🔧 Initializing components...")
    processor = DocumentProcessor(chunk_size=500, chunk_overlap=50)
    chroma = ChromaDBManager()

    # Check existing collection
    stats = chroma.get_stats()
    print(f"📊 Current collection stats:")
    print(f"   - Total chunks: {stats['total_chunks']}")
    print(f"   - Embedding type: {stats['embedding_type']}")
    print(f"   - Database path: {stats['db_path']}")
    print()

    if stats['total_chunks'] > 0:
        if reset:
            print("🗑️  Resetting collection...")
            chroma.reset_collection()
        else:
            response = input("⚠️  Collection already has chunks. Reset? (y/n): ")
            if response.lower() == 'y':
                print("🗑️  Resetting collection...")
                chroma.reset_collection()
            else:
                print("✅ Keeping existing chunks.")
                return

    # Check if docs directory exists
    if not docs_dir.exists():
        print(f"❌ Directory not found: {docs_dir}")
        print(f"   Creating directory and adding sample documentation...")
        docs_dir.mkdir(parents=True, exist_ok=True)
        print(f"   Please add .txt or .pdf files to {docs_dir} and run again.")
        return

    # Process all documents
    print(f"📁 Processing documents from: {docs_dir}")
    print()

    chunks = processor.process_directory(docs_dir)

    if not chunks:
        print("❌ No documents found or processed.")
        print(f"   Supported formats: .txt, .md, .pdf")
        print(f"   Please add documents to {docs_dir}")
        return

    print()
    print(f"✂️  Total chunks created: {len(chunks)}")
    print()

    # Add chunks to ChromaDB
    print("💾 Adding chunks to ChromaDB...")
    ids = chroma.add_chunks(chunks)

    print(f"✅ Successfully added {len(ids)} chunks!")
    print()

    # Show final stats
    stats = chroma.get_stats()
    print("📊 Final collection stats:")
    print(f"   - Total chunks: {stats['total_chunks']}")
    print(f"   - Collection: {stats['collection_name']}")
    print(f"   - Embedding type: {stats['embedding_type']}")
    print()

    # Test search
    print("🔍 Testing semantic search...")
    test_queries = [
        "database connection pool",
        "kubernetes deployment failure",
        "circuit breaker pattern"
    ]

    for query in test_queries:
        results = chroma.search(query, n_results=2)
        print(f"\n   Query: '{query}'")
        if results['documents']:
            for i, (doc, meta) in enumerate(zip(results['documents'], results['metadatas'])):
                print(f"   {i+1}. Source: {meta.get('filename')}")
                print(f"      Type: {meta.get('doc_type')}")
                print(f"      Preview: {doc[:80]}...")
        else:
            print("      No results found")

    print()
    print("=" * 60)
    print("✨ Document ingestion complete!")
    print("=" * 60)


def main():
    """Main entry point."""
    # Get docs directory
    docs_dir = BASE_DIR / "docs"

    # Check for command line arguments
    reset = "--reset" in sys.argv or "-r" in sys.argv

    # Run ingestion
    ingest_documents(docs_dir, reset=reset)


if __name__ == "__main__":
    main()
