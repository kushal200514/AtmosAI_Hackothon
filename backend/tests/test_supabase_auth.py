import pytest
import jwt
from datetime import datetime, timezone, timedelta
from fastapi.testclient import TestClient
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.main import app
from app.core.config import settings
from app.core.auth import verify_supabase_jwt, AuthenticatedUser

client = TestClient(app)

TEST_SECRET = "super-secret-test-jwt-key-32-chars-long!"

@pytest.fixture(autouse=True)
def configure_test_jwt_secret():
    """Temporarily configure SUPABASE_JWT_SECRET for isolated testing."""
    original_secret = settings.SUPABASE_JWT_SECRET
    original_url = settings.SUPABASE_URL
    settings.SUPABASE_JWT_SECRET = TEST_SECRET
    settings.SUPABASE_URL = "https://test-project.supabase.co"
    yield
    settings.SUPABASE_JWT_SECRET = original_secret
    settings.SUPABASE_URL = original_url

def create_test_token(user_id: str, email: str, expired: bool = False, bad_secret: bool = False, aud: str = "authenticated"):
    secret = "wrong-secret-key-for-failure-test!!" if bad_secret else TEST_SECRET
    now = datetime.now(timezone.utc)
    exp = (now - timedelta(hours=1)) if expired else (now + timedelta(hours=2))
    
    payload = {
        "sub": user_id,
        "email": email,
        "aud": aud,
        "iss": "https://test-project.supabase.co/auth/v1",
        "exp": int(exp.timestamp()),
        "iat": int(now.timestamp()),
        "role": "authenticated"
    }
    return jwt.encode(payload, secret, algorithm="HS256")

def test_verify_valid_supabase_jwt():
    """Verify that a valid Supabase token is successfully verified."""
    token = create_test_token("user_alpha_uuid", "alpha@atmosai.org")
    payload = verify_supabase_jwt(token)
    assert payload["sub"] == "user_alpha_uuid"
    assert payload["email"] == "alpha@atmosai.org"
    assert payload["aud"] == "authenticated"

def test_verify_expired_jwt_raises_401():
    """Verify that an expired token is rejected with 401 Unauthorized."""
    token = create_test_token("user_alpha_uuid", "alpha@atmosai.org", expired=True)
    with pytest.raises(Exception) as excinfo:
        verify_supabase_jwt(token)
    assert "401" in str(excinfo.value) or "expired" in str(excinfo.value).lower()

def test_verify_tampered_jwt_raises_401():
    """Verify that a token signed with the wrong secret is rejected."""
    token = create_test_token("user_alpha_uuid", "alpha@atmosai.org", bad_secret=True)
    with pytest.raises(Exception) as excinfo:
        verify_supabase_jwt(token)
    assert "401" in str(excinfo.value) or "invalid" in str(excinfo.value).lower()

def test_endpoint_derives_user_from_verified_bearer_token():
    """Verify that GET /api/user/profile extracts user identity strictly from Bearer JWT."""
    token = create_test_token("user_jwt_verified_123", "verified@atmosai.org")
    headers = {"Authorization": f"Bearer {token}"}
    
    # Initialize profile for this user
    client.post(f"/api/user/profile?user_id=user_jwt_verified_123", json={
        "full_name": "Verified User",
        "city": "Bengaluru",
        "locality": "Indiranagar",
        "user_category": "runner"
    })

    # Call endpoint with token (without user_id query param)
    res = client.get("/api/user/profile", headers=headers)
    assert res.status_code == 200
    profile = res.json()["profile"]
    assert profile["id"] == "user_jwt_verified_123"
    assert profile["user_category"] == "runner"

def test_user_a_cannot_access_user_b_profile_via_token():
    """Verify isolation: User A's token resolves User A's profile, ignoring spoofed user_id in params."""
    token_a = create_test_token("user_a_uuid", "a@atmosai.org")
    headers_a = {"Authorization": f"Bearer {token_a}"}

    # Setup User A
    client.post("/api/user/profile?user_id=user_a_uuid", json={
        "full_name": "User Alpha",
        "user_category": "student"
    })

    # Setup User B
    client.post("/api/user/profile?user_id=user_b_uuid", json={
        "full_name": "User Beta",
        "user_category": "parent"
    })

    # User A tries to pass ?user_id=user_b_uuid while authenticated with token A
    # The server derives identity from the verified Bearer token!
    res = client.get("/api/user/profile?user_id=user_b_uuid", headers=headers_a)
    assert res.status_code == 200
    data = res.json()["profile"]
    assert data["id"] == "user_a_uuid"
    assert data["full_name"] == "User Alpha"
    assert data["user_category"] == "student"

def test_demo_token_fallback():
    """Verify that demo token fallback works when configured in demo mode."""
    demo_token = "demo_token_demo_eval_user"
    payload = verify_supabase_jwt(demo_token)
    assert payload["sub"] == "demo_eval_user"
    assert payload["is_demo"] is True

