# Architecture

## System Overview

The Enterprise Incident Response Agent is a CLI-based tool that leverages LLMs to analyze incident logs and generate structured reports. The system follows a modular, pipeline-based architecture.

## High-Level Architecture

```
┌─────────────────┐
│   CLI Input     │
│  (main.py)      │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Log Parser     │
│  (validation)   │
└────────┬────────┘
         │
         ▼
┌─────────────────────────────────────┐
│    Incident Analysis Chain          │
│  ┌───────────────────────────────┐  │
│  │  Step 1: Extract Information  │  │
│  └──────────┬────────────────────┘  │
│             ▼                        │
│  ┌───────────────────────────────┐  │
│  │  Step 2: Analyze Root Cause   │  │
│  └──────────┬────────────────────┘  │
│             ▼                        │
│  ┌───────────────────────────────┐  │
│  │  Step 3: Generate Recommendations│ │
│  └──────────┬────────────────────┘  │
│             ▼                        │
│  ┌───────────────────────────────┐  │
│  │  Step 4: Structure Report     │  │
│  └──────────┬────────────────────┘  │
└─────────────┼───────────────────────┘
              ▼
┌─────────────────────────────┐
│   LLM Client Layer          │
│  ┌──────────┐  ┌──────────┐│
│  │ OpenAI   │  │Anthropic ││
│  │ Client   │  │ Client   ││
│  └──────────┘  └──────────┘│
└─────────────┬───────────────┘
              ▼
┌─────────────────────────────┐
│   JSON Output               │
│   (structured report)       │
└─────────────────────────────┘
```

## Core Components

### 1. CLI Entry Point (`main.py`)

**Responsibilities:**
- Parse command-line arguments
- Load incident log files
- Initialize the analysis chain
- Output results

**Interactions:**
- Reads log files from disk
- Instantiates IncidentAnalysisChain
- Writes JSON output to stdout or file

### 2. Incident Analysis Chain (`incident_chain.py`)

**Responsibilities:**
- Orchestrate the multi-step analysis pipeline
- Pass context between steps
- Handle intermediate state

**Key Methods:**
- `analyze(log_content)` - Main entry point
- `_extract_information()` - Step 1
- `_analyze_root_cause()` - Step 2
- `_generate_recommendations()` - Step 3
- `_structure_report()` - Step 4

**Design Pattern:** Pipeline pattern with sequential steps

### 3. LLM Client Layer

#### OpenAI Client (`openai_client.py`)

**Responsibilities:**
- Initialize OpenAI API connection
- Send prompts and receive responses
- Handle API errors and retries

**Configuration:**
- Model selection (GPT-4, GPT-4o)
- Temperature and token limits
- API key management

#### Anthropic Client (`anthropic_client.py`)

**Responsibilities:**
- Initialize Anthropic API connection
- Send prompts and receive responses
- Handle API errors and retries

**Configuration:**
- Model selection (Claude Opus, Sonnet)
- Temperature and token limits
- API key management

### 4. Prompt Templates (`prompts.py`)

**Responsibilities:**
- Define prompt templates for each analysis step
- Provide consistent prompt structure
- Support variable substitution

**Templates:**
- `EXTRACT_INFORMATION_PROMPT`
- `ANALYZE_ROOT_CAUSE_PROMPT`
- `GENERATE_RECOMMENDATIONS_PROMPT`
- `STRUCTURE_REPORT_PROMPT`

## Data Flow

### Input Processing

```
Raw Log File → Read from disk → Validate format → Pass to chain
```

### Analysis Pipeline

```
Step 1: Raw logs → Structured extraction → Key facts
Step 2: Key facts → Root cause analysis → Cause + Evidence
Step 3: Cause + Evidence → Recommendation engine → Action items
Step 4: All data → JSON formatter → Structured report
```

### Output Generation

```
Structured data → JSON serialization → Output (stdout/file)
```

## Configuration Management

**Environment Variables (`.env`):**
- `OPENAI_API_KEY` - OpenAI authentication
- `ANTHROPIC_API_KEY` - Anthropic authentication
- `DEFAULT_PROVIDER` - Which LLM to use by default
- `MAX_TOKENS` - Response length limit
- `TEMPERATURE` - Creativity parameter
- `RETRY_ATTEMPTS` - Number of retry attempts on failure

## Error Handling Strategy

### API Errors
- Retry with exponential backoff
- Fall back to alternate provider if available
- Log errors for debugging

### Input Validation Errors
- Validate log format before processing
- Provide clear error messages
- Suggest fixes for common issues

### Output Errors
- Validate JSON structure
- Handle partial results gracefully
- Provide fallback formatting

## Security Considerations

### API Key Management
- Never commit API keys to version control
- Use environment variables
- Support multiple authentication methods

### Input Sanitization
- Validate log file paths
- Limit file size
- Sanitize special characters

### Output Safety
- Escape JSON properly
- Validate structured output
- Prevent injection attacks

## Performance Considerations

### API Call Optimization
- Batch requests where possible
- Cache intermediate results
- Set appropriate token limits

### Latency Management
- Sequential processing for Week 1
- Future: Parallel API calls for multiple steps
- Progress indicators for long operations

## Testing Strategy

### Unit Tests
- Test each component in isolation
- Mock LLM API responses
- Validate prompt templates

### Integration Tests
- Test full pipeline with sample logs
- Verify JSON output structure
- Test error handling paths

### End-to-End Tests
- Test CLI with real log files
- Verify output correctness
- Test with both LLM providers

## Extensibility Points

### Future Enhancements

**Week 2: RAG Integration**
- Add vector database for historical incidents
- Implement similarity search
- Enhance prompts with retrieved context

**Week 3: Agent Architecture**
- Convert to autonomous agent
- Add tool use capabilities
- Implement MCP (Model Context Protocol)

**Week 4: Multi-Agent System**
- Parallel analysis agents
- Consensus mechanisms
- LangGraph orchestration

**Week 5: Production Deployment**
- API server (FastAPI)
- Containerization (Docker)
- Cloud deployment (Railway)

## Technology Stack

### Core Dependencies
- Python 3.11
- openai (OpenAI SDK)
- anthropic (Anthropic SDK)
- python-dotenv (environment management)
- click (CLI framework)

### Development Tools
- pytest (testing)
- black (code formatting)
- ruff (linting)

### Future Dependencies
- chromadb (vector database)
- langchain (agent framework)
- langgraph (multi-agent orchestration)
- fastapi (API server)

## Deployment Architecture (Future)

```
┌──────────────┐
│   Client     │
└──────┬───────┘
       │ HTTP
       ▼
┌──────────────┐
│  FastAPI     │
│  Server      │
└──────┬───────┘
       │
       ▼
┌──────────────────────────┐
│  Incident Agent System   │
│  ┌────────┐  ┌────────┐ │
│  │Agent 1 │  │Agent 2 │ │
│  └────────┘  └────────┘ │
└──────┬───────────────────┘
       │
       ▼
┌──────────────────────────┐
│  External Services       │
│  - OpenAI API            │
│  - Anthropic API         │
│  - Vector DB             │
└──────────────────────────┘
```

## Monitoring and Observability (Future)

- API call metrics
- Latency tracking
- Error rate monitoring
- Cost tracking per analysis
- Usage analytics
