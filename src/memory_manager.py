"""
Memory Manager for Incident Response Agent

Handles both short-term (session) and long-term (persistent) memory.
Features: File locking, backup/restore, data validation, concurrent access safety.
"""

import json
import fcntl
import time
import shutil
import sqlite3
import uuid
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from pydantic import BaseModel, Field, field_validator, ConfigDict


class IncidentRecord(BaseModel):
    """Pydantic model for incident records."""
    incident_id: str
    timestamp: str
    summary: str
    root_cause: str
    recommendations: List[str]
    severity: str
    affected_services: List[str]
    incident_timestamp: Optional[str] = None
    events_by_severity: Optional[dict] = None

    @field_validator('severity')
    @classmethod
    def validate_severity(cls, v):
        valid_severities = ['LOW', 'MEDIUM', 'HIGH', 'CRITICAL']
        if v not in valid_severities:
            raise ValueError(f'Severity must be one of {valid_severities}')
        return v


class MemoryMetadata(BaseModel):
    """Pydantic model for memory metadata."""
    created_at: str
    total_incidents: int


class LongTermMemory(BaseModel):
    """Complete long-term memory schema."""
    incidents: List[IncidentRecord]
    root_causes: dict
    recommendations: dict
    user_preferences: dict
    metadata: MemoryMetadata

    model_config = ConfigDict(extra='forbid')


class MemoryManager:
    """Manages short-term and long-term memory for the agent."""

    def __init__(self, memory_dir: str = "./memory"):
        """
        Initialize memory manager with file locking and backup support.

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
        self.lock_file = self.memory_dir / ".memory.lock"
        self.backup_dir = self.memory_dir / "backups"
        self.backup_dir.mkdir(exist_ok=True)

        # Reports storage
        self.reports_db_file = self.memory_dir / "reports.db"
        self.reports_dir = self.memory_dir / "reports"
        self.reports_dir.mkdir(exist_ok=True)

        # Lock configuration
        self.max_retries = 10
        self.lock_timeout = 30
        self.max_backups = 7

        # Initialize SQLite database for reports
        self._init_reports_db()

        self.long_term = self._load_long_term()

    def _acquire_lock(self):
        """Acquire file lock with retry logic."""
        for attempt in range(self.max_retries):
            try:
                lock_file = open(self.lock_file, 'w')
                fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                return lock_file
            except IOError:
                if attempt == self.max_retries - 1:
                    raise TimeoutError(
                        f"Could not acquire lock after {self.max_retries} attempts"
                    )
                time.sleep(0.2 * (attempt + 1))
        return None

    def _release_lock(self, lock_file):
        """Release file lock."""
        if lock_file:
            try:
                fcntl.flock(lock_file.fileno(), fcntl.LOCK_UN)
                lock_file.close()
            except Exception as e:
                print(f"⚠️  Failed to release lock: {e}")

    def _create_backup(self):
        """Create timestamped backup of long-term memory."""
        if not self.long_term_file.exists():
            return

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = self.backup_dir / f"memory_{timestamp}.json.bak"

        try:
            shutil.copy2(self.long_term_file, backup_file)
        except Exception as e:
            print(f"⚠️  Backup failed: {e}")

    def _cleanup_old_backups(self):
        """Remove backups older than max_backups days."""
        now = datetime.now()
        cutoff_date = now - timedelta(days=self.max_backups)

        for backup_file in self.backup_dir.glob("memory_*.json.bak"):
            try:
                timestamp_str = backup_file.name.replace("memory_", "").replace(".json.bak", "")
                backup_date = datetime.strptime(timestamp_str, "%Y%m%d_%H%M%S")

                if backup_date < cutoff_date:
                    backup_file.unlink()
            except ValueError:
                pass

    def _load_from_backup(self) -> Dict[str, Any]:
        """Load from most recent backup if main file corrupted."""
        backup_files = sorted(self.backup_dir.glob("memory_*.json.bak"), reverse=True)

        for backup_file in backup_files:
            try:
                with open(backup_file, 'r') as f:
                    data = json.load(f)
                print(f"⚠️  Loaded from backup: {backup_file.name}")
                return data
            except json.JSONDecodeError:
                print(f"⚠️  Backup corrupted: {backup_file.name}")
                continue

        print("❌ No valid backup found")
        return self._get_default_long_term()

    def _get_default_long_term(self) -> Dict[str, Any]:
        """Get default empty long-term memory."""
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

    def _load_long_term(self) -> Dict[str, Any]:
        """Load long-term memory from disk with file locking and validation."""
        lock_file = self._acquire_lock()
        try:
            if self.long_term_file.exists():
                try:
                    with open(self.long_term_file, 'r') as f:
                        raw_data = json.load(f)

                    # Basic structure validation
                    if not isinstance(raw_data, dict) or 'metadata' not in raw_data:
                        print("❌ Invalid data structure")
                        return self._load_from_backup()

                    return raw_data

                except json.JSONDecodeError as e:
                    print(f"❌ JSON parse error: {e}")
                    return self._load_from_backup()
        finally:
            self._release_lock(lock_file)

        return self._get_default_long_term()

    def _save_long_term(self):
        """Save long-term memory to disk with file locking and atomic writes."""
        lock_file = self._acquire_lock()
        try:
            self._create_backup()

            temp_file = self.long_term_file.with_suffix('.tmp')
            with open(temp_file, 'w') as f:
                json.dump(self.long_term, f, indent=2)

            temp_file.replace(self.long_term_file)
            self._cleanup_old_backups()

        except Exception as e:
            print(f"❌ Failed to save long-term memory: {e}")
            raise
        finally:
            self._release_lock(lock_file)

    def get_backup_history(self) -> List[Dict[str, Any]]:
        """Get list of available backups."""
        backups = []
        for backup_file in sorted(self.backup_dir.glob("memory_*.json.bak"), reverse=True):
            try:
                stat = backup_file.stat()
                timestamp_str = backup_file.name.replace("memory_", "").replace(".json.bak", "")
                backup_date = datetime.strptime(timestamp_str, "%Y%m%d_%H%M%S")

                backups.append({
                    'filename': backup_file.name,
                    'timestamp': backup_date.isoformat(),
                    'size_kb': stat.st_size // 1024,
                    'path': str(backup_file)
                })
            except (ValueError, OSError):
                pass

        return backups

    def restore_from_backup(self, backup_file_path: str) -> bool:
        """Restore memory from a specific backup."""
        backup_path = Path(backup_file_path)

        if not backup_path.exists():
            print(f"❌ Backup not found: {backup_file_path}")
            return False

        try:
            with open(backup_path, 'r') as f:
                data = json.load(f)

            # Validate structure
            if not all(key in data for key in ['incidents', 'metadata']):
                print("❌ Invalid backup structure")
                return False

            self._create_backup()
            self.long_term = data
            self._save_long_term()
            print(f"✅ Restored from backup: {backup_file_path}")
            return True

        except Exception as e:
            print(f"❌ Restore failed: {e}")
            return False

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
        affected_services: List[str],
        incident_timestamp: Optional[str] = None,
        events_by_severity: Optional[Dict[str, List[Dict[str, str]]]] = None
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
            incident_timestamp: When the incident occurred (from logs)
            events_by_severity: Categorized events with timestamp and service (CRITICAL, ERROR, WARN, INFO)
        """
        # Reload to get latest state (important for concurrent access)
        self.long_term = self._load_long_term()

        incident_record = {
            'incident_id': incident_id,
            'timestamp': datetime.now().isoformat(),
            'summary': summary,
            'root_cause': root_cause,
            'recommendations': recommendations,
            'severity': severity,
            'affected_services': affected_services
        }

        # Add incident timestamp if provided
        if incident_timestamp:
            incident_record['incident_timestamp'] = incident_timestamp

        # Add categorized events if provided
        if events_by_severity:
            incident_record['events_by_severity'] = events_by_severity

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

    # ═══ REPORT MANAGEMENT (SQLite) ═══

    def _init_reports_db(self):
        """Initialize SQLite database schema for reports."""
        try:
            conn = sqlite3.connect(str(self.reports_db_file))
            cursor = conn.cursor()

            # Create reports table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS reports (
                    id TEXT PRIMARY KEY,
                    incident_id TEXT NOT NULL,
                    format TEXT NOT NULL,
                    file_path TEXT NOT NULL,
                    file_size INTEGER,
                    created_at TEXT NOT NULL,
                    download_count INTEGER DEFAULT 0,
                    created_timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            # Create index for faster queries
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_incident_id
                ON reports(incident_id)
            ''')

            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_created_at
                ON reports(created_at)
            ''')

            conn.commit()
            conn.close()
        except Exception as e:
            print(f"❌ Failed to initialize reports database: {e}")
            raise

    def save_report(
        self,
        incident_id: str,
        format: str,
        file_path: str,
        file_size: int = 0
    ) -> str:
        """
        Save report metadata to SQLite database.

        Args:
            incident_id: Associated incident ID
            format: Report format (pdf, json, csv)
            file_path: Path to saved report file
            file_size: Size of the file in bytes

        Returns:
            Report ID for later retrieval
        """
        report_id = str(uuid.uuid4())
        created_at = datetime.now().isoformat()

        try:
            conn = sqlite3.connect(str(self.reports_db_file))
            cursor = conn.cursor()

            cursor.execute('''
                INSERT INTO reports
                (id, incident_id, format, file_path, file_size, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (report_id, incident_id, format, file_path, file_size, created_at))

            conn.commit()
            conn.close()

            print(f"✅ Report saved: {report_id} ({format})")
            return report_id
        except Exception as e:
            print(f"❌ Failed to save report metadata: {e}")
            raise

    def get_report(self, report_id: str) -> Optional[Dict[str, Any]]:
        """Get report metadata by ID."""
        try:
            conn = sqlite3.connect(str(self.reports_db_file))
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            cursor.execute('''
                SELECT * FROM reports WHERE id = ?
            ''', (report_id,))

            row = cursor.fetchone()
            conn.close()

            if row:
                return dict(row)
            return None
        except Exception as e:
            print(f"❌ Failed to get report: {e}")
            return None

    def get_reports_by_incident(self, incident_id: str) -> List[Dict[str, Any]]:
        """Get all reports for a specific incident."""
        try:
            conn = sqlite3.connect(str(self.reports_db_file))
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            cursor.execute('''
                SELECT * FROM reports
                WHERE incident_id = ?
                ORDER BY created_at DESC
            ''', (incident_id,))

            rows = cursor.fetchall()
            conn.close()

            return [dict(row) for row in rows]
        except Exception as e:
            print(f"❌ Failed to get reports by incident: {e}")
            return []

    def list_reports(
        self,
        limit: int = 100,
        offset: int = 0,
        format_filter: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        List all reports with optional filtering.

        Args:
            limit: Maximum number of reports to return
            offset: Offset for pagination
            format_filter: Optional format filter (pdf, json, csv)

        Returns:
            List of report metadata dictionaries
        """
        try:
            conn = sqlite3.connect(str(self.reports_db_file))
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            if format_filter:
                cursor.execute('''
                    SELECT * FROM reports
                    WHERE format = ?
                    ORDER BY created_at DESC
                    LIMIT ? OFFSET ?
                ''', (format_filter, limit, offset))
            else:
                cursor.execute('''
                    SELECT * FROM reports
                    ORDER BY created_at DESC
                    LIMIT ? OFFSET ?
                ''', (limit, offset))

            rows = cursor.fetchall()
            conn.close()

            return [dict(row) for row in rows]
        except Exception as e:
            print(f"❌ Failed to list reports: {e}")
            return []

    def increment_download_count(self, report_id: str) -> bool:
        """Increment download count for a report."""
        try:
            conn = sqlite3.connect(str(self.reports_db_file))
            cursor = conn.cursor()

            cursor.execute('''
                UPDATE reports
                SET download_count = download_count + 1
                WHERE id = ?
            ''', (report_id,))

            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"❌ Failed to update download count: {e}")
            return False

    def get_report_stats(self) -> Dict[str, Any]:
        """Get statistics about saved reports."""
        try:
            conn = sqlite3.connect(str(self.reports_db_file))
            cursor = conn.cursor()

            # Total reports
            cursor.execute('SELECT COUNT(*) FROM reports')
            total_reports = cursor.fetchone()[0]

            # Reports by format
            cursor.execute('''
                SELECT format, COUNT(*) as count
                FROM reports
                GROUP BY format
            ''')
            by_format = {row[0]: row[1] for row in cursor.fetchall()}

            # Total downloads
            cursor.execute('SELECT SUM(download_count) FROM reports')
            total_downloads = cursor.fetchone()[0] or 0

            # Total storage used
            cursor.execute('SELECT SUM(file_size) FROM reports')
            total_size_bytes = cursor.fetchone()[0] or 0

            conn.close()

            return {
                'total_reports': total_reports,
                'by_format': by_format,
                'total_downloads': total_downloads,
                'total_size_mb': round(total_size_bytes / (1024 * 1024), 2)
            }
        except Exception as e:
            print(f"❌ Failed to get report stats: {e}")
            return {
                'total_reports': 0,
                'by_format': {},
                'total_downloads': 0,
                'total_size_mb': 0
            }
