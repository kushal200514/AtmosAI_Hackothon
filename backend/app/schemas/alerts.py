from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime

class AlertItem(BaseModel):
    id: str
    location_id: Optional[str] = None
    location_name: Optional[str] = None
    alert_type: str = Field(..., description="threshold_crossing, deterioration, forecast_surge, daily_summary, commute_advisory, improving_pollution, high_pollution")
    alert_source: str = Field(default="current_measurement", description="'current_measurement' vs 'forecast_prediction' vs 'daily_summary'")
    severity: str = Field(..., description="low, medium, high, critical")
    title: str
    message: str
    cpcb_category: Optional[str] = Field(default=None, description="Good, Satisfactory, Moderate, Poor, Very Poor, Severe")
    safety_recommendation: Optional[str] = Field(default=None, description="CPCB-aligned safety recommendation")
    sensitivity_note: Optional[str] = Field(default=None, description="Proactive note for sensitive individuals or guardians")
    current_aqi: Optional[int] = None
    predicted_aqi: Optional[int] = None
    profile_category: Optional[str] = None
    disclaimer: str = "AtmosAI environmental guidance is for informational and risk reduction purposes only and does not constitute personalized medical diagnosis or treatment advice."
    timestamp: datetime
    is_read: bool = False

class TelemetryPayload(BaseModel):
    device_id: str
    user_id: Optional[str] = None
    timestamp: datetime
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    heart_rate: Optional[int] = None
    step_count: Optional[int] = None
    activity_type: Optional[str] = "resting"
    ambient_pm25: Optional[float] = None
    source: str = "simulated_wearable_prototype"

class NotificationSettingsUpdate(BaseModel):
    high_pollution_threshold: Optional[int] = Field(default=None, ge=30, le=500)
    use_recommended_threshold: Optional[bool] = None
    custom_threshold: Optional[int] = Field(default=None, ge=30, le=500)
    threshold_crossing_alerts: Optional[bool] = None
    deterioration_alerts: Optional[bool] = None
    forecast_alerts: Optional[bool] = None
    surge_warnings: Optional[bool] = None
    daily_morning_brief: Optional[bool] = None
    commute_window_alerts: Optional[bool] = None
    improving_air_alerts: Optional[bool] = None
    monitored_locations: Optional[List[str]] = None

class NotificationSettingsOut(BaseModel):
    user_id: str
    user_category: str
    sensitivity_preference: str
    recommended_threshold: int
    recommended_threshold_reason: str
    current_threshold: int
    use_recommended_threshold: bool
    threshold_crossing_alerts: bool
    deterioration_alerts: bool
    forecast_alerts: bool
    surge_warnings: bool
    daily_morning_brief: bool
    commute_window_alerts: bool
    improving_air_alerts: bool
    monitored_locations: List[str]
