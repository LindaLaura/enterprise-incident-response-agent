"""
Evaluation Framework Module

Provides metrics for evaluating RAG system and LLM outputs:
- RAGAS: Retrieval and generation quality
- DeepEval: LLM output quality and domain-specific metrics
"""

# Import with graceful fallback for dependency issues
try:
    from .ragas_evaluator import RAGASEvaluator
except ImportError as e:
    print(f"⚠️  RAGAS import failed: {e}")
    RAGASEvaluator = None

try:
    from .deepeval_evaluator import DeepEvalEvaluator, ActionabilityMetric, ComprehensivenessMetric
except ImportError as e:
    print(f"⚠️  DeepEval import failed: {e}")
    DeepEvalEvaluator = None
    ActionabilityMetric = None
    ComprehensivenessMetric = None

__all__ = [
    "RAGASEvaluator",
    "DeepEvalEvaluator",
    "ActionabilityMetric",
    "ComprehensivenessMetric",
]
