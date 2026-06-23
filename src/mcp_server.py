"""
MCP Server for Incident Response Agent

Exposes RAG retrieval as an MCP tool for use by other agents.
"""

import os
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

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent
from rag_retriever import RAGRetriever


# Initialize RAG retriever
try:
    retriever = RAGRetriever()
    print(f"✅ RAG retriever initialized", file=sys.stderr)
except Exception as e:
    print(f"❌ Failed to initialize RAG retriever: {e}", file=sys.stderr)
    retriever = None

# Create MCP server
app = Server("incident-docs-server")


@app.list_tools()
async def list_tools() -> list[Tool]:
    """List available MCP tools."""
    return [
        Tool(
            name="search_incident_docs",
            description=(
                "Search the incident response documentation knowledge base. "
                "Returns relevant documentation chunks about runbooks, "
                "troubleshooting guides, and best practices."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search query for incident documentation"
                    },
                    "n_results": {
                        "type": "integer",
                        "description": "Number of results to return (default: 3)",
                        "default": 3
                    },
                    "doc_type": {
                        "type": "string",
                        "description": "Filter by document type (runbook, troubleshooting, etc.)",
                        "enum": ["runbook", "troubleshooting", "incident_report", "general"],
                        "default": None
                    }
                },
                "required": ["query"]
            }
        )
    ]


@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    """Handle tool calls."""
    if name != "search_incident_docs":
        raise ValueError(f"Unknown tool: {name}")

    if not retriever:
        return [TextContent(
            type="text",
            text="Error: RAG retriever not initialized"
        )]

    # Extract arguments
    query = arguments.get("query")
    n_results = arguments.get("n_results", 3)
    doc_type = arguments.get("doc_type")

    if not query:
        return [TextContent(
            type="text",
            text="Error: query parameter is required"
        )]

    try:
        # Perform search
        chunks = retriever.retrieve(query, n_results=n_results, doc_type=doc_type)

        if not chunks:
            return [TextContent(
                type="text",
                text=f"No documentation found for query: {query}"
            )]

        # Format results
        result_parts = [f"Found {len(chunks)} relevant documentation chunks:\n"]

        for i, chunk in enumerate(chunks, 1):
            meta = chunk['metadata']
            score = chunk['relevance_score']

            result_parts.append(f"\n--- Document {i} ---")
            result_parts.append(f"Source: {meta.get('filename', 'Unknown')}")
            result_parts.append(f"Type: {meta.get('doc_type', 'general')}")
            result_parts.append(f"Relevance: {score:.2f}")
            result_parts.append(f"\nContent:\n{chunk['content']}\n")

        return [TextContent(
            type="text",
            text="\n".join(result_parts)
        )]

    except Exception as e:
        return [TextContent(
            type="text",
            text=f"Error during search: {str(e)}"
        )]


async def main():
    """Run the MCP server."""
    async with stdio_server() as (read_stream, write_stream):
        await app.run(read_stream, write_stream, app.create_initialization_options())


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
