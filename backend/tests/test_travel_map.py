import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.main import app
from app.services.location.travel_map_service import (
    travel_map_service, 
    haversine, 
    get_aqi_category_and_color
)
from app.schemas.map import (
    GridCellForecast,
    StationMarker,
    TravelRouteResponse
)

client = TestClient(app)

def test_haversine_distance_calculation():
    """Test distance calculation between Bengaluru Central (12.9716, 77.5946) and Silk Board (12.9176, 77.6238)."""
    dist = haversine(12.9716, 77.5946, 12.9176, 77.6238)
    # Distance is approximately 6.7 to 7.2 km straight-line
    assert 6.0 <= dist <= 7.5

def test_aqi_category_and_color():
    """Test CPCB NAQI category and color mappings."""
    cat, col = get_aqi_category_and_color(35, 12.0)
    assert cat == "Good"
    assert col == "#10b981"

    cat, col = get_aqi_category_and_color(85, 45.0)
    assert cat == "Satisfactory"
    assert col == "#06b6d4"

    cat, col = get_aqi_category_and_color(165, 80.0)
    assert cat == "Moderate"
    assert col == "#f59e0b"

    cat, col = get_aqi_category_and_color(260, 110.0)
    assert cat == "Poor"
    assert col == "#f97316"

    cat, col = get_aqi_category_and_color(350, 190.0)
    assert cat == "Very Poor"
    assert col == "#ef4444"

@pytest.mark.asyncio
async def test_get_gridded_forecast_cells():
    """Test generating gridded atmospheric forecast overlay covering Greater Bengaluru."""
    cells = await travel_map_service.get_gridded_forecast()
    assert isinstance(cells, list)
    assert len(cells) == 12  # 4 rows x 3 columns grid

    first = cells[0]
    assert isinstance(first, GridCellForecast)
    assert len(first.bounds) == 2
    assert first.is_forecast is True
    assert "CAMS" in first.confidence_label or "Copernicus" in first.confidence_label or "Model" in first.confidence_label
    assert first.pm25 > 0
    assert first.aqi_category in ["Good", "Satisfactory", "Moderate", "Poor", "Very Poor", "Severe"]

@pytest.mark.asyncio
async def test_get_station_markers_provenance():
    """Test retrieving available monitoring station markers with coordinates, pollutant, and units."""
    markers = await travel_map_service.get_station_markers()
    assert isinstance(markers, list)
    assert len(markers) >= 5

    for m in markers:
        assert isinstance(m, StationMarker)
        assert m.latitude is not None
        assert m.longitude is not None
        assert m.pollutant == "PM2.5"
        assert m.unit == "µg/m³"
        assert m.measurement_type in ["measured", "model_forecast"]
        assert m.data_source is not None

@pytest.mark.asyncio
async def test_plan_travel_route_segmentation_and_nearest_station():
    """Test route planning segmentation, nearby station lookup, and time-weighted exposure."""
    res = await travel_map_service.plan_travel_route(
        origin_slug="yelahanka",
        destination_slug="silk_board",
        mode="driving"
    )

    assert isinstance(res, TravelRouteResponse)
    assert res.origin == "yelahanka"
    assert res.destination == "silk_board"
    assert res.total_distance_km > 0
    assert res.total_duration_minutes > 0
    assert res.total_exposure_index > 0
    assert len(res.route_geometry) > 0
    assert len(res.segments) >= 3

    # Verify each segment has proximity station lookup and provenance notes
    for seg in res.segments:
        assert seg.distance_km > 0
        assert seg.duration_mins > 0
        assert seg.estimated_pm25 > 0
        assert seg.nearest_station_name is not None
        assert seg.nearest_station_distance_km >= 0
        # Strict rule: Unmonitored street provenance statement
        assert "Unmonitored street segment" in seg.data_provenance_note
        assert seg.nearest_station_name in seg.data_provenance_note

    # Verify destination environmental info & indoor disclaimer
    assert res.destination_info is not None
    assert "outdoor telemetry does not represent indoor aqi" in res.destination_info.indoor_disclaimer.lower()

    # Verify data rules disclaimer
    assert "strictly distinguished" in res.data_rules_disclaimer.lower()

@pytest.mark.asyncio
async def test_plan_travel_route_modes():
    """Test travel route exposure for walking and cycling modes."""
    walk_res = await travel_map_service.plan_travel_route("hebbal", "bengaluru_central", mode="walking")
    assert walk_res.mode == "walking"
    assert "Walking" in walk_res.mode_label
    # Walking duration is higher than driving for same distance
    drive_res = await travel_map_service.plan_travel_route("hebbal", "bengaluru_central", mode="driving")
    assert walk_res.total_duration_minutes > drive_res.total_duration_minutes

    cycle_res = await travel_map_service.plan_travel_route("hebbal", "bengaluru_central", mode="cycling")
    assert cycle_res.mode == "cycling"
    assert "Cycling" in cycle_res.mode_label

def test_api_get_map_grid():
    """Test GET /api/map/grid endpoint."""
    response = client.get("/api/map/grid")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 12
    assert "bounds" in data[0]
    assert "pm25" in data[0]

def test_api_get_map_stations():
    """Test GET /api/map/stations endpoint."""
    response = client.get("/api/map/stations")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 5
    assert data[0]["pollutant"] == "PM2.5"
    assert data[0]["unit"] == "µg/m³"

def test_api_post_map_route():
    """Test POST /api/map/route endpoint."""
    payload = {
        "origin": "peenya",
        "destination": "whitefield",
        "mode": "driving"
    }
    response = client.post("/api/map/route", json=payload)
    assert response.status_code == 200
    data = response.json()

    assert data["origin"] == "peenya"
    assert data["destination"] == "whitefield"
    assert data["total_exposure_index"] > 0
    assert len(data["segments"]) > 0
    assert "destination_info" in data
    assert "indoor_disclaimer" in data["destination_info"]
    assert "alternative_comparison" in data
