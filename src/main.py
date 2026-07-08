"""
Enterprise Incident Response Agent - CLI Entry Point

Analyze incident logs with LangGraph orchestration, evaluation metrics, and optional LangSmith export.
"""


import os
import sys
import json
import asyncio
from pathlib import Path
from dotenv import load_dotenv
from datetime import datetime

# Load environment variables BEFORE importing modules
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
from .memory_manager import MemoryManager
from .rag_retriever import RAGRetriever
from .services.analysis_service import AnalysisService
from .evaluation.evaluation_orchestrator import EvaluationOrchestrator
from .langsmith_integration import (
    LangSmithEvaluationExporter,
    LangSmithExperimentRunner,
    setup_langsmith_evaluation_pipeline
)

async def run_analysis_with_evaluation(logs, incident_id):
    """Run analysis with evaluation and optional LangSmith export."""
    print("\n📊 Initializing Analysis Service...")

    try:
        # Initialize components
        memory_manager = MemoryManager(memory_dir="./memory")
        rag_retriever = RAGRetriever()
        llm_client = OpenAIClient() if os.getenv("DEFAULT_PROVIDER", "openai") == "openai" else AnthropicClient()

        # Initialize analysis service with LangGraph + evaluators
        analysis_service = AnalysisService(rag_retriever, memory_manager, llm_client)

        print("🚀 Running analysis with evaluation...")

        # Run analysis
        result = await analysis_service.run_analysis(
            logs=logs,
            incident_id=incident_id,
            use_langgraph=os.getenv("USE_LANGGRAPH", "true").lower() == "true"
        )

        print(f"✅ Analysis complete! (Duration: {result.get('duration_ms', 0)}ms)")

        return result

    except Exception as e:
        print(f"❌ Analysis error: {e}")
        raise


def export_to_langsmith():
    """Export metrics to LangSmith if API key is set."""
    api_key = os.getenv("LANGSMITH_API_KEY")

    if not api_key:
        print("⚠️  LANGSMITH_API_KEY not set - skipping export")
        return False

    try:
        print("\n📤 Exporting metrics to LangSmith...")

        # Set up datasets
        setup_langsmith_evaluation_pipeline()

        # Export metrics
        exporter = LangSmithEvaluationExporter()
        results = exporter.export_all_metrics(Path("memory/evaluation"))

        print("✅ Export complete!")
        for filename, success in results.items():
            status = "✅" if success else "❌"
            print(f"  {status} {filename}")

        return True

    except Exception as e:
        print(f"⚠️  Export failed: {e}")
        return False


def run_experiment(dataset_name: str = "orchestrator_metrics"):
    """Run an experiment on a dataset to evaluate model quality."""
    api_key = os.getenv("LANGSMITH_API_KEY")

    if not api_key:
        print("⚠️  LANGSMITH_API_KEY not set - experiments require LangSmith")
        return False

    try:
        print(f"\n🧪 Running experiment on dataset: {dataset_name}...")

        runner = LangSmithExperimentRunner()

        # Route to specialized experiment runners
        if dataset_name == "orchestrator_metrics":
            result = runner.run_orchestrator_metrics_experiment()
        elif dataset_name == "analysis_traces":
            result = runner.run_analysis_traces_experiment()
        elif dataset_name == "deepeval_metrics":
            result = runner.run_deepeval_metrics_experiment()
        elif dataset_name == "ragas_metrics":
            result = runner.run_ragas_metrics_experiment()
        else:
            result = runner.run_experiment(
                dataset_name=dataset_name,
                llm_callable=lambda x: str(x),
                evaluator_functions=[]
            )

        if result:
            print(f"✅ Experiment completed: {result.get('experiment_name')}")
            return True
        else:
            print(f"⚠️  Experiment failed or returned no results")
            return False

    except Exception as e:
        print(f"❌ Experiment failed: {e}")
        return False


def list_experiments(dataset_name: str = "orchestrator_metrics"):
    """List all experiments for a dataset."""
    api_key = os.getenv("LANGSMITH_API_KEY")

    if not api_key:
        print("⚠️  LANGSMITH_API_KEY not set")
        return

    try:
        runner = LangSmithExperimentRunner()
        experiments = runner.list_experiments(dataset_name)

        print(f"\n📊 Experiments for '{dataset_name}':")

        if experiments:
            for exp in experiments:
                print(f"   Dataset: {exp.get('name', 'unknown')}")
                print(f"   Dataset ID: {exp.get('dataset_id', 'N/A')}")
                print(f"   URL: {exp.get('url')}")
                print(f"   \n   👉 View experiments at: {exp.get('url')}")
        else:
            print("   (No datasets found)")

    except Exception as e:
        print(f"❌ Failed to list experiments: {e}")


def main():
    """Main CLI entry point."""

    # Step 1: Parse command-line arguments
    if len(sys.argv) < 2:
        print("Usage: python -m src.main <command> [options]")
        print("\nCommands:")
        print("  analyze <log_file>          Analyze incident logs")
        print("  experiment <dataset>        Run experiment on dataset (default: orchestrator_metrics)")
        print("  list-experiments <dataset>  List experiments for dataset")
        print("\nExamples:")
        print("  python -m src.main analyze sample_logs/api_failure.txt")
        print("  python -m src.main analyze sample_logs/api_failure.txt --langsmith")
        print("  python -m src.main experiment orchestrator_metrics")
        print("  python -m src.main list-experiments orchestrator_metrics")
        sys.exit(1)

    command = sys.argv[1]

    # Handle experiment commands
    if command == "experiment":
        dataset_name = sys.argv[2] if len(sys.argv) > 2 else "orchestrator_metrics"
        run_experiment(dataset_name)
        return

    if command == "list-experiments":
        dataset_name = sys.argv[2] if len(sys.argv) > 2 else "orchestrator_metrics"
        list_experiments(dataset_name)
        return

    if command != "analyze":
        print(f"Error: Unknown command '{command}'")
        print("Use 'analyze', 'experiment', or 'list-experiments'")
        sys.exit(1)

    # Handle analyze command (legacy: direct file path still works)
    if command == "analyze":
        log_file_path = sys.argv[2] if len(sys.argv) > 2 else None
    else:
        log_file_path = command  # Support old behavior: first arg is file path

    export_langsmith = "--langsmith" in sys.argv or os.getenv("LANGSMITH_AUTO_EXPORT", "false").lower() == "true"

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

    # Step 4: Generate incident ID from filename or timestamp
    incident_id = f"INC-CLI-{int(datetime.now().timestamp())}"
    print(f"Incident ID: {incident_id}\n")

    # Step 5: Run analysis with evaluation
    print("=== Incident Analysis ===")

    try:
        # Use new Analysis Service with LangGraph + Evaluation
        use_new_pipeline = os.getenv("USE_ANALYSIS_SERVICE", "true").lower() == "true"

        if use_new_pipeline:
            # NEW: Run with Analysis Service + Evaluation
            result = asyncio.run(run_analysis_with_evaluation(log_content, incident_id))
        else:
            # LEGACY: Run with traditional chain
            provider = os.getenv("DEFAULT_PROVIDER", "openai")
            if provider == "openai":
                llm_client = OpenAIClient()
                print("=== Using OpenAI ===")
            elif provider == "anthropic":
                llm_client = AnthropicClient()
                print("=== Using Anthropic ===")
            else:
                print(f"Error: Unknown provider '{provider}'")
                sys.exit(1)

            use_rag = os.getenv("USE_RAG", "true").lower() == "true"
            use_memory = os.getenv("USE_MEMORY", "true").lower() == "true"
            chain = IncidentAnalysisChain(llm_client, use_rag=use_rag, use_memory=use_memory)
            result = chain.analyze(log_content)

    except Exception as e:
        print(f"Error during analysis: {e}")
        sys.exit(1)

    # Step 6: Output the result
    print("\n=== Analysis Result ===")
    if isinstance(result, dict):
        print(json.dumps(result, indent=2, default=str))
    else:
        print(result)

    # Step 7: Save incident to memory
    if isinstance(result, dict):
        try:
            memory_manager = MemoryManager(memory_dir="./memory")

            # Extract data from report stage (the most comprehensive)
            report_stage = result.get('stages', {}).get('report', {})

            # Build incident record with extracted fields
            memory_manager.save_incident(
                incident_id=result.get('incident_id', incident_id),
                summary=report_stage.get('summary', result.get('stages', {}).get('report', {}).get('summary', 'Analysis completed')),
                root_cause=report_stage.get('root_cause', 'Unknown'),
                recommendations=report_stage.get('recommendations', result.get('recommendations', [])),
                severity=report_stage.get('severity', 'MEDIUM'),
                affected_services=report_stage.get('affected_services', []),
                incident_timestamp=report_stage.get('incident_timestamp'),
                events_by_severity=report_stage.get('events_by_severity'),
                technical_impact=report_stage.get('technical_impact'),
                business_impact=report_stage.get('business_impact'),
                confidence=report_stage.get('confidence'),
                affected_users=report_stage.get('affected_users'),
                duration=report_stage.get('duration'),
                timeline=report_stage.get('timeline'),
                next_steps=report_stage.get('next_steps'),
                incident_summary=report_stage.get('incident_summary'),
                source_analysis=report_stage.get('source_analysis'),
                rag_context=report_stage.get('rag_context'),
                memory_context=report_stage.get('memory_context'),
                root_cause_analysis=report_stage.get('root_cause_analysis'),
                metadata=report_stage.get('metadata'),
                status=report_stage.get('status', result.get('status'))
            )
            print(f"💾 Incident saved to memory with full analysis data")
        except Exception as e:
            print(f"⚠️  Could not save to memory: {e}")

    # Step 8: Export to LangSmith if requested
    if export_langsmith:
        export_to_langsmith()
        print("\n📊 View datasets at: https://smith.langchain.com/")
    else:
        print("\n💡 Tip: Add --langsmith flag to export metrics to LangSmith dashboard")
        print("   Or set LANGSMITH_AUTO_EXPORT=true in .env")

    print(f"\n✅ Analysis saved with incident ID: {incident_id}")


if __name__ == "__main__":
    main()
