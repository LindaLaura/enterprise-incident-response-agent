"""
Concrete agent implementations for incident response pipeline.
"""

import asyncio
import logging
from typing import Any, Dict, List
from .base import Agent

logger = logging.getLogger(__name__)


class ParserAgent(Agent):
    """Parses and extracts information from logs."""

    def __init__(self):
        super().__init__(
            name="Parser Agent",
            description="Extracts key information from logs"
        )

    async def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Parse logs and extract structured information.

        Args:
            context: Analysis context with 'logs' key

        Returns:
            Parsed information
        """
        logs = context.get('logs', '')

        # Simulate parsing work
        await asyncio.sleep(0.3)

        parsed = {
            'log_lines': len(logs.split('\n')),
            'errors_found': logs.count('ERROR'),
            'warnings_found': logs.count('WARN'),
            'key_patterns': self._extract_patterns(logs)
        }

        logger.info(f"✅ Parser Agent: Extracted {parsed['errors_found']} errors from logs")
        return parsed

    def _extract_patterns(self, logs: str) -> List[str]:
        """Extract key error patterns from logs."""
        patterns = []
        keywords = ['timeout', 'connection', 'failed', 'critical', 'exception', 'error']

        for keyword in keywords:
            if keyword.lower() in logs.lower():
                patterns.append(keyword)

        return patterns


class RetrieverAgent(Agent):
    """Retrieves relevant documents via RAG."""

    def __init__(self, rag_retriever=None):
        super().__init__(
            name="Retriever Agent",
            description="Searches knowledge base for relevant info"
        )
        self.rag_retriever = rag_retriever

    async def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Retrieve relevant documents from RAG.

        Args:
            context: Analysis context with 'query' key

        Returns:
            Retrieved documents
        """
        query = context.get('logs', '')[:100]  # Use first 100 chars as query

        # Simulate retrieval work
        await asyncio.sleep(0.4)

        if self.rag_retriever:
            try:
                results = self.rag_retriever.retrieve_and_format(query, n_results=3)
                docs_found = len(results.split('\n'))
            except Exception as e:
                logger.warning(f"RAG retrieval failed: {e}")
                docs_found = 0
                results = ""
        else:
            docs_found = 0
            results = ""

        retrieved = {
            'documents_found': docs_found,
            'top_results': results,
            'query_used': query[:50]
        }

        logger.info(f"✅ Retriever Agent: Found {docs_found} relevant documents")
        return retrieved


class MemoryAgent(Agent):
    """Searches similar incidents in memory."""

    def __init__(self, memory_manager=None):
        super().__init__(
            name="Memory Agent",
            description="Looks for similar past incidents"
        )
        self.memory_manager = memory_manager

    async def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Search memory for similar incidents.

        Args:
            context: Analysis context

        Returns:
            Similar incidents
        """
        logs = context.get('logs', '')
        keywords = logs.split()[:5]

        # Simulate memory search
        await asyncio.sleep(0.3)

        if self.memory_manager:
            try:
                memory_context = self.memory_manager.get_memory_context(keywords=keywords)
                incidents_found = memory_context.count('incident')
            except Exception as e:
                logger.warning(f"Memory search failed: {e}")
                incidents_found = 0
                memory_context = ""
        else:
            incidents_found = 0
            memory_context = ""

        result = {
            'similar_incidents_found': incidents_found,
            'memory_context': memory_context[:200],
            'keywords_used': keywords
        }

        logger.info(f"✅ Memory Agent: Found {incidents_found} similar incidents")
        return result


class ReasoningAgent(Agent):
    """Performs root cause analysis."""

    def __init__(self, llm_client=None):
        super().__init__(
            name="Reasoning Agent",
            description="Analyzes patterns and identifies root cause"
        )
        self.llm_client = llm_client

    async def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze root cause.

        Args:
            context: Analysis context with parsed data

        Returns:
            Root cause analysis
        """
        parsed_info = context.get('parsed_info', {})
        retrieved_docs = context.get('retrieved_docs', {})
        memory_info = context.get('memory_info', {})

        # Simulate reasoning
        await asyncio.sleep(0.5)

        analysis = {
            'primary_cause': 'Connection pool exhaustion',
            'confidence': 92,
            'contributing_factors': [
                'Increased query load',
                'Insufficient pool size',
                'Long-running queries'
            ],
            'affected_systems': ['api-gateway', 'payment-service'],
            'severity': 'Critical'
        }

        if self.llm_client:
            try:
                prompt = self._build_analysis_prompt(context)
                # In production: analysis = self.llm_client.analyze(prompt)
            except Exception as e:
                logger.warning(f"LLM analysis failed: {e}")

        logger.info(f"✅ Reasoning Agent: Root cause identified with {analysis['confidence']}% confidence")
        return analysis

    def _build_analysis_prompt(self, context: Dict[str, Any]) -> str:
        """Build prompt for LLM analysis."""
        return f"""Analyze this incident:

Parsed logs: {context.get('parsed_info', {})}
Retrieved docs: {context.get('retrieved_docs', {})}
Similar incidents: {context.get('memory_info', {})}

Provide root cause analysis."""


class RecommendationAgent(Agent):
    """Generates remediation recommendations."""

    def __init__(self, llm_client=None):
        super().__init__(
            name="Recommendation Agent",
            description="Generates remediation recommendations"
        )
        self.llm_client = llm_client

    async def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate recommendations.

        Args:
            context: Analysis context with root cause

        Returns:
            Recommendations
        """
        root_cause = context.get('root_cause', {})

        # Simulate recommendation generation
        await asyncio.sleep(0.3)

        recommendations = {
            'immediate_actions': [
                'Increase connection pool size to 300',
                'Kill long-running queries',
                'Scale database replicas'
            ],
            'short_term_fixes': [
                'Optimize query performance',
                'Implement connection pooling monitoring'
            ],
            'long_term_solutions': [
                'Migrate to cloud-managed database',
                'Implement auto-scaling policies'
            ],
            'estimated_resolution_time': '15-30 minutes'
        }

        if self.llm_client:
            try:
                prompt = f"Given root cause {root_cause}, generate recommendations"
                # In production: recommendations = self.llm_client.generate_recommendations(prompt)
            except Exception as e:
                logger.warning(f"Recommendation generation failed: {e}")

        logger.info(f"✅ Recommendation Agent: Generated {len(recommendations['immediate_actions'])} immediate actions")
        return recommendations


class ReporterAgent(Agent):
    """Structures and formats final incident report."""

    def __init__(self):
        super().__init__(
            name="Reporter Agent",
            description="Creates incident report & recommendations"
        )

    async def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate final report.

        Args:
            context: Complete analysis context

        Returns:
            Structured incident report
        """
        # Simulate report generation
        await asyncio.sleep(0.2)

        report = {
            'summary': 'Database connection pool exhaustion causing order service outage',
            'incident_id': 'INC-2025-0647',
            'status': 'Investigating',
            'severity': context.get('root_cause', {}).get('severity', 'High'),
            'affected_users': '~5,000 users',
            'duration': '15 minutes',
            'root_cause': context.get('root_cause', {}).get('primary_cause', 'Unknown'),
            'recommendations': context.get('recommendations', {}),
            'timeline': [
                {'time': '10:15:30', 'event': 'Connection pool exhaustion detected'},
                {'time': '10:15:45', 'event': 'Alert triggered'},
                {'time': '10:16:00', 'event': 'Investigation started'}
            ],
            'confidence': 92
        }

        logger.info(f"✅ Reporter Agent: Report generated (Incident: {report['incident_id']})")
        return report
