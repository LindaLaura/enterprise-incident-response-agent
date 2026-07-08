"""
RAGAS Evaluator for RAG System Quality Assessment

Evaluates retrieval and generation quality using RAGAS metrics:
- Context Precision: Are retrieved docs relevant to query?
- Context Recall: Were all relevant docs retrieved?
- Faithfulness: Is answer faithful to retrieved context?
- Answer Relevance: Does answer address the query?
"""

import json
import logging
import sys
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime
from datasets import Dataset
from types import ModuleType

logger = logging.getLogger(__name__)

# Patch for missing langchain_community.chat_models.vertexai
# This is needed because RAGAS 0.4.3 imports from an old langchain structure
# that's been moved/deprecated in newer versions
def _patch_missing_vertexai():
    """Monkey-patch missing ChatVertexAI to allow RAGAS to import."""
    try:
        # Create mock ChatVertexAI class
        class ChatVertexAI:
            """Mock ChatVertexAI for compatibility with RAGAS."""
            def __init__(self, *args, **kwargs):
                raise ImportError("VertexAI is not available. Use a different LLM provider.")

        # Create the module if it doesn't exist
        vertex_module = ModuleType('vertexai')
        vertex_module.ChatVertexAI = ChatVertexAI
        sys.modules['langchain_community.chat_models.vertexai'] = vertex_module
        logger.debug("✅ Created langchain_community.chat_models.vertexai module patch")
    except Exception as e:
        logger.warning(f"Could not apply vertexai patch: {e}")

_patch_missing_vertexai()

# Try to import RAGAS with fallback for missing dependencies
try:
    from ragas import evaluate
    # Note: answer_relevance doesn't exist in RAGAS 0.4.3, using answer_correctness instead
    from ragas.metrics import (
        context_precision,
        context_recall,
        faithfulness,
        answer_correctness
    )
    RAGAS_AVAILABLE = True
    logger.info("✅ RAGAS initialized successfully")
except ImportError as e:
    logger.warning(f"RAGAS not fully available (optional dependency issue): {e}")
    RAGAS_AVAILABLE = False
    # Create stub functions that return default values
    def evaluate(*args, **kwargs):
        raise RuntimeError("RAGAS is not available due to missing dependencies")

    context_precision = None
    context_recall = None
    faithfulness = None
    answer_correctness = None


class RAGASEvaluator:
    """Evaluates RAG system using RAGAS framework."""

    def __init__(self, eval_dir: Optional[str] = None):
        """
        Initialize RAGAS evaluator.

        Args:
            eval_dir: Directory to store evaluation results
        """
        if not RAGAS_AVAILABLE:
            raise RuntimeError(
                "RAGAS is not available. This is likely due to missing langchain dependencies. "
                "Try installing: pip install langchain-google-vertexai"
            )

        self.eval_dir = Path(eval_dir or "memory/evaluation")
        self.eval_dir.mkdir(parents=True, exist_ok=True)
        self.metrics_file = self.eval_dir / "ragas_metrics.json"
        self.metrics_history = self._load_metrics_history()

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

    def evaluate_retrieval(
        self,
        query: str,
        retrieved_docs: List[str],
        ground_truth: Optional[str] = None
    ) -> Dict[str, float]:
        """
        Evaluate retrieval quality.

        Args:
            query: Original query/question
            retrieved_docs: List of retrieved document chunks
            ground_truth: Expected answer (optional)

        Returns:
            Dict with context_precision and context_recall scores
        """
        try:
            # Prepare dataset for RAGAS
            data = {
                "question": [query],
                "contexts": [[retrieved_docs]],
                "ground_truths": [[ground_truth or query]]
            }
            dataset = Dataset.from_dict(data)

            # Evaluate
            result = evaluate(
                dataset,
                metrics=[context_precision, context_recall]
            )

            metrics = {
                "context_precision": float(result["context_precision"]),
                "context_recall": float(result["context_recall"]),
            }

            logger.info(f"✅ Retrieval evaluation: {metrics}")
            return metrics

        except Exception as e:
            logger.error(f"Retrieval evaluation failed: {e}")
            return {
                "context_precision": 0.0,
                "context_recall": 0.0,
                "error": str(e)
            }

    def evaluate_generation(
        self,
        query: str,
        answer: str,
        retrieved_context: List[str],
        ground_truth: Optional[str] = None
    ) -> Dict[str, float]:
        """
        Evaluate generation quality.

        Args:
            query: Original query
            answer: Generated answer
            retrieved_context: Retrieved context docs
            ground_truth: Expected answer (optional)

        Returns:
            Dict with faithfulness and answer_correctness scores
        """
        try:
            # Prepare dataset for RAGAS
            data = {
                "question": [query],
                "answer": [answer],
                "contexts": [[retrieved_context]],
                "ground_truths": [[ground_truth or answer]]
            }
            dataset = Dataset.from_dict(data)

            # Evaluate using available metrics
            # Note: answer_relevance not available in RAGAS 0.4.3, using answer_correctness
            result = evaluate(
                dataset,
                metrics=[faithfulness, answer_correctness]
            )

            metrics = {
                "faithfulness": float(result["faithfulness"]),
                "answer_correctness": float(result["answer_correctness"]),
            }

            logger.info(f"✅ Generation evaluation: {metrics}")
            return metrics

        except Exception as e:
            logger.error(f"Generation evaluation failed: {e}")
            return {
                "faithfulness": 0.0,
                "answer_correctness": 0.0,
                "error": str(e)
            }

    def evaluate_full_pipeline(
        self,
        query: str,
        retrieved_docs: List[str],
        answer: str,
        incident_id: str,
        ground_truth: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Evaluate complete RAG pipeline.

        Args:
            query: Original query
            retrieved_docs: Retrieved document chunks
            answer: Generated answer
            incident_id: ID for tracking
            ground_truth: Optional ground truth for more accurate scoring

        Returns:
            Comprehensive evaluation result with all metrics
        """
        logger.info(f"🔍 Evaluating RAG pipeline for {incident_id}")

        retrieval_metrics = self.evaluate_retrieval(
            query,
            retrieved_docs,
            ground_truth
        )

        generation_metrics = self.evaluate_generation(
            query,
            answer,
            retrieved_docs,
            ground_truth
        )

        # Calculate aggregate score
        all_scores = [
            retrieval_metrics.get("context_precision", 0),
            retrieval_metrics.get("context_recall", 0),
            generation_metrics.get("faithfulness", 0),
            generation_metrics.get("answer_correctness", 0),
        ]
        aggregate_score = sum(all_scores) / len(all_scores) if all_scores else 0

        result = {
            "incident_id": incident_id,
            "timestamp": datetime.now().isoformat(),
            "query": query,
            "num_retrieved_docs": len(retrieved_docs),
            "retrieval_metrics": retrieval_metrics,
            "generation_metrics": generation_metrics,
            "aggregate_score": aggregate_score,
            "status": self._get_quality_assessment(aggregate_score)
        }

        # Store in history
        self.metrics_history.append(result)
        self._save_metrics()

        logger.info(f"✅ Evaluation complete: score={aggregate_score:.2f}")
        return result

    def _get_quality_assessment(self, score: float) -> str:
        """Get quality assessment based on score."""
        if score >= 0.85:
            return "excellent"
        elif score >= 0.70:
            return "good"
        elif score >= 0.50:
            return "acceptable"
        else:
            return "poor"

    def get_metrics_summary(self, last_n: int = 10) -> Dict[str, Any]:
        """
        Get summary of recent evaluations.

        Args:
            last_n: Number of recent evaluations to summarize

        Returns:
            Summary statistics
        """
        if not self.metrics_history:
            return {"message": "No evaluation metrics available"}

        recent = self.metrics_history[-last_n:]

        # Calculate averages
        avg_precision = sum(
            m["retrieval_metrics"].get("context_precision", 0)
            for m in recent
        ) / len(recent)

        avg_recall = sum(
            m["retrieval_metrics"].get("context_recall", 0)
            for m in recent
        ) / len(recent)

        avg_faithfulness = sum(
            m["generation_metrics"].get("faithfulness", 0)
            for m in recent
        ) / len(recent)

        avg_correctness = sum(
            m["generation_metrics"].get("answer_correctness", 0)
            for m in recent
        ) / len(recent)

        avg_aggregate = sum(
            m["aggregate_score"] for m in recent
        ) / len(recent)

        return {
            "total_evaluations": len(self.metrics_history),
            "recent_count": len(recent),
            "average_context_precision": round(avg_precision, 3),
            "average_context_recall": round(avg_recall, 3),
            "average_faithfulness": round(avg_faithfulness, 3),
            "average_answer_correctness": round(avg_correctness, 3),
            "average_aggregate_score": round(avg_aggregate, 3),
            "quality_trend": self._calculate_trend(recent)
        }

    def _calculate_trend(self, recent: List[Dict]) -> str:
        """Calculate if metrics are improving or declining."""
        if len(recent) < 2:
            return "insufficient_data"

        first_half_avg = sum(
            m["aggregate_score"] for m in recent[:len(recent)//2]
        ) / (len(recent)//2)

        second_half_avg = sum(
            m["aggregate_score"] for m in recent[len(recent)//2:]
        ) / (len(recent) - len(recent)//2)

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
        logger.info("✅ Evaluation history cleared")
