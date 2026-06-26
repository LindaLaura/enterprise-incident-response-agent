"""
Incident Chatbot Service

Manages chat interactions with auto-truncation of conversation history and uploaded docs
to prevent memory leaks in long-running sessions.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime


class IncidentChatbot:
	"""Chatbot for incident analysis with memory management."""

	def __init__(self, llm_client, memory_manager, rag_retriever):
		"""
		Initialize chatbot with memory management.

		Args:
			llm_client: LLM client for analysis
			memory_manager: Memory manager for persistence
			rag_retriever: RAG retriever for documentation
		"""
		self.llm = llm_client
		self.memory = memory_manager
		self.rag = rag_retriever

		self.current_incident = None
		self.uploaded_docs = {}
		self.conversation_history = []

		# Memory management config
		self.max_conversation_history = 100
		self.max_uploaded_docs = 50
		self.history_cleanup_interval = 50
		self.message_count_since_cleanup = 0

	def add_conversation_message(self, role: str, content: str) -> None:
		"""
		Add message to conversation history with auto-cleanup.

		Args:
			role: Message role (user, bot, system)
			content: Message content
		"""
		self.conversation_history.append({
			"role": role,
			"content": content,
			"timestamp": datetime.now().isoformat()
		})

		self.message_count_since_cleanup += 1
		if self.message_count_since_cleanup >= self.history_cleanup_interval:
			self._cleanup_conversation_history()
			self.message_count_since_cleanup = 0

	def _cleanup_conversation_history(self) -> None:
		"""Truncate conversation history if too large."""
		if len(self.conversation_history) > self.max_conversation_history:
			self.conversation_history = \
				self.conversation_history[-self.max_conversation_history:]

	def _cleanup_uploaded_docs(self) -> None:
		"""Truncate uploaded docs registry if too large."""
		if len(self.uploaded_docs) > self.max_uploaded_docs:
			items = list(self.uploaded_docs.items())
			self.uploaded_docs = dict(items[-self.max_uploaded_docs:])

	def add_uploaded_doc(self, doc_name: str, chunks: List[str]) -> None:
		"""
		Register uploaded document with auto-cleanup.

		Args:
			doc_name: Name of the document
			chunks: Text chunks from the document
		"""
		self.uploaded_docs[doc_name] = chunks
		self._cleanup_uploaded_docs()

	def get_memory_stats(self) -> Dict[str, int]:
		"""
		Get current memory usage statistics.

		Returns:
			Dictionary with memory stats
		"""
		history_size = len(str(self.conversation_history).encode())
		docs_size = len(str(self.uploaded_docs).encode())

		return {
			'conversation_history_size': len(self.conversation_history),
			'uploaded_docs_count': len(self.uploaded_docs),
			'total_memory_kb': (history_size + docs_size) // 1024
		}

	def get_recent_history(self, limit: int = 10) -> List[Dict[str, Any]]:
		"""
		Get recent conversation history.

		Args:
			limit: Number of recent messages to return

		Returns:
			List of recent messages
		"""
		return self.conversation_history[-limit:]

	def clear_history(self) -> None:
		"""Clear conversation history."""
		self.conversation_history = []
		self.message_count_since_cleanup = 0

	def clear_uploaded_docs(self) -> None:
		"""Clear uploaded docs registry."""
		self.uploaded_docs = {}
