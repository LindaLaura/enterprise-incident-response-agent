"""
Multi-step incident analysis chain.

Orchestrates the prompt chain for incident analysis:
1. Extract key information from logs
2. Analyze root cause
3. Generate recommendations
4. Structure final report
"""

from typing import Dict, Any
import json
from prompts import STRUCTURE_REPORT_PROMPT, EXTRACT_INFORMATION_PROMPT, ANALYZE_ROOT_CAUSE_PROMPT, GENERATE_RECOMMENDATIONS_PROMPT


class IncidentAnalysisChain:
    """Multi-step chain for analyzing incidents."""

    def __init__(self, llm_client):
        """
        Initialize the analysis chain.

        Args:
            llm_client: LLM client (OpenAI or Anthropic)
        """
        self.llm = llm_client

    def analyze(self, log_content: str) -> Dict[str, Any]:
        """
        Run the full incident analysis chain.

        Args:
            log_content: Raw incident log text

        Returns:
            Structured incident report as dict
        """
        # Implement multi-step chain
        # Step 1: Extract information
        # Step 2: Analyze root cause
        # Step 3: Generate recommendations
        # Step 4: Structure report
   
        try:
            print("  Step 1/4: Extracting key information...")
            extracted_info = self._extract_information(log_content)

            print("  Step 2/4: Analyzing root cause...")
            root_cause = self._analyze_root_cause(extracted_info)

            print("  Step 3/4: Generating recommendations...")
            recommendations = self._generate_recommendations(root_cause)

            print("  Step 4/4: Structuring report...")
            report = self._structure_report(extracted_info, root_cause_analysis=root_cause, recommendations=recommendations)

            return report

        except Exception as e:
            return {
                "error": "Analysis failed",
                "message": str(e)
            }

    def _extract_information(self, log_content: str) -> str:
        """Extract key information from logs."""

        prompt = EXTRACT_INFORMATION_PROMPT.format(log_content=log_content)
        response = self.llm.generate(prompt)
        return response

    def _analyze_root_cause(self, extracted_info: str) -> str:
        """Analyze root cause based on extracted info."""

        prompt = ANALYZE_ROOT_CAUSE_PROMPT.format(extracted_info = extracted_info)
        response = self.llm.generate(prompt)
        return response

    def _generate_recommendations(self, root_cause_analysis: str) -> str:
        """Generate remediation recommendations."""

        prompt = GENERATE_RECOMMENDATIONS_PROMPT.format(root_cause_analysis=root_cause_analysis)
        response = self.llm.generate(prompt)
        return response

    def _structure_report(self, extracted_info: str, root_cause_analysis: str, recommendations: str) -> Dict[str, Any]:
        """Structure the final JSON report."""

        prompt = STRUCTURE_REPORT_PROMPT.format(
            extracted_info=extracted_info,
            root_cause_analysis=root_cause_analysis,
            recommendations=recommendations
        )
        response = self.llm.generate(prompt)


        cleaned_response = response.strip()

        if cleaned_response.startswith("```json"):
            cleaned_response = cleaned_response.removeprefix("```json").strip()

        if cleaned_response.startswith("```"):
            cleaned_response = cleaned_response.removeprefix("```").strip()

        if cleaned_response.endswith("```"):
            cleaned_response = cleaned_response.removesuffix("```").strip()

        report = json.loads(cleaned_response)

        try:
            report = json.loads(cleaned_response)
            return report
        except json.JSONDecodeError as e:
            return {
                "error": "Failed to parse JSON",
                "raw_response": response,
                "parse_error": str(e)
            }