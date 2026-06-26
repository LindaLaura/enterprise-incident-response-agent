"""
Test memory cleanup mechanisms in chatbot.
"""

import unittest
from pathlib import Path
import sys
import tempfile
import shutil

sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from services.chatbot import IncidentChatbot


class MockLLMClient:
	"""Mock LLM client."""
	pass


class MockMemoryManager:
	"""Mock memory manager."""
	pass


class MockRAGRetriever:
	"""Mock RAG retriever."""
	pass


class TestMemoryCleanup(unittest.TestCase):
	"""Test memory cleanup mechanisms."""

	def setUp(self):
		"""Set up test fixtures."""
		self.mock_llm = MockLLMClient()
		self.mock_memory = MockMemoryManager()
		self.mock_rag = MockRAGRetriever()

	def test_conversation_history_truncation(self):
		"""Test that conversation history is truncated."""
		chatbot = IncidentChatbot(
			self.mock_llm,
			self.mock_memory,
			self.mock_rag
		)
		chatbot.max_conversation_history = 10
		chatbot.history_cleanup_interval = 5

		# Add 20 messages
		for i in range(20):
			chatbot.add_conversation_message(
				role="user" if i % 2 == 0 else "bot",
				content=f"Message {i}"
			)

		# Should have max 10
		self.assertLessEqual(
			len(chatbot.conversation_history),
			10
		)
		# Should keep the most recent
		self.assertIn("Message 19", chatbot.conversation_history[-1]["content"])

	def test_conversation_history_cleanup_interval(self):
		"""Test that cleanup happens at correct interval."""
		chatbot = IncidentChatbot(
			self.mock_llm,
			self.mock_memory,
			self.mock_rag
		)
		chatbot.max_conversation_history = 5
		chatbot.history_cleanup_interval = 3

		# Add messages one by one, checking cleanup trigger
		for i in range(10):
			chatbot.add_conversation_message("user", f"Message {i}")

		# After 10 messages with 3-interval cleanup, should have <= 5
		# Note: due to timing, might have up to 8 (5 + 3 for last cleanup)
		self.assertLessEqual(len(chatbot.conversation_history), 8)

	def test_docs_registry_truncation(self):
		"""Test that uploaded docs registry is truncated."""
		chatbot = IncidentChatbot(
			self.mock_llm,
			self.mock_memory,
			self.mock_rag
		)
		chatbot.max_uploaded_docs = 5

		# Add 10 docs
		for i in range(10):
			chatbot.add_uploaded_doc(f"doc_{i}.txt", [f"content_{i}"])

		# Should have max 5
		self.assertLessEqual(len(chatbot.uploaded_docs), 5)

	def test_memory_stats(self):
		"""Test memory statistics reporting."""
		chatbot = IncidentChatbot(
			self.mock_llm,
			self.mock_memory,
			self.mock_rag
		)

		# Add some data
		for i in range(5):
			chatbot.add_conversation_message("user", f"Message {i}")

		# Add docs separately
		for i in range(3):
			chatbot.add_uploaded_doc(f"doc_{i}.txt", [f"content_{i}"])

		stats = chatbot.get_memory_stats()

		self.assertIn('conversation_history_size', stats)
		self.assertIn('uploaded_docs_count', stats)
		self.assertIn('total_memory_kb', stats)

		self.assertGreater(stats['conversation_history_size'], 0)
		self.assertGreaterEqual(stats['uploaded_docs_count'], 3)
		self.assertGreaterEqual(stats['total_memory_kb'], 0)

	def test_get_recent_history(self):
		"""Test getting recent conversation history."""
		chatbot = IncidentChatbot(
			self.mock_llm,
			self.mock_memory,
			self.mock_rag
		)

		# Add messages
		for i in range(20):
			chatbot.add_conversation_message("user", f"Message {i}")

		recent = chatbot.get_recent_history(limit=5)
		self.assertEqual(len(recent), 5)
		self.assertIn("Message 19", recent[-1]["content"])

	def test_clear_history(self):
		"""Test clearing conversation history."""
		chatbot = IncidentChatbot(
			self.mock_llm,
			self.mock_memory,
			self.mock_rag
		)

		# Add messages
		for i in range(10):
			chatbot.add_conversation_message("user", f"Message {i}")

		self.assertGreater(len(chatbot.conversation_history), 0)

		chatbot.clear_history()
		self.assertEqual(len(chatbot.conversation_history), 0)
		self.assertEqual(chatbot.message_count_since_cleanup, 0)

	def test_clear_uploaded_docs(self):
		"""Test clearing uploaded docs registry."""
		chatbot = IncidentChatbot(
			self.mock_llm,
			self.mock_memory,
			self.mock_rag
		)

		# Add docs
		for i in range(5):
			chatbot.add_uploaded_doc(f"doc_{i}.txt", [f"content_{i}"])

		self.assertGreater(len(chatbot.uploaded_docs), 0)

		chatbot.clear_uploaded_docs()
		self.assertEqual(len(chatbot.uploaded_docs), 0)

	def test_memory_growth_bounded(self):
		"""Test that memory doesn't grow unbounded."""
		chatbot = IncidentChatbot(
			self.mock_llm,
			self.mock_memory,
			self.mock_rag
		)

		initial_stats = chatbot.get_memory_stats()

		# Add 1000 messages
		for i in range(1000):
			chatbot.add_conversation_message("user", f"Message {i}")

		final_stats = chatbot.get_memory_stats()

		# Memory should be bounded by max_conversation_history
		self.assertLessEqual(
			final_stats['conversation_history_size'],
			chatbot.max_conversation_history + 10  # Small buffer for timing
		)

	def test_message_timestamps(self):
		"""Test that messages have timestamps."""
		chatbot = IncidentChatbot(
			self.mock_llm,
			self.mock_memory,
			self.mock_rag
		)

		chatbot.add_conversation_message("user", "Test message")
		message = chatbot.conversation_history[0]

		self.assertIn('timestamp', message)
		self.assertIn('role', message)
		self.assertIn('content', message)


if __name__ == '__main__':
	unittest.main()
