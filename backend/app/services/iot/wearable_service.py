import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
import uuid

from app.services.environmental.aggregator import aggregator
from app.schemas.alerts import AlertItem, TelemetryPayload
from app.schemas.profile import (
    UserProfile, 
    UserCategory, 
    AgeGroup, 
    OutdoorTimeDuration, 
    SensitivityPreference, 
    NotificationPreferences
)

logger = logging.getLogger("atmosai.wearable")

class WearableAndAlertService:
    def __init__(self):
        self.telemetry_history: List[TelemetryPayload] = []
        self.user_profiles: Dict[str, UserProfile] = {
            "default_user": UserProfile(
                id="default_user",
                full_name="Active Citizen",
                email="user@atmosai.org",
                age_group=AgeGroup.AGE_26_45,
                city="Bengaluru",
                locality="Central",
                preferred_language="en",
                user_category=UserCategory.GENERAL_PUBLIC,
                outdoor_time_duration=OutdoorTimeDuration.DURATION_1_TO_3H,
                preferred_activities=["walking", "running", "commuting"],
                environmental_info_preferences=["pm25_focus", "weather_focus", "health_advice"],
                sensitivity_preference=SensitivityPreference.NONE,
                notifications=NotificationPreferences(
                    surge_warnings=True,
                    daily_morning_brief=True,
                    commute_window_alerts=True,
                    high_pollution_threshold=100,
                    improving_air_alerts=True
                ),
                primary_location="bengaluru_central",
                onboarding_completed=True,
                onboarding_step=5
            )
        }

    def get_user_profile(self, user_id: str = "default_user") -> UserProfile:
        if user_id not in self.user_profiles:
            self.user_profiles[user_id] = UserProfile(
                id=user_id,
                full_name="New Citizen",
                email=f"{user_id}@atmosai.org" if "@" not in user_id else user_id,
                onboarding_completed=False,
                onboarding_step=1
            )
        return self.user_profiles[user_id]

    def update_user_profile(self, user_id: str, updates: Dict[str, Any]) -> UserProfile:
        current = self.get_user_profile(user_id)
        current_data = current.model_dump()
        
        # Merge nested notifications if provided
        if "notifications" in updates and isinstance(updates["notifications"], dict):
            current_data["notifications"].update(updates["notifications"])
            del updates["notifications"]
        elif "notifications" in updates and hasattr(updates["notifications"], "model_dump"):
            current_data["notifications"].update(updates["notifications"].model_dump())
            del updates["notifications"]
            
        current_data.update({k: v for k, v in updates.items() if v is not None})
        updated_profile = UserProfile(**current_data)
        self.user_profiles[user_id] = updated_profile
        return updated_profile

    async def get_system_alerts(
        self, 
        profile_type: Optional[str] = None, 
        user_id: str = "default_user",
        location: Optional[str] = None
    ) -> List[AlertItem]:
        """
        Dynamically derives smart alerts based on current atmospheric conditions across Bengaluru,
        filtered strictly by the user's notification preferences and CPCB safety recommendations.
        """
        from app.services.alerts.smart_alert_service import smart_alert_service
        profile = self.get_user_profile(user_id)
        if profile_type:
            p_data = profile.model_dump()
            p_data["profile_type"] = profile_type
            profile = UserProfile(**p_data)
        return await smart_alert_service.generate_smart_alerts(profile, target_location=location)

    def record_telemetry(self, payload: TelemetryPayload) -> Dict[str, Any]:
        self.telemetry_history.append(payload)
        if len(self.telemetry_history) > 100:
            self.telemetry_history.pop(0)

        risk_alert = None
        if payload.heart_rate and payload.heart_rate > 140 and payload.ambient_pm25 and payload.ambient_pm25 > 60:
            risk_alert = (
                "High heart rate detected in elevated ambient PM2.5 environment. "
                "Consider cooling down or moving to an indoor ventilated area."
            )

        return {
            "status": "success",
            "received_at": datetime.now(timezone.utc).isoformat(),
            "device_id": payload.device_id,
            "contextual_advisory": risk_alert,
            "disclaimer": "Wearable prototype data is contextual and does not constitute medical monitoring."
        }

wearable_service = WearableAndAlertService()
