import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.main import app
from app.services.ai.service import ai_service
from app.services.ai.fallback_provider import rule_fallback_provider
from app.schemas.profile import ProfileType

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
async def test_rule_fallback_advice_runner():
    with patch("app.services.environmental.openmeteo_client.openmeteo_client.get_air_quality", new=AsyncMock(return_value=MOCK_AIR)), \
         patch("app.services.environmental.openmeteo_client.openmeteo_client.get_live_weather", new=AsyncMock(return_value=MOCK_WEATHER)), \
         patch("app.services.environmental.openaq_client.openaq_client.get_latest_measurements", new=AsyncMock(return_value=None)):

        res = await ai_service.get_advice("bengaluru_central", ProfileType.RUNNER)
        assert res is not None
        assert res.profile_type == ProfileType.RUNNER
        assert len(res.profile_specific_recommendations) >= 1
        assert "medical" in res.disclaimer.lower()
        assert res.activity_guidance.best_time_window is not None
        assert res.activity_guidance.outdoor_exercise_allowed in [True, False]

@pytest.mark.asyncio
async def test_rule_fallback_advice_respiratory_sensitive():
    with patch("app.services.environmental.openmeteo_client.openmeteo_client.get_air_quality", new=AsyncMock(return_value=MOCK_AIR)), \
         patch("app.services.environmental.openmeteo_client.openmeteo_client.get_live_weather", new=AsyncMock(return_value=MOCK_WEATHER)), \
         patch("app.services.environmental.openaq_client.openaq_client.get_latest_measurements", new=AsyncMock(return_value=None)):

        res = await ai_service.get_advice("bengaluru_central", ProfileType.RESPIRATORY_SENSITIVE)
        assert res is not None
        assert res.profile_type == ProfileType.RESPIRATORY_SENSITIVE
        assert any("inhaler" in r.lower() or "mask" in r.lower() or "transit" in r.lower() for r in res.profile_specific_recommendations)

def test_api_profiles_endpoint():
    response = client.get("/api/profiles")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 6
    ids = [p["id"] for p in data]
    assert "runner" in ids
    assert "respiratory_sensitive" in ids
    assert "parent" in ids
    assert "delivery_worker" in ids
    assert "office_commuter" in ids
    assert "general_public" in ids

def test_api_advice_endpoint_get():
    with patch("app.services.environmental.openmeteo_client.openmeteo_client.get_air_quality", new=AsyncMock(return_value=MOCK_AIR)), \
         patch("app.services.environmental.openmeteo_client.openmeteo_client.get_live_weather", new=AsyncMock(return_value=MOCK_WEATHER)), \
         patch("app.services.environmental.openaq_client.openaq_client.get_latest_measurements", new=AsyncMock(return_value=None)):

        response = client.get("/api/advice?location=bengaluru_central&profile=parent")
        assert response.status_code == 200
        data = response.json()
        assert data["profile_type"] == "parent"
        assert "headline_summary" in data
        assert "evidence_based_explanation" in data
        assert "activity_guidance" in data
        assert "disclaimer" in data

def test_api_advice_endpoint_post():
    with patch("app.services.environmental.openmeteo_client.openmeteo_client.get_air_quality", new=AsyncMock(return_value=MOCK_AIR)), \
         patch("app.services.environmental.openmeteo_client.openmeteo_client.get_live_weather", new=AsyncMock(return_value=MOCK_WEATHER)), \
         patch("app.services.environmental.openaq_client.openaq_client.get_latest_measurements", new=AsyncMock(return_value=None)):

        response = client.post("/api/advice", json={"location": "bengaluru_central", "profile_type": "delivery_worker"})
        assert response.status_code == 200
        data = response.json()
        assert data["profile_type"] == "delivery_worker"
        assert len(data["profile_specific_recommendations"]) > 0

