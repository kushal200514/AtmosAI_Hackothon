import httpx
import logging
from typing import Dict, Any, Optional
from datetime import datetime, timezone
from app.core.config import settings

logger = logging.getLogger("atmosai.openmeteo")

class OpenMeteoClient:
    def __init__(self):
        self.weather_url = settings.OPEN_METEO_WEATHER_URL
        self.air_quality_url = settings.OPEN_METEO_AIR_QUALITY_URL

    async def get_live_weather(self, lat: float, lon: float) -> Optional[Dict[str, Any]]:
        """
        Fetches current weather covariates: temperature, relative humidity, wind speed, wind direction, surface pressure.
        """
        params = {
            "latitude": lat,
            "longitude": lon,
            "current": "temperature_2m,relative_humidity_2m,precipitation,surface_pressure,wind_speed_10m,wind_direction_10m",
            "hourly": "temperature_2m,relative_humidity_2m,wind_speed_10m,wind_direction_10m",
            "timezone": "UTC"
        }
        try:
            async with httpx.AsyncClient(timeout=6.0) as client:
                res = await client.get(self.weather_url, params=params)
                if res.status_code == 200:
                    return res.json()
                logger.warning(f"Open-Meteo Weather error {res.status_code}: {res.text}")
        except Exception as e:
            logger.error(f"Failed to fetch Open-Meteo weather: {e}")
        return None

    async def get_air_quality(self, lat: float, lon: float) -> Optional[Dict[str, Any]]:
        """
        Fetches current and hourly PM2.5, PM10, NO2, SO2, O3, CO from Open-Meteo Atmospheric Chemistry model.
        """
        params = {
            "latitude": lat,
            "longitude": lon,
            "current": "pm10,pm2_5,carbon_monoxide,nitrogen_dioxide,sulphur_dioxide,ozone",
            "hourly": "pm10,pm2_5",
            "timezone": "UTC"
        }
        try:
            async with httpx.AsyncClient(timeout=6.0) as client:
                res = await client.get(self.air_quality_url, params=params)
                if res.status_code == 200:
                    return res.json()
                logger.warning(f"Open-Meteo Air Quality error {res.status_code}: {res.text}")
        except Exception as e:
            logger.error(f"Failed to fetch Open-Meteo air quality: {e}")
        return None

openmeteo_client = OpenMeteoClient()

