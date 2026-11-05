import pytest
from datetime import datetime, timezone, timedelta
from fastapi.testclient import TestClient
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.main import app
from app.services.data_reliability_service import (
    DataReliabilityService, 
    reliability_service
)
from app.schemas.reliability import (
    SourceType, 
    FreshnessStatus, 
    EnvironmentalReadingMetadata,
    LocationReliabilitySummary
)
from app.schemas.environmental import LiveEnvironmentalData

client = TestClient(app)

def test_fresh_measurement():
    """Test measurement age <= 1 hour is classified as FRESH and marked live."""
    service = DataReliabilityService()
    now = datetime(2026, 11, 5, 12, 0, 0, tzinfo=timezone.utc)
    # Observed 25 minutes ago
    obs_time = now - timedelta(minutes=25)
    
    meta = service.create_reliability_metadata(
        pollutant="PM2.5",
        value=35.4,
        source="OpenAQ Ground Station (BTM Layout)",
        source_type=SourceType.MEASURED,
        observed_at=obs_time,
        reference_time=now
    )
    
    assert meta.freshness_status == FreshnessStatus.FRESH
    assert meta.age_minutes == 25.0
    assert meta.is_live is True
    assert meta.confidence_level == "HIGH"
    assert "Freshness reflects telemetry age" in meta.disclaimer

def test_aging_measurement():
    """Test measurement age between 1 and 3 hours is classified as AGING."""
    service = DataReliabilityService()
    now = datetime(2026, 11, 5, 12, 0, 0, tzinfo=timezone.utc)
    # Observed 100 minutes ago (1 hour 40 mins)
    obs_time = now - timedelta(minutes=100)
    
    meta = service.create_reliability_metadata(
        pollutant="PM2.5",
        value=42.0,
        source="OpenAQ Ground Station (Hebbal)",
        source_type=SourceType.MEASURED,
        observed_at=obs_time,
        reference_time=now
    )
    
    assert meta.freshness_status == FreshnessStatus.AGING
    assert meta.age_minutes == 100.0
    assert meta.is_live is False
    assert meta.confidence_level == "MODERATE"
    assert "aging" in meta.confidence_reason.lower()

def test_stale_measurement():
    """Test measurement age > 3 hours is classified as STALE and cannot be marked live."""
    service = DataReliabilityService()
    now = datetime(2026, 11, 5, 12, 0, 0, tzinfo=timezone.utc)
    # Observed 240 minutes ago (4 hours)
    obs_time = now - timedelta(minutes=240)
    
    meta = service.create_reliability_metadata(
        pollutant="PM2.5",
        value=68.5,
        source="OpenAQ Ground Station (Silk Board)",
        source_type=SourceType.MEASURED,
        observed_at=obs_time,
        reference_time=now
    )
    
    assert meta.freshness_status == FreshnessStatus.STALE
    assert meta.age_minutes == 240.0
    assert meta.is_live is False
    assert meta.confidence_level == "LOW"
    assert "STALE" in meta.confidence_reason

def test_missing_timestamp():
    """Test missing or invalid timestamp is safely classified as UNAVAILABLE."""
    service = DataReliabilityService()
    now = datetime(2026, 11, 5, 12, 0, 0, tzinfo=timezone.utc)
    
    meta = service.create_reliability_metadata(
        pollutant="PM2.5",
        value=35.0,
        source="Unverified Station",
        observed_at=None,
        reference_time=now
    )
    
    assert meta.freshness_status == FreshnessStatus.UNAVAILABLE
    assert meta.is_live is False
    assert meta.confidence_level == "NONE"

def test_forecast_data_classification():
    """Test that future model forecasts are classified as FORECAST and not asserted as live observation."""
    service = DataReliabilityService()
    now = datetime(2026, 11, 5, 12, 0, 0, tzinfo=timezone.utc)
    target_time = now + timedelta(hours=3)
    
    meta = service.create_reliability_metadata(
        pollutant="PM2.5",
        value=55.2,
        source="AtmosAI LightGBM Multi-Horizon Predictor",
        is_forecast=True,
        observed_at=target_time,
        reference_time=now
    )
    
    assert meta.source_type == SourceType.FORECAST
    assert meta.is_live is False  # Forecast is never claimed as live current observation
    assert meta.confidence_level == "MODERATE"
    assert "projection" in meta.confidence_reason.lower() or "estimate" in meta.confidence_reason.lower()

def test_estimated_gridded_data_classification():
    """Test gridded model data (like Copernicus CAMS) is classified as ESTIMATED."""
    service = DataReliabilityService()
    now = datetime(2026, 11, 5, 12, 0, 0, tzinfo=timezone.utc)
    obs_time = now - timedelta(minutes=45)
    
    meta = service.create_reliability_metadata(
        pollutant="PM2.5",
        value=30.0,
        source="Open-Meteo (Copernicus CAMS European Atmospheric Model)",
        observed_at=obs_time,
        reference_time=now
    )
    
    assert meta.source_type == SourceType.ESTIMATED
    assert meta.freshness_status == FreshnessStatus.FRESH
    assert meta.is_live is True

def test_external_api_unavailable_handling():
    """Test system reports DATA UNAVAILABLE when upstream APIs fail and does not fabricate measurements."""
    service = DataReliabilityService()
    now = datetime(2026, 11, 5, 12, 0, 0, tzinfo=timezone.utc)
    
    meta = service.create_reliability_metadata(
        pollutant="PM2.5",
        value=None,
        source="None (Upstream APIs Unreachable)",
        observed_at=None,
        reference_time=now
    )
    
    assert meta.value is None
    assert meta.freshness_status == FreshnessStatus.UNAVAILABLE
    assert meta.is_live is False
    assert meta.confidence_level == "NONE"

def test_out_of_bounds_environmental_reading():
    """Test that physically impossible readings (negative concentrations, extreme anomalies) are rejected."""
    service = DataReliabilityService()
    
    # 1. Negative concentration
    is_valid, clean_val, err = service.validate_reading_value("PM2.5", -12.5)
    assert is_valid is False
    assert clean_val is None
    assert "Negative concentration" in err
    
    # 2. NaN / Infinite
    is_valid, clean_val, err = service.validate_reading_value("PM2.5", float("nan"))
    assert is_valid is False
    assert "Invalid mathematical value" in err
    
    # 3. Exceeds sensor envelope
    is_valid, clean_val, err = service.validate_reading_value("PM2.5", 9999.0)
    assert is_valid is False
    assert "exceeds physical sensor envelope" in err

def test_stale_data_protection_in_recommendations():
    """Test stale data suppresses high confidence and attaches advisory warnings."""
    service = DataReliabilityService()
    now = datetime(2026, 11, 5, 12, 0, 0, tzinfo=timezone.utc)
    obs_time = now - timedelta(hours=5)  # 5 hours old -> STALE
    
    meta = service.create_reliability_metadata(
        pollutant="PM2.5",
        value=45.0,
        source="OpenAQ Station (Old)",
        observed_at=obs_time,
        reference_time=now
    )
    
    eval_result = service.assess_recommendation_confidence(meta)
    assert eval_result["confidence"] == "LOW"
    assert "CAUTION: Stale data detected" in eval_result["warning"]
    assert "Freshness reflects telemetry age" in eval_result["disclaimer"]

def test_api_endpoint_environmental_reliability():
    """Test the /api/environmental/reliability endpoint returns full metadata and freshness."""
    response = client.get("/api/environmental/reliability?location=bengaluru_central")
    assert response.status_code == 200
    data = response.json()
    
    assert "overall_freshness" in data
    assert "dominant_source_type" in data
    assert "primary_reading" in data
    assert data["overall_freshness"] in ("FRESH", "AGING", "STALE", "UNAVAILABLE")
    assert data["dominant_source_type"] in ("MEASURED", "FORECAST", "ESTIMATED", "DEMO")
    
    primary = data["primary_reading"]
    assert "pollutant" in primary
    assert "source" in primary
    assert "retrieved_at" in primary
    assert "freshness_status" in primary
    assert "disclaimer" in primary
    assert "Freshness reflects telemetry age" in primary["disclaimer"]

def test_live_forecast_endpoint_includes_reliability():
    """Test the /api/forecast/live endpoint returns reliability_metadata."""
    response = client.get("/api/forecast/live?location=bengaluru_central")
    assert response.status_code == 200
    data = response.json()
    
    assert "reliability_metadata" in data
    rel = data["reliability_metadata"]
    if rel:
        assert "freshness_status" in rel
        assert "source_type" in rel
        assert "disclaimer" in rel
