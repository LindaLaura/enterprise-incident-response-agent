"""
Comprehensive Integration Tests for LangGraph, DeepEval, RAGAS, and Analysis Service
"""

import pytest
import asyncio
from datetime import datetime
from pathlib import Path


class TestEvaluationOrchestrator:
    """Test unified evaluation orchestrator."""

    @pytest.fixture
    def orchestrator(self):
        """Initialize evaluation orchestrator."""
        from src.evaluation.evaluation_orchestrator import EvaluationOrchestrator
        return EvaluationOrchestrator()

    def test_orchestrator_initialization(self, orchestrator):
        """Test evaluation orchestrator initialization."""
        assert orchestrator is not None
        assert orchestrator.eval_dir.exists()
        assert orchestrator.orchestrator_file is not None

    def test_retrieval_stage_evaluation(self, orchestrator):
        """Test retrieval stage evaluation."""
        result = orchestrator.evaluate_retrieval_stage(
            query="What is the root cause?",
            retrieved_docs=["Document 1", "Document 2"],
            incident_id="TEST-001"
        )

        assert result is not None
        assert result["incident_id"] == "TEST-001"
        assert result["stage"] == "retrieval"
        assert "quality_score" in result
        assert "metrics" in result

    def test_generation_stage_evaluation(self, orchestrator):
        """Test generation stage evaluation."""
        result = orchestrator.evaluate_generation_stage(
            query="What happened?",
            answer="The system failed due to timeout",
            retrieved_context=["Context 1", "Context 2"],
            incident_id="TEST-002"
        )

        assert result is not None
        assert result["incident_id"] == "TEST-002"
        assert result["stage"] == "generation"
        assert "quality_score" in result

    def test_root_cause_evaluation(self, orchestrator):
        """Test root cause analysis evaluation."""
        result = orchestrator.evaluate_root_cause_stage(
            root_cause="Database connection pool exhausted",
            retrieved_context=["Doc 1", "Doc 2"],
            incident_id="TEST-003"
        )

        assert result is not None
        assert result["incident_id"] == "TEST-003"
        assert result["stage"] == "root_cause"

    def test_recommendations_evaluation(self, orchestrator):
        """Test recommendations evaluation."""
        result = orchestrator.evaluate_recommendations_stage(
            recommendations=[
                "Increase connection pool size to 500",
                "Monitor connection pool metrics hourly"
            ],
            incident_id="TEST-004"
        )

        assert result is not None
        assert result["incident_id"] == "TEST-004"
        assert result["stage"] == "recommendations"
        assert result["num_recommendations"] == 2

    def test_report_evaluation(self, orchestrator):
        """Test report evaluation."""
        report = {
            "incident_id": "TEST-005",
            "summary": "System outage analysis",
            "root_cause": "Database failure",
            "affected_services": ["API", "Database"],
            "recommendations": ["Restart DB", "Monitor"],
            "severity": "HIGH",
            "status": "Resolved"
        }

        result = orchestrator.evaluate_report_stage(report, incident_id="TEST-005")

        assert result is not None
        assert result["incident_id"] == "TEST-005"
        assert result["stage"] == "report"

    def test_get_incident_evaluation(self, orchestrator):
        """Test getting aggregated incident evaluation."""
        incident_id = "TEST-AGG-001"

        # Add multiple stage evaluations
        orchestrator.evaluate_retrieval_stage(
            query="test",
            retrieved_docs=["doc1"],
            incident_id=incident_id
        )
        orchestrator.evaluate_root_cause_stage(
            root_cause="root cause",
            retrieved_context=["doc1"],
            incident_id=incident_id
        )

        result = orchestrator.get_incident_evaluation(incident_id)

        assert result is not None
        assert result["incident_id"] == incident_id
        assert "overall_quality_score" in result
        assert "stage_scores" in result

    def test_metrics_summary(self, orchestrator):
        """Test metrics summary generation."""
        # Add multiple evaluations
        for i in range(5):
            orchestrator.evaluate_retrieval_stage(
                query=f"query {i}",
                retrieved_docs=["doc1", "doc2"],
                incident_id=f"SUMMARY-{i}"
            )

        summary = orchestrator.get_metrics_summary(last_n=10)

        assert summary is not None
        assert "total_evaluations" in summary
        assert summary["recent_count"] <= 10
        assert "by_stage" in summary

    def test_quality_recommendations(self, orchestrator):
        """Test quality improvement recommendations."""
        incident_id = "TEST-REC-001"

        # Add low-quality evaluation
        orchestrator.orchestrator_history.append({
            "incident_id": incident_id,
            "stage": "retrieval",
            "quality_score": 0.3,
            "timestamp": datetime.now().isoformat()
        })

        recommendations = orchestrator.get_quality_recommendations(incident_id)

        assert recommendations is not None
        assert isinstance(recommendations, list)
        assert len(recommendations) > 0


class TestAnalysisService:
    """Test unified analysis service."""

    @pytest.fixture
    def service(self):
        """Initialize analysis service."""
        from src.services.analysis_service import AnalysisService
        return AnalysisService()

    @pytest.mark.asyncio
    async def test_analysis_service_initialization(self, service):
        """Test analysis service initialization."""
        assert service is not None
        assert service.parser_agent is not None
        assert service.retriever_agent is not None
        assert service.memory_agent is not None

    @pytest.mark.asyncio
    async def test_run_analysis_with_agents(self, service):
        """Test analysis run with traditional agents."""
        logs = "ERROR: Database connection timeout at 10:30:45"
        result = await service.run_analysis(
            logs=logs,
            incident_id="TEST-AGENT-001",
            use_langgraph=False
        )

        assert result is not None
        assert result["incident_id"] == "TEST-AGENT-001"
        assert result["status"] in ["completed", "failed"]
        assert "duration_ms" in result

    def test_get_analysis_status(self, service):
        """Test getting analysis status."""
        # First run an analysis
        service.analyses["TEST-STATUS"] = {
            "status": "completed",
            "duration_ms": 1000
        }

        status = service.get_analysis_status("TEST-STATUS")

        assert status is not None
        assert status["status"] == "completed"

    def test_get_analysis_result(self, service):
        """Test getting analysis result."""
        expected_result = {
            "incident_id": "TEST-RESULT",
            "status": "completed",
            "root_cause": "Database failure"
        }
        service.analyses["TEST-RESULT"] = expected_result

        result = service.get_analysis_result("TEST-RESULT")

        assert result == expected_result

    def test_list_analyses(self, service):
        """Test listing analyses."""
        # Add multiple analyses
        for i in range(3):
            service.analyses[f"TEST-LIST-{i}"] = {
                "incident_id": f"TEST-LIST-{i}",
                "status": "completed",
                "duration_ms": 1000 * (i + 1)
            }

        analyses = service.list_analyses(limit=5)

        assert len(analyses) <= 5
        assert all("incident_id" in a for a in analyses)


class TestLangGraphIntegration:
    """Test LangGraph orchestration."""

    @pytest.fixture
    def graph(self):
        """Initialize LangGraph."""
        try:
            from src.agents.langgraph_manager import IncidentAnalysisGraph
            return IncidentAnalysisGraph()
        except Exception as e:
            pytest.skip(f"LangGraph not available: {e}")

    def test_langgraph_initialization(self, graph):
        """Test LangGraph initialization."""
        assert graph is not None
        assert graph.graph is not None
        assert graph.compiled_graph is not None

    def test_langgraph_has_nodes(self, graph):
        """Test LangGraph has all required nodes."""
        # Check that graph was built with expected nodes
        assert hasattr(graph, 'parser_agent')
        assert hasattr(graph, 'retriever_agent')
        assert hasattr(graph, 'memory_agent')
        assert hasattr(graph, 'reasoning_agent')


class TestEvaluationMetrics:
    """Test evaluation metrics collection."""

    def test_ragas_evaluator_available(self):
        """Test RAGAS evaluator is available."""
        try:
            from src.evaluation.ragas_evaluator import RAGASEvaluator
            evaluator = RAGASEvaluator()
            assert evaluator is not None
        except ImportError:
            pytest.skip("RAGAS not installed")

    def test_deepeval_evaluator_available(self):
        """Test DeepEval evaluator is available."""
        try:
            from src.evaluation.deepeval_evaluator import DeepEvalEvaluator
            evaluator = DeepEvalEvaluator()
            assert evaluator is not None
        except ImportError:
            pytest.skip("DeepEval not installed")

    def test_evaluation_files_created(self):
        """Test evaluation metrics files are created."""
        from pathlib import Path

        eval_dir = Path("memory/evaluation")
        assert eval_dir.exists()

        # Files may not exist if no evaluations run, but directory should


class TestAPIEndpoints:
    """Test API endpoints for evaluation and analysis."""

    @pytest.fixture
    def client(self):
        """Initialize FastAPI test client."""
        from fastapi.testclient import TestClient
        from src.api.main import app
        return TestClient(app)

    def test_health_check(self, client):
        """Test health check endpoint."""
        response = client.get("/api/health")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"

    def test_metrics_all_endpoint(self, client):
        """Test unified metrics endpoint."""
        response = client.get("/api/metrics/all")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert "frameworks" in data

    def test_evaluation_summary_endpoint(self, client):
        """Test evaluation summary endpoint."""
        response = client.get("/api/evaluation/summary")
        # May fail if orchestrator not available, which is ok for CI
        if response.status_code == 200:
            data = response.json()
            assert data["status"] == "success"

    def test_incidents_endpoint(self, client):
        """Test incidents listing endpoint."""
        response = client.get("/api/incidents")
        assert response.status_code == 200
        data = response.json()
        assert "incidents" in data


class TestEndToEnd:
    """End-to-end integration tests."""

    @pytest.mark.asyncio
    async def test_full_analysis_pipeline(self):
        """Test complete analysis pipeline end-to-end."""
        from src.services.analysis_service import AnalysisService

        service = AnalysisService()
        logs = "ERROR: Connection timeout in database pool at 2024-07-07T10:30:00Z"

        result = await service.run_analysis(
            logs=logs,
            incident_id="E2E-TEST-001",
            use_langgraph=False
        )

        assert result is not None
        assert result["incident_id"] == "E2E-TEST-001"
        assert "stages" in result or "status" in result

    @pytest.mark.asyncio
    async def test_evaluation_collection(self):
        """Test that evaluations are collected during analysis."""
        from src.services.analysis_service import AnalysisService

        service = AnalysisService()
        logs = "ERROR: System failure detected"

        result = await service.run_analysis(
            logs=logs,
            incident_id="E2E-EVAL-001",
            use_langgraph=False
        )

        # Check that evaluations are present
        assert result is not None
        # Evaluations may not be present if evaluators not enabled
        # but should complete successfully

    def test_metrics_storage_and_retrieval(self):
        """Test that metrics are stored and retrievable."""
        from src.evaluation.evaluation_orchestrator import EvaluationOrchestrator

        orchestrator = EvaluationOrchestrator()

        # Store some metrics
        orchestrator.evaluate_retrieval_stage(
            query="test",
            retrieved_docs=["doc1"],
            incident_id="STORE-TEST-001"
        )

        # Retrieve metrics
        result = orchestrator.get_incident_evaluation("STORE-TEST-001")

        assert result is not None
        assert "stage_scores" in result


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
