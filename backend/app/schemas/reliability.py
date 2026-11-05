from datetime import datetime
from enum import Enum
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field

class SourceType(str, Enum):
    MEASURED = "MEASURED"
    FORECAST = "FORECAST"
    ESTIMATED = "ESTIMATED"
    DEMO = "DEMO"

class FreshnessStatus(str, Enum):
    FRESH = "FRESH"
    AGING = "AGING"
    STALE = "STALE"
    UNAVAILABLE = "UNAVAILABLE"

class EnvironmentalReadingMetadata(BaseModel):
    pollutant: str = Field(default="PM2.5", description="Pollutant identifier (e.g. PM2.5, PM10, AQI)")
    value: Optional[float] = Field(None, description="Observed, estimated, or forecasted numerical reading")
    unit: str = Field(default="µg/m³", description="Measurement unit")
    source: str = Field(..., description="Provider or telemetry network identity")
    source_type: SourceType = Field(..., description="Classification: MEASURED, FORECAST, ESTIMATED, DEMO")
    station_name: Optional[str] = Field(None, description="Physical sensor station name if available")
    station_latitude: Optional[float] = Field(None, description="Station geographic latitude")
    station_longitude: Optional[float] = Field(None, description="Station geographic longitude")
    station_distance_km: Optional[float] = Field(None, description="Distance from queried location to station in km")
    observed_at: Optional[datetime] = Field(None, description="Timestamp of physical observation or forecast target in UTC")
    retrieved_at: datetime = Field(..., description="Timestamp when AtmosAI retrieved/processed this reading in UTC")
    freshness_status: FreshnessStatus = Field(..., description="FRESH (<=1h), AGING (1-3h), STALE (>3h), or UNAVAILABLE")
    
    # Transparency and protection attributes
    age_minutes: Optional[float] = Field(None, description="Age of data in minutes relative to retrieval time")
    is_live: bool = Field(True, description="True only if fresh measured/estimated telemetry, False if stale/forecast/demo")
    confidence_level: str = Field(default="HIGH", description="Confidence tier: HIGH, MODERATE, LOW, NONE")
    confidence_reason: Optional[str] = Field(None, description="Human-understandable rationale for data reliability and confidence")
    disclaimer: str = Field(
        default="Freshness reflects telemetry age, not guaranteed sensor accuracy.",
        description="Mandatory scientific transparency disclaimer"
    )

class LocationReliabilitySummary(BaseModel):
    location_id: str
    location_name: str
    overall_freshness: FreshnessStatus
    dominant_source_type: SourceType
    primary_reading: EnvironmentalReadingMetadata
    readings: Dict[str, EnvironmentalReadingMetadata] = Field(default_factory=dict)
    can_recommend_confidently: bool
    confidence_explanation: str

