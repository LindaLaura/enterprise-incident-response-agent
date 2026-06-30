"""
Base Agent class for incident response system.

Provides common interface for all agents.
"""

from abc import ABC, abstractmethod
from enum import Enum
from typing import Any, Dict, Optional
from datetime import datetime
import time


class AgentStatus(str, Enum):
    """Agent execution status."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


class Agent(ABC):
    """Base class for incident response agents."""

    def __init__(self, name: str, description: str):
        """
        Initialize agent.

        Args:
            name: Agent name
            description: What this agent does
        """
        self.name = name
        self.description = description
        self.status = AgentStatus.PENDING
        self.start_time = None
        self.end_time = None
        self.duration = None
        self.output = None
        self.error = None

    @abstractmethod
    async def execute(self, context: Dict[str, Any]) -> Any:
        """
        Execute agent logic.

        Args:
            context: Shared context with analysis data

        Returns:
            Agent output result
        """
        pass

    async def run(self, context: Dict[str, Any]) -> Any:
        """
        Run agent with status tracking.

        Args:
            context: Shared context

        Returns:
            Agent output
        """
        self.status = AgentStatus.IN_PROGRESS
        self.start_time = datetime.now()

        try:
            self.output = await self.execute(context)
            self.status = AgentStatus.COMPLETED
            return self.output
        except Exception as e:
            self.error = str(e)
            self.status = AgentStatus.FAILED
            raise
        finally:
            self.end_time = datetime.now()
            if self.start_time and self.end_time:
                self.duration = f"{(self.end_time - self.start_time).total_seconds():.1f}s"

    def get_status(self) -> Dict[str, Any]:
        """Get agent status snapshot."""
        return {
            "name": self.name,
            "description": self.description,
            "status": self.status.value,
            "duration": self.duration,
            "error": self.error,
            "has_output": self.output is not None
        }
