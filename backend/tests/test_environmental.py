import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock
from datetime import datetime, timezone
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.main import app
from app.services.environmental.aqi_calculator import compute_naqi
from app.services.environmental.cache_manager import TTLCache, cache_manager
from app.services.environmental.aggregator import aggregator
from app.schemas.environmental import DataAvailabilityStatus, MeasurementType

client = TestClient(app)

MOCK_OPENMETEO_AIR = {
    "current": {
        "time": "2026-11-05T13:00",
        "interval": 3600,
        "pm10": 18.4,
        "pm2_5": 14.2,
        "carbon_monoxide": 290.0,
        "nitrogen_dioxide": 4.1,
        "sulphur_dioxide": 5.2,
        "ozone": 115.0
    }
}

MOCK_OPENMETEO_WEATHER = {
    "current": {
        "time": "2026-11-05T13:00",
        "interval": 900,
        "temperature_2m": 27.4,
        "relative_humidity_2m": 56.0,
        "wind_speed_10m": 11.2,
        "wind_direction_10m": 125.0,
        "surface_pressure": 915.2,
        "precipitation": 0.0
    }
}

def test_naqi_calculation():
    # Good
    res_good = compute_naqi(15.0)
    assert res_good["aqi"] <= 50
    assert res_good["category"] == "Good"

    # Moderate
    res_mod = compute_naqi(75.0)
    assert 101 <= res_mod["aqi"] <= 200
    assert res_mod["category"] == "Moderate"

    # Very Poor
    res_poor = compute_naqi(150.0)
    assert 301 <= res_poor["aqi"] <= 400
    assert res_poor["category"] == "Very Poor"

def test_ttl_cache_logic():
    cache = TTLCache(default_ttl_seconds=1)
    cache.set("test_key", {"val": 42}, ttl_seconds=1)
    val, is_stale, created_at = cache.get("test_key")
    assert val == {"val": 42}
    assert not is_stale
    assert created_at is not None

def test_api_locations():
    response = client.get("/api/locations")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 7
    first = data[0]
    assert "name" in first
    assert "latitude" in first
    assert "longitude" in first

def test_api_forecast_live_provenance_and_units():
    cache_manager.clear()
    with patch("app.services.environmental.openmeteo_client.openmeteo_client.get_air_quality", new=AsyncMock(return_value=MOCK_OPENMETEO_AIR)), \
         patch("app.services.environmental.openmeteo_client.openmeteo_client.get_live_weather", new=AsyncMock(return_value=MOCK_OPENMETEO_WEATHER)), \
         patch("app.services.environmental.openaq_client.openaq_client.get_latest_measurements", new=AsyncMock(return_value=None)):

        response = client.get("/api/forecast/live?location=bengaluru_central")
        assert response.status_code == 200
        data = response.json()
        assert data["pm25"] == 14.2
        assert data["pm10"] == 18.4
        assert data["carbon_monoxide"] == 290.0
        assert data["observation_time_iso"] == "2026-11-05T13:00"
        assert data["measurement_type"] == "model_forecast"
        assert data["data_availability_status"] == "live"
        assert data["is_stale"] is False
        assert "units" in data
        assert data["units"]["pm25"] == "ug/m3"
        assert data["units"]["temperature"] == "C"

@pytest.mark.asyncio
async def test_missing_data_no_hallucinations():
    """Verify that when APIs fail and cache is empty, we report UNAVAILABLE and None for pm25 rather than fake numbers."""
    cache_manager.clear()
    with patch("app.services.environmental.openmeteo_client.openmeteo_client.get_air_quality", new=AsyncMock(return_value=None)), \
         patch("app.services.environmental.openmeteo_client.openmeteo_client.get_live_weather", new=AsyncMock(return_value=None)), \
         patch("app.services.environmental.openaq_client.openaq_client.get_latest_measurements", new=AsyncMock(return_value=None)):
        
        data = await aggregator.get_live_data("bengaluru_central")
        assert data.pm25 is None
        assert data.aqi is None
        assert data.data_availability_status == DataAvailabilityStatus.UNAVAILABLE
        assert "could not provide live measurements" in data.error_detail

@pytest.mark.asyncio
async def test_cached_fallback_on_api_outage():
    """Verify that when live refresh fails but cached data exists, it is clearly flagged as CACHED and is_stale = True."""
    cache_manager.clear()
    # 1. Populate cache with a known verified reading
    with patch("app.services.environmental.openmeteo_client.openmeteo_client.get_air_quality", new=AsyncMock(return_value=MOCK_OPENMETEO_AIR)), \
         patch("app.services.environmental.openmeteo_client.openmeteo_client.get_live_weather", new=AsyncMock(return_value=MOCK_OPENMETEO_WEATHER)), \
         patch("app.services.environmental.openaq_client.openaq_client.get_latest_measurements", new=AsyncMock(return_value=None)):
        
        real_data = await aggregator.get_live_data("bengaluru_central")
        assert real_data.pm25 == 14.2
        original_time = real_data.observation_time_iso

    # 2. Simulate downstream outage
    with patch("app.services.environmental.openmeteo_client.openmeteo_client.get_air_quality", new=AsyncMock(return_value=None)), \
         patch("app.services.environmental.openmeteo_client.openmeteo_client.get_live_weather", new=AsyncMock(return_value=None)), \
         patch("app.services.environmental.openaq_client.openaq_client.get_latest_measurements", new=AsyncMock(return_value=None)):
        
        # Expire cache entry by force to trigger re-fetch attempt
        cache_manager._store["live:bengaluru_central"]["expires_at"] = 0
        cached_result = await aggregator.get_live_data("bengaluru_central")
        
        assert cached_result.data_availability_status == DataAvailabilityStatus.CACHED
        assert cached_result.is_stale is True
        assert cached_result.observation_time_iso == original_time
        assert "Displaying cached data" in cached_result.error_detail
