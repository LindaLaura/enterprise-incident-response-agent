"""
Enterprise Incident Response Agent - CLI Entry Point

Week 1 MVP: Analyze incident logs and generate structured reports.
"""

import os
import sys
import json
from dotenv import load_dotenv

load_dotenv()

print("CLI started")

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

    # Step 4: Run incident analysis chain (placeholder)
    print("=== Incident Analysis ===")
    print("Note: LLM integration not yet implemented")
    print("Log content preview:")
    print("-" * 50)
    print(log_content[:500] + "..." if len(log_content) > 500 else log_content)
    print("-" * 50)

    # TODO: Initialize LLM client based on DEFAULT_PROVIDER
    # TODO: Create IncidentAnalysisChain
    # TODO: Run analysis: result = chain.analyze(log_content)

    # Step 5: Output placeholder result
    placeholder_result = {
        "status": "placeholder",
        "message": "Analysis chain not yet implemented",
        "log_file": log_file_path,
        "log_length": len(log_content)
    }

    print("\n=== Analysis Result (Placeholder) ===")
    print(json.dumps(placeholder_result, indent=2))


if __name__ == "__main__":
    main()
