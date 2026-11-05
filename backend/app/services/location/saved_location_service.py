import math
import uuid
import logging
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional, Tuple

from app.schemas.saved_location import (
    LocationType,
    NearestStationInfo,
    SavedLocationAirQuality,
    SavedLocationCreate,
    SavedLocationUpdate,
    SavedLocationOut,
    LocationSearchResult
)
from app.database.supabase_client import db_manager, SEED_LOCATIONS
from app.services.environmental.openmeteo_client import openmeteo_client
from app.services.environmental.openaq_client import openaq_client
from app.services.environmental.aqi_calculator import compute_naqi
from app.services.data_reliability_service import reliability_service
from app.schemas.reliability import FreshnessStatus, SourceType

logger = logging.getLogger("atmosai.saved_locations")

# Pre-indexed Bengaluru Geocoded Knowledge Base for instant search
BENGALURU_KNOWLEDGE_BASE = [
    {
        "display_name": "Indiranagar (100 Feet Rd)",
        "address": "100 Feet Road, Indiranagar, Bengaluru, Karnataka 560038",
        "latitude": 12.9784,
        "longitude": 77.6408,
        "place_type": "residential_commercial"
    },
    {
        "display_name": "Koramangala (Sony World Signal)",
        "address": "80 Feet Road, 4th Block, Koramangala, Bengaluru, Karnataka 560034",
        "latitude": 12.9352,
        "longitude": 77.6245,
        "place_type": "residential_commercial"
    },
    {
        "display_name": "Whitefield (ITPL Campus)",
        "address": "International Tech Park, Whitefield, Bengaluru, Karnataka 560066",
        "latitude": 12.9866,
        "longitude": 77.7380,
        "place_type": "tech_hub"
    },
    {
        "display_name": "Bellandur (Ecospace Business Park)",
        "address": "Outer Ring Road, Bellandur, Bengaluru, Karnataka 560103",
        "latitude": 12.9260,
        "longitude": 77.6843,
        "place_type": "tech_hub"
    },
    {
        "display_name": "PES University (RR Campus)",
        "address": "100 Feet Ring Road, BSK III Stage, Bengaluru, Karnataka 560085",
        "latitude": 12.9344,
        "longitude": 77.5345,
        "place_type": "college_school"
    },
    {
        "display_name": "IISc (Indian Institute of Science)",
        "address": "CV Raman Rd, Malleshwaram, Bengaluru, Karnataka 560012",
        "latitude": 13.0219,
        "longitude": 77.5671,
        "place_type": "college_school"
    },
    {
        "display_name": "Electronic City Phase 1",
        "address": "Hosur Road, Electronic City, Bengaluru, Karnataka 560100",
        "latitude": 12.8452,
        "longitude": 77.6602,
        "place_type": "tech_hub"
    },
    {
        "display_name": "HSR Layout (Sector 2)",
        "address": "27th Main Rd, Sector 2, HSR Layout, Bengaluru, Karnataka 560102",
        "latitude": 12.9121,
        "longitude": 77.6446,
        "place_type": "residential"
    },
    {
        "display_name": "Jayanagar 4th Block",
        "address": "9th Main Rd, 4th Block, Jayanagar, Bengaluru, Karnataka 560011",
        "latitude": 12.9308,
        "longitude": 77.5838,
        "place_type": "residential"
    },
    {
        "display_name": "Malleshwaram (Sampige Road)",
        "address": "Sampige Road, Malleshwaram, Bengaluru, Karnataka 560003",
        "latitude": 13.0031,
        "longitude": 77.5643,
        "place_type": "residential"
    },
    {
        "display_name": "Silk Board Junction",
        "address": "Hosur Road / Outer Ring Rd, Bengaluru, Karnataka 560068",
        "latitude": 12.9177,
        "longitude": 77.6238,
        "place_type": "transit_hub"
    },
    {
        "display_name": "Hebbal Flyover / Estuary",
        "address": "Bellary Road, Hebbal, Bengaluru, Karnataka 560024",
        "latitude": 13.0358,
        "longitude": 77.5970,
        "place_type": "transit_hub"
    },
    {
        "display_name": "Cubbon Park / High Court",
        "address": "Kasturba Road, Central Bengaluru, Karnataka 560001",
        "latitude": 12.9763,
        "longitude": 77.5929,
        "place_type": "favourite_place"
    },
    {
        "display_name": "Manyata Tech Park (Nagavara)",
        "address": "Thanisandra Main Rd, Nagavara, Bengaluru, Karnataka 560045",
        "latitude": 13.0478,
        "longitude": 77.6206,
        "place_type": "tech_hub"
    },
    {
        "display_name": "Kempegowda International Airport (BLR)",
        "address": "KIAL Rd, Devanahalli, Bengaluru, Karnataka 560300",
        "latitude": 13.1986,
        "longitude": 77.7066,
        "place_type": "transit_hub"
    }
]

class SavedLocationService:
    """
    Manages user-saved locations (Home, College / School, Office, Favourite Place, Custom).
    Calculates nearest monitoring station proximity, retrieves multi-pollutant measurements,
    and safeguards data transparency.
    """
    def __init__(self):
        # In-memory user isolation store: user_id -> Dict[location_id, dict]
        self._user_locations: Dict[str, Dict[str, Dict[str, Any]]] = {}
        self._init_default_user_locations()

    def _init_default_user_locations(self):
        """Seed realistic saved locations for default_user."""
        user_id = "default_user"
        now = datetime.now(timezone.utc)
        
        home_id = "loc-home-001"
        office_id = "loc-office-002"
        college_id = "loc-college-003"
        
        self._user_locations[user_id] = {
            home_id: {
                "location_id": home_id,
                "user_id": user_id,
                "location_name": "My Home (Indiranagar)",
                "location_type": LocationType.HOME,
                "address": "100 Feet Road, Indiranagar, Bengaluru",
                "latitude": 12.9784,
                "longitude": 77.6408,
                "created_at": now,
                "is_primary": True
            },
            office_id: {
                "location_id": office_id,
                "user_id": user_id,
                "location_name": "Bellandur Tech Office",
                "location_type": LocationType.OFFICE,
                "address": "Ecospace Business Park, Outer Ring Rd, Bellandur",
                "latitude": 12.9260,
                "longitude": 77.6843,
                "created_at": now,
                "is_primary": False
            },
            college_id: {
                "location_id": college_id,
                "user_id": user_id,
                "location_name": "PES University Campus",
                "location_type": LocationType.COLLEGE_SCHOOL,
                "address": "100 Feet Ring Road, BSK III Stage, Bengaluru",
                "latitude": 12.9344,
                "longitude": 77.5345,
                "created_at": now,
                "is_primary": False
            }
        }

    @staticmethod
    def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Calculate Great Circle distance between coordinates in kilometers."""
        r = 6371.0
        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)
        a = (math.sin(dlat / 2) ** 2 + 
             math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * 
             math.sin(dlon / 2) ** 2)
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        return round(r * c, 2)

    async def find_nearest_station(self, lat: float, lon: float) -> Tuple[Dict[str, Any], float]:
        """
        Finds the nearest registered CPCB/KSPCB monitoring station from region database.
        Returns (station_dict, distance_km).
        """
        stations = await db_manager.get_locations()
        if not stations:
            stations = SEED_LOCATIONS
            
        closest_station = None
        min_dist = float("inf")
        
        for st in stations:
            st_lat = st.get("latitude")
            st_lon = st.get("longitude")
            if st_lat is not None and st_lon is not None:
                dist = self.haversine_km(lat, lon, st_lat, st_lon)
                if dist < min_dist:
                    min_dist = dist
                    closest_station = st
                    
        if closest_station is None:
            # Fallback to Central Bengaluru if list empty
            fallback = SEED_LOCATIONS[0]
            return fallback, self.haversine_km(lat, lon, fallback["latitude"], fallback["longitude"])
            
        return closest_station, round(min_dist, 2)

    def search_locations(self, query: str) -> List[LocationSearchResult]:
        """
        Searches available localities and landmarks across Bengaluru with nearest station proximity.
        """
        q = (query or "").strip().lower()
        if not q:
            # Return top 5 popular spots
            matches = BENGALURU_KNOWLEDGE_BASE[:5]
        else:
            matches = [
                place for place in BENGALURU_KNOWLEDGE_BASE
                if q in place["display_name"].lower() or q in place["address"].lower()
            ]
            
        results = []
        for place in matches:
            # Calculate distance to nearest seed station
            closest_st, dist = min(
                [(st, self.haversine_km(place["latitude"], place["longitude"], st["latitude"], st["longitude"])) 
                 for st in SEED_LOCATIONS],
                key=lambda x: x[1]
            )
            results.append(LocationSearchResult(
                display_name=place["display_name"],
                address=place["address"],
                latitude=place["latitude"],
                longitude=place["longitude"],
                place_type=place.get("place_type"),
                nearest_station_name=closest_st["display_name"],
                nearest_station_distance_km=round(dist, 2)
            ))
        return results

    # ------------------ CRUD Operations (User Protected) ------------------

    def get_saved_locations(self, user_id: str) -> List[SavedLocationOut]:
        """Retrieve all saved locations belonging strictly to user_id."""
        locations_dict = self._user_locations.get(user_id, {})
        # Sort primary first, then by created_at descending
        sorted_locs = sorted(
            locations_dict.values(),
            key=lambda x: (not x.get("is_primary", False), x.get("created_at") or datetime.min),
            reverse=False
        )
        return [SavedLocationOut(**loc) for loc in sorted_locs]

    def get_saved_location(self, user_id: str, location_id: str) -> Optional[SavedLocationOut]:
        """Retrieve a specific saved location with strict user ownership validation."""
        user_locs = self._user_locations.get(user_id, {})
        loc = user_locs.get(location_id)
        if not loc:
            return None
        return SavedLocationOut(**loc)

    def add_saved_location(self, user_id: str, data: SavedLocationCreate) -> SavedLocationOut:
        """Create and store a new location for user_id."""
        if user_id not in self._user_locations:
            self._user_locations[user_id] = {}
            
        loc_id = f"loc-{uuid.uuid4().hex[:8]}"
        is_first = len(self._user_locations[user_id]) == 0
        should_be_primary = data.is_primary or is_first

        # If marking this new location as primary, demote existing primary locations
        if should_be_primary:
            for l in self._user_locations[user_id].values():
                l["is_primary"] = False

        record = {
            "location_id": loc_id,
            "user_id": user_id,
            "location_name": data.location_name,
            "location_type": data.location_type,
            "address": data.address or f"Lat: {data.latitude:.4f}, Lon: {data.longitude:.4f}",
            "latitude": round(data.latitude, 5),
            "longitude": round(data.longitude, 5),
            "created_at": datetime.now(timezone.utc),
            "is_primary": should_be_primary
        }

        self._user_locations[user_id][loc_id] = record
        return SavedLocationOut(**record)

    def update_saved_location(
        self, 
        user_id: str, 
        location_id: str, 
        updates: SavedLocationUpdate
    ) -> Optional[SavedLocationOut]:
        """Update an existing saved location. Enforces ownership check."""
        user_locs = self._user_locations.get(user_id, {})
        if location_id not in user_locs:
            return None

        current = user_locs[location_id]

        # Handle primary promotion
        if updates.is_primary is True:
            for l in user_locs.values():
                l["is_primary"] = False
            current["is_primary"] = True
        elif updates.is_primary is False:
            current["is_primary"] = False

        if updates.location_name is not None:
            current["location_name"] = updates.location_name
        if updates.location_type is not None:
            current["location_type"] = updates.location_type
        if updates.address is not None:
            current["address"] = updates.address
        if updates.latitude is not None:
            current["latitude"] = round(updates.latitude, 5)
        if updates.longitude is not None:
            current["longitude"] = round(updates.longitude, 5)

        return SavedLocationOut(**current)

    def delete_saved_location(self, user_id: str, location_id: str) -> bool:
        """Delete a saved location. Enforces ownership check and reassigns primary if needed."""
        user_locs = self._user_locations.get(user_id, {})
        if location_id not in user_locs:
            return False

        was_primary = user_locs[location_id].get("is_primary", False)
        del user_locs[location_id]

        # If deleted location was primary, promote the remaining first location to primary
        if was_primary and user_locs:
            first_rem = next(iter(user_locs.values()))
            first_rem["is_primary"] = True

        return True

    def set_primary_location(self, user_id: str, location_id: str) -> Optional[SavedLocationOut]:
        """Convenience function to set a location as the primary default place."""
        user_locs = self._user_locations.get(user_id, {})
        if location_id not in user_locs:
            return None

        for l in user_locs.values():
            l["is_primary"] = False
        user_locs[location_id]["is_primary"] = True

        return SavedLocationOut(**user_locs[location_id])

    # ------------------ Air Quality Intelligence for Saved Places ------------------

    async def get_air_quality_for_saved_location(
        self, 
        user_id: str, 
        location_id: str
    ) -> Optional[SavedLocationAirQuality]:
        """
        Retrieves real-time environmental telemetry, valid CPCB NAQI, nearest station proximity,
        and forecast trend for a saved place.
        """
        user_locs = self._user_locations.get(user_id, {})
        loc = user_locs.get(location_id)
        if not loc:
            return None

        lat = loc["latitude"]
        lon = loc["longitude"]
        query_now = datetime.now(timezone.utc)

        # 1. Identify nearest physical monitoring station
        closest_station, distance_km = await self.find_nearest_station(lat, lon)
        nearest_info = NearestStationInfo(
            station_name=closest_station["display_name"],
            station_code=closest_station.get("station_code"),
            distance_km=distance_km,
            latitude=closest_station["latitude"],
            longitude=closest_station["longitude"],
            source="CPCB / Karnataka State PCB Ground Network",
            is_representative=(distance_km < 2.5)  # Station only close proxy if < 2.5 km
        )

        # 2. Concurrently fetch atmospheric data for exact coordinates
        pm25: Optional[float] = None
        pm10: Optional[float] = None
        co: Optional[float] = None
        no2: Optional[float] = None
        so2: Optional[float] = None
        o3: Optional[float] = None
        obs_time: Optional[str] = None
        data_source = "Open-Meteo (Copernicus CAMS Model)"
        source_type = "ESTIMATED"
        pred_3h: Optional[float] = None
        pred_6h: Optional[float] = None
        forecast_summary = "Atmospheric conditions projected to remain steady."

        try:
            air_res = await openmeteo_client.get_air_quality(lat, lon)
            if air_res and "current" in air_res:
                curr = air_res["current"]
                pm25 = curr.get("pm2_5")
                pm10 = curr.get("pm10")
                co = curr.get("carbon_monoxide")
                no2 = curr.get("nitrogen_dioxide")
                so2 = curr.get("sulphur_dioxide")
                o3 = curr.get("ozone")
                obs_time = curr.get("time")

            # Extract hourly model predictions for 3h & 6h horizons
            if air_res and "hourly" in air_res and "pm2_5" in air_res["hourly"]:
                hourly_pm = air_res["hourly"]["pm2_5"]
                if len(hourly_pm) >= 7:
                    pred_3h = round(hourly_pm[3], 1)
                    pred_6h = round(hourly_pm[6], 1)
                    diff = pred_3h - (pm25 or pred_3h)
                    if diff > 3.0:
                        forecast_summary = f"Rising trend: PM2.5 projected to reach {pred_3h} µg/m³ in +3h."
                    elif diff < -3.0:
                        forecast_summary = f"Improving dispersion: PM2.5 projected to decline to {pred_3h} µg/m³ in +3h."
                    else:
                        forecast_summary = f"Steady PM2.5 level around {pred_3h} µg/m³ expected over next 3–6 hours."
        except Exception as e:
            logger.warning(f"Failed to query Open-Meteo for saved location ({lat}, {lon}): {e}")

        # 3. Check physical sensor override if nearby station has OpenAQ live reading
        try:
            if distance_km < 3.0:
                openaq_res = await openaq_client.get_latest_measurements(
                    closest_station["latitude"], closest_station["longitude"]
                )
                if openaq_res and "sensors" in openaq_res:
                    for s in openaq_res["sensors"]:
                        p_name = s.get("parameter", {}).get("name")
                        val = s.get("latest", {}).get("value")
                        if p_name == "pm25" and val is not None:
                            pm25 = float(val)
                            obs_time = s.get("latest", {}).get("datetime")
                            source_type = "MEASURED"
                            data_source = f"OpenAQ Ground Station ({closest_station['display_name']})"
                            break
        except Exception as e:
            logger.debug(f"OpenAQ lookup skipped: {e}")

        # 4. Handle complete absence of data
        if pm25 is None:
            return SavedLocationAirQuality(
                location_id=loc["location_id"],
                location_name=loc["location_name"],
                location_type=loc["location_type"],
                latitude=lat,
                longitude=lon,
                address=loc.get("address"),
                pm25=None,
                pm10=None,
                aqi=None,
                aqi_category=None,
                risk_level=None,
                dominant_pollutant=None,
                nearest_station=nearest_info,
                source="No Upstream Telemetry Available",
                source_type="ESTIMATED",
                observed_at=None,
                freshness_status="UNAVAILABLE",
                age_minutes=None,
                forecast_summary="No forecast available (environmental APIs unreachable)",
                disclaimer="No nearby measurement available. Zero synthetic replacement values fabricated."
            )

        # 5. Compute CPCB NAQI strictly using valid multi-pollutant methodology
        aqi_info = compute_naqi(pm25=pm25, pm10=pm10, no2=no2, so2=so2, co=co, o3=o3)

        # 6. Evaluate freshness
        valid_obs_dt = reliability_service.validate_timestamp(obs_time)
        freshness = reliability_service.determine_freshness(
            observed_at=valid_obs_dt,
            reference_time=query_now,
            source_type=SourceType.MEASURED if source_type == "MEASURED" else SourceType.ESTIMATED
        )
        age_mins = reliability_service.calculate_measurement_age(valid_obs_dt, query_now)

        return SavedLocationAirQuality(
            location_id=loc["location_id"],
            location_name=loc["location_name"],
            location_type=loc["location_type"],
            latitude=lat,
            longitude=lon,
            address=loc.get("address"),
            pm25=round(pm25, 1) if pm25 is not None else None,
            pm10=round(pm10, 1) if pm10 is not None else None,
            aqi=aqi_info["aqi"],
            aqi_category=aqi_info["category"],
            risk_level=aqi_info["risk_level"],
            dominant_pollutant=aqi_info["dominant_pollutant"],
            nearest_station=nearest_info,
            source=data_source,
            source_type=source_type,
            observed_at=obs_time,
            freshness_status=freshness.value,
            age_minutes=age_mins,
            forecast_summary=forecast_summary,
            predicted_pm25_3h=pred_3h,
            predicted_pm25_6h=pred_6h,
            disclaimer=f"Nearest monitoring station is {distance_km} km away ({closest_station['display_name']}). Freshness reflects telemetry age, not guaranteed sensor accuracy."
        )

# Global singleton
saved_location_service = SavedLocationService()

