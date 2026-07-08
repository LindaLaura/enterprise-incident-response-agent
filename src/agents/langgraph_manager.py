"""
LangGraph-based Multi-Agent Orchestration

Converts the sequential agent pipeline into a graph-based system with:
- Conditional routing (e.g., re-retrieve if low confidence)
- Parallel execution branches
- Persistent state checkpoints
- Human-in-the-loop capabilities
"""

import logging
from typing import Any, Dict, Optional, Annotated
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

from langgraph.graph import StateGraph, START, END
try:
    from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver
except ImportError:
    from langgraph.checkpoint.sqlite import SqliteSaver as AsyncSqliteSaver

from .agents import (
    ParserAgent,
    RetrieverAgent,
    MemoryAgent,
    ReasoningAgent,
    RecommendationAgent,
    ReporterAgent
)

logger = logging.getLogger(__name__)


@dataclass
class AnalysisState:
    """State object passed through the analysis graph."""

    # Input
    logs: str

    # Pipeline outputs
    parsed_info: Dict[str, Any] = field(default_factory=dict)
    retrieved_docs: list = field(default_factory=list)
    retrieval_attempts: int = 0
    confidence: float = 0.0
    memory_info: Dict[str, Any] = field(default_factory=dict)
    root_cause: str = ""
    root_cause_data: Dict[str, Any] = field(default_factory=dict)
    recommendations: list = field(default_factory=list)
    final_report: Dict[str, Any] = field(default_factory=dict)

    # Metadata
    evaluation_metrics: Dict[str, Any] = field(default_factory=dict)
    execution_trace: list = field(default_factory=list)
    start_time: str = ""
    errors: list = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert state to dictionary."""
        return {
            "logs": self.logs,
            "parsed_info": self.parsed_info,
            "retrieved_docs": self.retrieved_docs,
            "retrieval_attempts": self.retrieval_attempts,
            "confidence": self.confidence,
            "memory_info": self.memory_info,
            "root_cause": self.root_cause,
            "root_cause_data": self.root_cause_data,
            "recommendations": self.recommendations,
            "final_report": self.final_report,
            "evaluation_metrics": self.evaluation_metrics,
            "execution_trace": self.execution_trace,
            "errors": self.errors,
        }


class IncidentAnalysisGraph:
    """Graph-based incident analysis orchestration."""

    def __init__(
        self,
        rag_retriever=None,
        memory_manager=None,
        llm_client=None,
        checkpoint_dir: Optional[str] = None
    ):
        """
        Initialize the analysis graph.

        Args:
            rag_retriever: RAG retriever instance
            memory_manager: Memory manager instance
            llm_client: LLM client instance
            checkpoint_dir: Directory for checkpoints
        """
        self.rag_retriever = rag_retriever
        self.memory_manager = memory_manager
        self.llm_client = llm_client

        # Initialize agents
        self.parser_agent = ParserAgent()
        self.retriever_agent = RetrieverAgent(rag_retriever)
        self.memory_agent = MemoryAgent(memory_manager)
        self.reasoning_agent = ReasoningAgent(llm_client)
        self.recommendation_agent = RecommendationAgent(llm_client)
        self.reporter_agent = ReporterAgent()

        # Build graph
        self.graph = self._build_graph()

        # Setup checkpointing
        checkpoint_path = Path(checkpoint_dir or "memory/checkpoints")
        checkpoint_path.mkdir(parents=True, exist_ok=True)
        try:
            self.checkpointer = AsyncSqliteSaver(str(checkpoint_path / "checkpoints.db"))
        except TypeError:
            # Fallback if AsyncSqliteSaver doesn't exist
            logger.warning("AsyncSqliteSaver not available, using synchronous checkpointer")
            self.checkpointer = None

        # Compiled graph with checkpointing
        self.compiled_graph = self.graph.compile(checkpointer=self.checkpointer)

    def _build_graph(self) -> StateGraph:
        """Build the analysis graph with nodes and edges."""
        graph = StateGraph(AnalysisState)

        # Add nodes
        graph.add_node("parse", self._parse_node)
        graph.add_node("retrieve", self._retrieve_node)
        graph.add_node("confidence_check", self._confidence_check_node)
        graph.add_node("memory", self._memory_node)
        graph.add_node("reason", self._reason_node)
        graph.add_node("recommend", self._recommend_node)
        graph.add_node("report", self._report_node)

        # Add edges: linear path
        graph.add_edge(START, "parse")
        graph.add_edge("parse", "retrieve")
        graph.add_edge("retrieve", "confidence_check")

        # Conditional edge: if confidence too low, re-retrieve
        graph.add_conditional_edges(
            "confidence_check",
            self._route_on_confidence,
            {
                "re_retrieve": "retrieve",
                "continue": "memory"
            }
        )

        # Parallel branches: memory feeds into both reasoning and recommendations
        graph.add_edge("memory", "reason")
        graph.add_edge("memory", "recommend")

        # Both must complete before reporting
        graph.add_edge("reason", "report")
        graph.add_edge("recommend", "report")

        # End
        graph.add_edge("report", END)

        return graph

    async def _parse_node(self, state: AnalysisState) -> Dict[str, Any]:
        """Parse logs."""
        logger.info("📝 Parsing logs...")
        try:
            context = {"logs": state.logs}
            result = await self.parser_agent.run(context)

            state.parsed_info = result
            state.execution_trace.append({
                "node": "parse",
                "status": "success",
                "timestamp": datetime.now().isoformat()
            })
            return state.to_dict()
        except Exception as e:
            logger.error(f"Parse failed: {e}")
            state.errors.append({"node": "parse", "error": str(e)})
            raise

    async def _retrieve_node(self, state: AnalysisState) -> Dict[str, Any]:
        """Retrieve relevant documents."""
        logger.info("🔍 Retrieving documents...")
        try:
            context = {
                "logs": state.logs,
                "parsed_info": state.parsed_info
            }
            result = await self.retriever_agent.run(context)

            state.retrieved_docs = result.get("documents", [])
            state.confidence = result.get("confidence", 0.0)
            state.retrieval_attempts += 1

            state.execution_trace.append({
                "node": "retrieve",
                "status": "success",
                "docs_found": len(state.retrieved_docs),
                "confidence": state.confidence,
                "timestamp": datetime.now().isoformat()
            })

            logger.info(f"✅ Retrieved {len(state.retrieved_docs)} docs (confidence: {state.confidence:.2f})")
            return state.to_dict()
        except Exception as e:
            logger.error(f"Retrieve failed: {e}")
            state.errors.append({"node": "retrieve", "error": str(e)})
            raise

    def _route_on_confidence(self, state: AnalysisState) -> str:
        """Route based on retrieval confidence."""
        # Allow up to 2 retrieval attempts
        if state.confidence < 0.7 and state.retrieval_attempts < 2:
            logger.warning(
                f"⚠️ Low confidence ({state.confidence:.2f}), re-retrieving..."
            )
            return "re_retrieve"
        else:
            return "continue"

    def _confidence_check_node(self, state: AnalysisState) -> Dict[str, Any]:
        """Check confidence and route accordingly."""
        state.execution_trace.append({
            "node": "confidence_check",
            "confidence": state.confidence,
            "attempt": state.retrieval_attempts,
            "timestamp": datetime.now().isoformat()
        })
        return state.to_dict()

    async def _memory_node(self, state: AnalysisState) -> Dict[str, Any]:
        """Query incident memory."""
        logger.info("📚 Querying memory...")
        try:
            context = {
                "logs": state.logs,
                "parsed_info": state.parsed_info,
                "retrieved_docs": state.retrieved_docs
            }
            result = await self.memory_agent.run(context)

            state.memory_info = result

            state.execution_trace.append({
                "node": "memory",
                "status": "success",
                "similar_incidents": len(result.get("similar_incidents", [])),
                "timestamp": datetime.now().isoformat()
            })

            logger.info(f"✅ Found {len(result.get('similar_incidents', []))} similar incidents")
            return state.to_dict()
        except Exception as e:
            logger.error(f"Memory query failed: {e}")
            state.errors.append({"node": "memory", "error": str(e)})
            # Don't raise - memory is optional
            return state.to_dict()

    async def _reason_node(self, state: AnalysisState) -> Dict[str, Any]:
        """Analyze root cause."""
        logger.info("🧠 Analyzing root cause...")
        try:
            context = {
                "logs": state.logs,
                "parsed_info": state.parsed_info,
                "retrieved_docs": state.retrieved_docs,
                "memory_info": state.memory_info
            }
            result = await self.reasoning_agent.run(context)

            state.root_cause = result.get("root_cause", "")
            state.root_cause_data = result

            state.execution_trace.append({
                "node": "reason",
                "status": "success",
                "confidence": result.get("confidence", 0),
                "timestamp": datetime.now().isoformat()
            })

            logger.info(f"✅ Root cause identified (confidence: {result.get('confidence', 0)}%)")
            return state.to_dict()
        except Exception as e:
            logger.error(f"Reasoning failed: {e}")
            state.errors.append({"node": "reason", "error": str(e)})
            raise

    async def _recommend_node(self, state: AnalysisState) -> Dict[str, Any]:
        """Generate recommendations."""
        logger.info("💡 Generating recommendations...")
        try:
            context = {
                "logs": state.logs,
                "parsed_info": state.parsed_info,
                "root_cause": state.root_cause,
                "memory_info": state.memory_info
            }
            result = await self.recommendation_agent.run(context)

            state.recommendations = result.get("recommendations", [])

            state.execution_trace.append({
                "node": "recommend",
                "status": "success",
                "recommendations_count": len(state.recommendations),
                "timestamp": datetime.now().isoformat()
            })

            logger.info(f"✅ Generated {len(state.recommendations)} recommendations")
            return state.to_dict()
        except Exception as e:
            logger.error(f"Recommendations failed: {e}")
            state.errors.append({"node": "recommend", "error": str(e)})
            raise

    async def _report_node(self, state: AnalysisState) -> Dict[str, Any]:
        """Generate final report."""
        logger.info("📄 Generating report...")
        try:
            context = {
                "logs": state.logs,
                "parsed_info": state.parsed_info,
                "retrieved_docs": state.retrieved_docs,
                "memory_info": state.memory_info,
                "root_cause": state.root_cause_data,
                "recommendations": state.recommendations
            }
            result = await self.reporter_agent.run(context)

            state.final_report = result

            state.execution_trace.append({
                "node": "report",
                "status": "success",
                "timestamp": datetime.now().isoformat()
            })

            logger.info("✅ Report generated")
            return state.to_dict()
        except Exception as e:
            logger.error(f"Report generation failed: {e}")
            state.errors.append({"node": "report", "error": str(e)})
            raise

    async def run_analysis(self, logs: str, thread_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Run the analysis pipeline.

        Args:
            logs: Input logs to analyze
            thread_id: Optional thread ID for checkpoint management

        Returns:
            Final analysis report with metadata
        """
        logger.info(f"🚀 Starting analysis graph (thread: {thread_id})")

        initial_state = AnalysisState(logs=logs, start_time=datetime.now().isoformat())

        # Run the compiled graph
        config = {
            "configurable": {"thread_id": thread_id or "default"}
        } if thread_id else None

        try:
            final_state = await self.compiled_graph.ainvoke(
                initial_state.to_dict(),
                config=config
            )

            logger.info("🎉 Analysis complete!")
            return final_state

        except Exception as e:
            logger.error(f"❌ Analysis failed: {e}")
            raise

    def get_checkpoint(self, thread_id: str) -> Optional[Dict]:
        """Retrieve checkpoint for a thread."""
        try:
            # This would require custom checkpoint access
            # For now, return None
            return None
        except Exception as e:
            logger.error(f"Failed to get checkpoint: {e}")
            return None

    def resume_analysis(self, thread_id: str) -> Optional[Dict]:
        """Resume analysis from checkpoint."""
        checkpoint = self.get_checkpoint(thread_id)
        if checkpoint:
            logger.info(f"📌 Resuming from checkpoint: {thread_id}")
            return checkpoint
        return None
