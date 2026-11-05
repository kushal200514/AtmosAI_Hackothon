import pytest
from datetime import datetime, timezone
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.main import app
from app.services.location.saved_location_service import (
    SavedLocationService,
    saved_location_service
)
from app.schemas.saved_location import (
    LocationType,
    SavedLocationCreate,
    SavedLocationUpdate
)

client = TestClient(app)

def test_unauthenticated_get_locations_returns_stations():
    """Verify backward compatibility: GET /api/locations without user identity returns monitoring stations."""
    res = client.get("/api/locations")
    assert res.status_code == 200
    data = res.json()
    assert isinstance(data, list)
    assert len(data) >= 7
    assert "station_code" in data[0] or "name" in data[0]

def test_get_saved_locations_for_user():
    """Verify GET /api/locations?user_id=default_user returns user's saved places."""
    res = client.get("/api/locations?user_id=default_user")
    assert res.status_code == 200
    data = res.json()
    assert isinstance(data, list)
    assert len(data) >= 3
    # Check default pre-seeded types
    types = [d["location_type"] for d in data]
    assert LocationType.HOME.value in types
    assert LocationType.OFFICE.value in types
    assert LocationType.COLLEGE_SCHOOL.value in types

def test_create_saved_location():
    """Test saving a new location."""
    payload = {
        "location_name": "Cubbon Park Jogging Track",
        "location_type": "favourite_place",
        "address": "Kasturba Road, Bengaluru",
        "latitude": 12.9763,
        "longitude": 77.5929,
        "is_primary": False
    }
    res = client.post("/api/locations?user_id=test_user_1", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["location_name"] == "Cubbon Park Jogging Track"
    assert data["location_type"] == "favourite_place"
    assert data["latitude"] == 12.9763
    assert data["longitude"] == 77.5929
    assert data["user_id"] == "test_user_1"
    # First location should be primary
    assert data["is_primary"] is True
    assert "location_id" in data

def test_edit_saved_location():
    """Test updating name and type of a saved location."""
    # First create
    create_res = client.post("/api/locations?user_id=test_user_edit", json={
        "location_name": "Old Name",
        "location_type": "custom",
        "latitude": 12.9500,
        "longitude": 77.6000
    })
    loc_id = create_res.json()["location_id"]

    # Update
    update_payload = {
        "location_name": "New Renamed Spot",
        "location_type": "favourite_place",
        "address": "Renamed Address"
    }
    update_res = client.put(f"/api/locations/{loc_id}?user_id=test_user_edit", json=update_payload)
    assert update_res.status_code == 200
    updated_data = update_res.json()
    assert updated_data["location_name"] == "New Renamed Spot"
    assert updated_data["location_type"] == "favourite_place"
    assert updated_data["address"] == "Renamed Address"

def test_delete_saved_location():
    """Test deleting a saved location."""
    create_res = client.post("/api/locations?user_id=test_user_del", json={
        "location_name": "Temporary Place",
        "location_type": "custom",
        "latitude": 12.9500,
        "longitude": 77.6000
    })
    loc_id = create_res.json()["location_id"]

    # Delete
    del_res = client.delete(f"/api/locations/{loc_id}?user_id=test_user_del")
    assert del_res.status_code == 200
    assert del_res.json()["status"] == "success"

    # Confirm deleted
    get_res = client.get("/api/locations?user_id=test_user_del")
    loc_ids = [d["location_id"] for d in get_res.json()]
    assert loc_id not in loc_ids

def test_user_isolation_protection():
    """A user must only access, modify, or delete their own saved locations."""
    # User A creates a place
    res_a = client.post("/api/locations?user_id=user_alpha", json={
        "location_name": "Alpha Secret Spot",
        "location_type": "custom",
        "latitude": 12.9200,
        "longitude": 77.6100
    })
    loc_id_a = res_a.json()["location_id"]

    # User B tries to update User A's place -> 404
    update_res = client.put(f"/api/locations/{loc_id_a}?user_id=user_beta", json={
        "location_name": "Hacked Name"
    })
    assert update_res.status_code == 404

    # User B tries to delete User A's place -> 404
    del_res = client.delete(f"/api/locations/{loc_id_a}?user_id=user_beta")
    assert del_res.status_code == 404

    # User B tries to read air quality for User A's place -> 404
    aq_res = client.get(f"/api/locations/{loc_id_a}/air-quality?user_id=user_beta")
    assert aq_res.status_code == 404

def test_location_search():
    """Test searching for locations with nearest monitoring station proximity."""
    res = client.get("/api/locations/search?q=indiranagar")
    assert res.status_code == 200
    results = res.json()
    assert len(results) >= 1
    first = results[0]
    assert "Indiranagar" in first["display_name"]
    assert first["nearest_station_name"] is not None
    assert first["nearest_station_distance_km"] > 0.0

def test_air_quality_nearby_station():
    """Test air quality retrieval for location with nearby monitoring station."""
    # Central Bengaluru location (close to Bengaluru Central station)
    create_res = client.post("/api/locations?user_id=test_aq_user", json={
        "location_name": "MG Road Office",
        "location_type": "office",
        "latitude": 12.9716,
        "longitude": 77.5946
    })
    loc_id = create_res.json()["location_id"]

    res = client.get(f"/api/locations/{loc_id}/air-quality?user_id=test_aq_user")
    assert res.status_code == 200
    aq = res.json()
    assert "nearest_station" in aq
    assert aq["nearest_station"]["distance_km"] < 2.5
    assert aq["nearest_station"]["is_representative"] is True
    assert "disclaimer" in aq

def test_air_quality_distant_station():
    """Test air quality retrieval for distant location (e.g. Airport) reports actual distance."""
    # Devanahalli Airport (far from downtown central station)
    create_res = client.post("/api/locations?user_id=test_aq_user", json={
        "location_name": "Airport Lounge",
        "location_type": "custom",
        "latitude": 13.1986,
        "longitude": 77.7066
    })
    loc_id = create_res.json()["location_id"]

    res = client.get(f"/api/locations/{loc_id}/air-quality?user_id=test_aq_user")
    assert res.status_code == 200
    aq = res.json()
    assert aq["nearest_station"]["distance_km"] > 10.0
    # Station is distant, so is_representative must be False
    assert aq["nearest_station"]["is_representative"] is False

def test_air_quality_unavailable_api_handling():
    """Test handling when environmental API is unavailable - does not fabricate data."""
    create_res = client.post("/api/locations?user_id=test_aq_user", json={
        "location_name": "Remote Farm",
        "location_type": "favourite_place",
        "latitude": 12.8000,
        "longitude": 77.4000
    })
    loc_id = create_res.json()["location_id"]

    with patch("app.services.environmental.openmeteo_client.openmeteo_client.get_air_quality", new=AsyncMock(return_value=None)), \
         patch("app.services.environmental.openaq_client.openaq_client.get_latest_measurements", new=AsyncMock(return_value=None)):
        res = client.get(f"/api/locations/{loc_id}/air-quality?user_id=test_aq_user")
        assert res.status_code == 200
        aq = res.json()
        assert aq["freshness_status"] == "UNAVAILABLE"
        assert aq["pm25"] is None
        assert "Zero synthetic" in aq["disclaimer"]

