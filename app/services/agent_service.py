"""Reusable tool-agent service for non-CLI callers."""

from collections.abc import Callable
import logging


logger = logging.getLogger(__name__)


class AgentService:
    """Invoke a prepared agent and normalize its final message."""

    def __init__(self, executor: object):
        self._executor = executor

    def answer(self, user_input: str) -> str:
        """Run the agent and return its final response as text."""
        if not user_input.strip():
            raise ValueError("user_input must not be empty")
        response = self._executor.invoke(
            {"messages": [{"role": "user", "content": user_input}]}
        )
        messages = response.get("messages", []) if isinstance(response, dict) else []
        if messages:
            result = str(messages[-1].content)
        else:
            result = str(response)
        logger.info("Agent request completed")
        return result
