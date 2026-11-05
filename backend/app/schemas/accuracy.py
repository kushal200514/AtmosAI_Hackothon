from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime

class ForecastValidationRecord(BaseModel):
    id: str
    location_name: str
    location_id: Optional[str] = None
    pollutant: str = Field(default="PM2.5", description="Pollutant name")
    horizon_hours: int = Field(..., description="Forecast horizon in hours (1, 3, 6)")
    generated_at: datetime
    target_timestamp: datetime
    actual_observed_at: Optional[datetime] = None
    predicted_pm25: float
    actual_pm25: Optional[float] = None
    absolute_error: Optional[float] = None
    squared_error: Optional[float] = None
    is_validated: bool = False
    forecast_source: str = "AtmosAI LightGBM v1.0"
    model_identifier: str = "lgbm_pm25"
    observation_source: Optional[str] = None
    data_source: str = Field(default="MEASURED", description="'MEASURED', 'FORECAST', 'ESTIMATED', or 'SIMULATED'")
    validation_status: str = Field(default="pending", description="'validated', 'pending', 'rejected_stale', 'rejected_incompatible'")
    notes: Optional[str] = None

class AccuracyChartDataPoint(BaseModel):
    timestamp_iso: str
    display_time: str
    predicted_pm25: float
    actual_pm25: Optional[float] = None
    absolute_error: Optional[float] = None
    pollutant: str = "PM2.5"
    data_source: str = "MEASURED"

class AccuracyMetricsResponse(BaseModel):
    location_name: str
    display_name: str
    horizon_hours: int
    date_range: str
    date_range_label: str
    validated_sample_count: int
    mae: Optional[float] = None
    rmse: Optional[float] = None
    baseline_mae: Optional[float] = None
    baseline_rmse: Optional[float] = None
    mae_improvement_pct: Optional[float] = None
    forecast_source: str
    observation_source: str
    data_freshness_iso: str
    has_sufficient_data: bool
    status_message: str
    data_mode: str = Field(default="real", description="'real' or 'demo'")
    is_demo: bool = Field(default=False, description="True if simulated demo data mode")
    demo_disclaimer: Optional[str] = None
    model_name: Optional[str] = None
    model_methodology: Optional[str] = None
    pollutant: str = "PM2.5"
    chart_data: List[AccuracyChartDataPoint]
    forecast_history: List[ForecastValidationRecord]
