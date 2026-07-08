# Complete Framework Implementation Guide

## Overview

This document outlines the complete implementation of LangGraph, DeepEval, and RAGAS frameworks in the Enterprise Incident Response Agent.

## ✅ What Has Been Implemented

### 1. **Evaluation Orchestrator** (`src/evaluation/evaluation_orchestrator.py`)

Unified orchestration layer that aggregates metrics from DeepEval and RAGAS across the entire pipeline.

**Key Components:**
- `evaluate_retrieval_stage()` - RAGAS-based retrieval quality assessment
- `evaluate_generation_stage()` - RAGAS-based answer quality assessment
- `evaluate_root_cause_stage()` - DeepEval-based root cause analysis quality
- `evaluate_recommendations_stage()` - DeepEval-based recommendation quality
- `evaluate_report_stage()` - DeepEval-based final report comprehensiveness
- `get_incident_evaluation()` - Aggregated metrics across all stages
- `get_quality_recommendations()` - Actionable improvement suggestions

**Storage:**
- Metrics saved to `memory/evaluation/orchestrator_metrics.json`
- Full history preserved for trend analysis

### 2. **Analysis Service** (`src/services/analysis_service.py`)

Comprehensive service orchestrating the complete incident analysis pipeline.

**Key Features:**
- **Dual Execution Modes:**
  - LangGraph-based orchestration (graph execution with state management)
  - Traditional agent pipeline (sequential execution)
  
- **Evaluation Integration:**
  - Each stage automatically evaluated using appropriate framework
  - Metrics aggregated during execution
  - Quality scores computed per stage

- **Checkpoint & Resume:**
  - Thread-based checkpoint management
  - Ability to resume interrupted analyses

**Main Methods:**
- `run_analysis()` - Execute full pipeline with evaluation
- `get_analysis_status()` - Check analysis progress
- `get_analysis_result()` - Retrieve completed analysis
- `list_analyses()` - List recent analyses

### 3. **LangGraph Integration** (Existing in `src/agents/langgraph_manager.py`)

Pre-existing graph-based orchestration that is now fully integrated:

**Graph Structure:**
```
START → parse → retrieve → confidence_check
                            ├─ (low confidence) → re_retrieve
                            └─ (good confidence) → memory
                                                 ├─ reason
                                                 └─ recommend
                                                     ↓
                                                  report
                                                     ↓
                                                   END
```

**Features:**
- Conditional routing based on retrieval confidence
- Parallel branches for reasoning and recommendations
- SqliteSaver checkpoints for resumable analysis
- State management via AnalysisState dataclass

### 4. **API Endpoints** (Updated `src/api/main.py`)

New endpoints for executing analyses and retrieving evaluation metrics:

#### Analysis Endpoints
- `POST /api/analysis/run` - Execute analysis with evaluation
- `GET /api/analysis/{incident_id}/status` - Check analysis status
- `GET /api/analysis/{incident_id}/result` - Get full result
- `GET /api/analysis/list` - List recent analyses

#### Evaluation Endpoints
- `GET /api/evaluation/incident/{incident_id}` - Aggregated incident evaluation
- `GET /api/evaluation/summary` - Summary across all incidents
- `GET /api/evaluation/recommendations/{incident_id}` - Quality recommendations
- `GET /api/evaluation/metrics` - Unified metrics from all frameworks

#### Existing Metrics Endpoints (Enhanced)
- `GET /api/metrics/ragas` - RAGAS metrics summary
- `GET /api/metrics/deepeval` - DeepEval metrics summary
- `GET /api/metrics/all` - All frameworks unified

### 5. **Comprehensive Tests** (`tests/test_integration_full.py`)

Test coverage for all components:

**Test Classes:**
- `TestEvaluationOrchestrator` - Orchestrator functionality
- `TestAnalysisService` - Service integration
- `TestLangGraphIntegration` - Graph orchestration
- `TestEvaluationMetrics` - Metrics collection
- `TestAPIEndpoints` - API functionality
- `TestEndToEnd` - Complete pipeline validation

**Run Tests:**
```bash
pytest tests/test_integration_full.py -v
```

## 🚀 How to Use

### 1. Enable Frameworks in `.env`

```bash
# Evaluation Frameworks
ENABLE_RAGAS=true
ENABLE_DEEPEVAL=true
USE_LANGGRAPH=true
ENABLE_EVALUATION_ORCHESTRATOR=true
ENABLE_ANALYSIS_SERVICE=true
```

### 2. Run Analysis with Evaluation

```python
from src.services.analysis_service import AnalysisService

service = AnalysisService(rag_retriever, memory_manager, llm_client)

# Run analysis with LangGraph orchestration
result = await service.run_analysis(
    logs="ERROR: Database connection timeout...",
    incident_id="INC-2024-001",
    use_langgraph=True  # Use LangGraph for orchestration
)

# Result includes:
# - stages: Individual stage outputs
# - evaluations: Quality metrics per stage
# - overall_quality: Aggregated quality score
# - recommendations: Improvement suggestions
```

### 3. Retrieve Evaluations

```python
from src.evaluation.evaluation_orchestrator import EvaluationOrchestrator

orchestrator = EvaluationOrchestrator()

# Get incident evaluation
eval_result = orchestrator.get_incident_evaluation("INC-2024-001")
# Returns:
# {
#   "incident_id": "INC-2024-001",
#   "overall_quality_score": 0.82,
#   "stage_scores": {
#     "retrieval": {"quality_score": 0.85, ...},
#     "root_cause": {"quality_score": 0.80, ...},
#     ...
#   }
# }

# Get summary across all incidents
summary = orchestrator.get_metrics_summary(last_n=10)

# Get improvement recommendations
recommendations = orchestrator.get_quality_recommendations("INC-2024-001")
```

### 4. API Usage

```bash
# Run analysis with evaluation
curl -X POST http://localhost:8000/api/analysis/run \
  -H "Content-Type: application/json" \
  -d '{
    "logs": "ERROR: System failure detected",
    "incident_id": "INC-2024-001",
    "use_langgraph": true
  }'

# Get incident evaluation
curl http://localhost:8000/api/evaluation/incident/INC-2024-001

# Get evaluation summary
curl http://localhost:8000/api/evaluation/summary

# Get quality recommendations
curl http://localhost:8000/api/evaluation/recommendations/INC-2024-001

# Get unified metrics
curl http://localhost:8000/api/evaluation/metrics
```

## 📊 Evaluation Framework Details

### RAGAS Metrics (Retrieval & Generation Quality)

Used in stages:
- **Retrieval Stage**: Evaluates if correct documents were retrieved
  - `context_precision`: % of retrieved docs that are relevant
  - `context_recall`: % of relevant docs that were retrieved

- **Generation Stage**: Evaluates if answer is accurate
  - `faithfulness`: Is answer faithful to retrieved context?
  - `answer_relevance`: Does answer address the query?

### DeepEval Metrics (LLM Output Quality)

Used in stages:
- **Root Cause Stage**: Analyzes root cause quality
  - `faithfulness`: Based on retrieved context
  - `hallucination_score`: Penalizes made-up information
  - `toxicity_score`: Checks for harmful content

- **Recommendations Stage**: Evaluates actionability
  - `actionability`: Checks for WHO, WHAT, WHEN, HOW
  - `relevancy`: Are recommendations relevant to incident?
  - `toxicity_score`: Checks for harmful content

- **Report Stage**: Evaluates comprehensiveness
  - `comprehensiveness`: All required fields present?
  - `summary_relevancy`: Quality of summary
  - `toxicity_score`: Checks for harmful content

### LangGraph Orchestration

Graph-based execution provides:
- **Conditional Routing**: Re-retrieve if confidence < 0.7
- **Parallel Execution**: Memory feeds into reason + recommend
- **State Management**: AnalysisState carries context
- **Checkpoint Persistence**: Can resume from checkpoints
- **Execution Tracing**: Full execution path recorded

## 📈 Metrics Storage & History

Metrics are persisted in JSON format:

```
memory/evaluation/
├── orchestrator_metrics.json      # Unified metrics
├── ragas_metrics.json             # RAGAS evaluation history
└── deepeval_metrics.json          # DeepEval evaluation history
```

Each metric entry includes:
- `incident_id`: Which incident it evaluates
- `stage`: Which pipeline stage (retrieval, generation, root_cause, recommendations, report)
- `timestamp`: When evaluation occurred
- `quality_score`: Aggregated quality (0.0 - 1.0)
- `metrics`: Framework-specific detailed metrics

## 🔄 Data Flow

```
Logs
 ↓
[Analysis Service]
 ↓
Parser → Retriever → Memory ─→ Reasoner → Recommendations → Reporter
 ↓         ↓         ↓         ↓         ↓                    ↓
 [Eval]   [RAGAS]   [Mem]     [DeepEval][DeepEval]         [DeepEval]
 ↓         ↓         ↓         ↓         ↓                    ↓
[Orchestrator aggregates all evaluations]
 ↓
Quality Score + Recommendations + Full Analysis Result
```

## 🛠️ Configuration

See `.env.example` for all available options:

```env
# Enable/disable frameworks
ENABLE_RAGAS=true
ENABLE_DEEPEVAL=true
USE_LANGGRAPH=true
ENABLE_EVALUATION_ORCHESTRATOR=true
ENABLE_ANALYSIS_SERVICE=true

# Directories
RAGAS_EVAL_DIR=memory/evaluation
DEEPEVAL_EVAL_DIR=memory/evaluation
LANGGRAPH_CHECKPOINT_DIR=memory/checkpoints
```

## 📝 Quality Score Thresholds

Default thresholds for quality assessment:

| Level | Score Range | Interpretation |
|-------|-------------|-----------------|
| Excellent | ≥ 0.85 | Production-ready |
| Good | ≥ 0.70 | Acceptable, minor improvements |
| Acceptable | ≥ 0.50 | Needs improvement |
| Poor | < 0.50 | Critical issues |

## 🧪 Running Tests

```bash
# All integration tests
pytest tests/test_integration_full.py -v

# Specific test class
pytest tests/test_integration_full.py::TestEvaluationOrchestrator -v

# Specific test
pytest tests/test_integration_full.py::TestEvaluationOrchestrator::test_orchestrator_initialization -v

# With coverage
pytest tests/test_integration_full.py --cov=src --cov-report=html
```

## 📊 Example Analysis Result

```json
{
  "incident_id": "INC-2024-001",
  "status": "completed",
  "stages": {
    "parser": {"errors_found": 5, "warnings_found": 2, ...},
    "retriever": {"documents_found": 3, "top_results": "...", ...},
    "retrieval_evaluation": {
      "quality_score": 0.85,
      "metrics": {"ragas": {"context_precision": 0.9, ...}}
    },
    "reasoning": {"root_cause": "Database timeout", ...},
    "root_cause_evaluation": {
      "quality_score": 0.82,
      "metrics": {"deepeval": {"faithfulness": 0.8, ...}}
    },
    "recommendations": {"recommendations": ["Increase pool size", ...], ...},
    "recommendations_evaluation": {
      "quality_score": 0.88,
      "metrics": {"deepeval": {"average_actionability": 0.9, ...}}
    },
    "report": {"summary": "Analysis complete", ...},
    "report_evaluation": {
      "quality_score": 0.84,
      "metrics": {"deepeval": {"comprehensiveness": 0.85, ...}}
    }
  },
  "overall_quality": {
    "incident_id": "INC-2024-001",
    "overall_quality_score": 0.84,
    "stage_scores": {
      "retrieval": 0.85,
      "root_cause": 0.82,
      "recommendations": 0.88,
      "report": 0.84
    }
  },
  "duration_ms": 2345,
  "recommendations": [
    "✅ Retrieval performing well",
    "📍 Root Cause: Fair quality - consider optimization",
    "✅ Recommendations excellent"
  ]
}
```

## ✨ Key Improvements Over Previous Implementation

1. **Unified Evaluation**: All metrics aggregated in one place
2. **Quality Scoring**: Consistent scoring across all stages
3. **Trend Analysis**: Historical metrics for improvement tracking
4. **Actionable Recommendations**: Specific improvement suggestions
5. **LangGraph Integration**: Graph-based orchestration with conditional routing
6. **API Integration**: REST endpoints for all functionality
7. **Comprehensive Testing**: Full test coverage
8. **Production Ready**: Error handling, logging, persistence

## 🚀 Next Steps

1. **Enable evaluation flags** in `.env`:
   ```bash
   ENABLE_RAGAS=true
   ENABLE_DEEPEVAL=true
   USE_LANGGRAPH=true
   ```

2. **Test the implementation**:
   ```bash
   pytest tests/test_integration_full.py -v
   ```

3. **Run analysis with evaluation**:
   ```bash
   curl -X POST http://localhost:8000/api/analysis/run \
     -H "Content-Type: application/json" \
     -d '{"logs": "ERROR: ...", "incident_id": "INC-001"}'
   ```

4. **Monitor quality metrics**:
   ```bash
   curl http://localhost:8000/api/evaluation/metrics
   ```

## 📚 File Structure

```
src/
├── evaluation/
│   ├── evaluation_orchestrator.py    ← NEW: Unified orchestrator
│   ├── deepeval_evaluator.py         (existing)
│   ├── ragas_evaluator.py            (existing)
│   └── __init__.py
├── services/
│   ├── analysis_service.py           ← NEW: Service layer
│   ├── chatbot.py
│   └── __init__.py
├── agents/
│   ├── langgraph_manager.py          (existing)
│   ├── agents.py                     (existing)
│   └── manager.py
├── api/
│   └── main.py                       (UPDATED: New endpoints)
└── ...

tests/
└── test_integration_full.py          ← NEW: Comprehensive tests

.env.example                          (UPDATED: New config options)
```

## 🎯 Success Criteria Met

✅ LangGraph fully integrated and orchestrating pipeline
✅ Unified evaluation metrics aggregation
✅ API endpoints for analysis and evaluation
✅ Comprehensive test coverage
✅ Quality scoring and recommendations
✅ Metric persistence and history
✅ Production-ready error handling
✅ Full documentation
