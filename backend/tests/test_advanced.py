import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.main import app
from app.services.location.travel_service import travel_service
from app.schemas.travel import TravelExposureRequest

client = TestClient(app)

MOCK_AIR = {
    "current": {
        "time": "2026-11-05T13:00",
        "interval": 3600,
        "pm10": 25.0,
        "pm2_5": 20.0,
        "carbon_monoxide": 280.0,
        "nitrogen_dioxide": 5.0,
        "sulphur_dioxide": 6.0,
        "ozone": 110.0
    }
}

MOCK_WEATHER = {
    "current": {
        "time": "2026-11-05T13:00",
        "interval": 900,
        "temperature_2m": 28.0,
        "relative_humidity_2m": 55.0,
        "wind_speed_10m": 9.5,
        "wind_direction_10m": 120.0,
        "surface_pressure": 915.0,
        "precipitation": 0.0
    }
}

@pytest.mark.asyncio
async def test_travel_exposure_calculation():
    with patch("app.services.environmental.openmeteo_client.openmeteo_client.get_air_quality", new=AsyncMock(return_value=MOCK_AIR)), \
         patch("app.services.environmental.openmeteo_client.openmeteo_client.get_live_weather", new=AsyncMock(return_value=MOCK_WEATHER)), \
         patch("app.services.environmental.openaq_client.openaq_client.get_latest_measurements", new=AsyncMock(return_value=None)):

        req = TravelExposureRequest(origin="bengaluru_central", destination="silk_board", mode="commute")
        res = await travel_service.calculate_exposure(req)
        assert res.estimated_duration_minutes > 0
        assert res.total_exposure_index > 0
        assert len(res.waypoints) == 3
        assert "not a measured biological inhaled dose" in res.disclaimer.lower()

def test_api_travel_exposure_endpoint():
    with patch("app.services.environmental.openmeteo_client.openmeteo_client.get_air_quality", new=AsyncMock(return_value=MOCK_AIR)), \
         patch("app.services.environmental.openmeteo_client.openmeteo_client.get_live_weather", new=AsyncMock(return_value=MOCK_WEATHER)), \
         patch("app.services.environmental.openaq_client.openaq_client.get_latest_measurements", new=AsyncMock(return_value=None)):

        payload = {"origin": "hebbal", "destination": "electronic_city", "mode": "commute"}
        response = client.post("/api/travel/exposure", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert "total_exposure_index" in data
        assert "waypoints" in data
        assert "advisory" in data

def test_api_alerts_endpoint():
    with patch("app.services.environmental.openmeteo_client.openmeteo_client.get_air_quality", new=AsyncMock(return_value=MOCK_AIR)), \
         patch("app.services.environmental.openmeteo_client.openmeteo_client.get_live_weather", new=AsyncMock(return_value=MOCK_WEATHER)), \
         patch("app.services.environmental.openaq_client.openaq_client.get_latest_measurements", new=AsyncMock(return_value=None)):

        response = client.get("/api/alerts?profile=runner")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1

def test_api_telemetry_endpoint():
    payload = {
        "device_id": "watch_sim_01",
        "timestamp": "2026-11-05T14:00:00Z",
        "heart_rate": 145,
        "step_count": 6420,
        "activity_type": "running",
        "ambient_pm25": 65.0
    }
    response = client.post("/api/telemetry", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert "contextual_advisory" in data
    assert "not constitute medical monitoring" in data["disclaimer"]

def test_api_user_profile_update():
    response = client.post("/api/user/profile", json={"profile_type": "parent", "full_name": "Rohan Sharma"})
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["profile"]["profile_type"] == "parent"

def test_api_location_and_activity():
    res_loc = client.post("/api/location/update", json={"latitude": 12.9716, "longitude": 77.5946})
    assert res_loc.status_code == 200

    res_act = client.post("/api/activity", json={"activity_type": "cycling", "timestamp": "2026-11-05T14:30:00Z"})
    assert res_act.status_code == 200

