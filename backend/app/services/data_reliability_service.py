import math
import logging
from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, Any, Tuple, Union

from app.schemas.reliability import (
    SourceType, 
    FreshnessStatus, 
    EnvironmentalReadingMetadata,
    LocationReliabilitySummary
)

logger = logging.getLogger("atmosai.reliability")

class DataReliabilityService:
    """
    AtmosAI Data Freshness and Reliability Engine.
    
    Guarantees strict environmental data provenance, enforces freshness thresholds,
    protects against stale or fabricated data, and distinguishes measured observations
    from forecasts and gridded models.
    """
    
    # Configurable initial application thresholds (in minutes)
    DEFAULT_FRESH_THRESHOLD_MINUTES: float = 60.0    # <= 1 hour
    DEFAULT_AGING_THRESHOLD_MINUTES: float = 180.0   # > 1 hour and <= 3 hours
    # Beyond 180 minutes is STALE
    
    # Physical sensor boundaries for QA
    VALID_BOUNDS = {
        "PM2.5": {"min": 0.0, "max": 1500.0, "unit": "µg/m³"},
        "PM10": {"min": 0.0, "max": 2500.0, "unit": "µg/m³"},
        "NO2": {"min": 0.0, "max": 1000.0, "unit": "µg/m³"},
        "SO2": {"min": 0.0, "max": 2000.0, "unit": "µg/m³"},
        "CO": {"min": 0.0, "max": 50000.0, "unit": "µg/m³"},
        "O3": {"min": 0.0, "max": 1000.0, "unit": "µg/m³"},
        "AQI": {"min": 0.0, "max": 500.0, "unit": "AQI"}
    }

    def __init__(
        self, 
        fresh_threshold_minutes: float = DEFAULT_FRESH_THRESHOLD_MINUTES,
        aging_threshold_minutes: float = DEFAULT_AGING_THRESHOLD_MINUTES
    ):
        self.fresh_threshold_minutes = fresh_threshold_minutes
        self.aging_threshold_minutes = aging_threshold_minutes

    @staticmethod
    def haversine_distance_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Calculate Great Circle distance between two coordinates in kilometers."""
        r = 6371.0  # Earth's radius in km
        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)
        a = (math.sin(dlat / 2) ** 2 + 
             math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * 
             math.sin(dlon / 2) ** 2)
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        return round(r * c, 2)

    def validate_timestamp(self, ts: Any) -> Optional[datetime]:
        """
        Validates, normalizes, and timezone-converts an incoming observation timestamp to UTC.
        Rejects invalid or corrupt date representations.
        """
        if ts is None:
            return None
            
        if isinstance(ts, datetime):
            if ts.tzinfo is None:
                # Naive datetime assumed to be UTC
                return ts.replace(tzinfo=timezone.utc)
            return ts.astimezone(timezone.utc)
            
        if isinstance(ts, (int, float)):
            try:
                # Handle epoch seconds or milliseconds
                if ts > 1e11:  # Milliseconds
                    ts = ts / 1000.0
                return datetime.fromtimestamp(ts, tz=timezone.utc)
            except Exception as e:
                logger.warning(f"Failed to parse numeric timestamp {ts}: {e}")
                return None
                
        if isinstance(ts, str):
            clean_str = ts.strip()
            if not clean_str:
                return None
            try:
                # Handle ISO strings with Z
                if clean_str.endswith("Z"):
                    clean_str = clean_str[:-1] + "+00:00"
                dt = datetime.fromisoformat(clean_str)
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=timezone.utc)
                return dt.astimezone(timezone.utc)
            except ValueError:
                # Try common fallback formats
                for fmt in ("%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d"):
                    try:
                        dt = datetime.strptime(clean_str, fmt)
                        return dt.replace(tzinfo=timezone.utc)
                    except ValueError:
                        continue
                logger.warning(f"Unrecognized timestamp format: {ts}")
                return None
                
        return None

    def validate_reading_value(
        self, 
        pollutant: str, 
        value: Any
    ) -> Tuple[bool, Optional[float], Optional[str]]:
        """
        Validates an environmental numerical reading against physical sensor constraints.
        Returns (is_valid, cleaned_value, error_reason).
        """
        if value is None:
            return False, None, "Reading value is missing or null."
            
        try:
            val_float = float(value)
        except (ValueError, TypeError):
            return False, None, f"Non-numeric value '{value}' received for {pollutant}."
            
        if math.isnan(val_float) or math.isinf(val_float):
            return False, None, f"Invalid mathematical value ({val_float}) for {pollutant}."
            
        bounds = self.VALID_BOUNDS.get(pollutant.upper())
        if bounds:
            if val_float < bounds["min"]:
                return False, None, f"Negative concentration ({val_float}) is physically impossible for {pollutant}."
            if val_float > bounds["max"]:
                return False, None, f"Value {val_float} exceeds physical sensor envelope ({bounds['max']} {bounds['unit']}) for {pollutant}."
                
        return True, round(val_float, 2), None

    def calculate_measurement_age(
        self, 
        observed_at: Optional[datetime], 
        reference_time: Optional[datetime] = None
    ) -> Optional[float]:
        """
        Calculates the age of an observation in minutes relative to reference_time (default UTC now).
        """
        if observed_at is None:
            return None
            
        ref = reference_time or datetime.now(timezone.utc)
        if ref.tzinfo is None:
            ref = ref.replace(tzinfo=timezone.utc)
        if observed_at.tzinfo is None:
            observed_at = observed_at.replace(tzinfo=timezone.utc)
            
        diff_seconds = (ref - observed_at).total_seconds()
        return round(diff_seconds / 60.0, 1)

    def determine_freshness(
        self, 
        observed_at: Optional[datetime], 
        reference_time: Optional[datetime] = None,
        is_stale_flag: bool = False,
        is_missing: bool = False,
        source_type: Optional[SourceType] = None
    ) -> FreshnessStatus:
        """
        Classifies data freshness according to AtmosAI rules:
        - FRESH: age <= 1 hour (60 min)
        - AGING: 1 hour < age <= 3 hours (60 - 180 min)
        - STALE: age > 3 hours (> 180 min) or upstream marked stale
        - UNAVAILABLE: missing data or unresolvable timestamp
        """
        if is_missing or observed_at is None:
            return FreshnessStatus.UNAVAILABLE
            
        if is_stale_flag:
            return FreshnessStatus.STALE
            
        age_mins = self.calculate_measurement_age(observed_at, reference_time)
        if age_mins is None:
            return FreshnessStatus.UNAVAILABLE
            
        # If timestamp is in the future beyond normal 15-min clock drift
        if age_mins < -15.0:
            if source_type == SourceType.FORECAST:
                return FreshnessStatus.FRESH
            # Sensor timestamp in far future is corrupt
            logger.warning(f"Future observation timestamp received: {observed_at}")
            return FreshnessStatus.STALE

        if age_mins <= self.fresh_threshold_minutes:
            return FreshnessStatus.FRESH
        elif age_mins <= self.aging_threshold_minutes:
            return FreshnessStatus.AGING
        else:
            return FreshnessStatus.STALE

    def classify_source_type(
        self, 
        source_name: str, 
        is_forecast: bool = False, 
        is_demo: bool = False,
        is_gridded: bool = False
    ) -> SourceType:
        """
        Classifies the source into one of four distinct types:
        MEASURED, FORECAST, ESTIMATED, or DEMO.
        """
        src_lower = (source_name or "").lower()
        
        if is_demo or "demo" in src_lower or "synthetic" in src_lower or "simulated" in src_lower:
            return SourceType.DEMO
            
        if is_forecast or "forecast" in src_lower or "predicted" in src_lower or "lightgbm" in src_lower:
            return SourceType.FORECAST
            
        if (is_gridded or "cams" in src_lower or "copernicus" in src_lower or 
            "gridded" in src_lower or "model" in src_lower or "estimated" in src_lower):
            return SourceType.ESTIMATED
            
        if ("openaq" in src_lower or "cpcb" in src_lower or "station" in src_lower or 
            "ground" in src_lower or "sensor" in src_lower or "measured" in src_lower):
            return SourceType.MEASURED
            
        # Default fallback to ESTIMATED rather than asserting physical measurement
        return SourceType.ESTIMATED

    def create_reliability_metadata(
        self,
        pollutant: str,
        value: Optional[float],
        source: str,
        source_type: Optional[SourceType] = None,
        observed_at: Any = None,
        station_name: Optional[str] = None,
        station_coords: Optional[Tuple[float, float]] = None,
        location_coords: Optional[Tuple[float, float]] = None,
        is_demo: bool = False,
        is_forecast: bool = False,
        is_stale_flag: bool = False,
        unit: Optional[str] = None,
        reference_time: Optional[datetime] = None
    ) -> EnvironmentalReadingMetadata:
        """
        Constructs a complete EnvironmentalReadingMetadata object adhering to strict
        provenance, freshness, and stale-data protection rules.
        """
        retrieved_at = reference_time or datetime.now(timezone.utc)
        if retrieved_at.tzinfo is None:
            retrieved_at = retrieved_at.replace(tzinfo=timezone.utc)
            
        # 1. Clean & Validate Value
        is_val_valid, clean_val, val_err = self.validate_reading_value(pollutant, value)
        
        # Determine appropriate unit
        clean_unit = unit or self.VALID_BOUNDS.get(pollutant.upper(), {}).get("unit", "µg/m³")
        
        # 2. Parse & Validate Timestamp
        valid_obs_time = self.validate_timestamp(observed_at)
        
        # 3. Classify Source
        classified_source_type = source_type or self.classify_source_type(
            source_name=source, 
            is_forecast=is_forecast, 
            is_demo=is_demo
        )
        
        # 4. Station distance
        station_lat = station_coords[0] if station_coords else None
        station_lon = station_coords[1] if station_coords else None
        station_distance_km = None
        if station_coords and location_coords:
            station_distance_km = self.haversine_distance_km(
                location_coords[0], location_coords[1],
                station_coords[0], station_coords[1]
            )
            
        # 5. Evaluate Freshness
        is_missing = (not is_val_valid) or (valid_obs_time is None)
        freshness = self.determine_freshness(
            observed_at=valid_obs_time,
            reference_time=retrieved_at,
            is_stale_flag=is_stale_flag,
            is_missing=is_missing,
            source_type=classified_source_type
        )
        
        # 6. Calculate Age in Minutes
        age_mins = self.calculate_measurement_age(valid_obs_time, retrieved_at)
        
        # 7. Stale Data Protection & Live Assertion
        # CRITICAL RULE: Stale data, demo data, forecasts, or missing data MUST NEVER be marked live.
        is_live = (
            freshness == FreshnessStatus.FRESH and 
            classified_source_type in (SourceType.MEASURED, SourceType.ESTIMATED) and 
            is_val_valid
        )
        
        # 8. Confidence Assessment & Explanations
        if freshness == FreshnessStatus.UNAVAILABLE or not is_val_valid:
            conf_level = "NONE"
            conf_reason = val_err or "Environmental telemetry is unavailable for this location."
        elif classified_source_type == SourceType.DEMO:
            conf_level = "LOW"
            conf_reason = "Demonstration data: do not use for actual health or safety decisions."
        elif freshness == FreshnessStatus.STALE:
            conf_level = "LOW"
            hrs = round((age_mins or 0) / 60.0, 1)
            conf_reason = f"Data is STALE (last recorded {hrs}h ago). Atmospheric conditions may have changed significantly."
        elif freshness == FreshnessStatus.AGING:
            conf_level = "MODERATE"
            hrs = round((age_mins or 0) / 60.0, 1)
            conf_reason = f"Data is aging ({hrs}h old). Acceptable for general awareness, but monitor for updates."
        elif classified_source_type == SourceType.FORECAST:
            conf_level = "MODERATE"
            conf_reason = "Model-projected estimate. Predictive confidence depends on forecast horizon."
        elif classified_source_type == SourceType.MEASURED:
            dist_str = f" from station {station_name} ({station_distance_km} km away)" if station_distance_km else ""
            conf_level = "HIGH"
            conf_reason = f"Verified fresh ground sensor observation{dist_str}."
        else: # ESTIMATED FRESH
            conf_level = "HIGH"
            conf_reason = "High-resolution gridded atmospheric analysis (CAMS model)."

        return EnvironmentalReadingMetadata(
            pollutant=pollutant,
            value=clean_val,
            unit=clean_unit,
            source=source,
            source_type=classified_source_type,
            station_name=station_name,
            station_latitude=station_lat,
            station_longitude=station_lon,
            station_distance_km=station_distance_km,
            observed_at=valid_obs_time,
            retrieved_at=retrieved_at,
            freshness_status=freshness,
            age_minutes=age_mins,
            is_live=is_live,
            confidence_level=conf_level,
            confidence_reason=conf_reason,
            disclaimer="Freshness reflects telemetry age, not guaranteed sensor accuracy."
        )

    def assess_recommendation_confidence(
        self, 
        metadata: EnvironmentalReadingMetadata
    ) -> Dict[str, Any]:
        """
        Enforces stale-data protection when generating health or activity recommendations.
        Prevents confident recommendations based on stale, missing, or demo data.
        """
        if metadata.freshness_status == FreshnessStatus.UNAVAILABLE or metadata.value is None:
            return {
                "can_recommend": False,
                "confidence": "NONE",
                "warning": "Data unavailable. Cannot generate environmental safety guidance without reliable measurements.",
                "disclaimer": metadata.disclaimer
            }
            
        if metadata.freshness_status == FreshnessStatus.STALE:
            return {
                "can_recommend": True,
                "confidence": "LOW",
                "warning": f"CAUTION: Stale data detected ({metadata.age_minutes}m old). This guidance is advisory only and current air quality may be worse or better.",
                "disclaimer": metadata.disclaimer
            }
            
        if metadata.source_type == SourceType.DEMO:
            return {
                "can_recommend": False,
                "confidence": "LOW",
                "warning": "Simulated/demo telemetry active. Recommendations are illustrative only.",
                "disclaimer": metadata.disclaimer
            }

        return {
            "can_recommend": True,
            "confidence": metadata.confidence_level,
            "warning": None,
            "disclaimer": metadata.disclaimer
        }

# Global singleton
reliability_service = DataReliabilityService()

