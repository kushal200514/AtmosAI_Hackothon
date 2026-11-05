import pytest
from fastapi.testclient import TestClient
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.main import app

client = TestClient(app)

def test_auth_status_endpoint():
    res = client.get("/api/auth/status")
    assert res.status_code == 200
    data = res.json()
    assert "provider" in data
    assert "mode" in data

def test_signup_creates_uncompleted_onboarding():
    res = client.post("/api/auth/signup", json={
        "email": "test_runner@atmosai.org",
        "password": "Password123!",
        "full_name": "Test Runner"
    })
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "success"
    assert data["user"]["onboarding_completed"] is False
    assert data["user"]["onboarding_step"] == 1

def test_login_returns_existing_profile_status():
    # Login as default_user
    res = client.post("/api/auth/login", json={
        "email": "default_user@atmosai.org",
        "password": "Password123!"
    })
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "success"
    # default_user has onboarding completed
    assert data["onboarding_completed"] is True

def test_onboarding_step_progression_and_completion():
    user_id = "test_progress_user"
    # Start onboarding at step 2
    res = client.post(f"/api/user/profile?user_id={user_id}", json={
        "user_category": "student",
        "onboarding_step": 2,
        "onboarding_completed": False
    })
    assert res.status_code == 200
    profile = res.json()["profile"]
    assert profile["onboarding_step"] == 2
    assert profile["onboarding_completed"] is False
    assert profile["user_category"] == "student"

    # Complete onboarding
    res2 = client.post(f"/api/user/profile?user_id={user_id}", json={
        "onboarding_step": 5,
        "onboarding_completed": True,
        "city": "Bengaluru",
        "locality": "Koramangala"
    })
    assert res2.status_code == 200
    profile2 = res2.json()["profile"]
    assert profile2["onboarding_step"] == 5
    assert profile2["onboarding_completed"] is True

