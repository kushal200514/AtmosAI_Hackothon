import pytest
from fastapi.testclient import TestClient
import numpy as np
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.main import app
from app.services.forecasting.demo_evaluation_service import demo_evaluation_service, DemoEvaluationService
from app.services.forecasting.accuracy_service import accuracy_service

client = TestClient(app)

def test_demo_dataset_generation_reproducibility():
    """Verify that demo data is reproducible with seed 42 and >= 168 hours per horizon."""
    svc1 = DemoEvaluationService()
    svc2 = DemoEvaluationService()
    
    assert len(svc1.records) == len(svc2.records)
    assert len(svc1.records) >= 168 * 3  # 168 hours for each of 1h, 3h, 6h
    
    # Check exact matching of values
    for r1, r2 in zip(svc1.records[:20], svc2.records[:20]):
        assert r1.id == r2.id
        assert r1.actual_pm25 == r2.actual_pm25
        assert r1.predicted_pm25 == r2.predicted_pm25
        assert r1.absolute_error == r2.absolute_error
        assert r1.squared_error == r2.squared_error

def test_demo_dataset_horizons_and_pollutant():
    """Verify supported horizons and pollutant info."""
    horizons = {r.horizon_hours for r in demo_evaluation_service.records}
    assert {1, 3, 6}.issubset(horizons)
    
    for r in demo_evaluation_service.records:
        assert r.pollutant == "PM2.5"
        assert "Bengaluru" in r.location_name
        assert r.data_source == "SIMULATED"
        assert r.is_validated is True
        assert r.actual_pm25 is not None
        assert r.predicted_pm25 is not None
        assert abs(r.absolute_error - abs(r.predicted_pm25 - r.actual_pm25)) < 1e-4

def test_dynamic_metric_calculation():
    """Verify that MAE and RMSE are computed dynamically from matched pairs."""
    records_1h = demo_evaluation_service.get_demo_records(horizon_hours=1, limit=500)
    metrics_1h = demo_evaluation_service.get_demo_accuracy_metrics(horizon_hours=1)
    
    assert metrics_1h.has_sufficient_data is True
    assert metrics_1h.is_demo is True
    assert metrics_1h.validated_sample_count == len(records_1h)
    
    # Calculate manual MAE & RMSE
    errors = [abs(r.predicted_pm25 - r.actual_pm25) for r in records_1h]
    expected_mae = round(float(np.mean(errors)), 2)
    expected_rmse = round(float(np.sqrt(np.mean([e**2 for e in errors]))), 2)
    
    assert metrics_1h.mae == expected_mae
    assert metrics_1h.rmse == expected_rmse
    assert metrics_1h.mae > 0
    assert metrics_1h.rmse >= metrics_1h.mae  # RMSE is always >= MAE

def test_zero_contamination_of_production_data():
    """Verify that simulated records never leak into production accuracy_service."""
    for r in accuracy_service.records:
        assert getattr(r, "data_source", None) != "SIMULATED"
    
    # Querying real mode on a fresh location returns real status
    real_metrics = accuracy_service.get_accuracy_metrics(location_name="fresh_test_location")
    assert real_metrics.is_demo is False
    assert real_metrics.has_sufficient_data is False

def test_api_forecast_accuracy_demo_mode():
    """Test GET /api/forecast/accuracy?mode=demo"""
    response = client.get("/api/forecast/accuracy?mode=demo&horizon=3")
    assert response.status_code == 200
    data = response.json()
    
    assert data["is_demo"] is True
    assert data["data_mode"] == "demo"
    assert data["has_sufficient_data"] is True
    assert data["validated_sample_count"] >= 168
    assert "SIMULATED DATA" in data["demo_disclaimer"]
    assert data["mae"] is not None
    assert data["rmse"] is not None
    assert len(data["chart_data"]) > 0
    assert data["chart_data"][0]["data_source"] == "SIMULATED"

def test_api_forecast_accuracy_real_mode_empty():
    """Test GET /api/forecast/accuracy?mode=real preserves unpopulated state."""
    response = client.get("/api/forecast/accuracy?mode=real&location=unpopulated_station")
    assert response.status_code == 200
    data = response.json()
    
    assert data["is_demo"] is False
    assert data["data_mode"] == "real"
    assert data["has_sufficient_data"] is False
    assert "Not enough data" in data["status_message"]

def test_api_evaluation_demo_data():
    """Test dedicated endpoint GET /api/evaluation/demo-data"""
    response = client.get("/api/evaluation/demo-data?horizon=6&limit=50")
    assert response.status_code == 200
    data = response.json()
    
    assert isinstance(data, list)
    assert len(data) == 50
    assert data[0]["pollutant"] == "PM2.5"
    assert data[0]["data_source"] == "SIMULATED"

def test_api_evaluation_metrics():
    """Test dedicated endpoint GET /api/evaluation/metrics"""
    response = client.get("/api/evaluation/metrics?horizon=1")
    assert response.status_code == 200
    data = response.json()
    
    assert data["is_demo"] is True
    assert data["mae"] > 0
    assert data["rmse"] > 0
    assert data["validated_sample_count"] >= 168

def test_api_evaluation_predictions():
    """Test dedicated endpoint GET /api/evaluation/predictions"""
    response = client.get("/api/evaluation/predictions?horizon=3&limit=25")
    assert response.status_code == 200
    data = response.json()
    
    assert isinstance(data, list)
    assert len(data) == 25
    assert data[0]["horizon_hours"] == 3
