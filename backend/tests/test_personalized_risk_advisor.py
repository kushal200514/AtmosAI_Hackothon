import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.main import app
from app.services.ai.service import ai_service
from app.schemas.profile import UserCategory, SensitivityPreference, UserProfileUpdate
from app.schemas.ai import PersonalizedRiskAdvisorResponse

client = TestClient(app)

MOCK_AIR = {
    "current": {
        "time": "2026-11-05T13:00",
        "interval": 3600,
        "pm10": 30.0,
        "pm2_5": 22.0,
        "carbon_monoxide": 250.0,
        "nitrogen_dioxide": 8.0,
        "sulphur_dioxide": 5.0,
        "ozone": 80.0
    }
}

MOCK_WEATHER = {
    "current": {
        "time": "2026-11-05T13:00",
        "interval": 900,
        "temperature_2m": 26.5,
        "relative_humidity_2m": 60.0,
        "wind_speed_10m": 9.0,
        "wind_direction_10m": 110.0,
        "surface_pressure": 915.0,
        "precipitation": 0.0
    }
}

ALL_TEST_PERSONAS = [
    "student",
    "runner",
    "office_commuter",
    "outdoor_worker",
    "parent",
    "general_public"
]

@pytest.mark.asyncio
async def test_all_six_personas_produce_distinct_recommendations():
    """Verify that all six specified user personas produce distinct, tailored recommendations."""
    with patch("app.services.environmental.openmeteo_client.openmeteo_client.get_air_quality", new=AsyncMock(return_value=MOCK_AIR)), \
         patch("app.services.environmental.openmeteo_client.openmeteo_client.get_live_weather", new=AsyncMock(return_value=MOCK_WEATHER)), \
         patch("app.services.environmental.openaq_client.openaq_client.get_latest_measurements", new=AsyncMock(return_value=None)):

        outputs = {}
        for persona in ALL_TEST_PERSONAS:
            adv = await ai_service.get_advice(
                location_slug="bengaluru_central",
                profile_type=persona
            )
            assert isinstance(adv, PersonalizedRiskAdvisorResponse)
            outputs[persona] = adv

            # 7 Required Outputs validation
            assert adv.current_environmental_status is not None
            assert len(adv.current_environmental_status) > 0
            assert isinstance(adv.potential_forecast_deterioration, bool)
            assert adv.recommended_action is not None
            assert len(adv.recommended_action) > 0
            assert adv.explanation is not None
            assert adv.data_source is not None
            assert adv.timestamp_iso is not None
            assert adv.confidence_status is not None

            # Non-medical disclaimer check
            assert "medical" in adv.disclaimer.lower()

        # Persona 1: STUDENT: Prioritize campus conditions and outdoor activity guidance
        student_adv = outputs["student"]
        student_all_text = " ".join(student_adv.profile_specific_recommendations).lower() + " " + student_adv.recommended_action.lower()
        assert "campus" in student_all_text

        # Persona 2: RUNNER: Prioritize workout-time forecasts and activity recommendations
        runner_adv = outputs["runner"]
        runner_all_text = " ".join(runner_adv.profile_specific_recommendations).lower() + " " + runner_adv.recommended_action.lower()
        assert any(k in runner_all_text for k in ["run", "workout", "aerobic", "training", "cardio"])

        # Persona 3: OFFICE COMMUTER: Prioritize commute-time pollution and AC recirculation
        commuter_adv = outputs["office_commuter"]
        commuter_all_text = " ".join(commuter_adv.profile_specific_recommendations).lower() + " " + commuter_adv.recommended_action.lower()
        assert any(k in commuter_all_text for k in ["traffic", "commute", "recirculation", "corridor", "windows", "junction"])

        # Persona 4: OUTDOOR WORKER: Prioritize shift exposure, breaks, and N95 masks
        worker_adv = outputs["outdoor_worker"]
        worker_all_text = " ".join(worker_adv.profile_specific_recommendations).lower() + " " + worker_adv.recommended_action.lower()
        assert any(k in worker_all_text for k in ["n95", "shift", "street", "break", "worker", "respirator"])

        # Persona 5: PARENT: Prioritize family outdoor activity and playground guidance
        parent_adv = outputs["parent"]
        parent_all_text = " ".join(parent_adv.profile_specific_recommendations).lower() + " " + parent_adv.recommended_action.lower()
        assert any(k in parent_all_text for k in ["playground", "child", "children", "stroller", "family"])

        # Persona 6: GENERAL PUBLIC: Prioritize overall air quality and daily guidance
        general_adv = outputs["general_public"]
        general_all_text = " ".join(general_adv.profile_specific_recommendations).lower() + " " + general_adv.recommended_action.lower()
        assert any(k in general_all_text for k in ["air quality", "daily", "standard", "activities", "ventilat"])

        # Ensure recommendations are distinct between personas
        assert student_adv.recommended_action != runner_adv.recommended_action
        assert runner_adv.recommended_action != commuter_adv.recommended_action
        assert commuter_adv.recommended_action != worker_adv.recommended_action
        assert worker_adv.recommended_action != parent_adv.recommended_action

@pytest.mark.asyncio
async def test_changing_user_profile_changes_recommendations():
    """Verify that updating a user's stored profile changes their advice recommendations dynamically."""
    with patch("app.services.environmental.openmeteo_client.openmeteo_client.get_air_quality", new=AsyncMock(return_value=MOCK_AIR)), \
         patch("app.services.environmental.openmeteo_client.openmeteo_client.get_live_weather", new=AsyncMock(return_value=MOCK_WEATHER)), \
         patch("app.services.environmental.openaq_client.openaq_client.get_latest_measurements", new=AsyncMock(return_value=None)):

        test_user = "test_persona_switcher"

        # Update to student
        up_s = client.post(f"/api/user/profile?user_id={test_user}", json={
            "user_category": "student",
            "preferred_activities": ["campus_walks", "outdoor_sports"],
            "outdoor_time_duration": "1_to_3h"
        })
        assert up_s.status_code == 200
        student_res = client.get(f"/api/advice?location=bengaluru_central&user_id={test_user}").json()
        assert "campus" in student_res["recommended_action"].lower() or any("campus" in r.lower() for r in student_res["profile_specific_recommendations"])

        # Switch profile to runner
        up_r = client.post(f"/api/user/profile?user_id={test_user}", json={
            "user_category": "runner",
            "preferred_activities": ["running", "cycling"],
            "outdoor_time_duration": "less_than_1h"
        })
        assert up_r.status_code == 200
        runner_res = client.get(f"/api/advice?location=bengaluru_central&user_id={test_user}").json()
        assert any(k in runner_res["recommended_action"].lower() for k in ["run", "workout", "aerobic", "training"]) or any("run" in r.lower() for r in runner_res["profile_specific_recommendations"])

        # Switch profile to parent
        up_p = client.post(f"/api/user/profile?user_id={test_user}", json={
            "user_category": "parent",
            "preferred_activities": ["playground_trips", "stroller_walks"],
            "outdoor_time_duration": "1_to_3h"
        })
        assert up_p.status_code == 200
        parent_res = client.get(f"/api/advice?location=bengaluru_central&user_id={test_user}").json()
        assert any(k in parent_res["recommended_action"].lower() for k in ["playground", "child", "children"]) or any("child" in r.lower() for r in parent_res["profile_specific_recommendations"])

        # Verify recommended actions are different
        assert student_res["recommended_action"] != runner_res["recommended_action"]
        assert runner_res["recommended_action"] != parent_res["recommended_action"]

def test_api_advice_endpoint_returns_all_required_fields():
    """Verify that GET /api/advice returns all 7 required advisor fields with genuine data."""
    with patch("app.services.environmental.openmeteo_client.openmeteo_client.get_air_quality", new=AsyncMock(return_value=MOCK_AIR)), \
         patch("app.services.environmental.openmeteo_client.openmeteo_client.get_live_weather", new=AsyncMock(return_value=MOCK_WEATHER)), \
         patch("app.services.environmental.openaq_client.openaq_client.get_latest_measurements", new=AsyncMock(return_value=None)):

        response = client.get("/api/advice?location=bengaluru_central&profile=outdoor_worker")
        assert response.status_code == 200
        data = response.json()

        # Verify all 7 required outputs
        assert "current_environmental_status" in data
        assert "potential_forecast_deterioration" in data
        assert "recommended_action" in data
        assert "explanation" in data
        assert "data_source" in data
        assert "timestamp_iso" in data
        assert "confidence_status" in data

        # Values validation
        assert data["profile_type"] == "outdoor_worker"
        assert isinstance(data["potential_forecast_deterioration"], bool)
        assert len(data["recommended_action"]) > 0
        assert "disclaimer" in data
        assert "medical" in data["disclaimer"].lower()
