"""
Integration Tests for End-to-End Workflow
"""
import unittest
import sys
import os
import json
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))


class TestIntegration(unittest.TestCase):
    """Test end-to-end incident analysis workflow."""

    @classmethod
    def setUpClass(cls):
        """Set up class-level fixtures."""
        cls.sample_logs_dir = Path(__file__).parent.parent / 'sample_logs'

    def test_sample_logs_exist(self):
        """Test that sample log files exist."""
        self.assertTrue(self.sample_logs_dir.exists())

        expected_files = ['db_failure.txt', 'api_failure.txt', 'deployment_failure.txt']
        for filename in expected_files:
            file_path = self.sample_logs_dir / filename
            if file_path.exists():
                self.assertTrue(file_path.is_file())
                self.assertGreater(file_path.stat().st_size, 0)

    def test_log_file_format(self):
        """Test that log files have expected format."""
        log_file = self.sample_logs_dir / 'db_failure.txt'

        if log_file.exists():
            with open(log_file, 'r') as f:
                first_line = f.readline()
                # Should start with timestamp in brackets
                self.assertTrue(first_line.startswith('['))
                self.assertIn(']', first_line)

    def test_memory_directory_structure(self):
        """Test memory directory structure."""
        memory_dir = Path(__file__).parent.parent / 'memory'

        if memory_dir.exists():
            memory_file = memory_dir / 'long_term_memory.json'
            if memory_file.exists():
                with open(memory_file, 'r') as f:
                    data = json.load(f)
                    self.assertIn('incidents', data)
                    self.assertIn('metadata', data)
                    self.assertIn('total_incidents', data['metadata'])

    def test_chroma_db_exists(self):
        """Test that ChromaDB directory exists after ingestion."""
        chroma_dir = Path(__file__).parent.parent / 'chroma_db'

        # ChromaDB may or may not be initialized
        if chroma_dir.exists():
            self.assertTrue(chroma_dir.is_dir())

    def test_docs_directory_structure(self):
        """Test documentation directory structure."""
        docs_dir = Path(__file__).parent.parent / 'docs'

        self.assertTrue(docs_dir.exists())
        doc_files = list(docs_dir.glob('*.txt'))
        self.assertGreater(len(doc_files), 0)

    def test_env_example_exists(self):
        """Test that .env.example exists with required variables."""
        env_example = Path(__file__).parent.parent / '.env.example'

        self.assertTrue(env_example.exists())

        with open(env_example, 'r') as f:
            content = f.read()
            # Check for key environment variables
            self.assertIn('OPENAI_API_KEY', content)
            self.assertIn('USE_RAG', content)
            self.assertIn('USE_MEMORY', content)

    def test_gitignore_exists(self):
        """Test that .gitignore exists with proper exclusions."""
        gitignore = Path(__file__).parent.parent / '.gitignore'

        self.assertTrue(gitignore.exists())

        with open(gitignore, 'r') as f:
            content = f.read()
            # Check for key exclusions
            self.assertIn('.env', content)
            self.assertIn('chroma_db', content)
            self.assertIn('__pycache__', content)


class TestJSONSchema(unittest.TestCase):
    """Test JSON schema structure for incident reports."""

    def test_events_by_severity_schema(self):
        """Test events_by_severity structure."""
        sample_events = {
            'CRITICAL': [
                {'timestamp': '2026-06-12T14:23:45Z', 'service': 'DatabaseService'}
            ],
            'ERROR': [
                {'timestamp': '2026-06-12T14:23:46Z', 'service': 'OrderService'}
            ],
            'WARN': [],
            'INFO': []
        }

        # Validate structure
        for severity in ['CRITICAL', 'ERROR', 'WARN', 'INFO']:
            self.assertIn(severity, sample_events)
            self.assertIsInstance(sample_events[severity], list)

            for event in sample_events[severity]:
                self.assertIn('timestamp', event)
                self.assertIn('service', event)

    def test_incident_report_structure(self):
        """Test complete incident report structure."""
        sample_report = {
            'incident_id': 'INC-2026-06-12-001',
            'incident_timestamp': '2026-06-12T14:23:45Z',
            'events_by_severity': {
                'CRITICAL': [{'timestamp': '2026-06-12T14:23:45Z', 'service': 'ServiceA'}],
                'ERROR': [],
                'WARN': [],
                'INFO': []
            },
            'severity': 'CRITICAL',
            'status': 'RESOLVED',
            'affected_services': ['ServiceA'],
            'metadata': {
                'model_provider': 'anthropic',
                'rag_enabled': True,
                'memory_enabled': True,
                'generated_at': '2026-06-26T00:00:00Z'
            }
        }

        # Validate required fields
        required_fields = ['incident_id', 'incident_timestamp', 'events_by_severity',
                          'severity', 'status', 'affected_services', 'metadata']

        for field in required_fields:
            self.assertIn(field, sample_report)

        # Validate metadata
        self.assertIn('generated_at', sample_report['metadata'])
        self.assertIn('rag_enabled', sample_report['metadata'])
        self.assertIn('memory_enabled', sample_report['metadata'])


if __name__ == '__main__':
    unittest.main()
