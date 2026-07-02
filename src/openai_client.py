"""
OpenAI API client wrapper.
"""

import os
import time
import logging
from openai import OpenAI
from openai import APIError, RateLimitError, APIConnectionError
from .langsmith_config import trace_function, LANGSMITH_ENABLED

logger = logging.getLogger(__name__)

if LANGSMITH_ENABLED:
    logger.info("✅ LangSmith tracing enabled for OpenAI Client")


class OpenAIClient:
    """Wrapper for OpenAI API calls."""

    def __init__(self):
        """Initialize OpenAI client."""
        self.api_key = os.getenv("OPENAI_API_KEY")
        self.base_url = os.getenv("OPENAI_BASE_URL")
        self.model = os.getenv("OPENAI_MODEL", "claude-sonnet")
        self.max_tokens = int(os.getenv("MAX_TOKENS", "2000"))
        self.temperature = float(os.getenv("TEMPERATURE", "0.7"))
        self.retry_attempts = int(os.getenv("RETRY_ATTEMPTS", "3"))

        if not self.api_key:
            raise ValueError("OPENAI_API_KEY environment variable is not set")

        # Initialize OpenAI client with optional base_url
        client_kwargs = {"api_key": self.api_key}
        if self.base_url:
            client_kwargs["base_url"] = self.base_url

        self.client = OpenAI(**client_kwargs)

    @trace_function(name="openai_generate", tags=["llm", "openai"])
    def generate(self, prompt: str) -> str:
        """
        Generate a response from OpenAI.

        Args:
            prompt: The prompt to send to the model

        Returns:
            Generated text response

        Raises:
            Exception: If all retry attempts fail
        """
        last_error = None

        for attempt in range(self.retry_attempts):
            try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "user", "content": prompt}
                    ],
                    max_tokens=self.max_tokens,
                    temperature=self.temperature
                )

                # Extract the response text
                return response.choices[0].message.content

            except RateLimitError as e:
                last_error = e
                wait_time = 2 ** attempt
                print(f"Rate limit hit. Retrying in {wait_time}s... (attempt {attempt + 1}/{self.retry_attempts})")
                time.sleep(wait_time)

            except APIConnectionError as e:
                last_error = e
                wait_time = 2 ** attempt
                print(f"Connection error. Retrying in {wait_time}s... (attempt {attempt + 1}/{self.retry_attempts})")
                time.sleep(wait_time)

            except APIError as e:
                last_error = e
                if attempt < self.retry_attempts - 1:
                    wait_time = 2 ** attempt
                    print(f"API error: {e}. Retrying in {wait_time}s... (attempt {attempt + 1}/{self.retry_attempts})")
                    time.sleep(wait_time)
                else:
                    raise Exception(f"OpenAI API error after {self.retry_attempts} attempts: {e}")

            except Exception as e:
                raise Exception(f"Unexpected error during OpenAI API call: {e}")

        raise Exception(f"Failed to generate response after {self.retry_attempts} attempts. Last error: {last_error}")

    def analyze(self, prompt: str) -> str:
        """Alias for generate method (backward compatibility)."""
        return self.generate(prompt)
