"""
LLM Integration module for OpenAI API communication.

Handles all interaction with the OpenAI API including:
- Model configuration and initialization
- Response generation with retry logic
- Token usage tracking
- Error handling
"""

import os
import time
from typing import List, Dict, Any, Optional
from openai import OpenAI, OpenAIError
import logging

logger = logging.getLogger(__name__)

# Models that require 'max_completion_tokens' instead of the legacy 'max_tokens'.
# Includes the o1/o3 reasoning series and GPT-5+.
_MAX_COMPLETION_TOKENS_PREFIXES = ("o1", "o3", "gpt-5")

# Models that do not support a custom temperature value (only the API default is accepted).
# Includes the o1/o3 reasoning series and GPT-5+.
_NO_TEMPERATURE_PREFIXES = ("o1", "o3", "gpt-5")


def _max_tokens_param(model: str) -> str:
    """Return the correct token-limit parameter name for *model*."""
    if any(model.startswith(p) for p in _MAX_COMPLETION_TOKENS_PREFIXES):
        return "max_completion_tokens"
    return "max_tokens"


def _supports_temperature(model: str) -> bool:
    """Return False for models that reject a custom temperature (GPT-5, o-series)."""
    return not any(model.startswith(p) for p in _NO_TEMPERATURE_PREFIXES)


class LLMIntegration:
    """Manages communication with OpenAI's API."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        max_retries: int = 3,
        timeout: int = 30
    ):
        """
        Initialize LLM integration.

        Args:
            api_key: OpenAI API key (defaults to env var OPENAI_API_KEY)
            model: Model to use (defaults to env var OPENAI_MODEL, then gpt-4o-mini)
            max_retries: Maximum number of retry attempts on failure
            timeout: Request timeout in seconds
        """
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OpenAI API key not found. Set OPENAI_API_KEY environment variable.")

        self.model = model or os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        self.max_retries = max_retries
        self.timeout = timeout

        # Initialize OpenAI client
        self.client = OpenAI(api_key=self.api_key)

        # Track usage statistics
        self.total_tokens_used = 0
        self.total_requests = 0
        self.total_errors = 0

        logger.info(f"LLM Integration initialized with model: {self.model}")

    def generate_response(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        tools: Optional[List[Dict[str, Any]]] = None,
        tool_choice: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generate a response from the LLM.

        Args:
            messages: List of message dicts with 'role' and 'content'
            temperature: Sampling temperature (0.0 to 2.0)
            max_tokens: Maximum tokens in response (None for model default)
            tools: Optional list of function/tool definitions
            tool_choice: How to use tools ("auto", "none", or specific tool)

        Returns:
            Dict containing:
                - content: The response text (if no tool calls)
                - tool_calls: List of tool calls (if tools were used)
                - usage: Token usage statistics
                - finish_reason: Why the model stopped generating

        Raises:
            OpenAIError: If the API request fails after retries
        """
        attempt = 0
        last_error = None

        while attempt < self.max_retries:
            try:
                # Build request parameters
                request_params = {
                    "model": self.model,
                    "messages": messages,
                    "timeout": self.timeout
                }

                if _supports_temperature(self.model):
                    request_params["temperature"] = temperature

                if max_tokens:
                    request_params[_max_tokens_param(self.model)] = max_tokens

                if tools:
                    request_params["tools"] = tools
                    if tool_choice:
                        request_params["tool_choice"] = tool_choice

                # Make API request
                logger.debug(
                    "LLM call starting (model=%s, messages=%d, tools=%s, attempt=%d)",
                    self.model,
                    len(messages),
                    tools is not None,
                    attempt + 1,
                )
                start_time = time.time()
                response = self.client.chat.completions.create(**request_params)
                elapsed_time = time.time() - start_time

                # Extract response data
                choice = response.choices[0]
                message = choice.message

                # Update statistics
                self.total_tokens_used += response.usage.total_tokens
                self.total_requests += 1

                # Log success
                logger.info(
                    f"LLM response generated in {elapsed_time:.2f}s "
                    f"(tokens: {response.usage.total_tokens})",
                    extra={
                        "model": self.model,
                        "token_count": response.usage.total_tokens,
                        "latency_ms": elapsed_time * 1000,
                    },
                )
                logger.debug(
                    "LLM response content (finish_reason=%s): %r",
                    choice.finish_reason,
                    (message.content or "")[:500],
                )
                if message.tool_calls:
                    logger.debug(
                        "LLM response tool_calls: %s",
                        [tc.function.name for tc in message.tool_calls],
                    )

                # Build result
                result = {
                    "finish_reason": choice.finish_reason,
                    "usage": {
                        "prompt_tokens": response.usage.prompt_tokens,
                        "completion_tokens": response.usage.completion_tokens,
                        "total_tokens": response.usage.total_tokens
                    },
                    "response_time": elapsed_time
                }

                # Add content or tool calls
                if message.content:
                    result["content"] = message.content

                if message.tool_calls:
                    result["tool_calls"] = [
                        {
                            "id": tc.id,
                            "type": tc.type,
                            "function": {
                                "name": tc.function.name,
                                "arguments": tc.function.arguments
                            }
                        }
                        for tc in message.tool_calls
                    ]

                return result

            except OpenAIError as e:
                attempt += 1
                last_error = e
                self.total_errors += 1

                logger.warning(
                    f"LLM request failed (attempt {attempt}/{self.max_retries}): {str(e)}"
                )

                if attempt < self.max_retries:
                    # Exponential backoff
                    sleep_time = 2 ** attempt
                    logger.info(f"Retrying in {sleep_time} seconds...")
                    time.sleep(sleep_time)

        # All retries failed
        logger.error(f"LLM request failed after {self.max_retries} attempts")
        raise last_error

    def get_statistics(self) -> Dict[str, Any]:
        """
        Get usage statistics.

        Returns:
            Dict with total_tokens_used, total_requests, total_errors
        """
        return {
            "total_tokens_used": self.total_tokens_used,
            "total_requests": self.total_requests,
            "total_errors": self.total_errors,
            "model": self.model
        }

    def reset_statistics(self):
        """Reset usage statistics to zero."""
        self.total_tokens_used = 0
        self.total_requests = 0
        self.total_errors = 0
        logger.info("LLM statistics reset")
