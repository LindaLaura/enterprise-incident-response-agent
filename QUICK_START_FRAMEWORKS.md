# Quick Start: LangGraph + DeepEval + RAGAS

Get the frameworks up and running in 5 minutes.

## 1. Configure Environment

Edit `.env`:

```bash
# Enable all frameworks
ENABLE_RAGAS=true
ENABLE_DEEPEVAL=true
USE_LANGGRAPH=true
ENABLE_EVALUATION_ORCHESTRATOR=true
ENABLE_ANALYSIS_SERVICE=true
```

## 2. Install Dependencies (if needed)

All dependencies are already in `requirements.txt`:

```bash
pip install -r requirements.txt
```

Verify installation:

```bash
python -c "import ragas; import deepeval; import langgraph; print('✅ All frameworks installed')"
```

## 3. Start the API

```bash
python -m src.api.main
```

Server runs at `http://localhost:8000`

## 4. Test the Pipeline

### Option A: Run Analysis via API

```bash
curl -X POST http://localhost:8000/api/analysis/run \
  -H "Content-Type: application/json" \
  -d '{
    "logs": "ERROR: Database connection pool exhausted at 10:30:45Z. Connection timeout after 30s.",
    "incident_id": "INC-2024-001",
    "use_langgraph": true
  }'
```

Response example:

```json
{
  "status": "success",
  "incident_id": "INC-2024-001",
  "analysis": {
    "status": "completed",
    "stages": {...},
    "overall_quality": {
      "overall_quality_score": 0.84,
      "stage_scores": {
        "retrieval": 0.85,
        "root_cause": 0.82,
        ...
      }
    }
  }
}
```

### Option B: Run Tests

```bash
pytest tests/test_integration_full.py -v
```

## 5. View Metrics

### Get Evaluation Summary

```bash
curl http://localhost:8000/api/evaluation/summary
```

### Get Incident Evaluation

```bash
curl http://localhost:8000/api/evaluation/incident/INC-2024-001
```

### Get Quality Recommendations

```bash
curl http://localhost:8000/api/evaluation/recommendations/INC-2024-001
```

### Get All Metrics

```bash
curl http://localhost:8000/api/evaluation/metrics
```

## 6. Monitor Results

Check metric files:

```bash
# View evaluation history
cat memory/evaluation/orchestrator_metrics.json | python -m json.tool | head -50

# View RAGAS metrics
cat memory/evaluation/ragas_metrics.json | python -m json.tool | head -50

# View DeepEval metrics
cat memory/evaluation/deepeval_metrics.json | python -m json.tool | head -50
```

## 7. Python Integration

Run analyses directly in Python:

```python
import asyncio
from src.services.analysis_service import AnalysisService
from src.memory_manager import MemoryManager
from src.rag_retriever import RAGRetriever
from src.openai_client import OpenAIClient

# Initialize service
memory_mgr = MemoryManager()
rag = RAGRetriever()
llm = OpenAIClient()
service = AnalysisService(rag, memory_mgr, llm)

# Run analysis
async def main():
    result = await service.run_analysis(
        logs="ERROR: System failed with timeout",
        incident_id="INC-2024-002",
        use_langgraph=True
    )
    
    print(f"Status: {result['status']}")
    print(f"Quality Score: {result['overall_quality']['overall_quality_score']}")
    print(f"Recommendations: {result['recommendations']}")

asyncio.run(main())
```

## Key Endpoints Reference

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/analysis/run` | POST | Execute analysis with evaluation |
| `/api/analysis/{id}/status` | GET | Check analysis status |
| `/api/analysis/{id}/result` | GET | Get full analysis result |
| `/api/evaluation/incident/{id}` | GET | Get incident evaluation |
| `/api/evaluation/summary` | GET | Get evaluation summary |
| `/api/evaluation/recommendations/{id}` | GET | Get improvement recommendations |
| `/api/evaluation/metrics` | GET | Get all metrics |

## Troubleshooting

### Framework not available

If you see "not available" messages:

1. Check `.env` settings are enabled
2. Verify installation: `pip install -r requirements.txt`
3. Check logs for specific errors

### No metrics collected

Metrics are only collected if:
1. Framework is enabled in `.env`
2. Analysis is run with `use_langgraph=true`
3. Framework dependencies are installed

### Tests fail

Run with verbose output:

```bash
pytest tests/test_integration_full.py -vv
```

Check that all dependencies are installed:

```bash
pip list | grep -E "ragas|deepeval|langgraph"
```

## Next: Advanced Usage

See `IMPLEMENTATION_COMPLETE.md` for:
- Detailed metric explanations
- Quality score thresholds
- Custom evaluations
- Checkpoint & resume functionality
- LangSmith tracing integration
- Production deployment

## Common Use Cases

### Run analysis for incident
```bash
curl -X POST http://localhost:8000/api/analysis/run \
  -H "Content-Type: application/json" \
  -d '{"logs": "ERROR: ...", "incident_id": "INC-2024-001"}'
```

### Check quality of analysis
```bash
curl http://localhost:8000/api/evaluation/incident/INC-2024-001
```

### Get improvement suggestions
```bash
curl http://localhost:8000/api/evaluation/recommendations/INC-2024-001
```

### Monitor trends
```bash
curl http://localhost:8000/api/evaluation/summary
```

## Success Indicators

✅ All frameworks running:
```bash
curl http://localhost:8000/api/evaluation/metrics | grep enabled
```

✅ Analyses completing:
```bash
curl http://localhost:8000/api/analysis/list
```

✅ Metrics being collected:
```bash
curl http://localhost:8000/api/evaluation/summary | grep total_evaluations
```

That's it! You're ready to use LangGraph, DeepEval, and RAGAS.

For detailed configuration and advanced features, see `IMPLEMENTATION_COMPLETE.md`.
