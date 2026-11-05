from abc import ABC, abstractmethod
from typing import Dict, Any
from app.schemas.ai import AIAdviceResponse

class BaseAIProvider(ABC):
    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Name of the AI provider (e.g. 'gemini', 'bedrock', 'rule_fallback')"""
        pass

    @abstractmethod
    async def generate_advice(self, context: Dict[str, Any]) -> AIAdviceResponse:
        """
        Generates structured environmental explanations and activity guidance.
        Context includes live telemetry, multi-horizon forecasts, user profile, and location.
        """
        pass

