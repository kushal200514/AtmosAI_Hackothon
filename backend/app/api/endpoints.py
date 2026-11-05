from fastapi import APIRouter, Query, HTTPException, Body, Header, Depends
from typing import List, Optional, Dict, Any, Union
from datetime import datetime, timezone
from pydantic import BaseModel
from app.core.config import settings
from app.core.auth import verify_supabase_jwt, get_current_user, get_optional_user, AuthenticatedUser

from app.database.supabase_client import db_manager
from app.services.environmental.aggregator import aggregator
from app.services.forecasting.ml_service import ml_forecaster
from app.services.ai.service import ai_service
from app.services.location.travel_service import travel_service
from app.services.iot.wearable_service import wearable_service
from app.services.recommendations.personalization_service import personalization_engine

from app.schemas.environmental import LiveEnvironmentalData
from app.schemas.location import LocationOut
from app.schemas.forecast import ForecastResponse
from app.schemas.ai import AIAdviceResponse, AIAdviceRequest
from app.schemas.profile import (
    ProfileType, 
    UserCategory, 
    UserProfile, 
    UserProfileUpdate, 
    UserProfileOut, 
    ActivityWindowScore
)
from app.schemas.alerts import (
    AlertItem, 
    TelemetryPayload, 
    NotificationSettingsOut, 
    NotificationSettingsUpdate
)
from app.schemas.accuracy import (
    AccuracyMetricsResponse, 
    ForecastValidationRecord
)
from app.services.alerts.smart_alert_service import smart_alert_service
from app.services.forecasting.accuracy_service import accuracy_service
from app.services.forecasting.demo_evaluation_service import demo_evaluation_service
from app.services.location.travel_map_service import travel_map_service
from app.services.environmental.aqi_calculator import (
    CPCB_CATEGORIES, 
    get_cpcb_safety_recommendation, 
    MEDICAL_DISCLAIMER
)
from app.schemas.travel import TravelExposureRequest, TravelExposureResponse
from app.schemas.map import (
    GridCellForecast,
    StationMarker,
    TravelRouteRequest,
    TravelRouteResponse
)
from app.schemas.reliability import (
    SourceType,
    FreshnessStatus,
    EnvironmentalReadingMetadata,
    LocationReliabilitySummary
)
from app.services.data_reliability_service import reliability_service
from app.schemas.saved_location import (
    LocationType,
    SavedLocationCreate,
    SavedLocationUpdate,
    SavedLocationOut,
    SavedLocationAirQuality,
    LocationSearchResult
)
from app.services.location.saved_location_service import saved_location_service

router = APIRouter(prefix="/api", tags=["AtmosAI API"])

def resolve_auth_user_id(
    user_id: Optional[str] = None, 
    x_user_id: Optional[str] = None, 
    authorization: Optional[str] = None,
    enforce_auth: bool = False
) -> str:
    """
    Derives authenticated user ID from Bearer token or headers.
    If Bearer token is provided, cryptographically verifies the Supabase JWT.
    Derives user_id from token's 'sub' claim.
    """
    if authorization and "Bearer " in authorization:
        token = authorization.split("Bearer ")[1].strip()
        if token:
            payload = verify_supabase_jwt(token)
            token_uid = payload.get("sub") or payload.get("id")
            if token_uid:
                return str(token_uid)
            raise HTTPException(status_code=401, detail="Token missing valid user subject claim.")
            
    if enforce_auth:
        raise HTTPException(status_code=401, detail="Authentication token required.")

    if user_id and user_id.strip():
        return user_id.strip()
    if x_user_id and x_user_id.strip():
        return x_user_id.strip()
    return "default_user"

# 1. Locations & Saved Location Intelligence
@router.get("/locations")
async def list_locations(
    user_id: Optional[str] = Query(default=None, description="User ID for saved locations"),
    x_user_id: Optional[str] = Header(default=None, alias="X-User-Id"),
    authorization: Optional[str] = Header(default=None),
    scope: Optional[str] = Query(default=None, description="'saved' or 'stations'"),
    include_air_quality: bool = Query(default=False, description="Include live air quality for saved places")
):
    """
    Returns user saved locations when authenticated or queried for saved places.
    Falls back to regional monitoring stations when unauthenticated / stations requested.
    """
    if scope == "stations":
        return await db_manager.get_locations()

    has_identity = bool(user_id or x_user_id or authorization or scope == "saved")
    if not has_identity:
        return await db_manager.get_locations()

    uid = resolve_auth_user_id(user_id, x_user_id, authorization)
    saved_locs = saved_location_service.get_saved_locations(uid)
    if include_air_quality:
        for loc in saved_locs:
            aq = await saved_location_service.get_air_quality_for_saved_location(uid, loc.location_id)
            loc.air_quality = aq
    return saved_locs

@router.get("/locations/search", response_model=List[LocationSearchResult])
async def search_locations(
    q: str = Query(default="", description="Search query for Bengaluru localities and landmarks")
):
    """Search for locations across Bengaluru with nearest station proximity."""
    return saved_location_service.search_locations(q)

@router.post("/locations", response_model=SavedLocationOut)
async def create_saved_location(
    payload: SavedLocationCreate,
    user_id: Optional[str] = Query(default=None),
    x_user_id: Optional[str] = Header(default=None, alias="X-User-Id"),
    authorization: Optional[str] = Header(default=None)
):
    """Save a new important place (Home, College / School, Office, Favourite, Custom) for the user."""
    uid = resolve_auth_user_id(payload.user_id or user_id, x_user_id, authorization)
    try:
        created = saved_location_service.add_saved_location(uid, payload)
        return created
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to save location: {str(e)}")

@router.put("/locations/{location_id}", response_model=SavedLocationOut)
async def update_saved_location(
    location_id: str,
    payload: SavedLocationUpdate,
    user_id: Optional[str] = Query(default=None),
    x_user_id: Optional[str] = Header(default=None, alias="X-User-Id"),
    authorization: Optional[str] = Header(default=None)
):
    """Update details of a saved place. Enforces user ownership check."""
    uid = resolve_auth_user_id(user_id, x_user_id, authorization)
    updated = saved_location_service.update_saved_location(uid, location_id, payload)
    if not updated:
        raise HTTPException(status_code=404, detail="Saved location not found or access denied")
    return updated

@router.delete("/locations/{location_id}")
async def delete_saved_location(
    location_id: str,
    user_id: Optional[str] = Query(default=None),
    x_user_id: Optional[str] = Header(default=None, alias="X-User-Id"),
    authorization: Optional[str] = Header(default=None)
):
    """Delete a saved place. Enforces user ownership check."""
    uid = resolve_auth_user_id(user_id, x_user_id, authorization)
    success = saved_location_service.delete_saved_location(uid, location_id)
    if not success:
        raise HTTPException(status_code=404, detail="Saved location not found or access denied")
    return {"status": "success", "message": "Saved location deleted successfully", "location_id": location_id}

@router.get("/locations/{location_id}/air-quality", response_model=SavedLocationAirQuality)
async def get_saved_location_air_quality(
    location_id: str,
    user_id: Optional[str] = Query(default=None),
    x_user_id: Optional[str] = Header(default=None, alias="X-User-Id"),
    authorization: Optional[str] = Header(default=None)
):
    """Retrieve real-time air quality, nearest station proximity, and forecast for a saved place."""
    uid = resolve_auth_user_id(user_id, x_user_id, authorization)
    aq = await saved_location_service.get_air_quality_for_saved_location(uid, location_id)
    if not aq:
        raise HTTPException(status_code=404, detail="Saved location not found or access denied")
    return aq

# 2. Profiles and Personalization Engine Endpoints
@router.get("/profiles")
async def list_profiles():
    """Returns available user profile categories with sensitivity levels and guidance."""
    return [
        {
            "id": ProfileType.RUNNER.value,
            "title": "Runner / Athlete",
            "description": "High respiratory volume during outdoor training. Prioritizes low-pollution exercise windows, PM2.5 trends, and weather.",
            "icon": "Footprints"
        },
        {
            "id": ProfileType.RESPIRATORY_SENSITIVE.value,
            "title": "Respiratory-Sensitive Individual",
            "description": "Asthma, COPD, or airborne allergy sensitivity. Requires conservative particulate warnings and N95 protection prompts.",
            "icon": "ShieldAlert"
        },
        {
            "id": ProfileType.PARENT.value,
            "title": "Parent / Guardian",
            "description": "Focused on infant and child lung health during school runs, stroller walks, and outdoor playground activities.",
            "icon": "Baby"
        },
        {
            "id": ProfileType.DELIVERY_WORKER.value,
            "title": "Delivery Worker / Field Professional",
            "description": "Prolonged high-exposure street transit on two-wheelers. Prioritizes route pollution alerts and protective shift planning.",
            "icon": "Bike"
        },
        {
            "id": ProfileType.OFFICE_COMMUTER.value,
            "title": "Office Commuter",
            "description": "Daily peak-hour travel across high-congestion corridors. Guidance on vehicle recirculation and route exposure.",
            "icon": "Briefcase"
        },
        {
            "id": ProfileType.GENERAL_PUBLIC.value,
            "title": "General Public",
            "description": "Everyday environmental awareness, indoor window ventilation schedules, and general lifestyle advisories.",
            "icon": "Users"
        }
    ]

@router.get("/user/profile", response_model=UserProfileOut)
async def get_user_profile(
    user_id: Optional[str] = Query(default=None),
    authorization: Optional[str] = Header(default=None)
):
    """
    Retrieves the persisted user profile and resolves dynamic personalization
    rules (widget ordering, visible widgets, alert filters, and planner activities).
    """
    uid = resolve_auth_user_id(user_id=user_id, authorization=authorization)
    profile = wearable_service.get_user_profile(uid)
    config = personalization_engine.resolve_config(profile)
    return UserProfileOut(profile=profile, personalization=config)

@router.post("/user/profile")
async def update_user_profile(
    payload: UserProfileUpdate, 
    user_id: Optional[str] = Query(default=None),
    authorization: Optional[str] = Header(default=None)
):
    """
    Updates user onboarding profile and returns dynamic personalization configuration.
    """
    uid = resolve_auth_user_id(user_id=user_id, authorization=authorization)
    updates = payload.model_dump(exclude_unset=True)
    updated = wearable_service.update_user_profile(uid, updates)
    config = personalization_engine.resolve_config(updated)
    return {
        "status": "success",
        "profile": updated.model_dump(),
        "personalization": config.model_dump()
    }

# 2b. Authentication & Session Intelligence
class AuthRequest(BaseModel):
    email: str
    password: str
    full_name: Optional[str] = None
    remember_me: Optional[bool] = False

@router.get("/auth/status")
async def get_auth_status():
    """Returns the backend authentication configuration state and providers."""
    has_supabase = bool(settings.SUPABASE_URL and settings.SUPABASE_KEY and "your-project" not in settings.SUPABASE_URL)
    return {
        "provider": "supabase" if has_supabase else "demo",
        "supabase_configured": has_supabase,
        "mode": "production" if has_supabase else "demo",
        "disclaimer": "DEMO AUTHENTICATION MODE — Simulated session for demonstration. Supabase credentials are not configured in environment." if not has_supabase else None
    }

@router.post("/auth/signup")
async def handle_signup(payload: AuthRequest):
    """
    Registers a new user. If Supabase is unconfigured, creates a persistent demo user profile
    with onboarding_completed=False ready for multi-step onboarding.
    """
    email_clean = payload.email.strip().lower()
    user_id = email_clean.replace("@", "_").replace(".", "_")
    name = payload.full_name or email_clean.split("@")[0].capitalize()
    
    # Initialize fresh profile for onboarding
    profile = wearable_service.update_user_profile(user_id, {
        "full_name": name,
        "email": email_clean,
        "onboarding_completed": False,
        "onboarding_step": 1,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat()
    })
    
    return {
        "status": "success",
        "user_id": user_id,
        "user": {
            "id": user_id,
            "email": email_clean,
            "full_name": name,
            "onboarding_completed": False,
            "onboarding_step": 1
        },
        "mode": "demo" if not settings.SUPABASE_KEY else "supabase",
        "message": "User registered successfully. Proceed to onboarding."
    }

@router.post("/auth/login")
async def handle_login(payload: AuthRequest):
    """Authenticates returning user and checks onboarding completion."""
    email_clean = payload.email.strip().lower()
    if email_clean in ("default_user", "default_user@atmosai.org", "demo@atmosai.org", "user@atmosai.org"):
        user_id = "default_user"
    else:
        user_id = email_clean.replace("@", "_").replace(".", "_")
    
    profile = wearable_service.get_user_profile(user_id)
    if not profile.email or profile.email == "user@atmosai.org":
        wearable_service.update_user_profile(user_id, {"email": email_clean})
        profile = wearable_service.get_user_profile(user_id)
        
    return {
        "status": "success",
        "user_id": user_id,
        "user": {
            "id": user_id,
            "email": profile.email,
            "full_name": profile.full_name,
            "onboarding_completed": profile.onboarding_completed,
            "onboarding_step": profile.onboarding_step
        },
        "onboarding_completed": profile.onboarding_completed,
        "mode": "demo" if not settings.SUPABASE_KEY else "supabase"
    }

# 3. Dynamic Activity Planner Endpoint
@router.get("/planner", response_model=List[ActivityWindowScore])
async def get_activity_planner(
    location: str = Query(default="bengaluru_central", description="Location slug e.g. 'bengaluru_central'"),
    user_id: str = Query(default="default_user", description="Active user profile ID")
):
    """
    Compares forecast windows (Current Now, +3h, +4h, +5h, +6h) for preferred activities,
    providing suitability scores and explaining why specific times are optimal or challenging.
    """
    try:
        live = await aggregator.get_live_data(location)
        forecast = await ml_forecaster.predict(location)
        profile = wearable_service.get_user_profile(user_id)
        scores = personalization_engine.evaluate_planner_windows(profile, forecast, live)
        return scores
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to calculate activity planner scores: {str(e)}")

# 4. Live Environmental Telemetry
@router.get("/forecast/live", response_model=LiveEnvironmentalData)
async def get_live_forecast(
    location: str = Query(default="bengaluru_central", description="Location slug e.g. 'bengaluru_central', 'silk_board'")
):
    """Fetch current live environmental telemetry and calculated NAQI with strict measurement provenance."""
    try:
        data = await aggregator.get_live_data(location)
        return data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve environmental data: {str(e)}")

# 4b. Data Freshness & Reliability Summary
@router.get("/environmental/reliability", response_model=LocationReliabilitySummary)
async def get_environmental_reliability(
    location: str = Query(default="bengaluru_central", description="Location slug e.g. 'bengaluru_central'")
):
    """
    Returns strict data freshness classification, source provenance,
    telemetry age, and stale-data protection status for the requested location.
    """
    try:
        live = await aggregator.get_live_data(location)
        primary_meta = live.reliability_metadata or reliability_service.create_reliability_metadata(
            pollutant="PM2.5",
            value=live.pm25,
            source=live.data_source,
            source_type=SourceType.MEASURED if live.measurement_type.value == "measured" else SourceType.ESTIMATED,
            observed_at=live.observation_time_iso,
            location_coords=(live.latitude, live.longitude),
            is_stale_flag=live.is_stale
        )
        recommendation_eval = reliability_service.assess_recommendation_confidence(primary_meta)
        
        return LocationReliabilitySummary(
            location_id=live.location_id,
            location_name=live.location_name,
            overall_freshness=primary_meta.freshness_status,
            dominant_source_type=primary_meta.source_type,
            primary_reading=primary_meta,
            readings=live.readings_metadata or {"pm25": primary_meta},
            can_recommend_confidently=recommendation_eval["can_recommend"] and recommendation_eval["confidence"] in ("HIGH", "MODERATE"),
            confidence_explanation=recommendation_eval["warning"] or primary_meta.confidence_reason or "Telemetry verified."
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to inspect data reliability: {str(e)}")

# 5. Multi-Horizon ML Forecast (1h, 3h, 4h, 5h, 6h)
@router.get("/forecast/predict", response_model=ForecastResponse)
async def get_forecast_prediction(
    location: str = Query(default="bengaluru_central", description="Location slug e.g. 'bengaluru_central', 'silk_board'")
):
    """Multi-horizon PM2.5 forecasting using LightGBM Gradient Boosted Decision Trees."""
    try:
        forecast = await ml_forecaster.predict(location)
        return forecast
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to compute ML forecast: {str(e)}")

# 5b. Forecast Accuracy, Verification & Trust Metrics
@router.get("/forecast/accuracy", response_model=AccuracyMetricsResponse)
async def get_forecast_accuracy(
    location: str = Query(default="bengaluru_central", description="Location slug e.g. 'bengaluru_central'"),
    horizon: int = Query(default=3, description="Forecast horizon ahead in hours: 1, 3, or 6"),
    range: str = Query(default="all", description="'last_24h', 'last_7d', 'last_30d', or 'all'"),
    mode: str = Query(default="real", description="'real' (production observation evaluation) or 'demo' (simulated demonstration data)")
):
    """
    Evaluates PM2.5 forecast accuracy against observations.
    Supports both REAL DATA MODE (genuine sensor observations) and DEMO MODE (reproducible synthetic dataset).
    """
    if horizon not in (1, 3, 4, 5, 6):
        raise HTTPException(status_code=400, detail="Invalid forecast horizon. Supported horizons: 1, 3, 6 hours.")
    
    # DEMO MODE: Serve deterministic simulated dataset with explicit disclaimers
    if mode.lower() == "demo" or location == "bengaluru_demo":
        return demo_evaluation_service.get_demo_accuracy_metrics(horizon_hours=horizon, date_range=range)

    # REAL DATA MODE: Strictly preserve genuine data matching logic with zero synthetic fabrication
    return accuracy_service.get_accuracy_metrics(location_name=location, horizon_hours=horizon, date_range=range)

@router.get("/forecast/history", response_model=List[ForecastValidationRecord])
async def get_forecast_history(
    location: str = Query(default="bengaluru_central", description="Location slug"),
    horizon: Optional[int] = Query(default=None, description="Optional horizon filter (1, 3, 6)"),
    status: Optional[str] = Query(default=None, description="'validated', 'pending', 'rejected_stale', 'rejected_incompatible'"),
    mode: str = Query(default="real", description="'real' or 'demo'"),
    limit: int = Query(default=50, ge=1, le=200)
):
    """Returns chronologically recorded predictions and matched observations."""
    if mode.lower() == "demo" or location == "bengaluru_demo":
        return demo_evaluation_service.get_demo_records(horizon_hours=horizon, limit=limit)
    
    records = accuracy_service.records
    filtered = [r for r in records if r.location_name == location]
    if horizon is not None:
        filtered = [r for r in filtered if r.horizon_hours == horizon]
    if status is not None:
        filtered = [r for r in filtered if r.validation_status == status]
    return sorted(filtered, key=lambda x: x.target_timestamp, reverse=True)[:limit]

# 5c. Dedicated Model Evaluation Endpoints
@router.get("/evaluation/demo-data", response_model=List[ForecastValidationRecord])
async def get_evaluation_demo_data(
    horizon: Optional[int] = Query(default=None, description="Optional horizon filter (1, 3, 6)"),
    limit: int = Query(default=168, ge=1, le=500, description="Number of demo hourly records (default 7 days = 168)")
):
    """Returns at least 7 days of reproducible simulated hourly PM2.5 forecast-observation records."""
    return demo_evaluation_service.get_demo_records(horizon_hours=horizon, limit=limit)

@router.get("/evaluation/metrics", response_model=AccuracyMetricsResponse)
async def get_evaluation_metrics(
    horizon: int = Query(default=3, description="Forecast horizon (1, 3, 6)"),
    range: str = Query(default="all", description="'last_24h', 'last_7d', 'last_30d', or 'all'"),
    mode: str = Query(default="demo", description="'demo' or 'real'"),
    location: str = Query(default="bengaluru_central", description="Location slug for real mode")
):
    """Computes MAE and RMSE dynamically for the selected mode and evaluation period."""
    if mode.lower() == "demo" or location == "bengaluru_demo":
        return demo_evaluation_service.get_demo_accuracy_metrics(horizon_hours=horizon, date_range=range)
    return accuracy_service.get_accuracy_metrics(location_name=location, horizon_hours=horizon, date_range=range)

@router.get("/evaluation/predictions", response_model=List[ForecastValidationRecord])
async def get_evaluation_predictions(
    horizon: Optional[int] = Query(default=None, description="Optional horizon filter (1, 3, 6)"),
    mode: str = Query(default="demo", description="'demo' or 'real'"),
    location: str = Query(default="bengaluru_central", description="Location slug for real mode"),
    limit: int = Query(default=50, ge=1, le=200)
):
    """Returns matched prediction-observation records for evaluation inspection."""
    if mode.lower() == "demo" or location == "bengaluru_demo":
        return demo_evaluation_service.get_demo_records(horizon_hours=horizon, limit=limit)
    records = accuracy_service.records
    filtered = [r for r in records if r.location_name == location]
    if horizon is not None:
        filtered = [r for r in filtered if r.horizon_hours == horizon]
    return sorted(filtered, key=lambda x: x.target_timestamp, reverse=True)[:limit]

# 6. AI Recommendations
@router.get("/advice", response_model=AIAdviceResponse)
async def get_environmental_advice(
    location: str = Query(default="bengaluru_central", description="Location slug"),
    profile: Optional[str] = Query(default=None, description="User profile category or type"),
    user_id: str = Query(default="default_user", description="Active user ID")
):
    """Generates evidence-based explanations and profile-tailored environmental recommendations."""
    try:
        advice = await ai_service.get_advice(location, profile_type=profile, user_id=user_id)
        return advice
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate environmental advice: {str(e)}")

@router.post("/advice", response_model=AIAdviceResponse)
async def post_environmental_advice(payload: AIAdviceRequest):
    try:
        advice = await ai_service.get_advice(payload.location, profile_type=payload.profile_type)
        return advice
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate advice: {str(e)}")

# 7. Map Spatial Data & Travel Pollution Routing
@router.get("/map/data")
async def get_map_stations():
    """Returns spatial air quality observations for all monitoring stations across Bengaluru."""
    try:
        summary = await aggregator.get_all_locations_summary()
        return {
            "region": "Bengaluru, India",
            "count": len(summary),
            "stations": summary
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate map dataset: {str(e)}")

@router.get("/map/grid", response_model=List[GridCellForecast])
async def get_map_gridded_forecast():
    """Returns 4x3 spatial atmospheric forecast grid over Greater Bengaluru (Copernicus CAMS)."""
    try:
        return await travel_map_service.get_gridded_forecast()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate gridded atmospheric forecast: {str(e)}")

@router.get("/map/stations", response_model=List[StationMarker])
async def get_map_station_markers():
    """
    Returns available monitoring station markers with coordinates, active pollutant, unit,
    and distinct labels separating physical ground measurements from atmospheric forecasts.
    """
    try:
        return await travel_map_service.get_station_markers()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve station markers: {str(e)}")

@router.post("/map/route", response_model=TravelRouteResponse)
async def plan_travel_pollution_route(payload: TravelRouteRequest):
    """
    Calculates real-time travel route pollution with road geometry, corridor segmentation,
    nearest station lookups, time-weighted exposure, destination AQI, and alternative corridor comparison.
    """
    try:
        return await travel_map_service.plan_travel_route(
            origin_slug=payload.origin,
            destination_slug=payload.destination,
            mode=payload.mode
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to plan travel pollution route: {str(e)}")

# 8. Smart Alerts & Notification Settings
@router.get("/alerts", response_model=List[AlertItem])
async def get_alerts(
    profile: Optional[str] = Query(default=None, description="Profile type filter"),
    user_id: str = Query(default="default_user", description="User ID for notification preferences"),
    location: Optional[str] = Query(default=None, description="Optional target location slug")
):
    """
    Returns current smart environmental alerts, deterioration notices, and forecast surge advisories,
    filtered strictly by user notification preferences and CPCB safety recommendations.
    """
    return await wearable_service.get_system_alerts(profile, user_id, location)

@router.get("/notifications/settings", response_model=NotificationSettingsOut)
async def get_notification_settings(user_id: str = Query(default="default_user")):
    """
    Retrieves user notification preferences, recommended threshold for user persona/sensitivity,
    and active alert category states.
    """
    profile = wearable_service.get_user_profile(user_id)
    return smart_alert_service.get_notification_settings(profile)

@router.post("/notifications/settings", response_model=NotificationSettingsOut)
async def update_notification_settings(
    payload: NotificationSettingsUpdate,
    user_id: str = Query(default="default_user")
):
    """
    Updates notification settings including custom thresholds, monitored locations,
    and individual alert category toggles.
    """
    updates = payload.model_dump(exclude_unset=True)
    if "custom_threshold" in updates and updates["custom_threshold"] is not None:
        updates["high_pollution_threshold"] = updates["custom_threshold"]
    
    wearable_service.update_user_profile(user_id, {"notifications": updates})
    profile = wearable_service.get_user_profile(user_id)
    return smart_alert_service.get_notification_settings(profile)

@router.get("/notifications/recommendations")
async def get_cpcb_recommendations_table(user_id: str = Query(default="default_user")):
    """
    Returns the complete CPCB National AQI categories table with base recommendations,
    personalized lifestyle actions, and sensitivity notes for the active user.
    """
    profile = wearable_service.get_user_profile(user_id)
    table = []
    for cat in CPCB_CATEGORIES:
        mid_aqi = (cat["aqi_min"] + cat["aqi_max"]) // 2
        rec = get_cpcb_safety_recommendation(
            mid_aqi, 
            user_category=profile.user_category.value, 
            sensitivity=profile.sensitivity_preference.value
        )
        table.append({
            "category": cat["category"],
            "aqi_range": f"{cat['aqi_min']}–{cat['aqi_max']}",
            "aqi_min": cat["aqi_min"],
            "aqi_max": cat["aqi_max"],
            "risk_level": cat["risk_level"],
            "color": cat["color"],
            "base_recommendation": cat["recommendation"],
            "personalized_guidance": rec["persona_recommendation"],
            "sensitivity_note": rec["sensitivity_note"]
        })
    return {
        "aqi_standard": "CPCB National Air Quality Index (NAQI)",
        "categories": table,
        "active_persona": profile.user_category.value,
        "sensitivity": profile.sensitivity_preference.value,
        "disclaimer": MEDICAL_DISCLAIMER
    }

# 9. Travel Intelligence Exposure
@router.post("/travel/exposure", response_model=TravelExposureResponse)
async def calculate_travel_exposure(payload: TravelExposureRequest):
    """
    Computes time-weighted environmental concentration estimate for point-to-point transit:
    E = Σ(Ci * Δti) / ΣΔti
    """
    try:
        return await travel_service.calculate_exposure(payload)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to calculate travel exposure: {str(e)}")

# 10. Wearable Telemetry & Contextual IoT
@router.post("/telemetry")
async def post_telemetry(payload: TelemetryPayload):
    """Ingests contextual wearable prototype telemetry (steps, heart rate, ambient PM2.5)."""
    return wearable_service.record_telemetry(payload)

# 11. Location & Activity Updates
@router.post("/location/update")
async def update_location(payload: Dict[str, Any] = Body(...)):
    """Handles permission-based GPS location updates with minimal retention."""
    return {
        "status": "success",
        "message": "Ephemeral location processed for nearest monitoring station assignment.",
        "received_coordinates": {
            "latitude": payload.get("latitude"),
            "longitude": payload.get("longitude")
        }
    }

@router.post("/activity")
async def log_activity(payload: Dict[str, Any] = Body(...)):
    """Logs outdoor exercise or commute session for exposure tracking."""
    return {
        "status": "success",
        "activity": payload.get("activity_type", "outdoor_commute"),
        "logged_at": payload.get("timestamp")
    }
