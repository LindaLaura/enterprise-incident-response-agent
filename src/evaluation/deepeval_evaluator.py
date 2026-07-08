"""
DeepEval Evaluator for LLM Output Quality Assessment

Evaluates LLM-generated incident analysis outputs:
- Root cause analysis: factuality, coherence, completeness
- Recommendations: actionability, clarity, relevance
- Overall report: comprehensiveness, accuracy
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime
from deepeval.metrics import (
    FaithfulnessMetric,
    AnswerRelevancyMetric,
    ContextualRelevancyMetric,
    HallucinationMetric,
    ToxicityMetric
)
from deepeval.test_case import LLMTestCase

logger = logging.getLogger(__name__)


class ActionabilityMetric:
    """Custom metric: Are recommendations actionable?"""

    def __init__(self):
        self.name = "Actionability"
        self.threshold = 0.7

    def measure(self, recommendation: str) -> float:
        """
        Measure if recommendation is actionable.

        Checks for:
        - WHO: Who should perform this action?
        - WHAT: What specific action?
        - WHEN: When should it be done?
        - HOW: How to do it?
        """
        score = 0.0
        has_who = any(w in recommendation.lower() for w in ["team", "engineer", "ops", "admin", "manager"])
        has_what = any(w in recommendation.lower() for w in ["execute", "perform", "run", "check", "verify", "restart", "deploy"])
        has_when = any(w in recommendation.lower() for w in ["immediately", "within", "before", "after", "first", "next", "hours", "minutes"])
        has_how = any(w in recommendation.lower() for w in ["using", "with", "by", "via", "through", "execute", "command", "script"])

        # Score: 1 point per element found
        if has_what:
            score += 0.25  # WHAT is most critical
        if has_who:
            score += 0.25
        if has_when:
            score += 0.25
        if has_how:
            score += 0.25

        return min(score, 1.0)


class ComprehensivenessMetric:
    """Custom metric: Is the report comprehensive?"""

    def __init__(self):
        self.name = "Comprehensiveness"
        self.threshold = 0.7
        self.required_fields = [
            "incident_id",
            "summary",
            "root_cause",
            "affected_services",
            "recommendations",
            "severity",
            "status"
        ]

    def measure(self, report: Dict[str, Any]) -> float:
        """
        Measure comprehensiveness of incident report.

        Checks for:
        - All required fields present
        - Non-empty values
        - Sufficient detail (word count)
        """
        score = 0.0
        total_checks = len(self.required_fields) + 2  # +2 for detail and evidence

        # Check required fields
        fields_present = 0
        for field in self.required_fields:
            if field in report and report[field]:
                fields_present += 1

        score += (fields_present / len(self.required_fields)) * 0.7

        # Check for sufficient detail
        summary = str(report.get("summary", ""))
        root_cause = str(report.get("root_cause", ""))
        detail_text = summary + " " + root_cause

        if len(detail_text.split()) > 50:  # At least 50 words
            score += 0.15

        # Check for evidence/supporting info
        if report.get("root_cause_analysis", {}).get("supporting_evidence"):
            score += 0.15

        return min(score, 1.0)


class DeepEvalEvaluator:
    """Evaluates LLM outputs using DeepEval framework."""

    def __init__(self, eval_dir: Optional[str] = None):
        """
        Initialize DeepEval evaluator.

        Args:
            eval_dir: Directory to store evaluation results
        """
        self.eval_dir = Path(eval_dir or "memory/evaluation")
        self.eval_dir.mkdir(parents=True, exist_ok=True)
        self.metrics_file = self.eval_dir / "deepeval_metrics.json"
        self.metrics_history = self._load_metrics_history()

        # Initialize metrics
        self.faithfulness = FaithfulnessMetric()
        self.answer_relevancy = AnswerRelevancyMetric()
        self.hallucination = HallucinationMetric()
        self.toxicity = ToxicityMetric()
        self.actionability = ActionabilityMetric()
        self.comprehensiveness = ComprehensivenessMetric()

    def _load_metrics_history(self) -> List[Dict]:
        """Load existing metrics from file."""
        if self.metrics_file.exists():
            try:
                with open(self.metrics_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"Failed to load metrics history: {e}")
        return []

    def _save_metrics(self):
        """Save metrics history to file."""
        try:
            with open(self.metrics_file, 'w') as f:
                json.dump(self.metrics_history, f, indent=2, default=str)
        except Exception as e:
            logger.error(f"Failed to save metrics: {e}")

    def evaluate_root_cause(
        self,
        root_cause: str,
        retrieved_context: List[str],
        incident_id: str
    ) -> Dict[str, Any]:
        """
        Evaluate root cause analysis.

        Args:
            root_cause: Generated root cause explanation
            retrieved_context: Retrieved documents used
            incident_id: Incident ID for tracking

        Returns:
            Evaluation scores
        """
        logger.info(f"📊 Evaluating root cause for {incident_id}")

        try:
            # Create test case
            context_str = " ".join(retrieved_context[:3])  # Top 3 docs
            test_case = LLMTestCase(
                input=f"What is the root cause of this incident?",
                actual_output=root_cause,
                retrieval_context=retrieved_context,
                expected_output="Incident root cause analysis"
            )

            # Evaluate
            faithfulness_score = self.faithfulness.measure(test_case)
            hallucination_score = 1.0 - self.hallucination.measure(test_case)  # Invert (lower is better)
            toxicity_score = 1.0 - self.toxicity.measure(test_case)  # Invert

            result = {
                "incident_id": incident_id,
                "timestamp": datetime.now().isoformat(),
                "output_type": "root_cause",
                "faithfulness": float(faithfulness_score),
                "hallucination_score": float(hallucination_score),
                "toxicity_score": float(toxicity_score),
                "aggregate_score": (
                    float(faithfulness_score) * 0.5 +
                    float(hallucination_score) * 0.3 +
                    float(toxicity_score) * 0.2
                )
            }

            logger.info(f"✅ Root cause evaluation: {result['aggregate_score']:.2f}")
            self.metrics_history.append(result)
            self._save_metrics()

            return result

        except Exception as e:
            logger.error(f"Root cause evaluation failed: {e}")
            return {
                "incident_id": incident_id,
                "output_type": "root_cause",
                "error": str(e),
                "aggregate_score": 0.0
            }

    def evaluate_recommendations(
        self,
        recommendations: List[str],
        incident_id: str,
        context: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Evaluate recommendations quality.

        Args:
            recommendations: List of generated recommendations
            incident_id: Incident ID for tracking
            context: Optional incident context

        Returns:
            Evaluation scores
        """
        logger.info(f"📊 Evaluating recommendations for {incident_id}")

        try:
            scores = []
            actionability_scores = []

            for i, rec in enumerate(recommendations):
                # Actionability check
                actionability = self.actionability.measure(rec)
                actionability_scores.append(actionability)

                # Create test case
                test_case = LLMTestCase(
                    input=f"What should we do? Context: {context or 'N/A'}",
                    actual_output=rec,
                    expected_output="Actionable recommendation"
                )

                # Evaluate
                relevancy = self.answer_relevancy.measure(test_case)
                toxicity = 1.0 - self.toxicity.measure(test_case)

                scores.append({
                    "recommendation": rec[:100],  # First 100 chars
                    "actionability": actionability,
                    "relevancy": relevancy,
                    "toxicity": toxicity,
                    "score": (actionability * 0.5 + relevancy * 0.3 + toxicity * 0.2)
                })

            avg_actionability = sum(actionability_scores) / len(actionability_scores) if actionability_scores else 0
            avg_scores = sum(s["score"] for s in scores) / len(scores) if scores else 0

            result = {
                "incident_id": incident_id,
                "timestamp": datetime.now().isoformat(),
                "output_type": "recommendations",
                "num_recommendations": len(recommendations),
                "average_actionability": float(avg_actionability),
                "average_relevancy": float(avg_scores),
                "aggregate_score": float(avg_scores),
                "recommendation_scores": scores
            }

            logger.info(f"✅ Recommendations evaluation: {result['aggregate_score']:.2f}")
            self.metrics_history.append(result)
            self._save_metrics()

            return result

        except Exception as e:
            logger.error(f"Recommendations evaluation failed: {e}")
            return {
                "incident_id": incident_id,
                "output_type": "recommendations",
                "error": str(e),
                "aggregate_score": 0.0
            }

    def evaluate_report(
        self,
        report: Dict[str, Any],
        incident_id: str
    ) -> Dict[str, Any]:
        """
        Evaluate overall incident report.

        Args:
            report: Complete incident report
            incident_id: Incident ID for tracking

        Returns:
            Evaluation scores
        """
        logger.info(f"📊 Evaluating report for {incident_id}")

        try:
            # Comprehensiveness check
            comprehensiveness = self.comprehensiveness.measure(report)

            # Check summary/description
            summary = report.get("summary", "")
            test_case = LLMTestCase(
                input="Summarize this incident",
                actual_output=summary,
                expected_output="Clear incident summary"
            )

            answer_relevancy = self.answer_relevancy.measure(test_case)
            toxicity = 1.0 - self.toxicity.measure(test_case)

            result = {
                "incident_id": incident_id,
                "timestamp": datetime.now().isoformat(),
                "output_type": "report",
                "comprehensiveness": float(comprehensiveness),
                "summary_relevancy": float(answer_relevancy),
                "toxicity_score": float(toxicity),
                "aggregate_score": (
                    float(comprehensiveness) * 0.4 +
                    float(answer_relevancy) * 0.4 +
                    float(toxicity) * 0.2
                ),
                "required_fields_present": len([
                    f for f in self.comprehensiveness.required_fields
                    if f in report and report[f]
                ]) / len(self.comprehensiveness.required_fields)
            }

            logger.info(f"✅ Report evaluation: {result['aggregate_score']:.2f}")
            self.metrics_history.append(result)
            self._save_metrics()

            return result

        except Exception as e:
            logger.error(f"Report evaluation failed: {e}")
            return {
                "incident_id": incident_id,
                "output_type": "report",
                "error": str(e),
                "aggregate_score": 0.0
            }

    def get_metrics_summary(self, last_n: int = 10) -> Dict[str, Any]:
        """
        Get summary of recent evaluations.

        Args:
            last_n: Number of recent evaluations

        Returns:
            Summary statistics
        """
        if not self.metrics_history:
            return {"message": "No evaluation metrics available"}

        recent = self.metrics_history[-last_n:]

        # Group by output type
        by_type = {}
        for metric in recent:
            output_type = metric.get("output_type", "unknown")
            if output_type not in by_type:
                by_type[output_type] = []
            by_type[output_type].append(metric)

        # Calculate averages per type
        summaries = {}
        for output_type, metrics in by_type.items():
            avg_score = sum(m.get("aggregate_score", 0) for m in metrics) / len(metrics)
            summaries[output_type] = {
                "count": len(metrics),
                "average_score": round(avg_score, 3),
                "samples": [
                    {
                        "incident_id": m["incident_id"],
                        "score": round(m.get("aggregate_score", 0), 3),
                        "timestamp": m.get("timestamp")
                    }
                    for m in metrics[-3:]  # Last 3
                ]
            }

        return {
            "total_evaluations": len(self.metrics_history),
            "recent_count": len(recent),
            "by_output_type": summaries,
            "overall_trend": self._calculate_trend(recent)
        }

    def _calculate_trend(self, recent: List[Dict]) -> str:
        """Calculate if metrics are improving or declining."""
        if len(recent) < 2:
            return "insufficient_data"

        first_half_avg = sum(
            m.get("aggregate_score", 0) for m in recent[:len(recent)//2]
        ) / max(1, len(recent)//2)

        second_half_avg = sum(
            m.get("aggregate_score", 0) for m in recent[len(recent)//2:]
        ) / max(1, len(recent) - len(recent)//2)

        diff = second_half_avg - first_half_avg
        if diff > 0.05:
            return "improving"
        elif diff < -0.05:
            return "declining"
        else:
            return "stable"

    def reset_history(self):
        """Clear evaluation history."""
        self.metrics_history = []
        self._save_metrics()
        logger.info("✅ DeepEval history cleared")
