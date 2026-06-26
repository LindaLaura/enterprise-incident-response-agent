"""
Tests for Memory Manager
"""
import unittest
import sys
import json
import tempfile
import shutil
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from memory_manager import MemoryManager


class TestMemoryManager(unittest.TestCase):
    """Test memory management functionality."""

    def setUp(self):
        """Set up test fixtures with temporary directory."""
        self.temp_dir = tempfile.mkdtemp()
        self.memory = MemoryManager(memory_dir=self.temp_dir)

    def tearDown(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_initialization(self):
        """Test memory manager initialization."""
        self.assertIsNotNone(self.memory)
        self.assertEqual(self.memory.long_term['metadata']['total_incidents'], 0)
        self.assertEqual(len(self.memory.long_term['incidents']), 0)

    def test_save_incident(self):
        """Test saving incident to memory."""
        self.memory.save_incident(
            incident_id='INC-TEST-001',
            summary='Test incident',
            root_cause='Test root cause',
            recommendations=['Fix A', 'Fix B'],
            severity='HIGH',
            affected_services=['ServiceA', 'ServiceB'],
            incident_timestamp='2026-06-12T14:23:45Z',
            events_by_severity={
                'CRITICAL': [{'timestamp': '2026-06-12T14:23:45Z', 'service': 'ServiceA'}],
                'ERROR': [{'timestamp': '2026-06-12T14:23:46Z', 'service': 'ServiceB'}],
                'WARN': [],
                'INFO': []
            }
        )

        self.assertEqual(self.memory.long_term['metadata']['total_incidents'], 1)
        self.assertEqual(len(self.memory.long_term['incidents']), 1)

        incident = self.memory.long_term['incidents'][0]
        self.assertEqual(incident['incident_id'], 'INC-TEST-001')
        self.assertEqual(incident['severity'], 'HIGH')
        self.assertEqual(incident['incident_timestamp'], '2026-06-12T14:23:45Z')
        self.assertIn('events_by_severity', incident)

    def test_get_similar_incidents(self):
        """Test retrieving similar incidents."""
        # Save multiple incidents
        self.memory.save_incident(
            incident_id='INC-TEST-001',
            summary='Database connection failure',
            root_cause='Connection pool exhausted',
            recommendations=['Restart DB'],
            severity='CRITICAL',
            affected_services=['DatabaseService']
        )

        self.memory.save_incident(
            incident_id='INC-TEST-002',
            summary='API timeout issues',
            root_cause='Network latency',
            recommendations=['Check network'],
            severity='HIGH',
            affected_services=['APIGateway']
        )

        # Search by keywords
        similar = self.memory.get_similar_incidents(['database', 'connection'], limit=5)
        self.assertGreater(len(similar), 0)
        self.assertEqual(similar[0]['incident_id'], 'INC-TEST-001')

    def test_short_term_memory(self):
        """Test short-term memory operations."""
        self.memory.set_current_incident({'id': 'TEST-001', 'severity': 'HIGH'})
        self.assertEqual(self.memory.short_term['current_incident']['id'], 'TEST-001')

        self.memory.add_conversation_context('User message', role='user')
        self.assertEqual(len(self.memory.short_term['conversation_context']), 1)

        self.memory.add_analysis_step('Step 1', 'Result 1')
        self.assertEqual(len(self.memory.short_term['analysis_steps']), 1)

    def test_memory_persistence(self):
        """Test that memory persists to disk."""
        self.memory.save_incident(
            incident_id='INC-TEST-PERSIST',
            summary='Test persistence',
            root_cause='Testing',
            recommendations=['Test'],
            severity='LOW',
            affected_services=['TestService']
        )

        # Create new memory manager with same directory
        new_memory = MemoryManager(memory_dir=self.temp_dir)
        self.assertEqual(new_memory.long_term['metadata']['total_incidents'], 1)
        self.assertEqual(new_memory.long_term['incidents'][0]['incident_id'], 'INC-TEST-PERSIST')

    def test_get_stats(self):
        """Test memory statistics."""
        self.memory.save_incident(
            incident_id='INC-STATS-001',
            summary='Stats test',
            root_cause='Testing stats',
            recommendations=['Test'],
            severity='MEDIUM',
            affected_services=['StatsService']
        )

        stats = self.memory.get_stats()
        self.assertEqual(stats['total_incidents'], 1)
        self.assertIn('memory_file', stats)

    def test_events_by_severity_structure(self):
        """Test events_by_severity structure in memory."""
        events = {
            'CRITICAL': [
                {'timestamp': '2026-06-12T14:23:45Z', 'service': 'DatabaseService'},
                {'timestamp': '2026-06-12T14:23:46Z', 'service': 'OrderService'}
            ],
            'ERROR': [
                {'timestamp': '2026-06-12T14:23:47Z', 'service': 'APIGateway'}
            ],
            'WARN': [],
            'INFO': []
        }

        self.memory.save_incident(
            incident_id='INC-EVENTS-001',
            summary='Events test',
            root_cause='Testing events structure',
            recommendations=['Test'],
            severity='CRITICAL',
            affected_services=['DatabaseService', 'OrderService'],
            incident_timestamp='2026-06-12T14:23:45Z',
            events_by_severity=events
        )

        incident = self.memory.long_term['incidents'][0]
        self.assertIn('events_by_severity', incident)
        self.assertEqual(len(incident['events_by_severity']['CRITICAL']), 2)
        self.assertEqual(incident['events_by_severity']['CRITICAL'][0]['service'], 'DatabaseService')


if __name__ == '__main__':
    unittest.main()
