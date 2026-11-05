import pytest
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.database.supabase_client import db_manager, SEED_LOCATIONS
from app.schemas.location import LocationOut
from app.schemas.profile import UserProfileBase, ProfileType

@pytest.mark.asyncio
async def test_locations_retrieval():
    locations = await db_manager.get_locations()
    assert len(locations) >= 7
    names = [loc["name"] for loc in locations]
    assert "bengaluru_central" in names
    assert "silk_board" in names
    assert "electronic_city" in names
    assert "hebbal" in names
    assert "peenya" in names

@pytest.mark.asyncio
async def test_location_by_name():
    loc = await db_manager.get_location_by_name("bengaluru_central")
    assert loc is not None
    assert loc["city"] == "Bengaluru"
    assert loc["latitude"] == pytest.approx(12.9716, rel=1e-3)
    assert loc["longitude"] == pytest.approx(77.5946, rel=1e-3)

def test_profile_types():
    profile = UserProfileBase(profile_type=ProfileType.RUNNER, full_name="Athletic User")
    assert profile.profile_type == "runner"
    assert profile.full_name == "Athletic User"

    all_types = [p.value for p in ProfileType]
    assert "runner" in all_types
    assert "respiratory_sensitive" in all_types
    assert "parent" in all_types
    assert "delivery_worker" in all_types
    assert "office_commuter" in all_types
    assert "general_public" in all_types

