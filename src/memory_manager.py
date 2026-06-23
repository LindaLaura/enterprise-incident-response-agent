"""
Memory Manager for Incident Response Agent

Handles both short-term (session) and long-term (persistent) memory.
"""

import json
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime


class MemoryManager:
    """Manages short-term and long-term memory for the agent."""

    def __init__(self, memory_dir: str = "./memory"):
        """
        Initialize memory manager.

        Args:
            memory_dir: Directory for persistent memory storage
        """
        self.memory_dir = Path(memory_dir)
        self.memory_dir.mkdir(parents=True, exist_ok=True)

        # Short-term memory (current session)
        self.short_term = {
            'current_incident': None,
            'conversation_context': [],
            'retrieved_docs': [],
            'analysis_steps': []
        }

        # Long-term memory file
        self.long_term_file = self.memory_dir / "long_term_memory.json"
        self.long_term = self._load_long_term()

    def _load_long_term(self) -> Dict[str, Any]:
        """Load long-term memory from disk."""
        if self.long_term_file.exists():
            try:
                with open(self.long_term_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                print(f"⚠️  Failed to load long-term memory: {e}")

        # Initialize empty long-term memory
        return {
            'incidents': [],
            'root_causes': {},
            'recommendations': {},
            'user_preferences': {},
            'metadata': {
                'created_at': datetime.now().isoformat(),
                'total_incidents': 0
            }
        }

    def _save_long_term(self):
        """Save long-term memory to disk."""
        try:
            with open(self.long_term_file, 'w') as f:
                json.dump(self.long_term, f, indent=2)
        except Exception as e:
            print(f"⚠️  Failed to save long-term memory: {e}")

    # Short-term memory methods

    def set_current_incident(self, incident_info: Dict[str, Any]):
        """
        Set current incident being analyzed.

        Args:
            incident_info: Dictionary with incident information
        """
        self.short_term['current_incident'] = incident_info

    def add_conversation_context(self, message: str, role: str = "user"):
        """
        Add to conversation context.

        Args:
            message: Message text
            role: Role (user, assistant, system)
        """
        self.short_term['conversation_context'].append({
            'role': role,
            'content': message,
            'timestamp': datetime.now().isoformat()
        })

        # Keep only last 10 messages
        if len(self.short_term['conversation_context']) > 10:
            self.short_term['conversation_context'] = \
                self.short_term['conversation_context'][-10:]

    def add_analysis_step(self, step_name: str, result: Any):
        """
        Record an analysis step.

        Args:
            step_name: Name of the analysis step
            result: Result or summary of the step
        """
        self.short_term['analysis_steps'].append({
            'step': step_name,
            'result': result,
            'timestamp': datetime.now().isoformat()
        })

    def get_short_term_context(self) -> str:
        """
        Get formatted short-term memory context.

        Returns:
            Formatted context string
        """
        parts = []

        if self.short_term['current_incident']:
            parts.append("\n--- Current Incident Context ---")
            incident = self.short_term['current_incident']
            for key, value in incident.items():
                parts.append(f"{key}: {value}")

        if self.short_term['conversation_context']:
            parts.append("\n--- Recent Conversation ---")
            for msg in self.short_term['conversation_context'][-3:]:
                parts.append(f"{msg['role']}: {msg['content'][:100]}...")

        return "\n".join(parts) if parts else ""

    # Long-term memory methods

    def save_incident(
        self,
        incident_id: str,
        summary: str,
        root_cause: str,
        recommendations: List[str],
        severity: str,
        affected_services: List[str]
    ):
        """
        Save incident to long-term memory.

        Args:
            incident_id: Unique incident identifier
            summary: Incident summary
            root_cause: Root cause analysis
            recommendations: List of recommendations
            severity: Incident severity
            affected_services: List of affected services
        """
        incident_record = {
            'incident_id': incident_id,
            'timestamp': datetime.now().isoformat(),
            'summary': summary,
            'root_cause': root_cause,
            'recommendations': recommendations,
            'severity': severity,
            'affected_services': affected_services
        }

        self.long_term['incidents'].append(incident_record)
        self.long_term['metadata']['total_incidents'] += 1

        # Store root cause for future reference
        if root_cause:
            cause_key = self._extract_cause_key(root_cause)
            if cause_key not in self.long_term['root_causes']:
                self.long_term['root_causes'][cause_key] = []
            self.long_term['root_causes'][cause_key].append(incident_id)

        # Save to disk
        self._save_long_term()

    def get_similar_incidents(
        self,
        keywords: List[str],
        limit: int = 3
    ) -> List[Dict[str, Any]]:
        """
        Retrieve similar past incidents.

        Args:
            keywords: Keywords to search for
            limit: Maximum number of incidents to return

        Returns:
            List of similar incident records
        """
        if not keywords:
            return self.long_term['incidents'][-limit:]

        # Simple keyword matching
        matches = []
        keywords_lower = [k.lower() for k in keywords]

        for incident in reversed(self.long_term['incidents']):
            score = 0
            text = (
                f"{incident.get('summary', '')} "
                f"{incident.get('root_cause', '')} "
                f"{' '.join(incident.get('affected_services', []))}"
            ).lower()

            for keyword in keywords_lower:
                if keyword in text:
                    score += 1

            if score > 0:
                matches.append((score, incident))

        # Sort by score and return top matches
        matches.sort(key=lambda x: x[0], reverse=True)
        return [incident for _, incident in matches[:limit]]

    def get_root_cause_history(self, cause_type: str) -> List[str]:
        """
        Get history of incidents with similar root cause.

        Args:
            cause_type: Type of root cause

        Returns:
            List of incident IDs
        """
        return self.long_term['root_causes'].get(cause_type, [])

    def set_user_preference(self, key: str, value: Any):
        """
        Set a user preference.

        Args:
            key: Preference key
            value: Preference value
        """
        self.long_term['user_preferences'][key] = value
        self._save_long_term()

    def get_user_preference(self, key: str, default: Any = None) -> Any:
        """
        Get a user preference.

        Args:
            key: Preference key
            default: Default value if not found

        Returns:
            Preference value
        """
        return self.long_term['user_preferences'].get(key, default)

    def get_memory_context(
        self,
        include_similar: bool = True,
        keywords: Optional[List[str]] = None
    ) -> str:
        """
        Get formatted memory context for prompts.

        Args:
            include_similar: Whether to include similar past incidents
            keywords: Keywords for finding similar incidents

        Returns:
            Formatted memory context string
        """
        parts = ["\n--- Memory Context ---"]

        # Add statistics
        total = self.long_term['metadata']['total_incidents']
        parts.append(f"\nTotal past incidents analyzed: {total}")

        # Add similar incidents
        if include_similar and total > 0:
            similar = self.get_similar_incidents(keywords or [], limit=2)
            if similar:
                parts.append("\nSimilar Past Incidents:")
                for incident in similar:
                    parts.append(
                        f"\n- [{incident['incident_id']}] {incident['severity']} | "
                        f"{', '.join(incident['affected_services'][:2])}"
                    )
                    parts.append(f"  Root Cause: {incident['root_cause'][:150]}...")

        # Add user preferences
        if self.long_term['user_preferences']:
            parts.append("\nUser Preferences:")
            for key, value in self.long_term['user_preferences'].items():
                parts.append(f"- {key}: {value}")

        return "\n".join(parts)

    def get_stats(self) -> Dict[str, Any]:
        """Get memory statistics."""
        return {
            'total_incidents': self.long_term['metadata']['total_incidents'],
            'root_cause_types': len(self.long_term['root_causes']),
            'user_preferences': len(self.long_term['user_preferences']),
            'short_term_context_items': len(self.short_term['conversation_context']),
            'memory_file': str(self.long_term_file)
        }

    def clear_short_term(self):
        """Clear short-term memory (new session)."""
        self.short_term = {
            'current_incident': None,
            'conversation_context': [],
            'retrieved_docs': [],
            'analysis_steps': []
        }

    def _extract_cause_key(self, root_cause: str) -> str:
        """
        Extract a key from root cause description.

        Args:
            root_cause: Root cause text

        Returns:
            Simplified key
        """
        # Simple extraction - could be improved with NLP
        keywords = ['connection', 'memory', 'deployment', 'network',
                    'timeout', 'configuration', 'resource', 'authentication']

        root_cause_lower = root_cause.lower()
        for keyword in keywords:
            if keyword in root_cause_lower:
                return keyword

        return 'other'
