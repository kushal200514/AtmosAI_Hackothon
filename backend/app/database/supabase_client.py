import os
import logging
from typing import Optional, Dict, Any, List
from supabase import create_client, Client
from app.core.config import settings

logger = logging.getLogger("atmosai.database")

# In-memory store fallback for development / local testing when Supabase keys are not set
SEED_LOCATIONS = [
    {
        "id": "11111111-1111-1111-1111-111111111101",
        "name": "bengaluru_central",
        "display_name": "Bengaluru Central ",
        "city": "Bengaluru",
        "state": "Karnataka",
        "country": "India",
        "latitude": 12.9716,
        "longitude": 77.5946,
        "station_code": "BLR-CEN-01",
        "is_active": True
    },
    {
        "id": "11111111-1111-1111-1111-111111111102",
        "name": "yelahanka",
        "display_name": "Yelahanka Satellite Town",
        "city": "Bengaluru",
        "state": "Karnataka",
        "country": "India",
        "latitude": 13.1007,
        "longitude": 77.5963,
        "station_code": "BLR-YLH-02",
        "is_active": True
    },
    {
        "id": "11111111-1111-1111-1111-111111111103",
        "name": "hebbal",
        "display_name": "Hebbal Flyover Junction",
        "city": "Bengaluru",
        "state": "Karnataka",
        "country": "India",
        "latitude": 13.0358,
        "longitude": 77.5970,
        "station_code": "BLR-HBL-03",
        "is_active": True
    },
    {
        "id": "11111111-1111-1111-1111-111111111104",
        "name": "peenya",
        "display_name": "Peenya Industrial Area",
        "city": "Bengaluru",
        "state": "Karnataka",
        "country": "India",
        "latitude": 13.0285,
        "longitude": 77.5197,
        "station_code": "BLR-PNY-04",
        "is_active": True
    },
    {
        "id": "11111111-1111-1111-1111-111111111105",
        "name": "koramangala",
        "display_name": "Koramangala 4th Block",
        "city": "Bengaluru",
        "state": "Karnataka",
        "country": "India",
        "latitude": 12.9352,
        "longitude": 77.6245,
        "station_code": "BLR-KRM-05",
        "is_active": True
    },
    {
        "id": "11111111-1111-1111-1111-111111111106",
        "name": "silk_board",
        "display_name": "Central Silk Board Junction",
        "city": "Bengaluru",
        "state": "Karnataka",
        "country": "India",
        "latitude": 12.9177,
        "longitude": 77.6238,
        "station_code": "BLR-CSB-06",
        "is_active": True
    },
    {
        "id": "11111111-1111-1111-1111-111111111107",
        "name": "electronic_city",
        "display_name": "Electronic City Phase 1",
        "city": "Bengaluru",
        "state": "Karnataka",
        "country": "India",
        "latitude": 12.8452,
        "longitude": 77.6602,
        "station_code": "BLR-ELC-07",
        "is_active": True
    },
    {
        "id": "11111111-1111-1111-1111-111111111108",
        "name": "whitefield",
        "display_name": "Whitefield (Tech Corridor / ITPL)",
        "city": "Bengaluru",
        "state": "Karnataka",
        "country": "India",
        "latitude": 12.9698,
        "longitude": 77.7499,
        "station_code": "BLR-WTF-08",
        "is_active": True
    },
    {
        "id": "11111111-1111-1111-1111-111111111109",
        "name": "jayanagar",
        "display_name": "Jayanagar 4th Block",
        "city": "Bengaluru",
        "state": "Karnataka",
        "country": "India",
        "latitude": 12.9299,
        "longitude": 77.5833,
        "station_code": "BLR-JYN-09",
        "is_active": True
    }
]

class DatabaseManager:
    """
    Unified Database abstraction managing Supabase client connectivity
    with transparent in-memory fallback for local development.
    """
    def __init__(self):
        self._client: Optional[Client] = None
        self._is_connected = False
        self._init_connection()

    def _init_connection(self):
        url = settings.SUPABASE_URL
        key = settings.SUPABASE_SERVICE_ROLE_KEY or settings.SUPABASE_KEY
        if url and key and "your-project" not in url:
            try:
                self._client = create_client(url, key)
                self._is_connected = True
                logger.info("Connected successfully to remote Supabase instance")
            except Exception as e:
                logger.warning(f"Could not initialize Supabase client: {e}. Falling back to local store.")
                self._is_connected = False
        else:
            logger.info("No remote Supabase credentials supplied; operating in local in-memory persistence mode.")
            self._is_connected = False

    @property
    def is_connected(self) -> bool:
        return self._is_connected

    @property
    def client(self) -> Optional[Client]:
        return self._client

    async def get_locations(self) -> List[Dict[str, Any]]:
        """Fetch all active monitoring stations"""
        if self._is_connected and self._client:
            try:
                res = self._client.table("locations").select("*").eq("is_active", True).execute()
                if res.data:
                    return res.data
            except Exception as e:
                logger.error(f"Error fetching locations from Supabase: {e}")
        return SEED_LOCATIONS

    async def get_location_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        """Find location by slug or name"""
        locations = await self.get_locations()
        for loc in locations:
            if loc["name"] == name or loc.get("station_code") == name:
                return loc
        return None

db_manager = DatabaseManager()

