from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

class GridCellForecast(BaseModel):
    cell_id: str
    bounds: List[List[float]] = Field(..., description="[[lat_min, lon_min], [lat_max, lon_max]]")
    center_lat: float
    center_lon: float
    pm25: float
    aqi: Optional[int] = None
    aqi_category: str
    color: str
    confidence_label: str = "Copernicus CAMS 0.1° Atmospheric Chemistry Model Forecast"
    is_forecast: bool = True
    timestamp_iso: str

class StationMarker(BaseModel):
    station_id: str
    name: str
    display_name: str
    latitude: float
    longitude: float
    pollutant: str = "PM2.5"
    unit: str = "µg/m³"
    pm25: Optional[float] = None
    pm10: Optional[float] = None
    aqi: Optional[int] = None
    aqi_category: Optional[str] = None
    risk_level: Optional[str] = None
    measurement_type: str = Field(..., description="'measured' (physical ground station) or 'model_forecast'")
    is_measured: bool = False
    data_source: str
    observation_time_iso: Optional[str] = None
    temperature_c: Optional[float] = None
    humidity_pct: Optional[float] = None
    wind_speed_kmh: Optional[float] = None
    wind_direction_deg: Optional[float] = None
    is_stale: bool = False
    data_availability_status: str = "available"

class RouteSegment(BaseModel):
    segment_id: int
    title: str
    start_point: List[float] = Field(..., description="[lat, lon]")
    end_point: List[float] = Field(..., description="[lat, lon]")
    coordinates: List[List[float]] = Field(..., description="List of [lat, lon] coordinates")
    distance_km: float
    duration_mins: float
    estimated_pm25: float
    aqi: Optional[int] = None
    aqi_category: str
    risk_color: str
    nearest_station_name: str
    nearest_station_distance_km: float
    nearest_station_is_measured: bool
    data_provenance_note: str

class DestinationAQInfo(BaseModel):
    name: str
    display_name: str
    latitude: float
    longitude: float
    pm25: Optional[float] = None
    aqi: Optional[int] = None
    aqi_category: Optional[str] = None
    risk_level: Optional[str] = None
    temperature_c: Optional[float] = None
    wind_speed_kmh: Optional[float] = None
    observation_time_iso: Optional[str] = None
    source: str
    is_measured: bool = False
    indoor_disclaimer: str = (
        "Outdoor air quality telemetry. Indoor environments vary with ventilation and filtration; "
        "outdoor telemetry does not represent indoor AQI."
    )

class AlternativeRouteComparison(BaseModel):
    has_sufficient_comparable_data: bool
    alternative_name: str
    distance_km: float
    duration_mins: float
    total_exposure_index: Optional[float] = None
    exposure_diff_pct: Optional[float] = None
    comparison_summary: str

class TravelRouteRequest(BaseModel):
    origin: str = Field(..., description="Starting location slug (e.g. 'yelahanka', 'bengaluru_central')")
    destination: str = Field(..., description="Destination location slug (e.g. 'silk_board', 'whitefield')")
    mode: str = Field(default="driving", description="'driving', 'cycling', or 'walking'")

class TravelRouteResponse(BaseModel):
    origin: str
    origin_display_name: str
    destination: str
    destination_display_name: str
    mode: str
    mode_label: str
    total_distance_km: float
    total_duration_minutes: float
    total_exposure_index: float = Field(..., description="Time-weighted concentration E = Σ(Ci * Δti) / ΣΔti")
    exposure_category: str
    safety_advisory: str
    route_geometry: List[List[float]] = Field(..., description="Full polyline coordinates [[lat, lon], ...]")
    segments: List[RouteSegment]
    destination_info: DestinationAQInfo
    alternative_comparison: Optional[AlternativeRouteComparison] = None
    data_rules_disclaimer: str = (
        "Measurements from physical ground stations are strictly distinguished from atmospheric model forecasts. "
        "Unmonitored street segments are estimated using proximity-weighted observations from nearest verified monitors."
    )

