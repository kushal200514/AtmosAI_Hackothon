import logging
from typing import Dict, Any, Optional

from app.core.config import settings
from app.services.ai.base import BaseAIProvider
from app.services.ai.gemini_provider import gemini_provider
from app.services.ai.bedrock_provider import bedrock_provider
from app.services.ai.fallback_provider import rule_fallback_provider
from app.services.recommendations.ai_explanation_service import ai_explanation_service
from app.services.environmental.aggregator import aggregator
from app.services.forecasting.ml_service import ml_forecaster
from app.schemas.ai import AIAdviceResponse
from app.schemas.profile import ProfileType, UserCategory

logger = logging.getLogger("atmosai.ai")

class AIService:
    def __init__(self):
        self._provider = self._resolve_provider()

    def _resolve_provider(self) -> BaseAIProvider:
        provider_name = settings.AI_PROVIDER.lower().strip()
        if provider_name == "gemini":
            return ai_explanation_service
        elif provider_name == "bedrock":
            return bedrock_provider
        elif provider_name == "rule_fallback":
            return rule_fallback_provider
        else:
            logger.info(f"Unrecognized AI provider '{provider_name}'; defaulting to Deterministic Engine + Gemini Explanation.")
            return ai_explanation_service

    async def get_advice(
        self, 
        location_slug: str = "bengaluru_central", 
        profile_type: Optional[Any] = None,
        user_id: str = "default_user"
    ) -> AIAdviceResponse:
        live = await aggregator.get_live_data(location_slug)
        forecast = await ml_forecaster.predict(location_slug)

        from app.services.iot.wearable_service import wearable_service
        user_prof = wearable_service.get_user_profile(user_id)

        resolved_profile_type = profile_type if profile_type is not None else user_prof.user_category
        
        # Check sensitivity or cautious mode
        cautious = (
            (user_prof.sensitivity_preference.value != "none") 
            or (user_prof.user_category == UserCategory.PARENT)
            or (str(resolved_profile_type).lower() == "parent")
            or (str(resolved_profile_type).lower() == "respiratory_sensitive")
        )

        notif = getattr(user_prof, "notifications", None)
        notif_dict = notif.model_dump() if hasattr(notif, "model_dump") else {}

        context = {
            "live": live,
            "forecast": forecast,
            "profile_type": resolved_profile_type,
            "user_category": user_prof.user_category,
            "preferred_language": user_prof.preferred_language,
            "preferred_activities": user_prof.preferred_activities,
            "outdoor_time_duration": getattr(user_prof, "outdoor_time_duration", "1-2 hours"),
            "sensitivity_preference": user_prof.sensitivity_preference.value if hasattr(user_prof.sensitivity_preference, "value") else str(user_prof.sensitivity_preference),
            "notification_preferences": notif_dict,
            "cautious_mode": cautious
        }

        return await self._provider.generate_advice(context)

ai_service = AIService()
