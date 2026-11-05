import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.main import app
from app.schemas.profile import (
    UserProfile, 
    UserCategory, 
    SensitivityPreference, 
    NotificationPreferences,
    AgeGroup,
    OutdoorTimeDuration
)
from app.services.recommendations.personalization_service import personalization_engine
from app.services.ai.service import ai_service
from app.services.iot.wearable_service import wearable_service

client = TestClient(app)

MOCK_AIR = {
    "current": {
        "time": "2026-11-05T13:00",
        "interval": 3600,
        "pm10": 45.0,
        "pm2_5": 38.0,
        "carbon_monoxide": 300.0,
        "nitrogen_dioxide": 12.0,
        "sulphur_dioxide": 8.0,
        "ozone": 85.0
    }
}

MOCK_WEATHER = {
    "current": {
        "time": "2026-11-05T13:00",
        "interval": 900,
        "temperature_2m": 29.0,
        "relative_humidity_2m": 50.0,
        "wind_speed_10m": 11.0,
        "wind_direction_10m": 90.0,
        "surface_pressure": 912.0,
        "precipitation": 0.0
    }
}

def test_six_personas_distinct_widget_order():
    """Verify that all 6 personas have tailored widget priorities matching persona rules."""
    personas = [
        UserCategory.STUDENT,
        UserCategory.RUNNER,
        UserCategory.OFFICE_COMMUTER,
        UserCategory.OUTDOOR_WORKER,
        UserCategory.PARENT,
        UserCategory.GENERAL_PUBLIC
    ]

    orders = {}
    for p in personas:
        user = UserProfile(user_category=p, full_name=f"User {p.value}")
        config = personalization_engine.resolve_config(user)
        orders[p.value] = config.widget_order
        assert len(config.widget_order) == 8
        assert len(config.visible_widgets) >= 7

    # Student prioritizes current_aqi and environmental_alerts
    assert orders["student"][0] == "current_aqi"
    assert orders["student"][1] == "environmental_alerts"

    # Runner prioritizes pm25_forecast and activity_planner
    assert orders["runner"][0] == "pm25_forecast"
    assert orders["runner"][1] == "activity_planner"

    # Office commuter prioritizes pm25_forecast and commute alerts
    assert orders["office_commuter"][0] == "pm25_forecast"
    assert orders["office_commuter"][1] == "environmental_alerts"

    # Outdoor worker prioritizes current_aqi and environmental_alerts
    assert orders["outdoor_worker"][0] == "current_aqi"
    assert orders["outdoor_worker"][1] == "environmental_alerts"

    # Parent prioritizes ai_insight and activity_planner
    assert orders["parent"][0] == "ai_insight"
    assert orders["parent"][1] == "activity_planner"

    # General public prioritizes current_aqi and pm25_forecast
    assert orders["general_public"][0] == "current_aqi"
    assert orders["general_public"][1] == "pm25_forecast"

def test_activity_planner_windows_evaluation():
    """Verify activity planner window evaluation with suitability scores and favorability explanations."""
    user = UserProfile(
        user_category=UserCategory.RUNNER, 
        preferred_activities=["running", "cycling"]
    )

    from app.schemas.environmental import LiveEnvironmentalData, WeatherConditions
    from app.schemas.forecast import ForecastResponse, ForecastPoint
    from datetime import datetime, timezone

    live = LiveEnvironmentalData(
        location_id="loc_1",
        location_name="bengaluru_central",
        display_name="Bengaluru Central",
        latitude=12.9716,
        longitude=77.5946,
        query_timestamp_iso=datetime.now(timezone.utc).isoformat(),
        data_source="Open-Meteo",
        aqi=65,
        aqi_category="Satisfactory",
        pm25=30.0,
        dominant_pollutant="PM2.5",
        risk_level="Low Risk",
        weather=WeatherConditions(temperature_c=28.0, relative_humidity_pct=50.0, wind_speed_kmh=12.0)
    )

    now = datetime.now(timezone.utc)
    forecast = ForecastResponse(
        location_id="loc_1",
        location_name="bengaluru_central",
        generated_at=now,
        forecast_points=[
            ForecastPoint(
                horizon_hours=3, 
                target_timestamp=now,
                target_time_label="16:00 (+3h)", 
                predicted_pm25=22.0, 
                confidence_lower=17.0, 
                confidence_upper=27.0, 
                trend="improving", 
                risk_level="Low Risk"
            ),
            ForecastPoint(
                horizon_hours=5, 
                target_timestamp=now,
                target_time_label="18:00 (+5h)", 
                predicted_pm25=48.0, 
                confidence_lower=40.0, 
                confidence_upper=56.0, 
                trend="rising", 
                risk_level="Moderate Risk"
            )
        ],
        primary_driving_factors=["Diurnal traffic pattern"],
        uncertainty_description="90% Prediction Interval",
        surge_detected=False
    )

    scores = personalization_engine.evaluate_planner_windows(user, forecast, live)
    assert len(scores) > 0
    
    # Check that explanations identify favorable vs challenging windows
    favorable = [s for s in scores if s.predicted_pm25 < 30.0]
    assert any("favorable" in s.explanation.lower() or "drop" in s.explanation.lower() for s in favorable)
    
    challenging = [s for s in scores if s.predicted_pm25 > 40.0]
    assert any("caution" in s.explanation.lower() or "increase" in s.explanation.lower() for s in challenging)

def test_alert_personalization_filtering():
    """Verify that alert types follow user notification settings."""
    user = UserProfile(
        id="test_filter_user",
        notifications=NotificationPreferences(
            high_pollution_threshold=200, # Very high threshold
            improving_air_alerts=False,
            commute_window_alerts=False,
            daily_morning_brief=False,
            forecast_alerts=False
        )
    )
    wearable_service.user_profiles["test_filter_user"] = user

    with patch("app.services.environmental.openmeteo_client.openmeteo_client.get_air_quality", new=AsyncMock(return_value=MOCK_AIR)), \
         patch("app.services.environmental.openmeteo_client.openmeteo_client.get_live_weather", new=AsyncMock(return_value=MOCK_WEATHER)), \
         patch("app.services.environmental.openaq_client.openaq_client.get_latest_measurements", new=AsyncMock(return_value=None)):

        # Since threshold is 200 and air is 38 ug/m3, and improving_air_alerts is disabled, alerts should be empty
        response = client.get("/api/alerts?user_id=test_filter_user")
        assert response.status_code == 200
        alerts = response.json()
        assert len(alerts) == 0

def test_multilingual_ai_assistance():
    """Verify multilingual output in Hindi and Kannada with appropriate disclaimers."""
    # Hindi Profile
    user_hi = UserProfile(
        id="user_hi",
        preferred_language="hi",
        user_category=UserCategory.STUDENT
    )
    wearable_service.user_profiles["user_hi"] = user_hi

    with patch("app.services.environmental.openmeteo_client.openmeteo_client.get_air_quality", new=AsyncMock(return_value=MOCK_AIR)), \
         patch("app.services.environmental.openmeteo_client.openmeteo_client.get_live_weather", new=AsyncMock(return_value=MOCK_WEATHER)), \
         patch("app.services.environmental.openaq_client.openaq_client.get_latest_measurements", new=AsyncMock(return_value=None)):

        res_hi = client.get("/api/advice?location=bengaluru_central&user_id=user_hi")
        assert res_hi.status_code == 200
        data_hi = res_hi.json()
        assert "AtmosAI मार्गदर्शन" in data_hi["disclaimer"]

    # Kannada Profile
    user_kn = UserProfile(
        id="user_kn",
        preferred_language="kn",
        user_category=UserCategory.PARENT
    )
    wearable_service.user_profiles["user_kn"] = user_kn

    with patch("app.services.environmental.openmeteo_client.openmeteo_client.get_air_quality", new=AsyncMock(return_value=MOCK_AIR)), \
         patch("app.services.environmental.openmeteo_client.openmeteo_client.get_live_weather", new=AsyncMock(return_value=MOCK_WEATHER)), \
         patch("app.services.environmental.openaq_client.openaq_client.get_latest_measurements", new=AsyncMock(return_value=None)):

        res_kn = client.get("/api/advice?location=bengaluru_central&user_id=user_kn")
        assert res_kn.status_code == 200
        data_kn = res_kn.json()
        assert "AtmosAI ಮಾರ್ಗದರ್ಶನವು" in data_kn["disclaimer"]

def test_api_user_profile_crud_and_personalization():
    """Verify GET and POST /api/user/profile endpoints dynamically return personalization configuration."""
    # 1. Update to Runner
    update_runner = {
        "user_category": "runner",
        "full_name": "Aarav Marathoner",
        "preferred_language": "en",
        "outdoor_time_duration": "3_to_6h",
        "preferred_activities": ["interval_training", "long_distance_running"]
    }
    res_post = client.post("/api/user/profile?user_id=test_crud_user", json=update_runner)
    assert res_post.status_code == 200
    data = res_post.json()
    assert data["status"] == "success"
    assert data["profile"]["user_category"] == "runner"
    assert data["personalization"]["widget_order"][0] == "pm25_forecast"

    # 2. Retrieve via GET
    res_get = client.get("/api/user/profile?user_id=test_crud_user")
    assert res_get.status_code == 200
    data_get = res_get.json()
    assert data_get["profile"]["full_name"] == "Aarav Marathoner"
    assert data_get["personalization"]["widget_order"][0] == "pm25_forecast"

    # 3. Update to Parent
    update_parent = {
        "user_category": "parent",
        "sensitivity_preference": "elderly_child_care"
    }
    res_post_p = client.post("/api/user/profile?user_id=test_crud_user", json=update_parent)
    assert res_post_p.status_code == 200
    data_p = res_post_p.json()
    assert data_p["personalization"]["widget_order"][0] == "ai_insight"
    assert data_p["personalization"]["cautious_mode"] is True

def test_api_planner_endpoint():
    """Verify /api/planner endpoint returns calculated scores for user's preferred activities."""
    with patch("app.services.environmental.openmeteo_client.openmeteo_client.get_air_quality", new=AsyncMock(return_value=MOCK_AIR)), \
         patch("app.services.environmental.openmeteo_client.openmeteo_client.get_live_weather", new=AsyncMock(return_value=MOCK_WEATHER)), \
         patch("app.services.environmental.openaq_client.openaq_client.get_latest_measurements", new=AsyncMock(return_value=None)):

        response = client.get("/api/planner?location=bengaluru_central")
        assert response.status_code == 200
        scores = response.json()
        assert isinstance(scores, list)
        assert len(scores) > 0
        first = scores[0]
        assert "activity_name" in first
        assert "suitability_score" in first
        assert "status" in first
        assert "explanation" in first
