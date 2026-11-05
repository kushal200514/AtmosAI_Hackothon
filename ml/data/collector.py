"""
AtmosAI ML Data Collector
Collects authentic historical air quality and meteorological observations
for Bengaluru, India from Open-Meteo European Atmospheric Chemistry archive.
"""
import urllib.request
import json
import os
import pandas as pd
from datetime import datetime

def collect_bengaluru_data(days: int = 60, output_path: str = None) -> pd.DataFrame:
    lat, lon = 12.9716, 77.5946
    print(f"Collecting {days} days of historical air quality and meteorological data for Bengaluru ({lat}, {lon})...")

    url_air = f"https://air-quality-api.open-meteo.com/v1/air-quality?latitude={lat}&longitude={lon}&hourly=pm10,pm2_5,carbon_monoxide,nitrogen_dioxide,ozone&past_days={days}&forecast_days=1"
    url_weather = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&hourly=temperature_2m,relative_humidity_2m,wind_speed_10m,wind_direction_10m,surface_pressure,precipitation&past_days={days}&forecast_days=1"

    req_a = urllib.request.Request(url_air, headers={"User-Agent": "AtmosAI-ML-Collector/1.0"})
    req_w = urllib.request.Request(url_weather, headers={"User-Agent": "AtmosAI-ML-Collector/1.0"})

    with urllib.request.urlopen(req_a, timeout=30) as res_a:
        data_a = json.loads(res_a.read().decode())["hourly"]

    with urllib.request.urlopen(req_w, timeout=30) as res_w:
        data_w = json.loads(res_w.read().decode())["hourly"]

    df_a = pd.DataFrame(data_a)
    df_w = pd.DataFrame(data_w)

    # Merge on timestamp
    df = pd.merge(df_a, df_w, on="time", how="inner")
    df.rename(columns={
        "time": "timestamp",
        "pm2_5": "pm25",
        "temperature_2m": "temperature",
        "relative_humidity_2m": "humidity",
        "wind_speed_10m": "wind_speed",
        "wind_direction_10m": "wind_direction"
    }, inplace=True)

    df["timestamp"] = pd.to_datetime(df["timestamp"])
    df.sort_values("timestamp", inplace=True)
    df.reset_index(drop=True, inplace=True)

    if output_path is None:
        curr_dir = os.path.dirname(os.path.abspath(__file__))
        output_path = os.path.join(curr_dir, "bengaluru_historical_raw.csv")

    df.to_csv(output_path, index=False)
    print(f"Successfully collected {len(df)} records. Saved to: {output_path}")
    return df

if __name__ == "__main__":
    collect_bengaluru_data()

