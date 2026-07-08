# LangSmith Integration Guide

## Overview

Complete LangSmith integration for tracking evaluation metrics and incident analysis traces as datasets.

## Setup

### 1. Configure LangSmith API Key

Add to `.env`:

```bash
LANGSMITH_API_KEY=your_langsmith_api_key_here
LANGSMITH_PROJECT=enterprise-incident-response-agent
LANGSMITH_ENDPOINT=https://api.smith.langchain.com
```

Get your API key from: https://smith.langchain.com/

### 2. Verify Integration

```bash
curl http://localhost:8000/api/langsmith/status
```

Response:

```json
{
  "status": "success",
  "langsmith": {
    "enabled": true,
    "available": true,
    "project": "enterprise-incident-response-agent",
    "api_key_set": true
  },
  "datasets_enabled": true
}
```

## Datasets Created

When LangSmith is enabled, the following datasets are automatically created:

1. **`orchestrator_metrics`** - Unified evaluation metrics from orchestrator
2. **`ragas_metrics`** - RAG evaluation metrics (retrieval & generation quality)
3. **`deepeval_metrics`** - DeepEval metrics (LLM output quality)
4. **`analysis_traces`** - Complete incident analysis execution traces

## API Endpoints

### 1. Export Metrics to LangSmith

Export all evaluation metrics to LangSmith datasets:

```bash
curl -X POST http://localhost:8000/api/langsmith/export-metrics
```

Response:

```json
{
  "status": "success",
  "exported_files": {
    "orchestrator_metrics.json": true,
    "ragas_metrics.json": true,
    "deepeval_metrics.json": true
  }
}
```

### 2. Create Custom Dataset

```bash
curl -X POST http://localhost:8000/api/langsmith/create-dataset \
  -H "Content-Type: application/json" \
  -d '{
    "name": "custom_evaluations",
    "description": "Custom evaluation dataset"
  }'
```

Response:

```json
{
  "status": "success",
  "dataset_id": "abc123...",
  "name": "custom_evaluations"
}
```

### 3. Log Evaluation to Dataset

```bash
curl -X POST http://localhost:8000/api/langsmith/log-evaluation \
  -H "Content-Type: application/json" \
  -d '{
    "dataset_id": "abc123...",
    "inputs": {
      "incident_id": "INC-2024-001",
      "stage": "retrieval",
      "query": "What is the root cause?"
    },
    "outputs": {
      "quality_score": 0.85,
      "context_precision": 0.9
    },
    "metadata": {
      "timestamp": "2024-07-07T10:30:00Z",
      "model": "claude-opus-4-8"
    }
  }'
```

### 4. Export Incident Analysis to LangSmith

```bash
curl -X POST http://localhost:8000/api/langsmith/export-incident \
  -H "Content-Type: application/json" \
  -d '{
    "incident_id": "INC-2024-001",
    "stages": {
      "retrieval": {"docs_found": 3},
      "root_cause": {"primary_cause": "Database timeout"},
      "recommendations": {"num_recommendations": 2}
    },
    "evaluations": {
      "retrieval": 0.85,
      "root_cause": 0.82,
      "recommendations": 0.88
    },
    "overall_quality": 0.85
  }'
```

### 5. Check LangSmith Status

```bash
curl http://localhost:8000/api/langsmith/status
```

## Python Integration

### Direct Integration

```python
from src.langsmith_integration import LangSmithDatasetTracker, LangSmithEvaluationExporter

# Initialize tracker
tracker = LangSmithDatasetTracker()

# Create dataset
dataset_id = tracker.create_evaluation_dataset(
    name="my_evaluations",
    description="My evaluation dataset"
)

# Log examples
tracker.log_evaluation_example(
    dataset_id=dataset_id,
    inputs={"query": "test", "incident_id": "INC-001"},
    outputs={"quality_score": 0.85},
    metadata={"model": "gpt-4"}
)

# Export metrics batch
exporter = LangSmithEvaluationExporter(tracker)
exporter.export_evaluation_metrics(Path("memory/evaluation/orchestrator_metrics.json"))
```

### Automatic Integration with Analysis Service

```python
from src.services.analysis_service import AnalysisService

# Run analysis
service = AnalysisService()
result = await service.run_analysis(
    logs="ERROR: Database timeout",
    incident_id="INC-2024-001"
)

# Manually export to LangSmith
from src.langsmith_integration import LangSmithDatasetTracker
tracker = LangSmithDatasetTracker()
tracker.log_analysis_trace(
    incident_id=result["incident_id"],
    stages=result.get("stages", {}),
    evaluations=result.get("evaluations", {}),
    overall_quality=result.get("overall_quality", {}).get("overall_quality_score", 0)
)
```

## Workflow: Complete End-to-End

### 1. Run Analysis

```bash
curl -X POST http://localhost:8000/api/analysis/run \
  -H "Content-Type: application/json" \
  -d '{
    "logs": "ERROR: System failure",
    "incident_id": "INC-2024-001",
    "use_langgraph": true
  }'
```

### 2. Export Metrics to LangSmith

```bash
curl -X POST http://localhost:8000/api/langsmith/export-metrics
```

### 3. Export Incident to LangSmith Trace

```bash
curl -X POST http://localhost:8000/api/langsmith/export-incident \
  -H "Content-Type: application/json" \
  -d '{
    "incident_id": "INC-2024-001",
    "stages": {...},
    "evaluations": {...},
    "overall_quality": 0.85
  }'
```

### 4. View in LangSmith Dashboard

Go to: https://smith.langchain.com/

- **Datasets tab**: See all exported datasets
  - `orchestrator_metrics` - All evaluation metrics
  - `ragas_metrics` - RAG quality metrics
  - `deepeval_metrics` - LLM output quality
  - `analysis_traces` - Individual incident traces

- **Traces tab**: See all incident analysis traces
  - Each trace includes stages, evaluations, quality scores

- **Runs tab**: See individual API call traces

## Dataset Structure

### Orchestrator Metrics Dataset

Input fields:
- `incident_id` - Incident identifier
- `stage` - Pipeline stage (retrieval, root_cause, recommendations, etc.)
- `timestamp` - When evaluation occurred

Output fields:
- `quality_score` - Aggregated quality (0.0 - 1.0)
- `metrics` - Framework-specific metrics

Example:
```json
{
  "inputs": {
    "incident_id": "INC-2024-001",
    "stage": "retrieval",
    "timestamp": "2024-07-07T10:30:00Z"
  },
  "outputs": {
    "quality_score": 0.85,
    "metrics": {
      "context_precision": 0.9,
      "context_recall": 0.8
    }
  }
}
```

### RAGAS Metrics Dataset

Tracks RAG system quality:

Output fields:
- `context_precision` - % of retrieved docs that are relevant
- `context_recall` - % of relevant docs retrieved
- `faithfulness` - Is answer faithful to context?
- `answer_relevance` - Does answer address query?

### DeepEval Metrics Dataset

Tracks LLM output quality:

Output fields:
- `faithfulness` - Based on retrieved context
- `hallucination_score` - Penalizes made-up info
- `toxicity_score` - Checks for harmful content
- `actionability` - For recommendations
- `comprehensiveness` - For reports

### Analysis Traces

Each trace includes:
- Incident ID
- All stages and outputs
- Evaluation results per stage
- Overall quality score
- Execution time

## Querying Datasets in LangSmith

### Via UI

1. Go to https://smith.langchain.com/
2. Click "Datasets" tab
3. Select dataset (e.g., "orchestrator_metrics")
4. View, filter, and search examples

### Via API

```python
from langsmith import Client

client = Client()

# List datasets
for dataset in client.list_datasets():
    print(f"Dataset: {dataset.name}")

# Get examples from dataset
examples = client.list_examples(dataset_name="orchestrator_metrics")
for example in examples:
    print(example)
```

## Troubleshooting

### LangSmith not enabled

**Error**: "LangSmith not configured"

**Fix**:
1. Set `LANGSMITH_API_KEY` in `.env`
2. Set `LANGSMITH_PROJECT` in `.env`
3. Restart API server

### API key not working

**Error**: "Failed to initialize LangSmith"

**Fix**:
1. Verify API key at https://smith.langchain.com/
2. Check key has not been revoked
3. Try creating a new key

### Datasets not created

**Error**: Datasets don't appear in LangSmith UI

**Fix**:
1. Check `LANGSMITH_API_KEY` is set
2. Run `/api/langsmith/export-metrics` manually
3. Check logs: `grep -i langsmith logs.txt`

## Performance Notes

- Exporting large metric files (>1000 examples) may take time
- Use `/api/langsmith/export-metrics` in background job for production
- Datasets are created once per project and reused

## Data Retention

LangSmith datasets are retained according to your plan:
- **Free tier**: 30 days
- **Plus tier**: 1 year
- **Enterprise**: Custom retention

## Security

- API keys are kept in `.env` (not committed to git)
- Data sent to LangSmith is encrypted
- See LangSmith privacy policy: https://smith.langchain.com/privacy

## Next Steps

1. Set up API key in `.env`
2. Run `/api/langsmith/status` to verify
3. Run some analyses
4. Export metrics: `curl -X POST http://localhost:8000/api/langsmith/export-metrics`
5. View datasets in LangSmith UI

## Files

- `src/langsmith_integration.py` - LangSmith integration implementation
- `src/langsmith_config.py` - LangSmith configuration
- `.env.example` - Configuration template (includes LANGSMITH_* settings)
