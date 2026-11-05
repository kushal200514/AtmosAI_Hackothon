from pydantic import BaseModel, Field
from typing import List, Optional

class WaypointExposure(BaseModel):
    name: str
    latitude: float
    longitude: float
    segment_duration_mins: float
    estimated_pm25: float
    aqi_category: str

class TravelExposureRequest(BaseModel):
    origin: str = Field(..., description="Starting location name (e.g. Yelahanka or Bengaluru Central)")
    destination: str = Field(..., description="Destination location name (e.g. Silk Board or Electronic City)")
    mode: str = "commute"  # "commute", "cycling", "walking"

class TravelExposureResponse(BaseModel):
    origin: str
    destination: str
    estimated_duration_minutes: int
    waypoints: List[WaypointExposure]
    average_pm25: float
    total_exposure_index: float = Field(..., description="Time-weighted environmental concentration estimate: E = Σ(Ci * Δti) / ΣΔti")
    risk_level: str
    advisory: str
    disclaimer: str = "This is a time-weighted environmental concentration estimate, not a measured biological inhaled dose."

