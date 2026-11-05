from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from enum import Enum
from datetime import datetime

from app.schemas.reliability import (
    SourceType, 
    FreshnessStatus, 
    EnvironmentalReadingMetadata
)

class MeasurementType(str, Enum):
    MEASURED = "measured"
    MODEL_FORECAST = "model_forecast"
    ESTIMATED = "estimated"
    SIMULATED = "simulated"

class DataAvailabilityStatus(str, Enum):
    LIVE = "live"
    CACHED = "cached"
    DEGRADED = "degraded"
    UNAVAILABLE = "unavailable"

class WeatherConditions(BaseModel):
    temperature_c: Optional[float] = Field(None, description="Temperature in Celsius")
    relative_humidity_pct: Optional[float] = Field(None, description="Relative Humidity (%)")
    wind_speed_kmh: Optional[float] = Field(None, description="Wind Speed at 10m (km/h)")
    wind_direction_deg: Optional[float] = Field(None, description="Wind Direction (degrees)")
    surface_pressure_hpa: Optional[float] = Field(None, description="Surface Atmospheric Pressure (hPa)")
    precipitation_mm: Optional[float] = Field(None, description="Precipitation (mm)")
    observation_time: Optional[str] = Field(None, description="Observation timestamp reported by meteorological sensor/model")

class LiveEnvironmentalData(BaseModel):
    location_id: str
    location_name: str
    display_name: str
    latitude: float
    longitude: float
    
    # Air Quality Parameters (Direct from API)
    pm25: Optional[float] = Field(None, description="PM2.5 concentration in ug/m3")
    pm10: Optional[float] = Field(None, description="PM10 concentration in ug/m3")
    carbon_monoxide: Optional[float] = Field(None, description="CO concentration in ug/m3")
    nitrogen_dioxide: Optional[float] = Field(None, description="NO2 concentration in ug/m3")
    sulphur_dioxide: Optional[float] = Field(None, description="SO2 concentration in ug/m3")
    ozone: Optional[float] = Field(None, description="O3 concentration in ug/m3")
    
    # NAQI Indices (Computed strictly when pm25 or pm10 is present)
    aqi: Optional[int] = Field(None, description="Calculated Indian NAQI")
    aqi_category: Optional[str] = Field(None, description="Good, Satisfactory, Moderate, Poor, Very Poor, Severe")
    risk_level: Optional[str] = Field(None, description="Low, Moderate, High, Critical")
    
    # Weather
    weather: Optional[WeatherConditions] = None
    
    # Data Provenance & Reliability (Master Prompt Section 9)
    observation_time_iso: Optional[str] = Field(None, description="Original observation timestamp from upstream provider")
    query_timestamp_iso: str = Field(..., description="Timestamp when AtmosAI processed this query")
    units: Dict[str, str] = Field(
        default_factory=lambda: {
            "pm25": "ug/m3",
            "pm10": "ug/m3",
            "co": "ug/m3",
            "no2": "ug/m3",
            "so2": "ug/m3",
            "ozone": "ug/m3",
            "temperature": "C",
            "humidity": "%",
            "wind_speed": "km/h"
        }
    )
    measurement_type: MeasurementType = MeasurementType.MODEL_FORECAST
    data_source: str = Field(..., description="Accurate identity of data provider")
    data_availability_status: DataAvailabilityStatus = DataAvailabilityStatus.LIVE
    is_stale: bool = False
    error_detail: Optional[str] = None
    
    # Reliability & Freshness Engine Metadata
    reliability_metadata: Optional[EnvironmentalReadingMetadata] = None
    readings_metadata: Optional[Dict[str, EnvironmentalReadingMetadata]] = None
