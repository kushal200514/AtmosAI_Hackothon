import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.main import app
from app.services.forecasting.ml_service import ml_forecaster

client = TestClient(app)

MOCK_AIR = {
    "current": {
        "time": "2026-11-05T13:00",
        "interval": 3600,
        "pm10": 20.0,
        "pm2_5": 16.5,
        "carbon_monoxide": 280.0,
        "nitrogen_dioxide": 5.0,
        "sulphur_dioxide": 6.0,
        "ozone": 110.0
    }
}

MOCK_WEATHER = {
    "current": {
        "time": "2026-11-05T13:00",
        "interval": 900,
        "temperature_2m": 28.0,
        "relative_humidity_2m": 55.0,
        "wind_speed_10m": 10.0,
        "wind_direction_10m": 120.0,
        "surface_pressure": 915.0,
        "precipitation": 0.0
    }
}

def test_ml_forecaster_initialization():
    assert ml_forecaster.is_trained is True
    assert len(ml_forecaster.models) == 5
    for h in [1, 3, 4, 5, 6]:
        assert h in ml_forecaster.models

@pytest.mark.asyncio
async def test_ml_prediction_generation():
    with patch("app.services.environmental.openmeteo_client.openmeteo_client.get_air_quality", new=AsyncMock(return_value=MOCK_AIR)), \
         patch("app.services.environmental.openmeteo_client.openmeteo_client.get_live_weather", new=AsyncMock(return_value=MOCK_WEATHER)), \
         patch("app.services.environmental.openaq_client.openaq_client.get_latest_measurements", new=AsyncMock(return_value=None)):

        forecast = await ml_forecaster.predict("bengaluru_central")
        assert forecast is not None
        assert forecast.location_name == "bengaluru_central"
        assert len(forecast.forecast_points) == 5

        for pt in forecast.forecast_points:
            assert pt.horizon_hours in [1, 3, 4, 5, 6]
            assert pt.predicted_pm25 > 0
            assert pt.confidence_lower <= pt.predicted_pm25
            assert pt.confidence_upper >= pt.predicted_pm25
            assert pt.trend in ["rising", "falling", "stable"]
            assert pt.risk_level in ["Low", "Low-Moderate", "Moderate", "High", "Critical"]

def test_api_forecast_predict_endpoint():
    with patch("app.services.environmental.openmeteo_client.openmeteo_client.get_air_quality", new=AsyncMock(return_value=MOCK_AIR)), \
         patch("app.services.environmental.openmeteo_client.openmeteo_client.get_live_weather", new=AsyncMock(return_value=MOCK_WEATHER)), \
         patch("app.services.environmental.openaq_client.openaq_client.get_latest_measurements", new=AsyncMock(return_value=None)):

        response = client.get("/api/forecast/predict?location=bengaluru_central")
        assert response.status_code == 200
        data = response.json()
        assert "forecast_points" in data
        assert len(data["forecast_points"]) == 5
        assert "primary_driving_factors" in data
        assert "model_name" in data
        assert "LightGBM" in data["model_name"]
        assert "uncertainty_description" in data

