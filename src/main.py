"""
Enterprise Incident Response Agent - CLI Entry Point

Week 1 MVP: Analyze incident logs and generate structured reports.
"""


import os
import sys
import json
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables BEFORE importing  modules
BASE_DIR = Path(__file__).resolve().parent.parent
ENV_FILE = BASE_DIR / ".env"

# Load .env file if it exists
if ENV_FILE.exists():
    load_dotenv(ENV_FILE, override=True)
else:
    # Fallback to searching default locations
    load_dotenv(override=True) 

from .openai_client import OpenAIClient
from .anthropic_client import AnthropicClient
from .incident_chain import IncidentAnalysisChain
from .prompts import EXTRACT_INFORMATION_PROMPT

def main():
    """Main CLI entry point."""

    # Step 1: Parse command-line arguments
    if len(sys.argv) < 2:
        print("Usage: python src/main.py <log_file_path>")
        print("Example: python src/main.py sample_logs/db_failure.txt")
        sys.exit(1)

    log_file_path = sys.argv[1]

    # Step 2: Validate the log file
    if not os.path.exists(log_file_path):
        print(f"Error: File '{log_file_path}' does not exist")
        sys.exit(1)

    if not os.path.isfile(log_file_path):
        print(f"Error: '{log_file_path}' is not a file")
        sys.exit(1)

    # Step 3: Read the log file
    try:
        with open(log_file_path, 'r') as f:
            log_content = f.read()
        print(f"\n=== Log file loaded: {log_file_path} ===")
        print(f"Log size: {len(log_content)} characters\n")
    except Exception as e:
        print(f"Error reading file: {e}")
        sys.exit(1)

    # Step 4: Initialize LLM and run incident analysis
    print("=== Incident Analysis ===")
    print("Initializing LLM client...")
    provider = os.getenv("DEFAULT_PROVIDER", "openai")  # Get from .env or default to "openai"
  
    if provider == "openai":
      llm_client = OpenAIClient()
      print("=== Using OpenAI ===")
    elif provider == "anthropic":
      llm_client = AnthropicClient()
      print("=== Using Anthropic ===")
    else:
      print(f"Error: Unknown provider '{provider}'")
      sys.exit(1)

    print("Creating analysis chain...")

    # Check if RAG and Memory should be enabled (can be controlled via env vars)
    use_rag = os.getenv("USE_RAG", "true").lower() == "true"
    use_memory = os.getenv("USE_MEMORY", "true").lower() == "true"
    chain = IncidentAnalysisChain(llm_client, use_rag=use_rag, use_memory=use_memory)

    print("Running analysis (this may take 30-60 seconds)...\n")

    try:
      result = chain.analyze(log_content)
      print("Analysis complete!")
    except Exception as e:
      print(f"Error during analysis: {e}")
      sys.exit(1)

    # Step 5: Output the real result
    print("\n=== Analysis Result ===")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
