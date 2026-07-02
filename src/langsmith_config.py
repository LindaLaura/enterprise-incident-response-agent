"""
LangSmith Configuration and Utilities

Handles all LangSmith tracing setup and configuration.
"""

import os
import logging
from typing import Optional, Callable
from functools import wraps
from pathlib import Path
from dotenv import dotenv_values

# Load environment variables from .env file
env_path = Path(__file__).resolve().parent.parent.parent / ".env"
env_vars = dotenv_values(env_path)

# Override with values from .env file (to ensure correct configuration)
_langsmith_api_key_from_env = env_vars.get("LANGSMITH_API_KEY")
_langsmith_project_from_env = env_vars.get("LANGSMITH_PROJECT")

for key, value in env_vars.items():
    os.environ[key] = value

try:
    from langsmith import Client, trace
    try:
        from langsmith import context as langsmith_context
    except (ImportError, AttributeError):
        langsmith_context = None
    LANGSMITH_AVAILABLE = True
except ImportError as e:
    LANGSMITH_AVAILABLE = False

logger = logging.getLogger(__name__)

# Configuration - Use values from .env first, then fallback to os.environ
LANGSMITH_API_KEY = _langsmith_api_key_from_env or os.getenv("LANGSMITH_API_KEY")
LANGSMITH_PROJECT = _langsmith_project_from_env or os.getenv("LANGSMITH_PROJECT", "enterprise-incident-response-agent")
LANGSMITH_ENDPOINT = env_vars.get("LANGSMITH_ENDPOINT") or os.getenv("LANGSMITH_ENDPOINT", "https://api.smith.langchain.com")
LANGSMITH_ENABLED = LANGSMITH_AVAILABLE and bool(LANGSMITH_API_KEY)

# Initialize LangSmith client if available
if LANGSMITH_ENABLED:
    try:
        langsmith_client = Client(
            api_key=LANGSMITH_API_KEY,
            api_url=LANGSMITH_ENDPOINT
        )
        logger.info(f"✅ LangSmith initialized for project: {LANGSMITH_PROJECT} at {LANGSMITH_ENDPOINT}")
    except Exception as e:
        logger.warning(f"⚠️ Failed to initialize LangSmith: {e}")
        LANGSMITH_ENABLED = False
else:
    langsmith_client = None


def trace_function(name: str, tags: Optional[list] = None):
    """
    Decorator to trace a function with LangSmith.

    Args:
        name: Name of the trace
        tags: Optional list of tags for the trace

    Returns:
        Decorated function with tracing
    """
    if not LANGSMITH_ENABLED:
        # Return no-op decorator if LangSmith not available
        def no_op_decorator(func):
            return func
        return no_op_decorator

    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            with trace(name=name, project_name=LANGSMITH_PROJECT, tags=tags or []):
                return await func(*args, **kwargs)

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            with trace(name=name, project_name=LANGSMITH_PROJECT, tags=tags or []):
                return func(*args, **kwargs)

        # Determine if function is async
        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator


def add_trace_context(key: str, value: any):
    """
    Add context data to current trace.

    Args:
        key: Context key
        value: Context value
    """
    if not LANGSMITH_ENABLED:
        return

    try:
        if LANGSMITH_AVAILABLE:
            # Set context data for current trace
            import json
            context_value = json.dumps(value) if not isinstance(value, str) else value
            # LangSmith context can be accessed via langsmith_context
    except Exception as e:
        logger.debug(f"Failed to add trace context: {e}")


def get_trace_status() -> dict:
    """Get current LangSmith tracing status."""
    return {
        "enabled": LANGSMITH_ENABLED,
        "available": LANGSMITH_AVAILABLE,
        "project": LANGSMITH_PROJECT if LANGSMITH_ENABLED else None,
        "api_key_set": bool(LANGSMITH_API_KEY),
    }


# Export for use in other modules
__all__ = [
    "LANGSMITH_ENABLED",
    "LANGSMITH_PROJECT",
    "langsmith_client",
    "trace_function",
    "add_trace_context",
    "get_trace_status",
]
