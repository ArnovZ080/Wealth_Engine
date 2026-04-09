"""
Base Agent — Abstract shell for AI agents.

Handles shared LLM client logic, retry mechanisms, and structured output parsing.
"""

import abc
import logging
from typing import Any, Dict, Optional
from pydantic import BaseModel

logger = logging.getLogger(__name__)

class BaseAgent(abc.ABC):
    """
    Abstract base for Gemini and Claude agents.
    """
    def __init__(self, name: str):
        self.name = name

    @abc.abstractmethod
    async def invoke(self, prompt: str, context: Optional[Dict[str, Any]] = None) -> Any:
        """Execute the agent loop."""
        pass

class LLMResponse(BaseModel):
    """Standardized shell for raw LLM outputs."""
    raw_text: str
    parsed_json: Optional[Dict[str, Any]] = None
    usage_metadata: Dict[str, Any] = {}
