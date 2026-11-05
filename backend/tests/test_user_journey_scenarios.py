import pytest
from fastapi.testclient import TestClient
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.main import app
from app.services.iot.wearable_service import wearable_service
from app.services.recommendations.personalization_service import personalization_engine
from app.schemas.profile import UserCategory

client = TestClient(app)

def test_scenario_1_new_user_signup_and_complete_onboarding():
    """Scenario 1: New user signs up, advances through steps, and completes onboarding."""
    email = "scenario1_new@atmosai.org"
    # Step 0: Signup
    res_signup = client.post("/api/auth/signup", json={
        "email": email,
        "password": "Password123!",
        "full_name": "Scenario One"
    })
    assert res_signup.status_code == 200
    user_data = res_signup.json()["user"]
    user_id = res_signup.json()["user_id"]
    assert user_data["onboarding_completed"] is False
    assert user_data["onboarding_step"] == 1

    # Step 1: Basic info update
    res_s1 = client.post(f"/api/user/profile?user_id={user_id}", json={
        "full_name": "Scenario One",
        "city": "Bengaluru",
        "locality": "Indiranagar",
        "preferred_language": "en",
        "onboarding_step": 2,
        "onboarding_completed": False
    })
    assert res_s1.status_code == 200

    # Step 2: Lifestyle category selection (Runner)
    res_s2 = client.post(f"/api/user/profile?user_id={user_id}", json={
        "user_category": "runner",
        "onboarding_step": 3,
        "onboarding_completed": False
    })
    assert res_s2.status_code == 200

    # Step 3: Activities & outdoor time
    res_s3 = client.post(f"/api/user/profile?user_id={user_id}", json={
        "preferred_activities": ["running", "interval_training"],
        "outdoor_time_duration": "1_to_3h",
        "onboarding_step": 4,
        "onboarding_completed": False
    })
    assert res_s3.status_code == 200

    # Step 4: Environmental preferences
    res_s4 = client.post(f"/api/user/profile?user_id={user_id}", json={
        "environmental_info_preferences": ["exercise_focus", "deterioration_alerts"],
        "sensitivity_preference": "none",
        "onboarding_step": 5,
        "onboarding_completed": False
    })
    assert res_s4.status_code == 200

    # Step 5: Location & Notifications (Complete Onboarding)
    res_s5 = client.post(f"/api/user/profile?user_id={user_id}", json={
        "primary_location": "bengaluru_central",
        "notifications": {
            "high_pollution_threshold": 101,
            "surge_warnings": True
        },
        "onboarding_step": 5,
        "onboarding_completed": True
    })
    assert res_s5.status_code == 200
    prof = res_s5.json()["profile"]
    assert prof["onboarding_completed"] is True
    assert prof["user_category"] == "runner"
    # Verify runner widget prioritization
    assert res_s5.json()["personalization"]["widget_order"][0] == "pm25_forecast"
    assert res_s5.json()["personalization"]["widget_order"][1] == "activity_planner"

def test_scenario_2_and_4_resume_onboarding_midway():
    """Scenario 2 & 4: User exits midway and later resumes at saved step."""
    email = "scenario2_midway@atmosai.org"
    client.post("/api/auth/signup", json={
        "email": email,
        "password": "Password123!",
        "full_name": "Midway User"
    })
    user_id = email.replace("@", "_").replace(".", "_")

    # User reached step 3 and closed browser
    client.post(f"/api/user/profile?user_id={user_id}", json={
        "user_category": "student",
        "onboarding_step": 3,
        "onboarding_completed": False
    })

    # User returns and logs in
    login_res = client.post("/api/auth/login", json={
        "email": email,
        "password": "Password123!"
    })
    assert login_res.status_code == 200
    assert login_res.json()["onboarding_completed"] is False
    assert login_res.json()["user"]["onboarding_step"] == 3

    # User resumes and finishes from step 3 onwards
    res_finish = client.post(f"/api/user/profile?user_id={user_id}", json={
        "preferred_activities": ["walking", "campus_walks"],
        "onboarding_step": 5,
        "onboarding_completed": True
    })
    assert res_finish.status_code == 200
    assert res_finish.json()["profile"]["onboarding_completed"] is True

def test_scenario_3_existing_user_direct_to_dashboard():
    """Scenario 3: Returning user with completed onboarding goes straight to dashboard."""
    res = client.post("/api/auth/login", json={
        "email": "default_user@atmosai.org",
        "password": "Password123!"
    })
    assert res.status_code == 200
    assert res.json()["onboarding_completed"] is True

def test_scenario_5_and_6_change_lifestyle_and_dashboard_updates():
    """Scenario 5 & 6: Changing category immediately reconfigures dashboard widget order."""
    user_id = "test_persona_switcher"
    # Set as Student
    r1 = client.post(f"/api/user/profile?user_id={user_id}", json={
        "user_category": "student"
    })
    order_student = r1.json()["personalization"]["widget_order"]
    assert order_student[0] == "current_aqi"
    assert order_student[1] == "environmental_alerts"

    # Switch to Runner
    r2 = client.post(f"/api/user/profile?user_id={user_id}", json={
        "user_category": "runner"
    })
    order_runner = r2.json()["personalization"]["widget_order"]
    assert order_runner[0] == "pm25_forecast"
    assert order_runner[1] == "activity_planner"

    # Switch to Cyclist
    r3 = client.post(f"/api/user/profile?user_id={user_id}", json={
        "user_category": "cyclist"
    })
    order_cyclist = r3.json()["personalization"]["widget_order"]
    assert order_cyclist[0] == "pm25_forecast"
    assert "Cycling" in r3.json()["personalization"]["priority_headline"]

def test_scenario_7_change_saved_location():
    """Scenario 7: User changes saved location and primary place."""
    user_id = "test_loc_user"
    create_res = client.post(f"/api/locations?user_id={user_id}", json={
        "location_name": "Home Sanctuary",
        "latitude": 12.9716,
        "longitude": 77.5946,
        "location_type": "home",
        "is_primary": True
    })
    assert create_res.status_code == 200
    loc_id = create_res.json()["location_id"]

    # Verify primary location reflects in saved places
    list_res = client.get(f"/api/locations?user_id={user_id}")
    assert list_res.status_code == 200
    assert any(l.get("location_id") == loc_id and l.get("is_primary") is True for l in list_res.json())

def test_scenario_8_logout_and_login():
    """Scenario 8: User logs out and logs in again, retaining saved preferences."""
    email = "scenario8@atmosai.org"
    user_id = email.replace("@", "_").replace(".", "_")
    client.post("/api/auth/signup", json={
        "email": email,
        "password": "Password123!",
        "full_name": "Persisted User"
    })
    client.post(f"/api/user/profile?user_id={user_id}", json={
        "city": "Bengaluru",
        "locality": "Koramangala",
        "user_category": "office_commuter",
        "onboarding_completed": True
    })

    # Subsequent login retrieves saved profile
    login_res = client.post("/api/auth/login", json={
        "email": email,
        "password": "Password123!"
    })
    assert login_res.status_code == 200
    assert login_res.json()["onboarding_completed"] is True
    # Check profile persistence
    prof = client.get(f"/api/user/profile?user_id={user_id}").json()["profile"]
    assert prof["locality"] == "Koramangala"
    assert prof["user_category"] == "office_commuter"

def test_scenario_9_unauthenticated_and_api_availability():
    """Scenario 9 & 10: Auth status endpoint provides graceful status even when external services vary."""
    res = client.get("/api/auth/status")
    assert res.status_code == 200
    data = res.json()
    assert data["provider"] in ("supabase", "demo")
    assert data["mode"] in ("production", "demo")
