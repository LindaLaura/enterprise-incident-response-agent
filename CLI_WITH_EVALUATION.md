# CLI with Evaluation & LangSmith Integration

The CLI has been updated to support evaluation metrics and LangSmith dataset export.

## Quick Start

### 1. Run analysis with evaluation (no LangSmith)

```bash
python -m src.main sample_logs/api_failure.txt
```

This will:
- ✅ Parse logs
- ✅ Run LangGraph orchestration
- ✅ Evaluate each stage (RAGAS + DeepEval)
- ✅ Save metrics locally to `memory/evaluation/`
- ✅ Display results

### 2. Run analysis AND export to LangSmith

```bash
# First, set your LangSmith API key in .env
LANGSMITH_API_KEY=your_key_from_smith.langchain.com

# Then run with --langsmith flag
python -m src.main sample_logs/api_failure.txt --langsmith
```

This will:
- ✅ Run analysis
- ✅ Evaluate each stage
- ✅ Save metrics locally
- ✅ **Export to LangSmith datasets**
- ✅ Display results + LangSmith link

### 3. Auto-export on every run

Set in `.env`:
```bash
LANGSMITH_AUTO_EXPORT=true
```

Then just run:
```bash
python -m src.main sample_logs/api_failure.txt
```

Every run will automatically export to LangSmith.

## Usage

```bash
# Basic usage
python -m src.main <log_file_path>

# With LangSmith export
python -m src.main <log_file_path> --langsmith

# Examples
python -m src.main sample_logs/api_failure.txt
python -m src.main sample_logs/db_failure.txt --langsmith
python -m src.main logs/incident-2024-07-07.txt --langsmith
```

## Configuration

Set in `.env`:

```bash
# Enable/disable frameworks
USE_LANGGRAPH=true              # Graph-based orchestration
ENABLE_RAGAS=true              # RAG evaluation
ENABLE_DEEPEVAL=true           # LLM output evaluation
ENABLE_EVALUATION_ORCHESTRATOR=true

# LangSmith (optional)
LANGSMITH_API_KEY=your_key_here
LANGSMITH_PROJECT=enterprise-incident-response-agent
LANGSMITH_AUTO_EXPORT=false    # Set to true to export every run

# Legacy chain (if you want to use old pipeline)
USE_ANALYSIS_SERVICE=true      # Set to false to use legacy chain
```

## Output Example

```
=== Log file loaded: sample_logs/api_failure.txt ===
Log size: 2456 characters

Incident ID: INC-CLI-1720337400

=== Incident Analysis ===
📊 Initializing Analysis Service...
🚀 Running analysis with evaluation...
✅ Analysis complete! (Duration: 2345ms)

=== Analysis Result ===
{
  "incident_id": "INC-CLI-1720337400",
  "status": "completed",
  "stages": {
    "parser": {...},
    "retriever": {...},
    "reasoning": {...},
    ...
  },
  "overall_quality": {
    "overall_quality_score": 0.84,
    "stage_scores": {
      "retrieval": 0.85,
      "root_cause": 0.82,
      "recommendations": 0.88,
      "report": 0.84
    }
  },
  "duration_ms": 2345
}

📤 Exporting metrics to LangSmith...
✅ Export complete!
  ✅ orchestrator_metrics.json
  ✅ ragas_metrics.json
  ✅ deepeval_metrics.json

📊 View datasets at: https://smith.langchain.com/

✅ Analysis saved with incident ID: INC-CLI-1720337400
```

## Data Flow

```
Log File
    ↓
CLI Analysis (LangGraph)
    ↓
Evaluation Stage
├─ RAGAS evaluation (retrieval quality)
├─ DeepEval evaluation (LLM output quality)
└─ Aggregated quality scores
    ↓
Local Files (memory/evaluation/)
├─ orchestrator_metrics.json
├─ ragas_metrics.json
└─ deepeval_metrics.json
    ↓ (if --langsmith flag or LANGSMITH_AUTO_EXPORT=true)
LangSmith Datasets
    ↓
LangSmith Dashboard (https://smith.langchain.com/)
```

## What Gets Exported to LangSmith

When you use `--langsmith` flag, the following datasets are created/updated:

1. **orchestrator_metrics** - Aggregated evaluations for all stages
2. **ragas_metrics** - RAG retrieval/generation quality
3. **deepeval_metrics** - LLM output quality metrics
4. **analysis_traces** - Full execution traces per incident

Each dataset contains examples with:
- **Inputs**: incident_id, stage, timestamp
- **Outputs**: quality_score, detailed metrics

## Troubleshooting

### Data not appearing in LangSmith

1. **Check API key is set**:
   ```bash
   grep LANGSMITH_API_KEY .env
   ```

2. **Verify export ran successfully**:
   ```bash
   python -m src.main sample_logs/api_failure.txt --langsmith
   # Look for: "✅ Export complete!"
   ```

3. **Check local files were created**:
   ```bash
   ls -la memory/evaluation/
   ```

4. **View LangSmith status**:
   ```bash
   curl http://localhost:8000/api/langsmith/status
   ```

### "LANGSMITH_API_KEY not set"

Add to `.env`:
```bash
LANGSMITH_API_KEY=your_key_from_smith.langchain.com
```

Get your key from: https://smith.langchain.com/

### Analysis fails

Check that frameworks are enabled in `.env`:
```bash
USE_LANGGRAPH=true
ENABLE_RAGAS=true
ENABLE_DEEPEVAL=true
```

Install dependencies:
```bash
pip install -r requirements.txt
```

## Examples

### Simple analysis
```bash
python -m src.main sample_logs/api_failure.txt
```

### Analyze and export
```bash
python -m src.main sample_logs/db_failure.txt --langsmith
```

### Analyze multiple files
```bash
for file in sample_logs/*.txt; do
  python -m src.main "$file" --langsmith
done
```

### View all metrics locally
```bash
cat memory/evaluation/orchestrator_metrics.json | python -m json.tool | head -50
```

### View datasets in LangSmith
```bash
# After running with --langsmith:
# Go to: https://smith.langchain.com/
# Click: Datasets tab
# See: orchestrator_metrics, ragas_metrics, deepeval_metrics
```

## Integration

The CLI now:
- ✅ Uses new Analysis Service (LangGraph + evaluation)
- ✅ Evaluates each pipeline stage automatically
- ✅ Saves metrics to local JSON files
- ✅ Exports to LangSmith if API key is set
- ✅ Falls back to legacy chain if `USE_ANALYSIS_SERVICE=false`

You can use the CLI to:
- Run batch analysis on multiple logs
- Automatically track evaluation metrics
- Build datasets in LangSmith for model monitoring
- Compare analysis quality across incidents
