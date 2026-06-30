"""
Agent Manager orchestrates multi-agent incident analysis pipeline.
"""

import asyncio
import logging
from typing import Any, Dict, List, Optional
from .agents import (
    ParserAgent,
    RetrieverAgent,
    MemoryAgent,
    ReasoningAgent,
    RecommendationAgent,
    ReporterAgent
)

logger = logging.getLogger(__name__)


class AgentManager:
    """Orchestrates execution of incident response agents."""

    def __init__(self, rag_retriever=None, memory_manager=None, llm_client=None):
        """
        Initialize agent manager.

        Args:
            rag_retriever: RAG retriever instance
            memory_manager: Memory manager instance
            llm_client: LLM client instance
        """
        self.rag_retriever = rag_retriever
        self.memory_manager = memory_manager
        self.llm_client = llm_client

        # Initialize agents in order
        self.agents = [
            ParserAgent(),
            RetrieverAgent(rag_retriever),
            MemoryAgent(memory_manager),
            ReasoningAgent(llm_client),
            RecommendationAgent(llm_client),
            ReporterAgent()
        ]

        self.agent_map = {agent.name: agent for agent in self.agents}
        self.context = {}

    async def run_analysis(self, logs: str, update_callback=None) -> Dict[str, Any]:
        """
        Run complete incident analysis pipeline.

        Args:
            logs: Input logs to analyze
            update_callback: Optional callback for status updates

        Returns:
            Final analysis report
        """
        self.context = {'logs': logs}

        logger.info("🚀 Starting agent pipeline...")

        for i, agent in enumerate(self.agents):
            try:
                logger.info(f"[{i+1}/{len(self.agents)}] Executing {agent.name}...")

                # Run agent
                result = await agent.run(self.context)

                # Store result in context for next agents
                context_key = self._get_context_key(agent.name)
                self.context[context_key] = result

                # Notify of progress
                if update_callback:
                    await update_callback({
                        'agent': agent.name,
                        'status': agent.status.value,
                        'duration': agent.duration
                    })

                logger.info(f"✅ {agent.name}: {agent.duration}")

            except Exception as e:
                logger.error(f"❌ {agent.name} failed: {e}")
                if update_callback:
                    await update_callback({
                        'agent': agent.name,
                        'status': 'failed',
                        'error': str(e)
                    })
                raise

        # Return final report from reporter agent
        report = self.agents[-1].output
        logger.info("🎉 Analysis complete!")

        return report

    def get_agents_status(self) -> List[Dict[str, Any]]:
        """Get status of all agents."""
        return [agent.get_status() for agent in self.agents]

    def get_agent_status(self, agent_name: str) -> Optional[Dict[str, Any]]:
        """Get status of specific agent."""
        agent = self.agent_map.get(agent_name)
        return agent.get_status() if agent else None

    def get_context(self) -> Dict[str, Any]:
        """Get current analysis context."""
        return self.context.copy()

    def _get_context_key(self, agent_name: str) -> str:
        """Map agent name to context key."""
        mapping = {
            'Parser Agent': 'parsed_info',
            'Retriever Agent': 'retrieved_docs',
            'Memory Agent': 'memory_info',
            'Reasoning Agent': 'root_cause',
            'Recommendation Agent': 'recommendations',
            'Reporter Agent': 'final_report'
        }
        return mapping.get(agent_name, agent_name.lower().replace(' ', '_'))

    def reset(self):
        """Reset all agents and context."""
        for agent in self.agents:
            agent.status = agent.status.__class__.PENDING
            agent.start_time = None
            agent.end_time = None
            agent.duration = None
            agent.output = None
            agent.error = None
        self.context = {}
