"""
AtmosAI Feature Engineering Pipeline
Constructs lag features, cyclical temporal transformations,
rolling atmospheric statistics, and multi-horizon prediction targets.
"""
import os
import numpy as np
import pandas as pd

FEATURE_COLUMNS = [
    # Meteorological covariates
    "temperature",
    "humidity",
    "wind_speed",
    "wind_direction",
    "surface_pressure",
    # Temporal & Rush-Hour features
    "hour",
    "dayofweek",
    "is_weekend",
    "is_rush_hour",
    "sin_hour",
    "cos_hour",
    # PM2.5 Auto-regressive Lags
    "pm25_lag_1",
    "pm25_lag_2",
    "pm25_lag_3",
    "pm25_lag_6",
    "pm25_lag_12",
    "pm25_lag_24",
    # Rolling Statistical Windows
    "pm25_roll_mean_3h",
    "pm25_roll_std_3h",
    "pm25_roll_mean_6h",
    "pm25_roll_mean_24h",
    "wind_roll_mean_3h",
    "temp_roll_mean_3h"
]

HORIZONS = [1, 3, 4, 5, 6]

def build_features(df_raw: pd.DataFrame) -> pd.DataFrame:
    df = df_raw.copy()
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    df = df.sort_values("timestamp").reset_index(drop=True)

    # Clean missing values using forward fill then backward fill
    df["pm25"] = df["pm25"].ffill().bfill()
    df["temperature"] = df["temperature"].ffill().bfill()
    df["humidity"] = df["humidity"].ffill().bfill()
    df["wind_speed"] = df["wind_speed"].ffill().bfill()
    df["wind_direction"] = df["wind_direction"].ffill().bfill()
    df["surface_pressure"] = df["surface_pressure"].ffill().bfill()

    # 1. Temporal features
    df["hour"] = df["timestamp"].dt.hour
    df["dayofweek"] = getattr(df["timestamp"].dt, "day_of_week", df["timestamp"].dt.dayofweek)
    df["is_weekend"] = df["dayofweek"].isin([5, 6]).astype(int)
    # Peak traffic / rush hour in Bengaluru (morning 8-11, evening 17-21)
    df["is_rush_hour"] = df["hour"].isin([8, 9, 10, 17, 18, 19, 20]).astype(int)
    
    # Cyclical hour encoding
    df["sin_hour"] = np.sin(2 * np.pi * df["hour"] / 24.0)
    df["cos_hour"] = np.cos(2 * np.pi * df["hour"] / 24.0)

    # 2. Lag features
    for lag in [1, 2, 3, 6, 12, 24]:
        df[f"pm25_lag_{lag}"] = df["pm25"].shift(lag)

    # 3. Rolling window statistics
    df["pm25_roll_mean_3h"] = df["pm25"].shift(1).rolling(window=3).mean()
    df["pm25_roll_std_3h"] = df["pm25"].shift(1).rolling(window=3).std().fillna(0)
    df["pm25_roll_mean_6h"] = df["pm25"].shift(1).rolling(window=6).mean()
    df["pm25_roll_mean_24h"] = df["pm25"].shift(1).rolling(window=24).mean()
    
    df["wind_roll_mean_3h"] = df["wind_speed"].shift(1).rolling(window=3).mean()
    df["temp_roll_mean_3h"] = df["temperature"].shift(1).rolling(window=3).mean()

    # 4. Multi-horizon targets (3, 4, 5, 6 hours ahead)
    for h in HORIZONS:
        df[f"target_{h}h"] = df["pm25"].shift(-h)

    # Drop edge rows containing NaNs from shifts
    df_clean = df.dropna().reset_index(drop=True)
    return df_clean

def run_pipeline(raw_csv: str = None, output_csv: str = None):
    curr_dir = os.path.dirname(os.path.abspath(__file__))
    ml_root = os.path.dirname(curr_dir)
    
    if raw_csv is None:
        raw_csv = os.path.join(ml_root, "data", "bengaluru_historical_raw.csv")
    if output_csv is None:
        output_csv = os.path.join(ml_root, "data", "bengaluru_features.csv")

    print(f"Reading raw data from: {raw_csv}")
    df_raw = pd.read_csv(raw_csv)
    df_features = build_features(df_raw)
    df_features.to_csv(output_csv, index=False)
    print(f"Engineered {len(FEATURE_COLUMNS)} features across {len(df_features)} observations.")
    print(f"Features saved to: {output_csv}")

if __name__ == "__main__":
    run_pipeline()
