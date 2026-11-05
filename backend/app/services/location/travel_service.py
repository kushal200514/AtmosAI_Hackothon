import math
from typing import Dict, Any, List
from app.database.supabase_client import db_manager
from app.services.environmental.aggregator import aggregator
from app.schemas.travel import TravelExposureRequest, TravelExposureResponse, WaypointExposure

# Haversine distance in km
def haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    R = 6371.0 # Earth radius in km
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (math.sin(dlat / 2.0) ** 2 +
         math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) *
         math.sin(dlon / 2.0) ** 2)
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return R * c

class TravelIntelligenceService:
    async def calculate_exposure(self, req: TravelExposureRequest) -> TravelExposureResponse:
        locations = await db_manager.get_locations()
        loc_map = {loc["name"]: loc for loc in locations}

        orig_loc = loc_map.get(req.origin) or loc_map.get("bengaluru_central")
        dest_loc = loc_map.get(req.destination) or loc_map.get("silk_board")

        # Straight-line distance & Bengaluru traffic speed factor (~18 km/h urban speed)
        dist_km = haversine(orig_loc["latitude"], orig_loc["longitude"], dest_loc["latitude"], dest_loc["longitude"])
        speed_kmh = 18.0 if req.mode == "commute" else (14.0 if req.mode == "cycling" else 4.5)
        duration_minutes = max(10, int((dist_km / speed_kmh) * 60))

        # Waypoints along the corridor
        orig_data = await aggregator.get_live_data(orig_loc["name"])
        dest_data = await aggregator.get_live_data(dest_loc["name"])

        # Midpoint estimation
        mid_lat = (orig_loc["latitude"] + dest_loc["latitude"]) / 2.0
        mid_lon = (orig_loc["longitude"] + dest_loc["longitude"]) / 2.0
        orig_pm = orig_data.pm25 or 25.0
        dest_pm = dest_data.pm25 or 30.0
        mid_pm = (orig_pm + dest_pm) / 2.0

        # Segment durations (split across 3 segments: start, transit corridor, arrival)
        t1 = round(duration_minutes * 0.25, 1)
        t2 = round(duration_minutes * 0.50, 1)
        t3 = round(duration_minutes * 0.25, 1)

        waypoints = [
            WaypointExposure(
                name=orig_loc["display_name"],
                latitude=orig_loc["latitude"],
                longitude=orig_loc["longitude"],
                segment_duration_mins=t1,
                estimated_pm25=round(orig_pm, 1),
                aqi_category=orig_data.aqi_category or "Moderate"
            ),
            WaypointExposure(
                name=f"Corridor Transit ({orig_loc['display_name']} -> {dest_loc['display_name']})",
                latitude=mid_lat,
                longitude=mid_lon,
                segment_duration_mins=t2,
                estimated_pm25=round(mid_pm, 1),
                aqi_category="Moderate"
            ),
            WaypointExposure(
                name=dest_loc["display_name"],
                latitude=dest_loc["latitude"],
                longitude=dest_loc["longitude"],
                segment_duration_mins=t3,
                estimated_pm25=round(dest_pm, 1),
                aqi_category=dest_data.aqi_category or "Moderate"
            )
        ]

        # Time-weighted concentration: E = Σ(Ci * Δti) / ΣΔti
        weighted_sum = (orig_pm * t1) + (mid_pm * t2) + (dest_pm * t3)
        total_time = t1 + t2 + t3
        exposure_index = round(weighted_sum / total_time, 1)

        # Advisory
        if exposure_index > 60:
            risk = "High"
            advisory = "High particulate corridor exposure. Keep vehicle windows closed with cabin recirculation active."
        elif exposure_index > 35:
            risk = "Moderate"
            advisory = "Moderate exposure anticipated. Consider departing 20 minutes earlier to avoid peak congestion."
        else:
            risk = "Low"
            advisory = "Corridor environmental quality is currently favorable."

        return TravelExposureResponse(
            origin=orig_loc["display_name"],
            destination=dest_loc["display_name"],
            estimated_duration_minutes=duration_minutes,
            waypoints=waypoints,
            average_pm25=round((orig_pm + dest_pm) / 2.0, 1),
            total_exposure_index=exposure_index,
            risk_level=risk,
            advisory=advisory
        )

travel_service = TravelIntelligenceService()

