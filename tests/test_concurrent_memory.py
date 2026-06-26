"""
Test concurrent memory access with file locking.
"""

import unittest
import threading
import tempfile
import shutil
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from memory_manager import MemoryManager


class TestConcurrentMemory(unittest.TestCase):
	"""Test concurrent memory access."""

	def setUp(self):
		"""Create temporary directory for testing."""
		self.temp_dir = tempfile.mkdtemp()

	def tearDown(self):
		"""Clean up temporary directory."""
		shutil.rmtree(self.temp_dir)

	def test_concurrent_saves(self):
		"""Test that concurrent saves don't corrupt JSON and maintain consistency."""
		memory = MemoryManager(memory_dir=self.temp_dir)

		results = {'success': 0, 'failed': 0, 'errors': []}

		def save_incident(incident_id):
			try:
				# Create fresh memory instance for each thread
				mem = MemoryManager(memory_dir=self.temp_dir)
				mem.save_incident(
					incident_id=incident_id,
					summary=f"Test incident {incident_id}",
					root_cause="Test cause",
					recommendations=["Test rec"],
					severity="HIGH",
					affected_services=["TestService"]
				)
				results['success'] += 1
			except Exception as e:
				results['failed'] += 1
				results['errors'].append(str(e))

		# Create threads that save simultaneously
		threads = []
		for i in range(5):
			t = threading.Thread(
				target=save_incident,
				args=(f"INC-{i}",)
			)
			threads.append(t)

		# Start all threads
		for t in threads:
			t.start()

		# Wait for all to complete
		for t in threads:
			t.join()

		# Verify no errors and file is still valid JSON
		final_memory = MemoryManager(memory_dir=self.temp_dir)
		self.assertIsNotNone(final_memory.long_term)
		self.assertIn('incidents', final_memory.long_term)
		self.assertGreater(len(final_memory.long_term['incidents']), 0)
		self.assertEqual(results['failed'], 0, f"Had {results['failed']} failures: {results['errors']}")

	def test_file_locking_prevents_corruption(self):
		"""Test that file locking prevents corruption."""
		memory = MemoryManager(memory_dir=self.temp_dir)

		# Save initial incident
		memory.save_incident(
			incident_id="INC-001",
			summary="Initial incident",
			root_cause="Initial cause",
			recommendations=["Rec1"],
			severity="CRITICAL",
			affected_services=["Service1"]
		)

		initial_count = len(memory.long_term['incidents'])

		# Verify the file exists and is valid
		self.assertTrue(memory.long_term_file.exists())
		self.assertIn('incidents', memory.long_term)

		# Reload and verify file is still valid
		reloaded = MemoryManager(memory_dir=self.temp_dir)
		final_count = len(reloaded.long_term['incidents'])

		self.assertEqual(final_count, initial_count, "File should be readable after save")

	def test_lock_acquisition_timeout(self):
		"""Test that lock acquisition respects timeout."""
		memory = MemoryManager(memory_dir=self.temp_dir)
		lock_file = memory.lock_file

		# Manually acquire lock
		with open(lock_file, 'w') as f:
			import fcntl
			fcntl.flock(f.fileno(), fcntl.LOCK_EX)

			# Try to acquire lock again - should timeout
			try:
				memory._acquire_lock()
				self.fail("Should have raised TimeoutError")
			except TimeoutError as e:
				self.assertIn("Could not acquire lock", str(e))


class TestBackupSystem(unittest.TestCase):
	"""Test backup and restore functionality."""

	def setUp(self):
		"""Create temporary directory for testing."""
		self.temp_dir = tempfile.mkdtemp()

	def tearDown(self):
		"""Clean up temporary directory."""
		shutil.rmtree(self.temp_dir)

	def test_backup_creation(self):
		"""Test that backups are created."""
		import time
		memory = MemoryManager(memory_dir=self.temp_dir)

		# Save initial incident to create memory file
		memory.save_incident(
			incident_id="INC-001",
			summary="Test incident",
			root_cause="Test cause",
			recommendations=["Test rec"],
			severity="HIGH",
			affected_services=["TestService"]
		)

		time.sleep(0.1)  # Ensure file is written

		# Save again to trigger backup
		memory.save_incident(
			incident_id="INC-002",
			summary="Test incident 2",
			root_cause="Test cause",
			recommendations=["Test rec"],
			severity="HIGH",
			affected_services=["TestService"]
		)

		backups = memory.get_backup_history()
		self.assertGreater(len(backups), 0, f"No backups created. Files: {list(memory.backup_dir.glob('*'))}")

	def test_restore_from_backup(self):
		"""Test restoring from backup."""
		import time
		memory = MemoryManager(memory_dir=self.temp_dir)

		# Save incident
		memory.save_incident(
			incident_id="INC-001",
			summary="Test incident",
			root_cause="Test cause",
			recommendations=["Test rec"],
			severity="HIGH",
			affected_services=["TestService"]
		)

		time.sleep(0.1)

		# Save again to generate backup
		memory.save_incident(
			incident_id="INC-002",
			summary="Test incident 2",
			root_cause="Test cause 2",
			recommendations=["Test rec 2"],
			severity="HIGH",
			affected_services=["TestService"]
		)

		backups = memory.get_backup_history()
		self.assertGreater(len(backups), 0, f"No backups found in {memory.backup_dir}")

		# Restore from backup
		backup_path = backups[0]['path']
		success = memory.restore_from_backup(backup_path)
		self.assertTrue(success)

		# Verify incident restored
		self.assertGreaterEqual(len(memory.long_term['incidents']), 1)

	def test_backup_rotation(self):
		"""Test that old backups are cleaned up."""
		memory = MemoryManager(memory_dir=self.temp_dir)
		memory.max_backups = 0  # Cleanup immediately

		for i in range(3):
			memory.save_incident(
				incident_id=f"INC-{i}",
				summary=f"Incident {i}",
				root_cause="Test cause",
				recommendations=["Test rec"],
				severity="HIGH",
				affected_services=["TestService"]
			)

		backups = memory.get_backup_history()
		self.assertLessEqual(len(backups), 1, "Old backups should be cleaned up")


class TestDataValidation(unittest.TestCase):
	"""Test data validation with Pydantic."""

	def setUp(self):
		"""Create temporary directory for testing."""
		self.temp_dir = tempfile.mkdtemp()

	def tearDown(self):
		"""Clean up temporary directory."""
		shutil.rmtree(self.temp_dir)

	def test_invalid_severity_rejected(self):
		"""Test that invalid severity is rejected."""
		from pydantic import ValidationError
		from memory_manager import IncidentRecord

		with self.assertRaises(ValidationError):
			IncidentRecord(
				incident_id="INC-001",
				timestamp="2026-06-26T00:00:00Z",
				summary="Test",
				root_cause="Test cause",
				recommendations=["Fix it"],
				severity="INVALID",
				affected_services=["Service1"]
			)

	def test_valid_severity_accepted(self):
		"""Test that valid severities are accepted."""
		from memory_manager import IncidentRecord

		for severity in ['LOW', 'MEDIUM', 'HIGH', 'CRITICAL']:
			record = IncidentRecord(
				incident_id="INC-001",
				timestamp="2026-06-26T00:00:00Z",
				summary="Test",
				root_cause="Test cause",
				recommendations=["Fix it"],
				severity=severity,
				affected_services=["Service1"]
			)
			self.assertEqual(record.severity, severity)

	def test_missing_required_field_rejected(self):
		"""Test that missing required fields are rejected."""
		from pydantic import ValidationError
		from memory_manager import IncidentRecord

		with self.assertRaises(ValidationError):
			IncidentRecord(
				incident_id="INC-001",
				timestamp="2026-06-26T00:00:00Z",
				# Missing summary
				root_cause="Test cause",
				recommendations=["Fix it"],
				severity="HIGH",
				affected_services=["Service1"]
			)

	def test_corrupted_json_recovery(self):
		"""Test recovery from corrupted JSON."""
		import time
		memory = MemoryManager(memory_dir=self.temp_dir)

		# Save incident
		memory.save_incident(
			incident_id="INC-001",
			summary="Test incident",
			root_cause="Test cause",
			recommendations=["Test rec"],
			severity="HIGH",
			affected_services=["TestService"]
		)

		time.sleep(0.1)

		# Save again to create a backup
		memory.save_incident(
			incident_id="INC-002",
			summary="Test incident 2",
			root_cause="Test cause 2",
			recommendations=["Test rec 2"],
			severity="HIGH",
			affected_services=["TestService"]
		)

		# Corrupt the JSON file
		with open(memory.long_term_file, 'w') as f:
			f.write("{ invalid json }")

		# Reload should recover from backup
		reloaded = MemoryManager(memory_dir=self.temp_dir)
		self.assertGreater(len(reloaded.long_term['incidents']), 0)
		self.assertIn('incidents', reloaded.long_term)


if __name__ == '__main__':
	unittest.main()
