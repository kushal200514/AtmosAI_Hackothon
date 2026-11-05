import pytest
from fastapi.testclient import TestClient
from datetime import datetime, timezone, timedelta
import math
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.main import app
from app.services.forecasting.accuracy_service import (
    ForecastAccuracyService, 
    accuracy_service
)
from app.schemas.accuracy import ForecastValidationRecord, AccuracyMetricsResponse

client = TestClient(app)

@pytest.fixture
def fresh_service():
    """Provides a fresh isolated instance of ForecastAccuracyService for deterministic unit testing."""
    service = ForecastAccuracyService()
    return service

def test_record_forecast_stores_required_metadata(fresh_service):
    """Test recording a forecast properly captures all required telemetry and provenance."""
    now = datetime.now(timezone.utc)
    target = now + timedelta(hours=3)

    record = fresh_service.record_forecast(
        location_name="bengaluru_central",
        horizon_hours=3,
        predicted_pm25=42.5,
        target_timestamp=target,
        forecast_source="AtmosAI LightGBM v1.0",
        model_identifier="lgbm_pm25_3h"
    )

    assert record.location_name == "bengaluru_central"
    assert record.horizon_hours == 3
    assert record.predicted_pm25 == 42.5
    assert record.target_timestamp == target
    assert record.is_validated is False
    assert record.validation_status == "pending"
    assert record.actual_pm25 is None
    assert record.absolute_error is None

    # Check that record is in memory
    assert any(r.id == record.id for r in fresh_service.records)

def test_match_observation_calculates_errors_accurately(fresh_service):
    """Test matching an observation computes exact absolute and squared errors."""
    now = datetime.now(timezone.utc)
    target = now + timedelta(hours=1)

    record = fresh_service.record_forecast(
        location_name="bengaluru_central",
        horizon_hours=1,
        predicted_pm25=35.0,
        target_timestamp=target,
        forecast_source="AtmosAI LightGBM v1.0",
        model_identifier="lgbm_pm25_1h"
    )

    # Actual observation arrives within 10 minutes of target
    obs_time = target + timedelta(minutes=10)
    matched = fresh_service.match_observation(
        location_name="bengaluru_central",
        observation_time=obs_time,
        actual_pm25=40.0,
        source="CPCB Bapuji Nagar Station",
        is_stale=False
    )

    assert len(matched) >= 1
    updated = next(r for r in fresh_service.records if r.id == record.id)
    assert updated.is_validated is True
    assert updated.validation_status == "validated"
    assert updated.actual_pm25 == 40.0
    assert updated.absolute_error == pytest.approx(5.0)
    assert updated.squared_error == pytest.approx(25.0)
    assert updated.observation_source == "CPCB Bapuji Nagar Station"

def test_match_observation_rejects_unrelated_locations(fresh_service):
    """Test that observations from Silk Board never match predictions for Central Bengaluru."""
    now = datetime.now(timezone.utc)
    target = now + timedelta(hours=3)

    record = fresh_service.record_forecast(
        location_name="bengaluru_central",
        horizon_hours=3,
        predicted_pm25=30.0,
        target_timestamp=target
    )

    # Observation arrives for silk_board at exact same time
    matched = fresh_service.match_observation(
        location_name="silk_board",
        observation_time=target,
        actual_pm25=95.0,
        source="Silk Board Traffic Station",
        is_stale=False
    )

    assert len(matched) == 0
    updated = next(r for r in fresh_service.records if r.id == record.id)
    assert updated.is_validated is False
    assert updated.validation_status == "pending"

def test_match_observation_rejects_stale_telemetry(fresh_service):
    """Test that stale observation telemetry is rejected and flagged."""
    now = datetime.now(timezone.utc)
    target = now + timedelta(hours=1)

    record = fresh_service.record_forecast(
        location_name="bengaluru_central",
        horizon_hours=1,
        predicted_pm25=40.0,
        target_timestamp=target
    )

    matched = fresh_service.match_observation(
        location_name="bengaluru_central",
        observation_time=target,
        actual_pm25=42.0,
        source="CPCB Bapuji Nagar",
        is_stale=True  # Stale data
    )

    assert len(matched) >= 1
    updated = next(r for r in fresh_service.records if r.id == record.id)
    assert updated.validation_status == "rejected_stale"
    assert updated.is_validated is False

def test_match_observation_rejects_incompatible_source(fresh_service):
    """Test that incompatible sources are rejected."""
    now = datetime.now(timezone.utc)
    target = now + timedelta(hours=3)

    record = fresh_service.record_forecast(
        location_name="bengaluru_central",
        horizon_hours=3,
        predicted_pm25=50.0,
        target_timestamp=target
    )

    matched = fresh_service.match_observation(
        location_name="bengaluru_central",
        observation_time=target,
        actual_pm25=55.0,
        source="Unverified Crowd Sensor",
        is_stale=False,
        is_compatible_source=False
    )

    assert len(matched) >= 1
    updated = next(r for r in fresh_service.records if r.id == record.id)
    assert updated.validation_status == "rejected_incompatible"
    assert updated.is_validated is False

def test_insufficient_data_guard():
    """Test that if fewer than 3 validated pairs exist, trust metrics return insufficient data message."""
    service = ForecastAccuracyService()
    # Clear out pre-populated benchmark data for testing empty state
    service.records.clear()

    # Add only 2 records
    now = datetime.now(timezone.utc)
    for i in range(2):
        t = now + timedelta(hours=i)
        service.record_forecast(
            location_name="bengaluru_central",
            horizon_hours=3,
            predicted_pm25=20.0 + i,
            target_timestamp=t
        )
        service.match_observation(
            location_name="bengaluru_central",
            observation_time=t,
            actual_pm25=22.0 + i,
            source="Test Station"
        )

    res = service.get_accuracy_metrics("bengaluru_central", horizon_hours=3, date_range="all")
    assert res.has_sufficient_data is False
    assert res.status_message == "Not enough data to evaluate forecast accuracy yet."
    assert res.mae is None
    assert res.rmse is None
    assert res.validated_sample_count == 2

def test_metrics_calculation_accuracy(fresh_service):
    """Test mathematical accuracy of MAE and RMSE across known synthetic validation records."""
    fresh_service.records.clear()
    now = datetime.now(timezone.utc)

    # 4 known samples:
    # y = [10, 20, 30, 40]
    # y_hat = [12, 18, 33, 44]
    # errors = [-2, +2, -3, -4]
    # abs_errors = [2, 2, 3, 4] -> sum = 11, MAE = 11/4 = 2.75
    # sq_errors = [4, 4, 9, 16] -> sum = 33, RMSE = sqrt(33/4) = sqrt(8.25) ≈ 2.8723
    test_pairs = [
        (10.0, 12.0),
        (20.0, 18.0),
        (30.0, 33.0),
        (40.0, 44.0)
    ]

    for i, (actual, pred) in enumerate(test_pairs):
        target = now + timedelta(hours=i)
        fresh_service.record_forecast(
            location_name="bengaluru_central",
            horizon_hours=3,
            predicted_pm25=pred,
            target_timestamp=target
        )
        fresh_service.match_observation(
            location_name="bengaluru_central",
            observation_time=target,
            actual_pm25=actual,
            source="Ground Validation Test Station"
        )

    metrics = fresh_service.get_accuracy_metrics("bengaluru_central", horizon_hours=3, date_range="all")
    assert metrics.has_sufficient_data is True
    assert metrics.validated_sample_count == 4
    assert metrics.mae == pytest.approx(2.75, abs=0.01)
    assert metrics.rmse == pytest.approx(math.sqrt(8.25), abs=0.01)
    assert len(metrics.chart_data) == 4

def test_genuine_out_of_sample_benchmark_initialized():
    """Verify that accuracy_service starts with genuine out-of-sample LightGBM benchmark records."""
    metrics_3h = accuracy_service.get_accuracy_metrics("bengaluru_central", horizon_hours=3, date_range="all")
    assert metrics_3h.has_sufficient_data is True
    assert metrics_3h.validated_sample_count >= 100
    # True out-of-sample LightGBM MAE for 3h is ~7.38 µg/m³
    assert 5.0 <= metrics_3h.mae <= 10.0
    assert 7.0 <= metrics_3h.rmse <= 14.0

    metrics_1h = accuracy_service.get_accuracy_metrics("bengaluru_central", horizon_hours=1, date_range="all")
    assert metrics_1h.has_sufficient_data is True
    assert metrics_1h.mae <= metrics_3h.mae  # 1h error should be lower than 3h error

    metrics_6h = accuracy_service.get_accuracy_metrics("bengaluru_central", horizon_hours=6, date_range="all")
    assert metrics_6h.has_sufficient_data is True
    assert metrics_6h.mae >= metrics_3h.mae  # 6h error should be higher than 3h error

def test_api_get_forecast_accuracy():
    """Test FastAPI GET /api/forecast/accuracy endpoint."""
    response = client.get("/api/forecast/accuracy?location=bengaluru_central&horizon=3&range=all")
    assert response.status_code == 200
    data = response.json()

    assert data["location_name"] == "bengaluru_central"
    assert data["horizon_hours"] == 3
    assert data["has_sufficient_data"] is True
    assert isinstance(data["mae"], (float, int))
    assert isinstance(data["rmse"], (float, int))
    assert data["validated_sample_count"] > 0
    assert len(data["chart_data"]) > 0
    assert "actual_pm25" in data["chart_data"][0]
    assert "predicted_pm25" in data["chart_data"][0]
    assert "observation_source" in data

def test_api_get_forecast_accuracy_invalid_horizon():
    """Test that invalid horizon returns 400 Bad Request."""
    response = client.get("/api/forecast/accuracy?location=bengaluru_central&horizon=12")
    assert response.status_code == 400
    assert "Supported horizons" in response.json()["detail"]

def test_api_get_forecast_history():
    """Test FastAPI GET /api/forecast/history endpoint."""
    response = client.get("/api/forecast/history?location=bengaluru_central&horizon=3&limit=10")
    assert response.status_code == 200
    history = response.json()

    assert isinstance(history, list)
    assert len(history) <= 10
    if len(history) > 0:
        first = history[0]
        assert "target_timestamp" in first
        assert "predicted_pm25" in first
        assert "validation_status" in first
        assert "forecast_source" in first
