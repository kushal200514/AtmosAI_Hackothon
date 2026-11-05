import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock
from datetime import datetime, timezone, timedelta
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.main import app
from app.schemas.profile import (
    UserProfile, 
    UserCategory, 
    SensitivityPreference, 
    NotificationPreferences
)
from app.services.alerts.smart_alert_service import smart_alert_service
from app.services.environmental.aqi_calculator import (
    compute_naqi, 
    get_cpcb_safety_recommendation, 
    CPCB_CATEGORIES,
    MEDICAL_DISCLAIMER
)
from app.services.iot.wearable_service import wearable_service

from app.services.environmental.cache_manager import cache_manager

client = TestClient(app)

@pytest.fixture(autouse=True)
def clear_caches_before_each_test():
    cache_manager.clear()
    smart_alert_service._sent_alerts_cache.clear()
    smart_alert_service._station_previous_state.clear()

MOCK_AIR_GOOD = {
    "current": {
        "time": "2026-11-05T13:00",
        "interval": 3600,
        "pm10": 20.0,
        "pm2_5": 12.0,
        "carbon_monoxide": 200.0,
        "nitrogen_dioxide": 15.0,
        "sulphur_dioxide": 5.0,
        "ozone": 30.0
    }
}

MOCK_AIR_POOR = {
    "current": {
        "time": "2026-11-05T13:00",
        "interval": 3600,
        "pm10": 280.0,
        "pm2_5": 110.0,
        "carbon_monoxide": 1500.0,
        "nitrogen_dioxide": 90.0,
        "sulphur_dioxide": 25.0,
        "ozone": 80.0
    }
}

MOCK_WEATHER = {
    "current": {
        "time": "2026-11-05T13:00",
        "interval": 900,
        "temperature_2m": 28.0,
        "relative_humidity_2m": 50.0,
        "wind_speed_10m": 9.0,
        "wind_direction_10m": 90.0,
        "surface_pressure": 915.0,
        "precipitation": 0.0
    }
}

def test_cpcb_categories_and_exact_safety_recommendations():
    """Verify all 6 CPCB NAQI categories and exact safety recommendations required by the prompt."""
    recs = {
        "Good": "Generally favourable outdoor conditions.",
        "Satisfactory": "Generally acceptable; sensitive individuals should remain aware.",
        "Moderate": "Sensitive individuals should consider reducing prolonged outdoor exertion.",
        "Poor": "Reduce prolonged outdoor exertion.",
        "Very Poor": "Avoid prolonged outdoor activities where possible.",
        "Severe": "Avoid unnecessary outdoor exposure and follow official advisories."
    }

    test_aqis = {
        "Good": 30,
        "Satisfactory": 75,
        "Moderate": 150,
        "Poor": 250,
        "Very Poor": 350,
        "Severe": 450
    }

    for cat_name, test_aqi in test_aqis.items():
        res = get_cpcb_safety_recommendation(test_aqi, user_category="runner", sensitivity="none")
        assert res["category"] == cat_name
        assert res["base_recommendation"] == recs[cat_name]
        assert "medical" in res["disclaimer"].lower()

def test_recommended_thresholds_per_persona_and_sensitivity():
    """Verify smart recommended notification thresholds based on sensitivity and archetype."""
    # Respiratory sensitive user gets strict threshold of 80
    user_asthma = UserProfile(
        user_category=UserCategory.GENERAL_PUBLIC, 
        sensitivity_preference=SensitivityPreference.ASTHMA_RESPIRATORY
    )
    rec_asthma = smart_alert_service.compute_recommended_threshold(user_asthma)
    assert rec_asthma["threshold"] == 80
    assert "respiratory" in rec_asthma["reason"].lower()

    # Parent gets 90
    user_parent = UserProfile(
        user_category=UserCategory.PARENT, 
        sensitivity_preference=SensitivityPreference.NONE
    )
    rec_parent = smart_alert_service.compute_recommended_threshold(user_parent)
    assert rec_parent["threshold"] == 90

    # Runner gets 100
    user_runner = UserProfile(
        user_category=UserCategory.RUNNER, 
        sensitivity_preference=SensitivityPreference.NONE
    )
    rec_runner = smart_alert_service.compute_recommended_threshold(user_runner)
    assert rec_runner["threshold"] == 100

    # Outdoor worker gets 120
    user_worker = UserProfile(
        user_category=UserCategory.OUTDOOR_WORKER, 
        sensitivity_preference=SensitivityPreference.NONE
    )
    rec_worker = smart_alert_service.compute_recommended_threshold(user_worker)
    assert rec_worker["threshold"] == 120

    # General public gets 150
    user_gp = UserProfile(
        user_category=UserCategory.GENERAL_PUBLIC, 
        sensitivity_preference=SensitivityPreference.NONE
    )
    rec_gp = smart_alert_service.compute_recommended_threshold(user_gp)
    assert rec_gp["threshold"] == 150

def test_cpcb_aqi_not_from_pm25_alone():
    """Verify CPCB NAQI computes sub-indices across multiple pollutants and takes the maximum."""
    # High PM10 with low PM2.5 -> PM10 must drive the AQI
    res = compute_naqi(pm25=15.0, pm10=220.0, no2=30.0)
    assert res["dominant_pollutant"] == "PM10"
    assert res["sub_indices"]["PM10"] > res["sub_indices"]["PM2.5"]
    assert res["aqi"] == res["sub_indices"]["PM10"]

    # High NO2 with low particulate -> NO2 drives the AQI
    res_no2 = compute_naqi(pm25=10.0, pm10=20.0, no2=250.0)
    assert res_no2["dominant_pollutant"] == "NO2"
    assert res_no2["aqi"] == res_no2["sub_indices"]["NO2"]

@pytest.mark.asyncio
async def test_threshold_crossing_alert_detection():
    """Verify threshold crossing generates current_measurement alerts with safety recommendation."""
    user = UserProfile(
        id="test_threshold_user",
        user_category=UserCategory.RUNNER,
        notifications=NotificationPreferences(
            high_pollution_threshold=90,
            threshold_crossing_alerts=True,
            daily_morning_brief=False,
            improving_air_alerts=False
        )
    )

    with patch("app.services.environmental.openmeteo_client.openmeteo_client.get_air_quality", new=AsyncMock(return_value=MOCK_AIR_POOR)), \
         patch("app.services.environmental.openmeteo_client.openmeteo_client.get_live_weather", new=AsyncMock(return_value=MOCK_WEATHER)), \
         patch("app.services.environmental.openaq_client.openaq_client.get_latest_measurements", new=AsyncMock(return_value=None)):

        alerts = await smart_alert_service.generate_smart_alerts(user)
        assert len(alerts) > 0
        crossing_alerts = [a for a in alerts if a.alert_type == "threshold_crossing"]
        assert len(crossing_alerts) > 0
        first = crossing_alerts[0]
        assert first.alert_source == "current_measurement"
        assert first.cpcb_category in ("Poor", "Very Poor", "Severe")
        assert first.safety_recommendation is not None
        assert "medical" in first.disclaimer.lower()

@pytest.mark.asyncio
async def test_pollution_deterioration_detection():
    """Verify alert is triggered when station air quality deteriorates significantly."""
    user = UserProfile(
        id="test_deterioration_user",
        notifications=NotificationPreferences(
            high_pollution_threshold=300, # higher than current so only deterioration fires
            threshold_crossing_alerts=False,
            deterioration_alerts=True,
            daily_morning_brief=False,
            improving_air_alerts=False,
            forecast_alerts=False,
            surge_warnings=False
        )
    )

    # Set initial low state
    smart_alert_service._station_previous_state["bengaluru_central"] = {
        "aqi": 35,
        "category": "Good",
        "updated_at": datetime.now(timezone.utc) - timedelta(minutes=10)
    }

    # Now simulate deteriorating air to Poor (AQI > 200)
    with patch("app.services.environmental.openmeteo_client.openmeteo_client.get_air_quality", new=AsyncMock(return_value=MOCK_AIR_POOR)), \
         patch("app.services.environmental.openmeteo_client.openmeteo_client.get_live_weather", new=AsyncMock(return_value=MOCK_WEATHER)), \
         patch("app.services.environmental.openaq_client.openaq_client.get_latest_measurements", new=AsyncMock(return_value=None)):

        alerts = await smart_alert_service.generate_smart_alerts(user, target_location="bengaluru_central")
        det_alerts = [a for a in alerts if a.alert_type == "deterioration"]
        assert len(det_alerts) >= 1
        assert det_alerts[0].alert_source == "current_measurement"
        assert "deterioration" in det_alerts[0].title.lower()

@pytest.mark.asyncio
async def test_forecast_based_alert_distinction():
    """Verify forecast-based surge advisories are clearly distinguished from current AQI alerts."""
    user = UserProfile(
        id="test_forecast_user",
        notifications=NotificationPreferences(
            threshold_crossing_alerts=False,
            deterioration_alerts=False,
            forecast_alerts=True,
            surge_warnings=True,
            daily_morning_brief=False,
            improving_air_alerts=False
        )
    )

    with patch("app.services.environmental.openmeteo_client.openmeteo_client.get_air_quality", new=AsyncMock(return_value=MOCK_AIR_GOOD)), \
         patch("app.services.environmental.openmeteo_client.openmeteo_client.get_live_weather", new=AsyncMock(return_value=MOCK_WEATHER)), \
         patch("app.services.environmental.openaq_client.openaq_client.get_latest_measurements", new=AsyncMock(return_value=None)):

        alerts = await smart_alert_service.generate_smart_alerts(user, target_location="bengaluru_central")
        forecast_alerts = [a for a in alerts if a.alert_source == "forecast_prediction"]
        # In mock data, forecast forecaster detects rising PM2.5
        for a in forecast_alerts:
            assert a.alert_source == "forecast_prediction"
            assert "forecast" in a.title.lower() or "surge" in a.title.lower()
            assert a.alert_source != "current_measurement"

@pytest.mark.asyncio
async def test_alert_deduplication():
    """Verify steady-state conditions do not produce duplicate alerts within the cooldown window."""
    user = UserProfile(
        id="test_dedup_user",
        notifications=NotificationPreferences(
            high_pollution_threshold=50,
            threshold_crossing_alerts=True,
            daily_morning_brief=False,
            improving_air_alerts=False
        )
    )

    with patch("app.services.environmental.openmeteo_client.openmeteo_client.get_air_quality", new=AsyncMock(return_value=MOCK_AIR_POOR)), \
         patch("app.services.environmental.openmeteo_client.openmeteo_client.get_live_weather", new=AsyncMock(return_value=MOCK_WEATHER)), \
         patch("app.services.environmental.openaq_client.openaq_client.get_latest_measurements", new=AsyncMock(return_value=None)):

        # First run generates alerts
        alerts_1 = await smart_alert_service.generate_smart_alerts(user, target_location="bengaluru_central")
        assert len([a for a in alerts_1 if a.alert_type == "threshold_crossing"]) == 1

        # Second immediate run with identical condition must suppress duplicate
        alerts_2 = await smart_alert_service.generate_smart_alerts(user, target_location="bengaluru_central")
        assert len([a for a in alerts_2 if a.alert_type == "threshold_crossing"]) == 0

def test_api_notification_settings_crud():
    """Verify GET and POST /api/notifications/settings."""
    # GET settings
    res = client.get("/api/notifications/settings?user_id=default_user")
    assert res.status_code == 200
    data = res.json()
    assert "recommended_threshold" in data
    assert "current_threshold" in data
    assert "threshold_crossing_alerts" in data
    assert "monitored_locations" in data

    # POST custom settings
    update_payload = {
        "custom_threshold": 165,
        "use_recommended_threshold": False,
        "deterioration_alerts": True,
        "forecast_alerts": False,
        "daily_morning_brief": True
    }
    res_post = client.post("/api/notifications/settings?user_id=default_user", json=update_payload)
    assert res_post.status_code == 200
    updated = res_post.json()
    assert updated["current_threshold"] == 165
    assert updated["use_recommended_threshold"] is False
    assert updated["forecast_alerts"] is False

def test_api_cpcb_recommendations_endpoint():
    """Verify GET /api/notifications/recommendations returns complete CPCB matrix."""
    res = client.get("/api/notifications/recommendations?user_id=default_user")
    assert res.status_code == 200
    data = res.json()
    assert data["aqi_standard"] == "CPCB National Air Quality Index (NAQI)"
    assert len(data["categories"]) == 6
    categories = [c["category"] for c in data["categories"]]
    assert categories == ["Good", "Satisfactory", "Moderate", "Poor", "Very Poor", "Severe"]
    assert "medical" in data["disclaimer"].lower()
