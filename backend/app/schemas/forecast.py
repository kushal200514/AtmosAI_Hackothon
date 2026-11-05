from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime

class ForecastPoint(BaseModel):
    horizon_hours: int = Field(..., ge=1, le=24, description="Horizon ahead (3, 4, 5, 6 hours)")
    target_timestamp: datetime
    target_time_label: str
    predicted_pm25: float
    confidence_lower: float
    confidence_upper: float
    trend: str = Field(..., description="'rising', 'falling', 'stable'")
    risk_level: str
    surge_warning: bool = False
    surge_reason: Optional[str] = None

class ForecastResponse(BaseModel):
    location_id: str
    location_name: str
    generated_at: datetime
    forecast_points: List[ForecastPoint]
    model_version: str = "lightgbm_pm25_v1.0"
    model_name: str = "LightGBM Gradient Boosted Decision Trees"
    uncertainty_description: str
    primary_driving_factors: List[str]
    surge_detected: bool = False
    data_source: str = "AtmosAI ML Engine + Open-Meteo Covariates"

