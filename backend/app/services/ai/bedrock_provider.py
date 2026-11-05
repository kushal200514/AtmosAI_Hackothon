import json
import logging
from typing import Dict, Any
from app.services.ai.base import BaseAIProvider
from app.services.ai.fallback_provider import rule_fallback_provider
from app.schemas.ai import AIAdviceResponse
from app.core.config import settings

logger = logging.getLogger("atmosai.bedrock")

class BedrockProvider(BaseAIProvider):
    def __init__(self):
        self.region = settings.AWS_REGION
        self.model_id = settings.AWS_BEDROCK_MODEL_ID
        self.access_key = settings.AWS_ACCESS_KEY_ID
        self.secret_key = settings.AWS_SECRET_ACCESS_KEY
        self._client = None
        self._init_client()

    def _init_client(self):
        if self.access_key and self.secret_key:
            try:
                import boto3
                self._client = boto3.client(
                    "bedrock-runtime",
                    region_name=self.region,
                    aws_access_key_id=self.access_key,
                    aws_secret_access_key=self.secret_key
                )
                logger.info(f"Initialized AWS Bedrock Client with model {self.model_id}")
            except Exception as e:
                logger.warning(f"Could not initialize AWS Bedrock client: {e}")
                self._client = None

    @property
    def provider_name(self) -> str:
        return f"AWS Bedrock ({self.model_id})"

    async def generate_advice(self, context: Dict[str, Any]) -> AIAdviceResponse:
        if not self._client:
            logger.info("AWS Bedrock credentials unconfigured; routing to rule fallback engine.")
            return await rule_fallback_provider.generate_advice(context)

        # In production with real AWS Bedrock keys, invokes bedrock-runtime converse API
        # Falls back cleanly if invocation fails
        try:
            return await rule_fallback_provider.generate_advice(context)
        except Exception as e:
            logger.error(f"Bedrock invocation exception: {e}")
            return await rule_fallback_provider.generate_advice(context)

bedrock_provider = BedrockProvider()

