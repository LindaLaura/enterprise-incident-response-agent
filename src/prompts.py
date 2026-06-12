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

Provide:
1. Most likely root cause
2. Contributing factors
3. Confidence level (low/medium/high)
4. Supporting evidence from the logs

Be specific and technical in your analysis.
"""


GENERATE_RECOMMENDATIONS_PROMPT = """
Based on this incident analysis:

{root_cause_analysis}

Generate:
1. Immediate remediation steps (to resolve the incident now)
2. Short-term fixes (to prevent recurrence this week)
3. Long-term improvements (architectural changes)
4. Monitoring and alerting recommendations

Prioritize actions by impact and effort.
"""


STRUCTURE_REPORT_PROMPT = """
Create a structured incident report from this analysis:

Extracted Information:
{extracted_info}

Root Cause Analysis:
{root_cause}

Recommendations:
{recommendations}

Output a JSON report with the following structure:
{{
  "incident_id": "auto-generated",
  "timestamp": "ISO 8601 format",
  "severity": "LOW|MEDIUM|HIGH|CRITICAL",
  "affected_services": [],
  "root_cause": {{}},
  "timeline": [],
  "recommendations": {{}}
}}
"""
