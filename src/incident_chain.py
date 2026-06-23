"""
Multi-step incident analysis chain.

Orchestrates the prompt chain for incident analysis:
1. Extract key information from logs
2. Analyze root cause (with RAG context)
3. Generate recommendations (with RAG context)
4. Structure final report
"""

from typing import Dict, Any, Optional
import json
from datetime import datetime
from prompts import STRUCTURE_REPORT_PROMPT, EXTRACT_INFORMATION_PROMPT, ANALYZE_ROOT_CAUSE_PROMPT, GENERATE_RECOMMENDATIONS_PROMPT
from rag_retriever import RAGRetriever
from memory_manager import MemoryManager


class IncidentAnalysisChain:
    """Multi-step chain for analyzing incidents with RAG and Memory support."""

    def __init__(self, llm_client, use_rag: bool = True, use_memory: bool = True):
        """
        Initialize the analysis chain.

        Args:
            llm_client: LLM client (OpenAI or Anthropic)
            use_rag: Whether to use RAG for enhanced context
            use_memory: Whether to use memory for context
        """
        self.llm = llm_client
        self.use_rag = use_rag
        self.use_memory = use_memory

        # Initialize RAG retriever if enabled
        self.retriever = None
        if use_rag:
            try:
                self.retriever = RAGRetriever()
                stats = self.retriever.get_stats()
                print(f"  📚 RAG enabled: {stats['total_chunks']} chunks ({stats['embedding_type']} embeddings)")
            except Exception as e:
                print(f"  ⚠️  RAG initialization failed: {e}")
                print(f"  ℹ️  Continuing without RAG support")
                self.use_rag = False

        # Initialize memory manager if enabled
        self.memory = None
        if use_memory:
            try:
                self.memory = MemoryManager()
                stats = self.memory.get_stats()
                print(f"  🧠 Memory enabled: {stats['total_incidents']} past incidents")
            except Exception as e:
                print(f"  ⚠️  Memory initialization failed: {e}")
                print(f"  ℹ️  Continuing without memory")
                self.use_memory = False

    def analyze(self, log_content: str) -> Dict[str, Any]:
        """
        Run the full incident analysis chain with RAG and memory.

        Args:
            log_content: Raw incident log text

        Returns:
            Structured incident report as dict
        """
        # Track context used for final report
        self.rag_context_used = {"documents": [], "chunks": []}
        self.memory_context_used = {"incidents": [], "preferences": []}

        try:
            # Step 1: Extract information
            print("  Step 1/5: Extracting key information...")
            extracted_info = self._extract_information(log_content)

            # Update memory with current incident
            if self.use_memory and self.memory:
                self.memory.set_current_incident({'extracted_info': extracted_info[:200]})

            # Step 2: Analyze root cause with RAG + memory
            print("  Step 2/5: Analyzing root cause (with context)...")
            root_cause = self._analyze_root_cause(extracted_info)

            # Step 3: Generate recommendations with RAG + memory
            print("  Step 3/5: Generating recommendations (with context)...")
            recommendations = self._generate_recommendations(root_cause)

            # Step 4: Structure report
            print("  Step 4/5: Structuring final report...")
            report = self._structure_report(
                extracted_info,
                root_cause_analysis=root_cause,
                recommendations=recommendations
            )

            # Step 5: Save to memory
            if self.use_memory and self.memory and 'error' not in report:
                print("  Step 5/5: Saving to memory...")
                self._save_to_memory(report)
            else:
                print("  Step 5/5: Complete")

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
        """Analyze root cause with RAG documentation and memory context."""

        # Retrieve relevant documentation if RAG is enabled
        rag_context = ""
        if self.use_rag and self.retriever:
            try:
                chunks = self.retriever.retrieve(extracted_info, n_results=2)
                if chunks:
                    # Track what was retrieved
                    for chunk in chunks:
                        doc_name = chunk['metadata'].get('filename', 'Unknown')
                        if doc_name not in self.rag_context_used['documents']:
                            self.rag_context_used['documents'].append(doc_name)
                        self.rag_context_used['chunks'].append({
                            'source': doc_name,
                            'type': chunk['metadata'].get('doc_type', 'general')
                        })
                    rag_context = self.retriever.format_context(chunks)
            except Exception as e:
                print(f"  ⚠️  RAG retrieval failed: {e}")

        # Get memory context if enabled
        memory_context = ""
        if self.use_memory and self.memory:
            try:
                # Extract keywords for finding similar incidents
                keywords = self._extract_keywords(extracted_info)
                similar_incidents = self.memory.get_similar_incidents(keywords, limit=2)

                # Track what was retrieved
                if similar_incidents:
                    for inc in similar_incidents:
                        self.memory_context_used['incidents'].append({
                            'id': inc.get('incident_id'),
                            'summary': inc.get('summary', '')[:100]
                        })

                memory_context = self.memory.get_memory_context(
                    include_similar=True,
                    keywords=keywords
                )
            except Exception as e:
                print(f"  ⚠️  Memory retrieval failed: {e}")

        # Enhance prompt with all context
        enhanced_info = extracted_info + rag_context + memory_context
        prompt = ANALYZE_ROOT_CAUSE_PROMPT.format(extracted_info=enhanced_info)
        response = self.llm.generate(prompt)
        return response

    def _generate_recommendations(self, root_cause_analysis: str) -> str:
        """Generate remediation recommendations with RAG and memory context."""

        # Retrieve relevant best practices if RAG is enabled
        rag_context = ""
        if self.use_rag and self.retriever:
            try:
                query = root_cause_analysis + " best practices solutions remediation"
                rag_context = self.retriever.retrieve_and_format(
                    query,
                    n_results=2
                )
            except Exception as e:
                print(f"  ⚠️  RAG retrieval failed: {e}")

        # Enhance prompt with all context
        enhanced_analysis = root_cause_analysis + rag_context
        prompt = GENERATE_RECOMMENDATIONS_PROMPT.format(root_cause_analysis=enhanced_analysis)
        response = self.llm.generate(prompt)
        return response

    def _structure_report(self, extracted_info: str, root_cause_analysis: str, recommendations: str) -> Dict[str, Any]:
        """Structure the final JSON report with RAG and memory context."""

        # Format RAG context for the prompt
        rag_context_str = self._format_rag_context()

        # Format memory context for the prompt
        memory_context_str = self._format_memory_context()

        prompt = STRUCTURE_REPORT_PROMPT.format(
            extracted_info=extracted_info,
            root_cause_analysis=root_cause_analysis,
            recommendations=recommendations,
            rag_context=rag_context_str,
            memory_context=memory_context_str
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

            # Inject current timestamp and actual metadata
            if 'metadata' not in report:
                report['metadata'] = {}

            report['metadata']['generated_at'] = datetime.now().isoformat()
            report['metadata']['rag_enabled'] = self.use_rag
            report['metadata']['memory_enabled'] = self.use_memory

            if self.use_memory and self.memory:
                stats = self.memory.get_stats()
                report['metadata']['total_incidents_in_memory'] = stats['total_incidents']

            return report
        except json.JSONDecodeError as e:
            return {
                "error": "Failed to parse JSON",
                "raw_response": response,
                "parse_error": str(e)
            }
    def _format_rag_context(self) -> str:
        """Format RAG context for prompt."""
        if not self.rag_context_used['documents']:
            return "No RAG documents were retrieved."

        parts = ["RAG Documents Retrieved:"]
        for doc in self.rag_context_used['documents']:
            parts.append(f"- {doc}")
        parts.append(f"\nTotal chunks used: {len(self.rag_context_used['chunks'])}")
        return "\n".join(parts)

    def _format_memory_context(self) -> str:
        """Format memory context for prompt."""
        if not self.memory_context_used['incidents']:
            return "No similar past incidents found in memory."

        parts = ["Similar Past Incidents:"]
        for inc in self.memory_context_used['incidents']:
            parts.append(f"- {inc['id']}: {inc['summary']}")
        return "\n".join(parts)

    def _extract_keywords(self, text: str) -> list:
        """Extract keywords from text for memory search."""
        keywords = []
        common_terms = ['database', 'connection', 'kubernetes', 'deployment',
                       'api', 'timeout', 'memory', 'network', 'service']

        text_lower = text.lower()
        for term in common_terms:
            if term in text_lower:
                keywords.append(term)

        return keywords[:5]

    def _save_to_memory(self, report: Dict[str, Any]):
        """Save incident report to long-term memory."""
        try:
            self.memory.save_incident(
                incident_id=report.get('incident_id', 'unknown'),
                summary=str(report.get('affected_services', [])),
                root_cause=str(report.get('root_cause', {}).get('primary_cause', '')),
                recommendations=[str(r) for r in report.get('recommendations', {}).get('immediate_actions', [])[:3]],
                severity=report.get('severity', 'UNKNOWN'),
                affected_services=report.get('affected_services', [])
            )
        except Exception as e:
            print(f"  ⚠️  Failed to save to memory: {e}")
