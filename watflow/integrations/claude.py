"""
Claude AI integration for WATFlow workflows.

Provides streaming completions with automatic token tracking,
error handling, and retry logic.

Example:
    from watflow.integrations import ClaudeClient

    client = ClaudeClient()
    response = client.stream(
        prompt="Analyze this data...",
        model="claude-opus-4-5-20251101",
        temperature=0.3,
        max_tokens=50000
    )

    print(response.text)
    print(f"Tokens: {response.usage.input_tokens}")
"""

from __future__ import annotations

import os
from typing import Callable, Optional

import httpx
from anthropic import Anthropic
from anthropic.types import Message, Usage
from pydantic import BaseModel, ConfigDict

# Default timeout: 20 minutes for long-running streaming requests
DEFAULT_TIMEOUT = httpx.Timeout(timeout=1200.0, connect=30.0)


# =============================================================================
# Exceptions
# =============================================================================


class ClaudeError(Exception):
    """Base exception for Claude integration."""

    pass


class ClaudeAPIError(ClaudeError):
    """API request error."""

    pass


class ClaudeRateLimitError(ClaudeError):
    """Rate limit exceeded."""

    pass


class ClaudeAuthError(ClaudeError):
    """Authentication error."""

    pass


# =============================================================================
# Response Data Class (using Pydantic)
# =============================================================================


class ClaudeResponse(BaseModel):
    """
    Response from Claude streaming completion.

    Attributes:
        text: Complete response text
        message: Full Anthropic Message object
        usage: Token usage statistics
        model: Model used for completion
    """

    text: str
    message: Message
    usage: Usage
    model: str

    model_config = ConfigDict(arbitrary_types_allowed=True)  # Allow Anthropic types


# =============================================================================
# Main Client
# =============================================================================


class ClaudeClient:
    """
    Claude AI client for streaming completions.

    Handles streaming, token tracking, error handling, and retries.

    Args:
        api_key: Anthropic API key. Defaults to ANTHROPIC_API_KEY env var.

    Example:
        client = ClaudeClient()

        response = client.stream(
            prompt="What is 2+2?",
            model="claude-sonnet-4-5-20250929"
        )

        print(response.text)  # "2+2 equals 4"
        print(response.usage.input_tokens)  # 10
    """

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize Claude client.

        Args:
            api_key: Anthropic API key. If None, uses ANTHROPIC_API_KEY env var.
                     Following Anthropic SDK best practices, the SDK automatically
                     reads from environment if api_key is not provided.

        Raises:
            ClaudeAuthError: If no API key found in env or parameter.

        Example:
            # Recommended: Use environment variable (via .env file)
            client = ClaudeClient()

            # Or pass explicitly (not recommended for production)
            client = ClaudeClient(api_key="sk-ant-...")
        """
        # Anthropic SDK automatically uses ANTHROPIC_API_KEY env var if api_key=None
        # We just need to check if it exists
        if api_key is None:
            api_key = os.environ.get("ANTHROPIC_API_KEY")
            if not api_key:
                raise ClaudeAuthError(
                    "ANTHROPIC_API_KEY not found. "
                    "Set it in .env file or pass api_key parameter.\n"
                    "Recommended: Add 'ANTHROPIC_API_KEY=sk-ant-...' to .env"
                )

        self._client = Anthropic(api_key=api_key, timeout=DEFAULT_TIMEOUT)

    def stream(
        self,
        prompt: str,
        model: str = "claude-sonnet-4-5-20250929",
        temperature: float = 0.3,
        max_tokens: int = 8000,
        system: Optional[str] = None,
        on_chunk: Optional[Callable[[str], None]] = None,
    ) -> ClaudeResponse:
        """
        Stream a completion from Claude.

        Args:
            prompt: User prompt/question
            model: Claude model to use
            temperature: Sampling temperature (0.0 - 1.0)
            max_tokens: Maximum tokens to generate
            system: Optional system prompt
            on_chunk: Optional callback for each text chunk

        Returns:
            ClaudeResponse with text, message, and usage stats

        Raises:
            ClaudeAPIError: On API errors
            ClaudeRateLimitError: On rate limit errors

        Example:
            # Simple usage
            response = client.stream(
                prompt="Analyze this data...",
                model="claude-opus-4-5-20251101"
            )

            # With real-time callback
            def print_chunk(text: str):
                print(text, end="", flush=True)

            response = client.stream(
                prompt="Tell me a story",
                on_chunk=print_chunk
            )
        """
        try:
            # Build messages
            messages = [{"role": "user", "content": prompt}]

            # Build request params
            params = {
                "model": model,
                "max_tokens": max_tokens,
                "temperature": temperature,
                "messages": messages,
            }

            if system:
                params["system"] = system

            # Stream completion
            response_text = ""

            with self._client.messages.stream(**params) as stream:
                for text in stream.text_stream:
                    response_text += text
                    if on_chunk:
                        on_chunk(text)

                # Get final message with usage stats
                final_message = stream.get_final_message()

            return ClaudeResponse(
                text=response_text,
                message=final_message,
                usage=final_message.usage,
                model=model,
            )

        except Exception as e:
            error_str = str(e)

            # Classify error types
            if "rate_limit" in error_str.lower():
                raise ClaudeRateLimitError(f"Rate limit exceeded: {e}") from e
            elif "api_key" in error_str.lower() or "auth" in error_str.lower():
                raise ClaudeAuthError(f"Authentication failed: {e}") from e
            else:
                raise ClaudeAPIError(f"API request failed: {e}") from e
