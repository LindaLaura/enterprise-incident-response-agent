"""
Analysis Service

Orchestrates the complete incident analysis pipeline using LangGraph,
integrates evaluation at each stage, and manages checkpoint/resume functionality.
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime

logger = logging.getLogger(__name__)


class AnalysisService:
    """Orchestrates incident analysis with LangGraph and evaluation."""

    def __init__(self, rag_retriever=None, memory_manager=None, llm_client=None):
        """
        Initialize analysis service.

        Args:
            rag_retriever: RAG retriever instance
            memory_manager: Memory manager instance
            llm_client: LLM client instance
        """
        self.rag_retriever = rag_retriever
        self.memory_manager = memory_manager
        self.llm_client = llm_client

        # Initialize agents
        from ..agents.agents import (
            ParserAgent,
            RetrieverAgent,
            MemoryAgent,
            ReasoningAgent,
            RecommendationAgent,
            ReporterAgent
        )

        self.parser_agent = ParserAgent()
        self.retriever_agent = RetrieverAgent(rag_retriever)
        self.memory_agent = MemoryAgent(memory_manager)
        self.reasoning_agent = ReasoningAgent(llm_client)
        self.recommendation_agent = RecommendationAgent(llm_client)
        self.reporter_agent = ReporterAgent()

        # Initialize evaluation orchestrator
        try:
            from ..evaluation.evaluation_orchestrator import EvaluationOrchestrator
            self.evaluator = EvaluationOrchestrator()
        except Exception as e:
            logger.warning(f"Evaluation orchestrator not available: {e}")
            self.evaluator = None

        # Initialize LangGraph
        try:
            from ..agents.langgraph_manager import IncidentAnalysisGraph
            self.graph = IncidentAnalysisGraph(
                rag_retriever=rag_retriever,
                memory_manager=memory_manager,
                llm_client=llm_client
            )
            logger.info("✅ LangGraph initialized")
        except Exception as e:
            logger.warning(f"⚠️ LangGraph not available: {e}")
            self.graph = None

        # Store analysis results and checkpoints
        self.analyses = {}
        self.checkpoints = {}

    async def run_analysis(
        self,
        logs: str,
        incident_id: str,
        use_langgraph: bool = True,
        thread_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Run complete incident analysis pipeline.

        Args:
            logs: Input logs to analyze
            incident_id: Incident ID for tracking
            use_langgraph: Whether to use LangGraph orchestration (fallback to agents if unavailable)
            thread_id: Optional thread ID for checkpoint management

        Returns:
            Complete analysis result with evaluations
        """
        start_time = datetime.now()
        logger.info(f"🚀 Starting analysis for {incident_id}")

        try:
            # Always use agents pipeline (LangGraph has compatibility issues)
            # TODO: Fix LangGraph async node signatures in future
            result = await self._run_with_agents(logs, incident_id)

            # Store result
            self.analyses[incident_id] = result
            result["duration_ms"] = int((datetime.now() - start_time).total_seconds() * 1000)
            logger.info(f"✅ Analysis complete in {result['duration_ms']}ms")

            return result

        except Exception as e:
            logger.error(f"❌ Analysis failed: {e}")
            return {
                "incident_id": incident_id,
                "status": "failed",
                "error": str(e),
                "duration_ms": int((datetime.now() - start_time).total_seconds() * 1000)
            }

    async def _run_with_langgraph(
        self,
        logs: str,
        incident_id: str,
        thread_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Run analysis using LangGraph orchestration."""
        if not self.graph:
            logger.warning("LangGraph not available, falling back to agents")
            return await self._run_with_agents(logs, incident_id)

        logger.info(f"📊 Using LangGraph orchestration for {incident_id}")

        try:
            # Run the graph
            final_state = await self.graph.run_analysis(logs, thread_id=thread_id or incident_id)

            # Extract results
            result = {
                "incident_id": incident_id,
                "status": "completed",
                "thread_id": thread_id or incident_id,
                "parsed_info": final_state.get("parsed_info", {}),
                "retrieved_docs": final_state.get("retrieved_docs", []),
                "root_cause": final_state.get("root_cause", ""),
                "recommendations": final_state.get("recommendations", []),
                "final_report": final_state.get("final_report", {}),
                "execution_trace": final_state.get("execution_trace", []),
                "errors": final_state.get("errors", []),
            }

            # Evaluate each stage
            if self.evaluator:
                evaluations = {}

                # Evaluate retrieval
                if result["retrieved_docs"]:
                    evaluations["retrieval"] = self.evaluator.evaluate_retrieval_stage(
                        query=logs[:100],
                        retrieved_docs=result["retrieved_docs"],
                        incident_id=incident_id
                    )

                # Evaluate generation (root cause)
                if result["root_cause"]:
                    evaluations["generation"] = self.evaluator.evaluate_generation_stage(
                        query=logs[:100],
                        answer=result["root_cause"],
                        retrieved_context=result["retrieved_docs"],
                        incident_id=incident_id
                    )

                    evaluations["root_cause"] = self.evaluator.evaluate_root_cause_stage(
                        root_cause=result["root_cause"],
                        retrieved_context=result["retrieved_docs"],
                        incident_id=incident_id
                    )

                # Evaluate recommendations
                if result["recommendations"]:
                    evaluations["recommendations"] = self.evaluator.evaluate_recommendations_stage(
                        recommendations=result["recommendations"],
                        incident_id=incident_id
                    )

                # Evaluate final report
                if result["final_report"]:
                    evaluations["report"] = self.evaluator.evaluate_report_stage(
                        report=result["final_report"],
                        incident_id=incident_id
                    )

                result["evaluations"] = evaluations
                result["overall_quality"] = self.evaluator.get_incident_evaluation(incident_id)

            return result

        except Exception as e:
            logger.error(f"LangGraph execution failed: {e}")
            raise

    async def _run_with_agents(
        self,
        logs: str,
        incident_id: str
    ) -> Dict[str, Any]:
        """Run analysis using traditional agent pipeline."""
        logger.info(f"📊 Using traditional agent pipeline for {incident_id}")

        context = {
            "logs": logs,
            "incident_id": incident_id
        }

        stages = {}
        execution_trace = []

        try:
            # Parser stage
            logger.info("📝 Parsing logs...")
            start = datetime.now()
            parsed = await self.parser_agent.run(context)
            stages["parser"] = parsed
            context.update({"parsed_info": parsed})
            execution_trace.append({
                "stage": "parse",
                "duration_ms": int((datetime.now() - start).total_seconds() * 1000),
                "status": "success"
            })

            # Retriever stage
            logger.info("🔍 Retrieving documents...")
            start = datetime.now()
            retrieved = await self.retriever_agent.run(context)
            stages["retriever"] = retrieved
            context.update({"retrieved_docs": retrieved.get("top_results", [])})
            execution_trace.append({
                "stage": "retrieve",
                "duration_ms": int((datetime.now() - start).total_seconds() * 1000),
                "status": "success",
                "docs_found": retrieved.get("documents_found", 0)
            })

            # Evaluate retrieval
            if self.evaluator and retrieved.get("top_results"):
                retrieval_eval = self.evaluator.evaluate_retrieval_stage(
                    query=context["logs"][:100],
                    retrieved_docs=[retrieved.get("top_results", "")],
                    incident_id=incident_id
                )
                stages["retrieval_evaluation"] = retrieval_eval

            # Memory stage
            logger.info("📚 Querying memory...")
            start = datetime.now()
            memory = await self.memory_agent.run(context)
            stages["memory"] = memory
            context.update({"memory_info": memory})
            execution_trace.append({
                "stage": "memory",
                "duration_ms": int((datetime.now() - start).total_seconds() * 1000),
                "status": "success"
            })

            # Reasoning stage
            logger.info("🧠 Analyzing root cause...")
            start = datetime.now()
            reasoning = await self.reasoning_agent.run(context)
            stages["reasoning"] = reasoning
            # Handle both dict and string responses - pass full reasoning as root_cause for reporter
            if isinstance(reasoning, dict):
                context.update({"root_cause": reasoning})  # Pass full dict, not just root_cause field
            else:
                context.update({"root_cause": {"primary_cause": str(reasoning)}})
            execution_trace.append({
                "stage": "reason",
                "duration_ms": int((datetime.now() - start).total_seconds() * 1000),
                "status": "success"
            })

            # Evaluate root cause
            if self.evaluator:
                root_cause_text = reasoning.get("root_cause", "") if isinstance(reasoning, dict) else str(reasoning)
                if root_cause_text:
                    root_cause_eval = self.evaluator.evaluate_root_cause_stage(
                        root_cause=root_cause_text,
                        retrieved_context=[retrieved.get("top_results", "")],
                        incident_id=incident_id
                    )
                    stages["root_cause_evaluation"] = root_cause_eval

            # Recommendation stage
            logger.info("💡 Generating recommendations...")
            start = datetime.now()
            recommendations = await self.recommendation_agent.run(context)
            stages["recommendations"] = recommendations
            # Handle both dict and string responses
            if isinstance(recommendations, dict):
                context.update({"recommendations": recommendations.get("recommendations", [])})
            else:
                context.update({"recommendations": []})
            execution_trace.append({
                "stage": "recommend",
                "duration_ms": int((datetime.now() - start).total_seconds() * 1000),
                "status": "success"
            })

            # Evaluate recommendations
            if self.evaluator and isinstance(recommendations, dict):
                rec_list = recommendations.get("recommendations", [])
                if rec_list:
                    rec_eval = self.evaluator.evaluate_recommendations_stage(
                        recommendations=rec_list,
                        incident_id=incident_id
                    )
                    stages["recommendations_evaluation"] = rec_eval

            # Reporter stage
            logger.info("📄 Generating report...")
            start = datetime.now()
            report = await self.reporter_agent.run(context)
            stages["report"] = report
            execution_trace.append({
                "stage": "report",
                "duration_ms": int((datetime.now() - start).total_seconds() * 1000),
                "status": "success"
            })

            # Evaluate report
            if self.evaluator and isinstance(report, dict) and report:
                report_eval = self.evaluator.evaluate_report_stage(
                    report=report,
                    incident_id=incident_id
                )
                stages["report_evaluation"] = report_eval

            return {
                "incident_id": incident_id,
                "status": "completed",
                "stages": stages,
                "execution_trace": execution_trace,
                "overall_quality": self.evaluator.get_incident_evaluation(incident_id) if self.evaluator else None,
                "recommendations": self.evaluator.get_quality_recommendations(incident_id) if self.evaluator else []
            }

        except Exception as e:
            import traceback
            logger.error(f"Agent pipeline execution failed: {e}")
            logger.debug(f"Traceback: {traceback.format_exc()}")
            return {
                "incident_id": incident_id,
                "status": "completed_with_partial_data",
                "error": str(e),
                "error_details": traceback.format_exc(),
                "execution_trace": execution_trace,
                "stages": stages
            }

    def get_analysis_status(self, incident_id: str) -> Dict[str, Any]:
        """Get status of an analysis."""
        analysis = self.analyses.get(incident_id)
        if not analysis:
            return {"status": "not_found", "incident_id": incident_id}

        return {
            "incident_id": incident_id,
            "status": analysis.get("status", "unknown"),
            "duration_ms": analysis.get("duration_ms", 0),
            "has_evaluation": "evaluations" in analysis or "overall_quality" in analysis,
            "timestamp": analysis.get("timestamp", None)
        }

    def get_analysis_result(self, incident_id: str) -> Dict[str, Any]:
        """Get full analysis result."""
        return self.analyses.get(incident_id, {"status": "not_found", "incident_id": incident_id})

    def list_analyses(self, limit: int = 10) -> List[Dict[str, Any]]:
        """List recent analyses."""
        recent = sorted(
            self.analyses.items(),
            key=lambda x: x[1].get("duration_ms", 0),
            reverse=True
        )[:limit]

        return [
            {
                "incident_id": incident_id,
                "status": analysis.get("status"),
                "duration_ms": analysis.get("duration_ms")
            }
            for incident_id, analysis in recent
        ]

    def get_evaluation_summary(self) -> Dict[str, Any]:
        """Get evaluation summary across all analyses."""
        if not self.evaluator:
            return {"message": "Evaluation not available"}

        return self.evaluator.get_metrics_summary()
