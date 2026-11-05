from datetime import datetime
from enum import Enum
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field

class LocationType(str, Enum):
    HOME = "home"
    COLLEGE_SCHOOL = "college_school"
    OFFICE = "office"
    FAVOURITE_PLACE = "favourite_place"
    CUSTOM = "custom"

class NearestStationInfo(BaseModel):
    station_name: str = Field(..., description="Name of the closest monitoring station")
    station_code: Optional[str] = Field(None, description="Official station code if registered")
    distance_km: float = Field(..., description="Euclidean / Great-circle distance to station in kilometers")
    latitude: float = Field(..., description="Station latitude")
    longitude: float = Field(..., description="Station longitude")
    source: str = Field(default="CPCB / Karnataka PCB", description="Operating network")
    is_representative: bool = Field(
        default=False, 
        description="True only if station is very close (< 2 km). Never assumed identical to exact location."
    )

class SavedLocationAirQuality(BaseModel):
    location_id: str
    location_name: str
    location_type: LocationType
    latitude: float
    longitude: float
    address: Optional[str] = None
    
    # Environmental measurements & valid Indian CPCB NAQI
    pm25: Optional[float] = Field(None, description="PM2.5 concentration in µg/m³")
    pm10: Optional[float] = Field(None, description="PM10 concentration in µg/m³")
    aqi: Optional[int] = Field(None, description="Calculated CPCB NAQI when valid multi-pollutant data exists")
    aqi_category: Optional[str] = Field(None, description="Good, Satisfactory, Moderate, Poor, Very Poor, Severe")
    risk_level: Optional[str] = Field(None, description="Low, Moderate, High, Critical")
    dominant_pollutant: Optional[str] = None
    
    # Nearest Station & Provenance
    nearest_station: Optional[NearestStationInfo] = None
    source: str = Field(..., description="Identity of environmental data provider")
    source_type: str = Field(default="ESTIMATED", description="MEASURED or ESTIMATED")
    observed_at: Optional[str] = Field(None, description="ISO timestamp of observation")
    freshness_status: str = Field(default="FRESH", description="FRESH, AGING, STALE, or UNAVAILABLE")
    age_minutes: Optional[float] = Field(None, description="Data age in minutes")
    
    # Multi-Horizon Forecast
    forecast_summary: Optional[str] = None
    predicted_pm25_3h: Optional[float] = None
    predicted_pm25_6h: Optional[float] = None
    
    # Data Quality Disclaimers
    disclaimer: str = Field(
        default="Nearest station distance is reported. Station observations may differ from localized microclimates.",
        description="Mandatory scientific transparency disclaimer"
    )

class SavedLocationBase(BaseModel):
    location_name: str = Field(..., min_length=1, max_length=100, description="User-chosen label for the place")
    location_type: LocationType = Field(default=LocationType.CUSTOM, description="Home, College / School, Office, Favourite Place, Custom")
    address: Optional[str] = Field(None, max_length=255, description="Street address or locality description")
    latitude: float = Field(..., ge=-90.0, le=90.0, description="Geographic latitude")
    longitude: float = Field(..., ge=-180.0, le=180.0, description="Geographic longitude")
    is_primary: bool = Field(default=False, description="Whether this is the default location for dashboard monitoring")

class SavedLocationCreate(SavedLocationBase):
    user_id: Optional[str] = Field(None, description="Owning user ID; resolved from auth context if omitted")

class SavedLocationUpdate(BaseModel):
    location_name: Optional[str] = Field(None, min_length=1, max_length=100)
    location_type: Optional[LocationType] = None
    address: Optional[str] = Field(None, max_length=255)
    latitude: Optional[float] = Field(None, ge=-90.0, le=90.0)
    longitude: Optional[float] = Field(None, ge=-180.0, le=180.0)
    is_primary: Optional[bool] = None

class SavedLocationOut(SavedLocationBase):
    location_id: str
    user_id: str
    created_at: datetime
    air_quality: Optional[SavedLocationAirQuality] = None

class LocationSearchResult(BaseModel):
    display_name: str
    address: str
    latitude: float
    longitude: float
    place_type: Optional[str] = None
    nearest_station_name: Optional[str] = None
    nearest_station_distance_km: Optional[float] = None

