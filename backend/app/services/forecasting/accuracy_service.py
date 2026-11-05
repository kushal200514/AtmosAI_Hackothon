import os
import sys
import json
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone, timedelta
import uuid
import numpy as np
import pandas as pd
import joblib

from app.schemas.accuracy import (
    ForecastValidationRecord, 
    AccuracyMetricsResponse, 
    AccuracyChartDataPoint
)
from app.services.environmental.cache_manager import cache_manager

logger = logging.getLogger("atmosai.accuracy")

class ForecastAccuracyService:
    """
    AtmosAI Forecast Accuracy and Trust Engine.
    Records generated predictions, matches actual environmental observations,
    rejects stale/incompatible data, and computes genuine MAE/RMSE metrics.
    """

    def __init__(self):
        self.records: List[ForecastValidationRecord] = []
        self._init_historical_evaluations()

    def _init_historical_evaluations(self):
        """
        Loads genuine, out-of-sample chronological test set predictions and observations
        from the trained LightGBM models and Bengaluru features dataset.
        Zero fabricated data.
        """
        curr_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.abspath(os.path.join(curr_dir, "..", "..", "..", ".."))
        features_csv = os.path.join(project_root, "ml", "data", "bengaluru_features.csv")
        artifacts_dir = os.path.join(project_root, "ml", "artifacts")

        if not os.path.exists(features_csv):
            logger.warning(f"Features dataset not found at {features_csv}. Cold start active.")
            return

        try:
            if project_root not in sys.path:
                sys.path.insert(0, project_root)
            from ml.preprocessing.features import FEATURE_COLUMNS
            df = pd.read_csv(features_csv)
            n_samples = len(df)
            test_start = int(n_samples * 0.85)
            df_test = df.iloc[test_start:].copy().reset_index(drop=True)

            for h in [1, 3, 6]:
                model_path = os.path.join(artifacts_dir, f"lgbm_pm25_{h}h.joblib")
                if not os.path.exists(model_path):
                    continue

                model = joblib.load(model_path)
                X_test = df_test[FEATURE_COLUMNS]
                preds = model.predict(X_test)
                actuals = df_test[f"target_{h}h"].values
                timestamps = pd.to_datetime(df_test["timestamp"])

                for i in range(len(df_test)):
                    t_gen = timestamps.iloc[i].to_pydatetime()
                    if t_gen.tzinfo is None:
                        t_gen = t_gen.replace(tzinfo=timezone.utc)
                    t_target = t_gen + timedelta(hours=h)

                    pred_val = float(preds[i])
                    act_val = float(actuals[i])
                    abs_err = abs(act_val - pred_val)
                    sq_err = (act_val - pred_val) ** 2

                    self.records.append(ForecastValidationRecord(
                        id=f"hist_{h}h_{i}",
                        location_name="bengaluru_central",
                        location_id="11111111-1111-1111-1111-111111111101",
                        horizon_hours=h,
                        generated_at=t_gen,
                        target_timestamp=t_target,
                        predicted_pm25=round(pred_val, 1),
                        actual_pm25=round(act_val, 1),
                        absolute_error=round(abs_err, 2),
                        squared_error=round(sq_err, 2),
                        is_validated=True,
                        forecast_source="AtmosAI LightGBM v1.0",
                        model_identifier=f"lgbm_pm25_{h}h",
                        observation_source="Open-Meteo CAMS Atmospheric Chemistry Model & Ground Validation",
                        validation_status="validated",
                        notes=f"Chronological test set sample #{i+1}"
                    ))
            
            logger.info(f"Initialized {len(self.records)} historical validated prediction-observation pairs.")
        except Exception as e:
            logger.error(f"Failed to load historical test evaluations: {e}")

    def record_forecast(
        self,
        location_name: str,
        horizon_hours: int,
        predicted_pm25: float,
        target_timestamp: datetime,
        generated_at: Optional[datetime] = None,
        source: Optional[str] = None,
        forecast_source: Optional[str] = None,
        model_identifier: str = "lgbm_pm25",
        location_id: Optional[str] = None
    ) -> ForecastValidationRecord:
        """
        Records a newly generated forecast for future matching against actual observations.
        """
        gen_time = generated_at or datetime.now(timezone.utc)
        src = forecast_source or source or "AtmosAI LightGBM v1.0"
        record = ForecastValidationRecord(
            id=str(uuid.uuid4()),
            location_name=location_name,
            location_id=location_id,
            horizon_hours=horizon_hours,
            generated_at=gen_time,
            target_timestamp=target_timestamp,
            predicted_pm25=round(predicted_pm25, 1),
            forecast_source=src,
            model_identifier=model_identifier,
            is_validated=False,
            validation_status="pending"
        )
        self.records.append(record)
        return record

    def match_observation(
        self,
        location_name: str,
        observation_time: datetime,
        actual_pm25: Optional[float],
        source: str,
        is_stale: bool = False,
        error_detail: Optional[str] = None,
        is_compatible_source: bool = True
    ) -> List[ForecastValidationRecord]:
        """
        Matches incoming actual observation against pending forecasts for the EXACT SAME location.
        Rejects stale or incompatible observations.
        """
        matched: List[ForecastValidationRecord] = []
        
        for r in self.records:
            # Strictly same location: Never compare unrelated locations
            if r.location_name != location_name:
                continue

            if r.is_validated or r.validation_status != "pending":
                continue

            # Check time alignment (tolerance window +-45 mins)
            time_diff = abs((r.target_timestamp - observation_time).total_seconds())
            if time_diff <= 2700: # 45 minutes
                # Reject stale observations
                if is_stale or error_detail is not None or actual_pm25 is None:
                    r.validation_status = "rejected_stale"
                    r.notes = f"Rejected: Stale or degraded sensor reading ({error_detail or 'stale observation'})."
                    matched.append(r)
                    continue

                # Reject incompatible data sources without clear provenance
                if not is_compatible_source:
                    r.validation_status = "rejected_incompatible"
                    r.notes = "Rejected: Incompatible sensor calibration provenance."
                    matched.append(r)
                    continue

                # Valid pairing!
                r.actual_pm25 = round(actual_pm25, 1)
                r.actual_observed_at = observation_time
                r.observation_source = source
                r.absolute_error = round(abs(actual_pm25 - r.predicted_pm25), 2)
                r.squared_error = round((actual_pm25 - r.predicted_pm25) ** 2, 2)
                r.is_validated = True
                r.validation_status = "validated"
                r.notes = f"Matched within {int(time_diff/60)}m of target timestamp."
                matched.append(r)

        return matched

    def get_accuracy_metrics(
        self,
        location_name: str = "bengaluru_central",
        horizon_hours: int = 3,
        date_range: str = "all"
    ) -> AccuracyMetricsResponse:
        """
        Computes MAE, RMSE, and sample count for the requested horizon and date range.
        If sample count < 3, reports 'Not enough data to evaluate forecast accuracy yet.'
        """
        now = datetime.now(timezone.utc)
        filtered = [
            r for r in self.records 
            if r.location_name == location_name and r.horizon_hours == horizon_hours
        ]

        # Determine reference time for filtering
        if filtered:
            latest_time = max(r.target_timestamp for r in filtered)
        else:
            latest_time = now

        date_label = "All Available Out-of-Sample Observations"
        if date_range == "last_24h":
            cutoff = latest_time - timedelta(hours=24)
            filtered = [r for r in filtered if r.target_timestamp >= cutoff]
            date_label = "Last 24 Hours"
        elif date_range == "last_7d":
            cutoff = latest_time - timedelta(days=7)
            filtered = [r for r in filtered if r.target_timestamp >= cutoff]
            date_label = "Last 7 Days"
        elif date_range == "last_30d":
            cutoff = latest_time - timedelta(days=30)
            filtered = [r for r in filtered if r.target_timestamp >= cutoff]
            date_label = "Last 30 Days"

        # Separate validated records
        validated = [r for r in filtered if r.is_validated and r.actual_pm25 is not None]
        N = len(validated)

        # Baseline metrics from ml/artifacts/metrics.json
        curr_dir = os.path.dirname(os.path.abspath(__file__))
        root_dir = os.path.dirname(os.path.dirname(os.path.dirname(curr_dir)))
        metrics_json_path = os.path.join(root_dir, "ml", "artifacts", "metrics.json")
        baseline_mae = None
        baseline_rmse = None
        improvement_pct = None

        if os.path.exists(metrics_json_path):
            try:
                with open(metrics_json_path, "r") as f:
                    meta = json.load(f)
                    h_info = meta.get("horizons", {}).get(f"{horizon_hours}h", {})
                    base = h_info.get("persistence_baseline", {})
                    baseline_mae = base.get("mae")
                    baseline_rmse = base.get("rmse")
                    improvement_pct = h_info.get("mae_improvement_pct")
            except Exception as e:
                logger.warning(f"Could not read baseline metrics: {e}")

        # Insufficient data check
        if N < 3:
            return AccuracyMetricsResponse(
                location_name=location_name,
                display_name=location_name.replace("_", " ").title(),
                horizon_hours=horizon_hours,
                date_range=date_range,
                date_range_label=date_label,
                validated_sample_count=N,
                mae=None,
                rmse=None,
                baseline_mae=baseline_mae,
                baseline_rmse=baseline_rmse,
                mae_improvement_pct=improvement_pct,
                forecast_source="AtmosAI LightGBM v1.0",
                observation_source="CPCB Ground Stations & CAMS Reanalysis",
                data_freshness_iso=now.isoformat(),
                has_sufficient_data=False,
                status_message="Not enough data to evaluate forecast accuracy yet.",
                chart_data=[],
                forecast_history=filtered[:30]
            )

        # Compute actual MAE and RMSE
        errors = [r.absolute_error for r in validated if r.absolute_error is not None]
        sq_errors = [r.squared_error for r in validated if r.squared_error is not None]

        mae = float(np.mean(errors))
        rmse = float(np.sqrt(np.mean(sq_errors)))

        # Build chart data sorted chronologically
        chart_points = []
        for r in sorted(validated, key=lambda x: x.target_timestamp):
            chart_points.append(AccuracyChartDataPoint(
                timestamp_iso=r.target_timestamp.isoformat(),
                display_time=r.target_timestamp.strftime("%b %d, %H:%M"),
                predicted_pm25=r.predicted_pm25,
                actual_pm25=r.actual_pm25,
                absolute_error=r.absolute_error
            ))

        return AccuracyMetricsResponse(
            location_name=location_name,
            display_name=location_name.replace("_", " ").title(),
            horizon_hours=horizon_hours,
            date_range=date_range,
            date_range_label=date_label,
            validated_sample_count=N,
            mae=round(mae, 2),
            rmse=round(rmse, 2),
            baseline_mae=baseline_mae,
            baseline_rmse=baseline_rmse,
            mae_improvement_pct=improvement_pct,
            forecast_source="AtmosAI LightGBM v1.0",
            observation_source="Open-Meteo CAMS Model & Ground Observation Validation",
            data_freshness_iso=now.isoformat(),
            has_sufficient_data=True,
            status_message=f"Validated against {N} chronological out-of-sample observation pairs.",
            chart_data=chart_points,
            forecast_history=sorted(filtered, key=lambda x: x.target_timestamp, reverse=True)[:50]
        )

accuracy_service = ForecastAccuracyService()
