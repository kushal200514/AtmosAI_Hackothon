from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from app.schemas.profile import ProfileType, UserCategory

class ActivityGuidance(BaseModel):
    outdoor_exercise_allowed: bool
    best_time_window: str
    recommended_duration_minutes: int
    mask_recommendation: str
    indoor_ventilation_advice: str

class PersonalizedRiskAdvisorResponse(BaseModel):
    # Context & User
    user_category: str
    profile_type: str
    location_name: str
    display_name: str
    timestamp_iso: str
    
    # Required Outputs
    current_environmental_status: str
    current_aqi: Optional[int] = None
    current_pm25: Optional[float] = None
    aqi_category: str
    potential_forecast_deterioration: bool
    deterioration_details: Optional[str] = None
    recommended_action: str
    explanation: str
    data_source: str
    confidence_status: str
    
    # Explanations & Persona Recommendations
    headline_summary: str
    evidence_based_explanation: str
    profile_specific_recommendations: List[str]
    activity_guidance: ActivityGuidance
    environmental_drivers_cited: List[str]
    ai_provider: str
    disclaimer: str = (
        "AtmosAI guidance is for environmental intelligence and risk reduction only. "
        "It does not constitute medical advice or disease diagnosis."
    )
    
    # Additional Context
    preferred_activities: List[str] = []
    outdoor_time_context: Optional[str] = None
    sensitivity_preference: Optional[str] = None
    forecast_trend: str = "stable"

# Backwards compatible alias for existing endpoints
AIAdviceResponse = PersonalizedRiskAdvisorResponse

class AIAdviceRequest(BaseModel):
    location: str = "bengaluru_central"
    profile_type: ProfileType = ProfileType.GENERAL_PUBLIC
    user_id: str = "default_user"
