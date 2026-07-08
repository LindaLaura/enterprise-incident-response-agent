"""
Unified Evaluation Orchestrator

Aggregates DeepEval and RAGAS metrics across the entire incident analysis pipeline.
Provides comprehensive quality assessment and trend analysis.
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime

logger = logging.getLogger(__name__)


class EvaluationOrchestrator:
    """Orchestrates evaluation across all pipeline stages."""

    def __init__(self, eval_dir: Optional[str] = None):
        """
        Initialize evaluation orchestrator.

        Args:
            eval_dir: Directory to store evaluation results
        """
        self.eval_dir = Path(eval_dir or "memory/evaluation")
        self.eval_dir.mkdir(parents=True, exist_ok=True)
        self.orchestrator_file = self.eval_dir / "orchestrator_metrics.json"
        self.ragas_file = self.eval_dir / "ragas_metrics.json"
        self.deepeval_file = self.eval_dir / "deepeval_metrics.json"
        self.analysis_traces_file = self.eval_dir / "analysis_traces.json"

        self.orchestrator_history = self._load_history()
        self.ragas_history = self._load_history_from_file(self.ragas_file)
        self.deepeval_history = self._load_history_from_file(self.deepeval_file)
        self.traces_history = self._load_history_from_file(self.analysis_traces_file)

        # Import evaluators
        try:
            from .deepeval_evaluator import DeepEvalEvaluator
            self.deepeval = DeepEvalEvaluator(str(self.eval_dir))
        except Exception as e:
            logger.warning(f"DeepEval not available: {e}")
            self.deepeval = None

        try:
            from .ragas_evaluator import RAGASEvaluator
            self.ragas = RAGASEvaluator(str(self.eval_dir))
        except Exception as e:
            logger.warning(f"RAGAS not available: {e}")
            self.ragas = None

    def _load_history(self) -> List[Dict]:
        """Load existing evaluation history from orchestrator file."""
        return self._load_history_from_file(self.orchestrator_file)

    def _load_history_from_file(self, file_path: Path) -> List[Dict]:
        """Load evaluation history from a specific file."""
        if file_path.exists():
            try:
                with open(file_path, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.debug(f"Failed to load history from {file_path.name}: {e}")
        return []

    def _save_history(self):
        """Save evaluation history."""
        try:
            with open(self.orchestrator_file, 'w') as f:
                json.dump(self.orchestrator_history, f, indent=2, default=str)
            # Also save RAGAS and DeepEval metrics if they exist
            with open(self.ragas_file, 'w') as f:
                json.dump(self.ragas_history, f, indent=2, default=str)
            with open(self.deepeval_file, 'w') as f:
                json.dump(self.deepeval_history, f, indent=2, default=str)
            with open(self.analysis_traces_file, 'w') as f:
                json.dump(self.traces_history, f, indent=2, default=str)
        except Exception as e:
            logger.error(f"Failed to save history: {e}")

    def evaluate_retrieval_stage(
        self,
        query: str,
        retrieved_docs: List[str],
        incident_id: str
    ) -> Dict[str, Any]:
        """
        Evaluate retrieval stage using RAGAS.

        Args:
            query: Retrieval query
            retrieved_docs: Retrieved documents
            incident_id: Incident ID

        Returns:
            Evaluation metrics
        """
        logger.info(f"📊 Evaluating retrieval stage for {incident_id}")

        result = {
            "incident_id": incident_id,
            "stage": "retrieval",
            "timestamp": datetime.now().isoformat(),
            "query_length": len(query),
            "docs_retrieved": len(retrieved_docs),
            "metrics": {}
        }

        if self.ragas:
            try:
                ragas_result = self.ragas.evaluate_retrieval(
                    query=query,
                    retrieved_docs=retrieved_docs
                )
                result["metrics"]["ragas"] = ragas_result
                result["quality_score"] = (
                    ragas_result.get("context_precision", 0) +
                    ragas_result.get("context_recall", 0)
                ) / 2
                logger.info(f"✅ Retrieval evaluation: {result['quality_score']:.2f}")
            except Exception as e:
                logger.warning(f"RAGAS retrieval evaluation failed: {e}")
                result["metrics"]["ragas"] = {"error": str(e)}
                result["quality_score"] = 0.0

        self.orchestrator_history.append(result)
        # Also save RAGAS metrics separately
        if "ragas" in result.get("metrics", {}):
            ragas_record = {
                "incident_id": incident_id,
                "stage": "retrieval",
                "timestamp": result.get("timestamp"),
                "metrics": result["metrics"]["ragas"]
            }
            self.ragas_history.append(ragas_record)
        self._save_history()
        return result

    def evaluate_generation_stage(
        self,
        query: str,
        answer: str,
        retrieved_context: List[str],
        incident_id: str
    ) -> Dict[str, Any]:
        """
        Evaluate generation stage using RAGAS.

        Args:
            query: Original query
            answer: Generated answer
            retrieved_context: Context used
            incident_id: Incident ID

        Returns:
            Evaluation metrics
        """
        logger.info(f"📊 Evaluating generation stage for {incident_id}")

        result = {
            "incident_id": incident_id,
            "stage": "generation",
            "timestamp": datetime.now().isoformat(),
            "answer_length": len(answer),
            "context_size": len(retrieved_context),
            "metrics": {}
        }

        if self.ragas:
            try:
                ragas_result = self.ragas.evaluate_generation(
                    query=query,
                    answer=answer,
                    retrieved_context=retrieved_context
                )
                result["metrics"]["ragas"] = ragas_result
                result["quality_score"] = (
                    ragas_result.get("faithfulness", 0) +
                    ragas_result.get("answer_relevance", 0)
                ) / 2
                logger.info(f"✅ Generation evaluation: {result['quality_score']:.2f}")
            except Exception as e:
                logger.warning(f"RAGAS generation evaluation failed: {e}")
                result["metrics"]["ragas"] = {"error": str(e)}
                result["quality_score"] = 0.0

        self.orchestrator_history.append(result)
        self._save_history()
        return result

    def evaluate_root_cause_stage(
        self,
        root_cause: str,
        retrieved_context: List[str],
        incident_id: str
    ) -> Dict[str, Any]:
        """
        Evaluate root cause analysis using DeepEval.

        Args:
            root_cause: Root cause explanation
            retrieved_context: Context used
            incident_id: Incident ID

        Returns:
            Evaluation metrics
        """
        logger.info(f"📊 Evaluating root cause stage for {incident_id}")

        result = {
            "incident_id": incident_id,
            "stage": "root_cause",
            "timestamp": datetime.now().isoformat(),
            "root_cause_length": len(root_cause),
            "metrics": {}
        }

        if self.deepeval:
            try:
                deepeval_result = self.deepeval.evaluate_root_cause(
                    root_cause=root_cause,
                    retrieved_context=retrieved_context,
                    incident_id=incident_id
                )
                result["metrics"]["deepeval"] = deepeval_result
                result["quality_score"] = deepeval_result.get("aggregate_score", 0.0)
                logger.info(f"✅ Root cause evaluation: {result['quality_score']:.2f}")
            except Exception as e:
                logger.warning(f"DeepEval root cause evaluation failed: {e}")
                result["metrics"]["deepeval"] = {"error": str(e)}
                result["quality_score"] = 0.0

        self.orchestrator_history.append(result)
        # Also save DeepEval metrics separately
        if "deepeval" in result.get("metrics", {}):
            deepeval_record = {
                "incident_id": incident_id,
                "stage": "root_cause",
                "timestamp": result.get("timestamp"),
                "metrics": result["metrics"]["deepeval"]
            }
            self.deepeval_history.append(deepeval_record)
        self._save_history()
        return result

    def evaluate_recommendations_stage(
        self,
        recommendations: List[str],
        incident_id: str,
        context: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Evaluate recommendations using DeepEval.

        Args:
            recommendations: Generated recommendations
            incident_id: Incident ID
            context: Optional context

        Returns:
            Evaluation metrics
        """
        logger.info(f"📊 Evaluating recommendations stage for {incident_id}")

        result = {
            "incident_id": incident_id,
            "stage": "recommendations",
            "timestamp": datetime.now().isoformat(),
            "num_recommendations": len(recommendations),
            "metrics": {}
        }

        if self.deepeval:
            try:
                deepeval_result = self.deepeval.evaluate_recommendations(
                    recommendations=recommendations,
                    incident_id=incident_id,
                    context=context
                )
                result["metrics"]["deepeval"] = deepeval_result
                result["quality_score"] = deepeval_result.get("aggregate_score", 0.0)
                logger.info(f"✅ Recommendations evaluation: {result['quality_score']:.2f}")
            except Exception as e:
                logger.warning(f"DeepEval recommendations evaluation failed: {e}")
                result["metrics"]["deepeval"] = {"error": str(e)}
                result["quality_score"] = 0.0

        self.orchestrator_history.append(result)
        # Also save DeepEval metrics separately
        if "deepeval" in result.get("metrics", {}):
            deepeval_record = {
                "incident_id": incident_id,
                "stage": "recommendations",
                "timestamp": result.get("timestamp"),
                "metrics": result["metrics"]["deepeval"]
            }
            self.deepeval_history.append(deepeval_record)
        self._save_history()
        return result

    def evaluate_report_stage(
        self,
        report: Dict[str, Any],
        incident_id: str
    ) -> Dict[str, Any]:
        """
        Evaluate final report using DeepEval.

        Args:
            report: Incident report
            incident_id: Incident ID

        Returns:
            Evaluation metrics
        """
        logger.info(f"📊 Evaluating report stage for {incident_id}")

        result = {
            "incident_id": incident_id,
            "stage": "report",
            "timestamp": datetime.now().isoformat(),
            "metrics": {}
        }

        if self.deepeval:
            try:
                deepeval_result = self.deepeval.evaluate_report(
                    report=report,
                    incident_id=incident_id
                )
                result["metrics"]["deepeval"] = deepeval_result
                result["quality_score"] = deepeval_result.get("aggregate_score", 0.0)
                logger.info(f"✅ Report evaluation: {result['quality_score']:.2f}")
            except Exception as e:
                logger.warning(f"DeepEval report evaluation failed: {e}")
                result["metrics"]["deepeval"] = {"error": str(e)}
                result["quality_score"] = 0.0

        self.orchestrator_history.append(result)
        # Also save DeepEval metrics separately
        if "deepeval" in result.get("metrics", {}):
            deepeval_record = {
                "incident_id": incident_id,
                "stage": "report",
                "timestamp": result.get("timestamp"),
                "metrics": result["metrics"]["deepeval"]
            }
            self.deepeval_history.append(deepeval_record)
        self._save_history()
        return result

    def get_incident_evaluation(self, incident_id: str) -> Dict[str, Any]:
        """
        Get aggregated evaluation for an incident.

        Args:
            incident_id: Incident ID

        Returns:
            Aggregated metrics
        """
        incident_evals = [
            e for e in self.orchestrator_history
            if e.get("incident_id") == incident_id
        ]

        if not incident_evals:
            return {"message": f"No evaluations found for {incident_id}"}

        stages = {}
        for stage_name in ["retrieval", "generation", "root_cause", "recommendations", "report"]:
            stage_evals = [e for e in incident_evals if e.get("stage") == stage_name]
            if stage_evals:
                latest = stage_evals[-1]
                stages[stage_name] = {
                    "quality_score": latest.get("quality_score", 0.0),
                    "timestamp": latest.get("timestamp"),
                    "metrics": latest.get("metrics", {})
                }

        # Calculate overall score
        scores = [s["quality_score"] for s in stages.values() if "quality_score" in s]
        overall_score = sum(scores) / len(scores) if scores else 0.0

        return {
            "incident_id": incident_id,
            "overall_quality_score": overall_score,
            "stage_scores": stages,
            "num_stages_evaluated": len(stages),
            "total_evaluations": len(incident_evals)
        }

    def get_metrics_summary(self, last_n: int = 10) -> Dict[str, Any]:
        """
        Get summary of recent evaluations across all incidents.

        Args:
            last_n: Number of recent evaluations to summarize

        Returns:
            Summary statistics
        """
        if not self.orchestrator_history:
            return {"message": "No evaluation metrics available"}

        recent = self.orchestrator_history[-last_n:]

        # Group by stage
        by_stage = {}
        for eval_result in recent:
            stage = eval_result.get("stage", "unknown")
            if stage not in by_stage:
                by_stage[stage] = []
            by_stage[stage].append(eval_result)

        # Calculate averages per stage
        stage_summaries = {}
        for stage, evals in by_stage.items():
            scores = [e.get("quality_score", 0) for e in evals]
            stage_summaries[stage] = {
                "count": len(evals),
                "average_score": round(sum(scores) / len(scores), 3) if scores else 0,
                "min_score": round(min(scores), 3) if scores else 0,
                "max_score": round(max(scores), 3) if scores else 0,
            }

        # Get unique incidents
        incidents = set(e.get("incident_id") for e in recent)

        return {
            "total_evaluations": len(self.orchestrator_history),
            "recent_count": len(recent),
            "unique_incidents": len(incidents),
            "by_stage": stage_summaries,
            "quality_trend": self._calculate_trend(recent)
        }

    def _calculate_trend(self, recent: List[Dict]) -> str:
        """Calculate if quality is improving or declining."""
        if len(recent) < 2:
            return "insufficient_data"

        scores = [e.get("quality_score", 0) for e in recent]
        first_half_avg = sum(scores[:len(scores)//2]) / max(1, len(scores)//2)
        second_half_avg = sum(scores[len(scores)//2:]) / max(1, len(scores) - len(scores)//2)

        diff = second_half_avg - first_half_avg
        if diff > 0.05:
            return "improving"
        elif diff < -0.05:
            return "declining"
        else:
            return "stable"

    def get_quality_recommendations(self, incident_id: str) -> List[str]:
        """
        Get recommendations for improving quality.

        Args:
            incident_id: Incident ID

        Returns:
            List of recommendations
        """
        eval_result = self.get_incident_evaluation(incident_id)
        recommendations = []

        if eval_result.get("message"):
            return ["No evaluations available"]

        for stage, score_info in eval_result.get("stage_scores", {}).items():
            score = score_info.get("quality_score", 0)

            if score < 0.5:
                recommendations.append(f"⚠️ {stage.upper()}: Poor quality ({score:.2f}) - needs improvement")
            elif score < 0.7:
                recommendations.append(f"📍 {stage.upper()}: Fair quality ({score:.2f}) - consider optimization")

        if not recommendations:
            recommendations.append("✅ All stages performing well")

        return recommendations

    def add_analysis_trace(
        self,
        incident_id: str,
        stages_executed: List[str],
        quality_scores: Dict[str, float],
        execution_time_seconds: Optional[float] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Add a complete analysis execution trace.

        This captures the full execution context including:
        - Which stages were executed
        - Quality scores for each stage
        - Execution timestamps and durations
        - Metadata about the analysis

        Args:
            incident_id: ID of the incident analyzed
            stages_executed: List of pipeline stages that ran
            quality_scores: Dict of stage -> quality_score mappings
            execution_time_seconds: Total execution time
            metadata: Additional metadata (e.g., model version, parameters)

        Returns:
            The trace record that was added
        """
        trace_record = {
            "incident_id": incident_id,
            "timestamp": datetime.now().isoformat(),
            "stages_executed": stages_executed,
            "num_stages": len(stages_executed),
            "quality_scores": quality_scores,
            "overall_quality_score": (
                sum(quality_scores.values()) / len(quality_scores)
                if quality_scores else 0.0
            ),
            "execution_time_seconds": execution_time_seconds,
            "metadata": metadata or {}
        }

        self.traces_history.append(trace_record)
        self._save_history()

        logger.info(
            f"✅ Analysis trace recorded for {incident_id}: "
            f"{len(stages_executed)} stages, "
            f"score={trace_record['overall_quality_score']:.2f}"
        )

        return trace_record

    def get_analysis_traces(
        self,
        incident_id: Optional[str] = None,
        last_n: int = 10
    ) -> Dict[str, Any]:
        """
        Get analysis execution traces.

        Args:
            incident_id: Filter by incident ID (optional)
            last_n: Number of recent traces to return

        Returns:
            Traces data with summary statistics
        """
        if not self.traces_history:
            return {"message": "No analysis traces available", "traces": []}

        # Filter by incident ID if provided
        traces = self.traces_history
        if incident_id:
            traces = [t for t in traces if t.get("incident_id") == incident_id]

        # Get most recent
        recent_traces = traces[-last_n:]

        # Calculate statistics
        if recent_traces:
            quality_scores = [t.get("overall_quality_score", 0) for t in recent_traces]
            execution_times = [
                t.get("execution_time_seconds", 0)
                for t in recent_traces
                if t.get("execution_time_seconds") is not None
            ]

            return {
                "incident_id": incident_id,
                "total_traces": len(traces),
                "recent_count": len(recent_traces),
                "traces": recent_traces,
                "statistics": {
                    "avg_quality_score": round(sum(quality_scores) / len(quality_scores), 3)
                    if quality_scores else 0,
                    "min_quality_score": round(min(quality_scores), 3) if quality_scores else 0,
                    "max_quality_score": round(max(quality_scores), 3) if quality_scores else 0,
                    "avg_execution_time_seconds": round(
                        sum(execution_times) / len(execution_times), 2
                    ) if execution_times else 0,
                    "most_common_stages": self._get_most_common_stages(recent_traces),
                }
            }

        return {"message": "No analysis traces found", "traces": []}

    def _get_most_common_stages(self, traces: List[Dict]) -> List[str]:
        """Get the most commonly executed stages from recent traces."""
        stage_counts = {}
        for trace in traces:
            for stage in trace.get("stages_executed", []):
                stage_counts[stage] = stage_counts.get(stage, 0) + 1

        # Sort by frequency
        sorted_stages = sorted(stage_counts.items(), key=lambda x: x[1], reverse=True)
        return [stage for stage, _ in sorted_stages[:5]]  # Top 5 stages

    def reset_history(self):
        """Clear evaluation history."""
        self.orchestrator_history = []
        self.traces_history = []
        self._save_history()
        logger.info("✅ Evaluation history cleared")
