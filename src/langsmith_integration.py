"""
LangSmith Integration for Evaluation Datasets

Creates datasets in LangSmith for tracking evaluation metrics and model performance.
"""

import json
import logging
from typing import Dict, List, Any, Optional, Callable
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)

try:
    from langsmith import Client
    from langsmith import trace as langsmith_trace
    from langsmith.evaluation import evaluate, EvaluationResult
    LANGSMITH_AVAILABLE = True
except ImportError:
    LANGSMITH_AVAILABLE = False
    logger.warning("LangSmith not installed - dataset tracking disabled")


class LangSmithDatasetTracker:
    """Track evaluations and create datasets in LangSmith."""

    def __init__(self, api_key: Optional[str] = None, project: str = "enterprise-incident-response-agent"):
        """
        Initialize LangSmith dataset tracker.

        Args:
            api_key: LangSmith API key
            project: LangSmith project name
        """
        import os

        self.api_key = api_key or os.getenv("LANGSMITH_API_KEY")
        self.project = project
        self.client = None

        if LANGSMITH_AVAILABLE and self.api_key:
            try:
                self.client = Client(api_key=self.api_key)
                logger.info(f"✅ LangSmith connected - {project}")
            except Exception as e:
                logger.warning(f"⚠️ Could not connect to LangSmith: {e}")

    def create_evaluation_dataset(self, name: str, description: str = "") -> Optional[str]:
        """
        Create a new evaluation dataset in LangSmith.

        Args:
            name: Dataset name
            description: Dataset description

        Returns:
            Dataset ID or None
        """
        if not self.client:
            return None

        try:
            # Try new API signature first
            try:
                dataset = self.client.create_dataset(
                    dataset_name=name,
                    description=description or f"Evaluation dataset created at {datetime.now().isoformat()}"
                )
            except TypeError:
                # Fallback to old API signature
                dataset = self.client.create_dataset(
                    name=name,
                    description=description or f"Evaluation dataset created at {datetime.now().isoformat()}"
                )

            logger.debug(f"✅ Created dataset: {name} (ID: {dataset.id})")
            return dataset.id
        except Exception as e:
            # Suppress "409 Conflict" errors - dataset already exists is OK
            if "409" in str(e) or "already exists" in str(e):
                logger.debug(f"Dataset {name} already exists (this is OK)")
                return None
            logger.debug(f"Could not create dataset {name}: {e}")
            return None

    def log_evaluation_example(
        self,
        dataset_id: str,
        inputs: Dict[str, Any],
        outputs: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Log an evaluation example to LangSmith dataset.

        Args:
            dataset_id: Dataset ID
            inputs: Input data for evaluation
            outputs: Output/expected data
            metadata: Additional metadata

        Returns:
            Success status
        """
        if not self.client:
            return False

        try:
            self.client.create_example(
                inputs=inputs,
                outputs=outputs,
                dataset_id=dataset_id,
                metadata=metadata or {}
            )
            return True
        except Exception as e:
            logger.error(f"Failed to log example: {type(e).__name__}: {e}")
            return False

    def log_evaluation_batch(
        self,
        dataset_name: str,
        evaluations: List[Dict[str, Any]]
    ) -> Optional[str]:
        """
        Create dataset (or get existing) and log batch of evaluations.

        Args:
            dataset_name: Dataset name
            evaluations: List of evaluation records

        Returns:
            Dataset ID or None
        """
        if not evaluations:
            return None

        if not self.client:
            return None

        # Try to get existing dataset, or create new one
        dataset_id = None
        try:
            # First try to get existing dataset
            datasets = list(self.client.list_datasets(dataset_name_contains=dataset_name))
            if datasets:
                dataset_id = datasets[0].id
                logger.info(f"✅ Using existing dataset: {dataset_name} (ID: {dataset_id})")
            else:
                # Create new if doesn't exist
                dataset_id = self.create_evaluation_dataset(
                    name=dataset_name,
                    description=f"Batch of {len(evaluations)} evaluations"
                )
        except Exception as e:
            logger.debug(f"Could not get dataset list: {e}")
            # Try to create as fallback
            dataset_id = self.create_evaluation_dataset(
                name=dataset_name,
                description=f"Batch of {len(evaluations)} evaluations"
            )

        if not dataset_id:
            return None

        # Log examples
        logged = 0
        for eval_record in evaluations:
            inputs = {
                "incident_id": eval_record.get("incident_id"),
                "stage": eval_record.get("stage"),
                "timestamp": eval_record.get("timestamp")
            }

            outputs = {
                "quality_score": eval_record.get("quality_score"),
                "metrics": eval_record.get("metrics", {})
            }

            if self.log_evaluation_example(dataset_id, inputs, outputs):
                logged += 1

        if logged > 0:
            logger.debug(f"✅ Logged {logged}/{len(evaluations)} examples to {dataset_name}")
        else:
            logger.debug(f"No examples logged to {dataset_name}")

        return dataset_id

    def log_analysis_trace(
        self,
        incident_id: str,
        stages: Dict[str, Any],
        evaluations: Dict[str, Any],
        overall_quality: float
    ) -> bool:
        """
        Log complete analysis execution as a trace.

        Args:
            incident_id: Incident ID
            stages: Stage outputs
            evaluations: Evaluation results
            overall_quality: Overall quality score

        Returns:
            Success status
        """
        if not self.client or not LANGSMITH_AVAILABLE:
            return False

        try:
            with langsmith_trace(
                name=f"incident_analysis_{incident_id}",
                project_name=self.project,
                tags=["evaluation", "analysis"]
            ) as trace:
                # Log stages
                for stage_name, stage_data in stages.items():
                    trace.add_metadata("stage", {
                        stage_name: {
                            "output": stage_data,
                            "timestamp": datetime.now().isoformat()
                        }
                    })

                # Log evaluations
                trace.add_metadata("evaluations", evaluations)

                # Log quality score
                trace.add_metadata("overall_quality_score", overall_quality)

            logger.info(f"✅ Logged trace for incident {incident_id}")
            return True
        except Exception as e:
            logger.warning(f"Failed to log trace: {e}")
            return False

    def get_or_create_metric_dataset(self) -> Optional[str]:
        """
        Get or create unified metric dataset.

        Returns:
            Dataset ID or None
        """
        if not self.client:
            return None

        try:
            # Try to get existing dataset
            datasets = self.client.list_datasets(name_contains="evaluation_metrics")
            if datasets:
                dataset_id = next(iter(datasets)).id
                logger.info(f"✅ Using existing metric dataset: {dataset_id}")
                return dataset_id

            # Create new dataset
            return self.create_evaluation_dataset(
                name="evaluation_metrics",
                description="Unified evaluation metrics across all pipeline stages"
            )
        except Exception as e:
            logger.warning(f"Failed to get/create metric dataset: {e}")
            return None


class LangSmithEvaluationExporter:
    """Export evaluation metrics to LangSmith datasets."""

    def __init__(self, tracker: Optional[LangSmithDatasetTracker] = None):
        """
        Initialize exporter.

        Args:
            tracker: LangSmith tracker instance
        """
        self.tracker = tracker or LangSmithDatasetTracker()

    def export_evaluation_metrics(self, metrics_file: Path) -> bool:
        """
        Export evaluation metrics from file to LangSmith.

        Args:
            metrics_file: Path to metrics JSON file

        Returns:
            Success status
        """
        if not metrics_file.exists():
            logger.warning(f"Metrics file not found: {metrics_file}")
            return False

        try:
            with open(metrics_file, 'r') as f:
                metrics = json.load(f)

            if not metrics:
                return False

            # Create dataset
            dataset_name = metrics_file.stem
            dataset_id = self.tracker.log_evaluation_batch(dataset_name, metrics)

            return dataset_id is not None

        except Exception as e:
            logger.error(f"Failed to export metrics: {e}")
            return False

    def export_all_metrics(self, eval_dir: Path = Path("memory/evaluation")) -> Dict[str, bool]:
        """
        Export all evaluation metrics files to LangSmith.

        Args:
            eval_dir: Evaluation directory

        Returns:
            Export status per file
        """
        results = {}

        if not eval_dir.exists():
            logger.warning(f"Evaluation directory not found: {eval_dir}")
            return results

        # Export all metric files (both *_metrics.json and analysis_traces.json)
        for metrics_file in eval_dir.glob("*.json"):
            if metrics_file.name.endswith(("_metrics.json", "_traces.json")):
                success = self.export_evaluation_metrics(metrics_file)
                results[metrics_file.name] = success
                logger.info(f"{'✅' if success else '❌'} Exported {metrics_file.name}")

        return results

    def create_evaluation_summary_dataset(
        self,
        summary: Dict[str, Any]
    ) -> Optional[str]:
        """
        Create dataset with evaluation summary.

        Args:
            summary: Evaluation summary data

        Returns:
            Dataset ID or None
        """
        return self.tracker.log_evaluation_batch(
            dataset_name="evaluation_summary",
            evaluations=[summary]
        )


def integrate_langsmith_with_orchestrator(orchestrator_metrics_file: Path) -> bool:
    """
    Integrate LangSmith with evaluation orchestrator.

    Args:
        orchestrator_metrics_file: Path to orchestrator metrics

    Returns:
        Success status
    """
    try:
        tracker = LangSmithDatasetTracker()
        exporter = LangSmithEvaluationExporter(tracker)

        return exporter.export_evaluation_metrics(orchestrator_metrics_file)

    except Exception as e:
        logger.error(f"Failed to integrate LangSmith: {e}")
        return False


def setup_langsmith_evaluation_pipeline():
    """
    Set up complete LangSmith integration for evaluation pipeline.

    Creates:
    - Evaluation metrics dataset
    - RAGAS metrics dataset
    - DeepEval metrics dataset
    - Pipeline execution traces
    """
    try:
        tracker = LangSmithDatasetTracker()

        if not tracker.client:
            logger.warning("LangSmith not available - evaluation export disabled")
            return False

        # Create datasets
        datasets = {
            "orchestrator_metrics": tracker.create_evaluation_dataset(
                "orchestrator_metrics",
                "Unified evaluation metrics from orchestrator"
            ),
            "ragas_metrics": tracker.create_evaluation_dataset(
                "ragas_metrics",
                "RAG evaluation metrics (retrieval & generation quality)"
            ),
            "deepeval_metrics": tracker.create_evaluation_dataset(
                "deepeval_metrics",
                "DeepEval metrics (LLM output quality)"
            ),
            "analysis_traces": tracker.create_evaluation_dataset(
                "analysis_traces",
                "Complete incident analysis execution traces"
            )
        }

        logger.info(f"✅ LangSmith datasets created: {datasets}")
        return True

    except Exception as e:
        logger.error(f"Failed to set up LangSmith pipeline: {e}")
        return False


class LangSmithExperimentRunner:
    """Run experiments to evaluate models against datasets."""

    def __init__(self, tracker: Optional[LangSmithDatasetTracker] = None):
        """
        Initialize experiment runner.

        Args:
            tracker: LangSmith tracker instance
        """
        self.tracker = tracker or LangSmithDatasetTracker()
        self.client = self.tracker.client if self.tracker else None

    def run_experiment(
        self,
        dataset_name: str,
        llm_callable: Callable[[Dict[str, Any]], str],
        evaluator_functions: List[Callable[[Dict[str, Any], str], EvaluationResult]],
        experiment_name: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Run experiment against a dataset.

        Args:
            dataset_name: Name of dataset to test against
            llm_callable: Function that takes example inputs and returns model output
            evaluator_functions: List of evaluator functions
            experiment_name: Name for this experiment run
            metadata: Additional metadata

        Returns:
            Experiment results or None
        """
        if not self.client or not LANGSMITH_AVAILABLE:
            logger.warning("LangSmith not available - cannot run experiment")
            return None

        try:
            # Get the dataset
            datasets = list(self.client.list_datasets(dataset_name_contains=dataset_name))
            if not datasets:
                logger.error(f"Dataset '{dataset_name}' not found")
                return None

            dataset_id = datasets[0].id
            logger.info(f"📊 Running experiment on dataset: {dataset_name}")

            # Run experiment with evaluators
            exp_name = experiment_name or f"{dataset_name}_exp_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

            results = evaluate(
                llm_callable,
                data=dataset_id,
                evaluators=evaluator_functions,
                experiment_prefix=exp_name,
                metadata=metadata or {"source": "enterprise-incident-response-agent"},
                num_repetitions=1
            )

            logger.info(f"✅ Experiment '{exp_name}' completed")
            return {
                "experiment_name": exp_name,
                "dataset_name": dataset_name,
                "status": "completed",
                "results": results
            }

        except Exception as e:
            logger.error(f"Failed to run experiment: {e}")
            return None

    def run_orchestrator_metrics_experiment(
        self,
        llm_callable: Optional[Callable] = None,
        experiment_name: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Run experiment on orchestrator_metrics dataset.

        Args:
            llm_callable: Optional LLM function (defaults to quality assessment)
            experiment_name: Name for experiment

        Returns:
            Experiment results or None
        """
        if not llm_callable:
            def default_assessor(example: Dict[str, Any]) -> str:
                incident_id = example.get("incident_id", "unknown")
                stage = example.get("stage", "unknown")
                return f"Evaluated {incident_id} at stage {stage}"
            llm_callable = default_assessor

        def quality_evaluator(run, example) -> EvaluationResult:
            """Evaluate prediction quality."""
            try:
                outputs = example.get("outputs", {})
                metrics = outputs.get("metrics", {}) if isinstance(outputs, dict) else {}
                quality_score = metrics.get("quality_score", 0.5)
                return EvaluationResult(
                    key="quality_score",
                    score=float(quality_score),
                    comment=f"Quality score: {quality_score}"
                )
            except Exception as e:
                logger.debug(f"Quality evaluator error: {e}")
                return EvaluationResult(key="quality_score", score=0.5, comment="Error")

        return self.run_experiment(
            dataset_name="orchestrator_metrics",
            llm_callable=llm_callable,
            evaluator_functions=[quality_evaluator],
            experiment_name=experiment_name or "orchestrator_quality_assessment"
        )

    def run_analysis_traces_experiment(
        self,
        experiment_name: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Run experiment on analysis_traces dataset.

        Args:
            experiment_name: Name for experiment

        Returns:
            Experiment results or None
        """
        def trace_assessor(example: Dict[str, Any]) -> str:
            incident_id = example.get("incident_id", "unknown")
            stages = example.get("stages_executed", [])
            return f"Trace for {incident_id} with {len(stages)} stages"

        def trace_evaluator(run, example) -> EvaluationResult:
            """Evaluate execution trace quality."""
            try:
                outputs = example.get("outputs", {})
                quality_scores = outputs.get("quality_scores", {}) if isinstance(outputs, dict) else {}
                overall_score = outputs.get("overall_quality_score", 0.5)

                return EvaluationResult(
                    key="overall_quality",
                    score=float(overall_score),
                    comment=f"Overall quality: {overall_score}"
                )
            except Exception as e:
                logger.debug(f"Trace evaluator error: {e}")
                return EvaluationResult(key="overall_quality", score=0.5, comment="Error")

        return self.run_experiment(
            dataset_name="analysis_traces",
            llm_callable=trace_assessor,
            evaluator_functions=[trace_evaluator],
            experiment_name=experiment_name or "analysis_traces_quality"
        )

    def run_deepeval_metrics_experiment(
        self,
        experiment_name: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Run experiment on deepeval_metrics dataset.

        Args:
            experiment_name: Name for experiment

        Returns:
            Experiment results or None
        """
        def deepeval_assessor(example: Dict[str, Any]) -> str:
            incident_id = example.get("incident_id", "unknown")
            stage = example.get("stage", "unknown")
            return f"DeepEval metrics for {incident_id} at {stage}"

        def deepeval_evaluator(run, example) -> EvaluationResult:
            """Evaluate DeepEval metrics."""
            try:
                outputs = example.get("outputs", {})
                aggregate_score = outputs.get("aggregate_score", 0) if isinstance(outputs, dict) else 0

                return EvaluationResult(
                    key="deepeval_score",
                    score=float(aggregate_score),
                    comment=f"DeepEval score: {aggregate_score}"
                )
            except Exception as e:
                logger.debug(f"DeepEval evaluator error: {e}")
                return EvaluationResult(key="deepeval_score", score=0.0, comment="Error")

        return self.run_experiment(
            dataset_name="deepeval_metrics",
            llm_callable=deepeval_assessor,
            evaluator_functions=[deepeval_evaluator],
            experiment_name=experiment_name or "deepeval_quality_assessment"
        )

    def run_ragas_metrics_experiment(
        self,
        experiment_name: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Run experiment on ragas_metrics dataset.

        Args:
            experiment_name: Name for experiment

        Returns:
            Experiment results or None
        """
        def ragas_assessor(example: Dict[str, Any]) -> str:
            incident_id = example.get("incident_id", "unknown")
            stage = example.get("stage", "unknown")
            return f"RAGAS metrics for {incident_id} at {stage}"

        def ragas_evaluator(run, example) -> EvaluationResult:
            """Evaluate RAGAS metrics."""
            try:
                outputs = example.get("outputs", {})
                if not isinstance(outputs, dict):
                    return EvaluationResult(key="ragas_score", score=0.0, comment="Invalid output")

                metrics = outputs.get("metrics", {})
                if isinstance(metrics, dict):
                    # Calculate average of available RAGAS metrics
                    scores = []
                    for key in ["context_precision", "context_recall", "faithfulness", "answer_relevance", "answer_correctness"]:
                        if key in metrics:
                            try:
                                scores.append(float(metrics[key]))
                            except (ValueError, TypeError):
                                pass

                    avg_score = sum(scores) / len(scores) if scores else 0.0
                else:
                    avg_score = 0.0

                return EvaluationResult(
                    key="ragas_score",
                    score=float(avg_score),
                    comment=f"RAGAS average: {avg_score}"
                )
            except Exception as e:
                logger.debug(f"RAGAS evaluator error: {e}")
                return EvaluationResult(key="ragas_score", score=0.0, comment="Error")

        return self.run_experiment(
            dataset_name="ragas_metrics",
            llm_callable=ragas_assessor,
            evaluator_functions=[ragas_evaluator],
            experiment_name=experiment_name or "ragas_quality_assessment"
        )

    def list_experiments(self, dataset_name: str) -> List[Dict[str, Any]]:
        """
        List all experiments for a dataset.

        Note: Returns dataset info with comparison URL - experiments are viewable in LangSmith UI.

        Args:
            dataset_name: Dataset name

        Returns:
            List of experiment details
        """
        if not self.client:
            return []

        try:
            datasets = list(self.client.list_datasets(dataset_name_contains=dataset_name))
            if not datasets:
                return []

            dataset = datasets[0]

            # Build comparison URL for this dataset
            # Format: https://smith.langchain.com/o/{org}/datasets/{dataset_id}/compare
            compare_url = f"https://smith.langchain.com/datasets/{dataset.id}/compare"

            return [{
                "name": dataset.name,
                "dataset_id": dataset.id,
                "url": compare_url,
                "description": dataset.description,
                "note": "View all experiments and runs in the LangSmith UI at the URL above"
            }]

        except Exception as e:
            logger.debug(f"Failed to list experiments: {e}")
            return []

    def get_experiment_summary(self, dataset_name: str) -> Dict[str, Any]:
        """
        Get summary of all experiments on a dataset.

        Args:
            dataset_name: Dataset name

        Returns:
            Experiment summary
        """
        experiments = self.list_experiments(dataset_name)

        return {
            "dataset_name": dataset_name,
            "total_experiments": len(experiments),
            "experiments": experiments,
            "created_at": datetime.now().isoformat()
        }


__all__ = [
    "LangSmithDatasetTracker",
    "LangSmithEvaluationExporter",
    "LangSmithExperimentRunner",
    "integrate_langsmith_with_orchestrator",
    "setup_langsmith_evaluation_pipeline",
]
