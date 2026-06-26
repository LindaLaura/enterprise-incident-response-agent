"""
Prompt templates for incident analysis chain.
"""


EXTRACT_INFORMATION_PROMPT = """
You are analyzing an incident log. Extract the following key information:

Incident Log:
{log_content}

Please extract and return:
1. Timestamp (when the incident started)
2. Affected services/components
3. Error types and messages
4. Severity level
5. Any patterns or repeated failures

Format your response as structured data.
"""


ANALYZE_ROOT_CAUSE_PROMPT = """
Based on the following incident information, analyze the root cause:

{extracted_info}

IMPORTANT INSTRUCTIONS:
- The information above may include log data, retrieved documentation, and past incident context
- Clearly identify which information comes from: logs, documentation, or memory
- Do NOT invent facts not supported by the provided information
- Focus on evidence-based analysis

Provide:
1. Most likely root cause
2. Contributing factors
3. Confidence level (low/medium/high)
4. Supporting evidence (cite source: logs, docs, or memory)

Be specific and technical in your analysis.
"""


GENERATE_RECOMMENDATIONS_PROMPT = """
Based on this incident analysis:

{root_cause_analysis}

IMPORTANT INSTRUCTIONS:
- The analysis above may include documentation from runbooks and past incidents
- Reference specific documentation when applicable
- Do NOT invent procedures not mentioned in the context
- Base recommendations on proven best practices from the documentation

Generate:
1. Immediate remediation steps (to resolve the incident now)
2. Short-term fixes (to prevent recurrence this week)
3. Long-term improvements (architectural changes)
4. Monitoring and alerting recommendations

Prioritize actions by impact and effort. Cite documentation sources when available.
"""


STRUCTURE_REPORT_PROMPT = """
Create a structured incident report from this analysis:

Extracted Information:
{extracted_info}

Root Cause Analysis:
{root_cause_analysis}

Recommendations:
{recommendations}

RAG Context Used:
{rag_context}

Memory Context Used:
{memory_context}

CRITICAL INSTRUCTIONS:
- Return ONLY valid JSON (no markdown, no code blocks)
- Do NOT invent document sources or memory references
- If no RAG documents were provided, set documents_used to []
- If no memory was provided, set similar_past_incidents to []
- Clearly separate information from: logs, retrieved documents, and memory
- Do NOT add fields beyond this schema

Use this exact JSON structure:

{{
  "incident_id": "auto-generated based on timestamp",
  "incident_timestamp": "ISO 8601 format - the FIRST timestamp from the logs (when THIS incident started)",
  "events_by_severity": {{
    "CRITICAL": [
      {{"timestamp": "ISO 8601", "service": "service name from log entry"}}
    ],
    "ERROR": [
      {{"timestamp": "ISO 8601", "service": "service name from log entry"}}
    ],
    "WARN": [
      {{"timestamp": "ISO 8601", "service": "service name from log entry"}}
    ],
    "INFO": [
      {{"timestamp": "ISO 8601", "service": "service name from log entry"}}
    ]
  }},
  "severity": "LOW|MEDIUM|HIGH|CRITICAL",
  "status": "ACTIVE|INVESTIGATING|RESOLVED",
  "affected_services": ["list of services from logs"],
  "incident_summary": "brief 1-2 sentence summary",
  "source_analysis": {{
    "log_evidence": ["key facts extracted from logs only"],
    "retrieved_documents": ["list of document filenames that were actually retrieved"],
    "memory_references": ["list of similar past incident IDs if any were found"]
  }},
  "root_cause": {{
    "primary_cause": "detailed root cause description",
    "confidence_level": "LOW|MEDIUM|HIGH|CRITICAL",
    "supporting_evidence": ["evidence items with source labels: [LOGS], [DOCS], or [MEMORY]"]
  }},
  "rag_context": {{
    "documents_used": ["exact filenames of retrieved documents or empty array"],
    "most_relevant_chunks": ["brief description of what documentation was found or empty array"],
    "retrieval_confidence": "description of how relevant the retrieved docs were, or 'N/A' if none"
  }},
  "memory_context": {{
    "similar_past_incidents": ["incident IDs and brief descriptions if any were found, or empty array"],
    "user_preferences_used": ["any user preferences that influenced the analysis, or empty array"],
    "previous_recommendations": ["relevant recommendations from past incidents if any, or empty array"]
  }},
  "timeline": [
    {{
      "timestamp": "ISO 8601",
      "event": "event description",
      "component": "service/component name",
      "severity": "severity level"
    }}
  ],
  "recommendations": {{
    "immediate_actions": ["actions to take now"],
    "short_term_fixes": ["fixes for this week"],
    "long_term_improvements": ["architectural changes"]
  }},
  "next_steps": ["prioritized list of next actions"],
  "metadata": {{
    "model_provider": "openai or anthropic",
    "rag_enabled": true,
    "memory_enabled": true,
    "total_incidents_in_memory": 0,
    "generated_at": "will be automatically populated with current timestamp"
  }}
}}
"""
