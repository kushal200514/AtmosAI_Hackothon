from pydantic import BaseModel, Field, ConfigDict, model_validator
from typing import Optional, List, Dict, Any
from enum import Enum

class UserCategory(str, Enum):
    STUDENT = "student"
    RUNNER = "runner"
    CYCLIST = "cyclist"
    OFFICE_COMMUTER = "office_commuter"
    OUTDOOR_WORKER = "outdoor_worker"
    PARENT = "parent"
    GENERAL_PUBLIC = "general_public"

class ProfileType(str, Enum):
    RUNNER = "runner"
    CYCLIST = "cyclist"
    RESPIRATORY_SENSITIVE = "respiratory_sensitive"
    PARENT = "parent"
    DELIVERY_WORKER = "delivery_worker"
    OUTDOOR_WORKER = "outdoor_worker"
    OFFICE_COMMUTER = "office_commuter"
    STUDENT = "student"
    GENERAL_PUBLIC = "general_public"

class AgeGroup(str, Enum):
    UNDER_18 = "under_18"
    AGE_18_25 = "18_25"
    AGE_26_45 = "26_45"
    AGE_46_65 = "46_65"
    AGE_65_PLUS = "65_plus"

class OutdoorTimeDuration(str, Enum):
    LESS_THAN_1H = "less_than_1h"
    DURATION_1_TO_3H = "1_to_3h"
    DURATION_3_TO_6H = "3_to_6h"
    MORE_THAN_6H = "more_than_6h"

class SensitivityPreference(str, Enum):
    NONE = "none"
    ASTHMA_RESPIRATORY = "asthma_respiratory"
    ALLERGIES = "allergies"
    ELDERLY_CHILD_CARE = "elderly_child_care"
    CARDIOVASCULAR = "cardiovascular"

class NotificationPreferences(BaseModel):
    high_pollution_threshold: int = Field(default=100, ge=30, le=500)
    use_recommended_threshold: bool = True
    custom_threshold: Optional[int] = Field(default=None, ge=30, le=500)
    
    threshold_crossing_alerts: bool = True
    deterioration_alerts: bool = True
    forecast_alerts: bool = True
    surge_warnings: bool = True
    daily_morning_brief: bool = True
    commute_window_alerts: bool = True
    improving_air_alerts: bool = True
    
    monitored_locations: List[str] = Field(
        default_factory=lambda: [
            "bengaluru_central",
            "silk_board",
            "electronic_city",
            "hebbal",
            "peenya",
            "yelahanka",
            "koramangala"
        ]
    )

class ActivityWindowScore(BaseModel):
    activity_name: str
    horizon_label: str
    target_time: str
    predicted_pm25: float
    suitability_score: int = Field(..., ge=0, le=100, description="0-100 score")
    status: str = Field(..., description="'Optimal', 'Moderate', 'Challenging'")
    explanation: str

class PersonalizedViewConfig(BaseModel):
    widget_order: List[str]
    visible_widgets: List[str]
    priority_headline: str
    primary_alert_types: List[str]
    planner_activities: List[str]
    language: str = "en"
    cautious_mode: bool = False

class UserProfileBase(BaseModel):
    full_name: str = "Atmos Citizen"
    email: Optional[str] = "user@atmosai.org"
    profile_type: Optional[str] = None
    age_group: Optional[AgeGroup] = AgeGroup.AGE_26_45
    city: str = "Bengaluru"
    locality: str = "Central"
    preferred_language: str = "en"  # 'en', 'hi', 'kn'
    user_category: UserCategory = UserCategory.GENERAL_PUBLIC
    outdoor_time_duration: OutdoorTimeDuration = OutdoorTimeDuration.DURATION_1_TO_3H
    preferred_activities: List[str] = Field(default_factory=lambda: ["walking", "running", "commuting"])
    environmental_info_preferences: List[str] = Field(default_factory=lambda: ["pm25_focus", "weather_focus", "health_advice"])
    sensitivity_preference: SensitivityPreference = SensitivityPreference.NONE
    notifications: NotificationPreferences = Field(default_factory=NotificationPreferences)
    primary_location: Optional[str] = "bengaluru_central"
    onboarding_completed: bool = False
    onboarding_step: int = 1
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

    @model_validator(mode="before")
    @classmethod
    def reconcile_category_and_type(cls, data: Any) -> Any:
        if isinstance(data, dict):
            pt = data.get("profile_type")
            uc = data.get("user_category")
            if pt and not uc:
                pt_str = str(pt.value if hasattr(pt, "value") else pt).lower()
                if pt_str == "runner":
                    data["user_category"] = UserCategory.RUNNER
                elif pt_str in ("delivery_worker", "outdoor_worker"):
                    data["user_category"] = UserCategory.OUTDOOR_WORKER
                elif pt_str == "parent":
                    data["user_category"] = UserCategory.PARENT
                elif pt_str == "student":
                    data["user_category"] = UserCategory.STUDENT
                elif pt_str == "office_commuter":
                    data["user_category"] = UserCategory.OFFICE_COMMUTER
                elif pt_str == "respiratory_sensitive":
                    data["user_category"] = UserCategory.GENERAL_PUBLIC
                    data["sensitivity_preference"] = SensitivityPreference.ASTHMA_RESPIRATORY
                else:
                    data["user_category"] = UserCategory.GENERAL_PUBLIC
            
            if not pt:
                cat_val = data.get("user_category")
                data["profile_type"] = str(cat_val.value if hasattr(cat_val, "value") else cat_val or "general_public")
        return data

class UserProfile(UserProfileBase):
    id: str = "default_user"

class UserProfileUpdate(BaseModel):
    full_name: Optional[str] = None
    email: Optional[str] = None
    age_group: Optional[AgeGroup] = None
    city: Optional[str] = None
    locality: Optional[str] = None
    preferred_language: Optional[str] = None
    user_category: Optional[UserCategory] = None
    outdoor_time_duration: Optional[OutdoorTimeDuration] = None
    preferred_activities: Optional[List[str]] = None
    environmental_info_preferences: Optional[List[str]] = None
    sensitivity_preference: Optional[SensitivityPreference] = None
    notifications: Optional[NotificationPreferences] = None
    profile_type: Optional[str] = None
    primary_location: Optional[str] = None
    onboarding_completed: Optional[bool] = None
    onboarding_step: Optional[int] = None

class UserProfileOut(BaseModel):
    profile: UserProfile
    personalization: PersonalizedViewConfig
    model_config = ConfigDict(from_attributes=True)
