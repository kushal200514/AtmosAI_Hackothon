import logging
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime, timezone
import asyncio

from app.database.supabase_client import db_manager
from app.services.environmental.openmeteo_client import openmeteo_client
from app.services.environmental.openaq_client import openaq_client
from app.services.environmental.cache_manager import cache_manager
from app.services.environmental.aqi_calculator import compute_naqi
from app.services.data_reliability_service import reliability_service
from app.schemas.reliability import SourceType, FreshnessStatus
from app.schemas.environmental import (
    LiveEnvironmentalData, 
    WeatherConditions, 
    MeasurementType, 
    DataAvailabilityStatus
)

logger = logging.getLogger("atmosai.aggregator")

class EnvironmentalAggregator:
    async def get_live_data(self, location_slug: str = "bengaluru_central") -> LiveEnvironmentalData:
        cache_key = f"live:{location_slug}"
        cached_val, is_stale, cached_time = cache_manager.get(cache_key)

        # Retrieve location metadata from database
        location = await db_manager.get_location_by_name(location_slug)
        if not location:
            location = await db_manager.get_location_by_name("bengaluru_central")

        lat = location["latitude"]
        lon = location["longitude"]
        query_now = datetime.now(timezone.utc)

        # If cache is valid and fresh (within 5 min TTL), return cached data
        if cached_val and not is_stale:
            return cached_val

        # Fetch fresh data concurrently from external providers
        weather_task = openmeteo_client.get_live_weather(lat, lon)
        air_task = openmeteo_client.get_air_quality(lat, lon)
        openaq_task = openaq_client.get_latest_measurements(lat, lon)

        weather_res, air_res, openaq_res = await asyncio.gather(
            weather_task, air_task, openaq_task, return_exceptions=True
        )

        # Check for errors in external calls
        weather_err = isinstance(weather_res, Exception) or weather_res is None
        air_err = isinstance(air_res, Exception) or air_res is None

        # 1. Parse Weather Data (Zero Hardcoded Values)
        weather_obj: Optional[WeatherConditions] = None
        if not weather_err and isinstance(weather_res, dict) and "current" in weather_res:
            curr_w = weather_res["current"]
            weather_obj = WeatherConditions(
                temperature_c=curr_w.get("temperature_2m"),
                relative_humidity_pct=curr_w.get("relative_humidity_2m"),
                wind_speed_kmh=curr_w.get("wind_speed_10m"),
                wind_direction_deg=curr_w.get("wind_direction_10m"),
                surface_pressure_hpa=curr_w.get("surface_pressure"),
                precipitation_mm=curr_w.get("precipitation"),
                observation_time=curr_w.get("time")
            )

        # 2. Parse Air Quality Data (Zero Hardcoded Values)
        pm25: Optional[float] = None
        pm10: Optional[float] = None
        co: Optional[float] = None
        no2: Optional[float] = None
        so2: Optional[float] = None
        o3: Optional[float] = None
        obs_time: Optional[str] = None
        measurement_type = MeasurementType.MODEL_FORECAST
        data_source = "Open-Meteo (CAMS Regional Model)"
        status = DataAvailabilityStatus.LIVE

        # Check Open-Meteo Air Quality
        if not air_err and isinstance(air_res, dict) and "current" in air_res:
            curr_a = air_res["current"]
            pm25 = curr_a.get("pm2_5")
            pm10 = curr_a.get("pm10")
            co = curr_a.get("carbon_monoxide")
            no2 = curr_a.get("nitrogen_dioxide")
            so2 = curr_a.get("sulphur_dioxide")
            o3 = curr_a.get("ozone")
            obs_time = curr_a.get("time")
            measurement_type = MeasurementType.MODEL_FORECAST
            data_source = "Open-Meteo (Copernicus CAMS European Atmospheric Model)"

        # Check OpenAQ Physical Ground Station Override (if authorized and available)
        station_name: Optional[str] = None
        station_coords: Optional[Tuple[float, float]] = None
        if isinstance(openaq_res, dict) and "sensors" in openaq_res:
            sensors_found = False
            for sensor in openaq_res.get("sensors", []):
                param = sensor.get("parameter", {}).get("name")
                val = sensor.get("latest", {}).get("value")
                time_val = sensor.get("latest", {}).get("datetime")
                if param == "pm25" and val is not None:
                    pm25 = float(val)
                    obs_time = time_val
                    sensors_found = True
                elif param == "pm10" and val is not None:
                    pm10 = float(val)
                    sensors_found = True
            if sensors_found:
                measurement_type = MeasurementType.MEASURED
                station_label = openaq_res.get("name", "CPCB Station")
                station_name = station_label
                if "coordinates" in openaq_res and isinstance(openaq_res["coordinates"], dict):
                    c = openaq_res["coordinates"]
                    if c.get("latitude") and c.get("longitude"):
                        station_coords = (float(c["latitude"]), float(c["longitude"]))
                data_source = f"OpenAQ Ground Station ({station_label})"

        # 3. Handle Complete Failure of Live APIs
        if pm25 is None:
            if cached_val:
                logger.warning(f"Live API unavailable for {location_slug}. Returning cached reading from {cached_time}")
                cached_copy = cached_val.model_copy()
                cached_copy.data_availability_status = DataAvailabilityStatus.CACHED
                cached_copy.is_stale = True
                cached_copy.error_detail = f"Live upstream refresh failed. Displaying cached data from {cached_time.isoformat() if cached_time else 'previous session'}."
                
                # Protect stale data: mark freshness as STALE and suppress live claim
                cached_copy.reliability_metadata = reliability_service.create_reliability_metadata(
                    pollutant="PM2.5",
                    value=cached_copy.pm25,
                    source=cached_copy.data_source,
                    source_type=SourceType.MEASURED if cached_copy.measurement_type == MeasurementType.MEASURED else SourceType.ESTIMATED,
                    observed_at=cached_copy.observation_time_iso or cached_time,
                    station_name=getattr(cached_copy.reliability_metadata, "station_name", None),
                    location_coords=(lat, lon),
                    is_stale_flag=True,
                    reference_time=query_now
                )
                return cached_copy
            
            # If no cached data exists, report UNAVAILABLE without fabricating values
            logger.error(f"Live environmental data unavailable for {location_slug} and no cache exists.")
            unavail_meta = reliability_service.create_reliability_metadata(
                pollutant="PM2.5",
                value=None,
                source="None (Upstream APIs Unreachable)",
                source_type=SourceType.ESTIMATED,
                observed_at=None,
                location_coords=(lat, lon),
                reference_time=query_now
            )
            return LiveEnvironmentalData(
                location_id=str(location["id"]),
                location_name=location["name"],
                display_name=location["display_name"],
                latitude=lat,
                longitude=lon,
                pm25=None,
                pm10=None,
                aqi=None,
                aqi_category=None,
                risk_level=None,
                weather=weather_obj,
                observation_time_iso=None,
                query_timestamp_iso=query_now.isoformat(),
                measurement_type=MeasurementType.ESTIMATED,
                data_source="None (Upstream APIs Unreachable)",
                data_availability_status=DataAvailabilityStatus.UNAVAILABLE,
                is_stale=False,
                error_detail="Upstream environmental APIs (Open-Meteo & OpenAQ) could not provide live measurements.",
                reliability_metadata=unavail_meta
            )

        # 4. Compute NAQI strictly using valid CPCB multi-pollutant methodology (not PM2.5 alone)
        aqi_info = compute_naqi(pm25=pm25, pm10=pm10, no2=no2, so2=so2, co=co, o3=o3)

        # Generate reliability metadata for primary reading (PM2.5) and additional pollutants
        primary_source_type = SourceType.MEASURED if measurement_type == MeasurementType.MEASURED else SourceType.ESTIMATED
        primary_meta = reliability_service.create_reliability_metadata(
            pollutant="PM2.5",
            value=round(pm25, 1) if pm25 is not None else None,
            source=data_source,
            source_type=primary_source_type,
            observed_at=obs_time,
            station_name=station_name,
            station_coords=station_coords,
            location_coords=(lat, lon),
            reference_time=query_now
        )
        
        readings_meta = {"pm25": primary_meta}
        if pm10 is not None:
            readings_meta["pm10"] = reliability_service.create_reliability_metadata(
                pollutant="PM10",
                value=round(pm10, 1),
                source=data_source,
                source_type=primary_source_type,
                observed_at=obs_time,
                station_name=station_name,
                station_coords=station_coords,
                location_coords=(lat, lon),
                reference_time=query_now
            )
        if aqi_info["aqi"] is not None:
            readings_meta["aqi"] = reliability_service.create_reliability_metadata(
                pollutant="AQI",
                value=float(aqi_info["aqi"]),
                unit="NAQI",
                source=f"CPCB NAQI Multi-Pollutant Calculation ({data_source})",
                source_type=primary_source_type,
                observed_at=obs_time,
                station_name=station_name,
                station_coords=station_coords,
                location_coords=(lat, lon),
                reference_time=query_now
            )

        result = LiveEnvironmentalData(
            location_id=str(location["id"]),
            location_name=location["name"],
            display_name=location["display_name"],
            latitude=lat,
            longitude=lon,
            pm25=round(pm25, 1) if pm25 is not None else None,
            pm10=round(pm10, 1) if pm10 is not None else None,
            carbon_monoxide=round(co, 1) if co is not None else None,
            nitrogen_dioxide=round(no2, 1) if no2 is not None else None,
            sulphur_dioxide=round(so2, 1) if so2 is not None else None,
            ozone=round(o3, 1) if o3 is not None else None,
            aqi=aqi_info["aqi"],
            aqi_category=aqi_info["category"],
            risk_level=aqi_info["risk_level"],
            dominant_pollutant=aqi_info["dominant_pollutant"],
            weather=weather_obj,
            observation_time_iso=obs_time,
            query_timestamp_iso=query_now.isoformat(),
            measurement_type=measurement_type,
            data_source=data_source,
            data_availability_status=status,
            is_stale=False,
            error_detail=None,
            reliability_metadata=primary_meta,
            readings_metadata=readings_meta
        )

        # Match observation with pending forecast validation records
        if result.pm25 is not None:
            try:
                from app.services.forecasting.accuracy_service import accuracy_service
                accuracy_service.match_observation(
                    location_name=location_slug,
                    observation_time=query_now,
                    actual_pm25=result.pm25,
                    source=result.data_source,
                    is_stale=result.is_stale,
                    error_detail=result.error_detail
                )
            except Exception as e:
                logger.warning(f"Could not match observation in accuracy service: {e}")

        # Save to cache
        cache_manager.set(cache_key, result, ttl_seconds=300)
        return result

    async def get_all_locations_summary(self) -> List[Dict[str, Any]]:
        locations = await db_manager.get_locations()
        results = []
        for loc in locations:
            live = await self.get_live_data(loc["name"])
            results.append({
                "id": loc["id"],
                "name": loc["name"],
                "display_name": loc["display_name"],
                "latitude": loc["latitude"],
                "longitude": loc["longitude"],
                "pm25": live.pm25,
                "pm10": live.pm10,
                "aqi": live.aqi,
                "aqi_category": live.aqi_category,
                "risk_level": live.risk_level,
                "temperature": live.weather.temperature_c if live.weather else None,
                "humidity": live.weather.relative_humidity_pct if live.weather else None,
                "wind_speed": live.weather.wind_speed_kmh if live.weather else None,
                "wind_direction": live.weather.wind_direction_deg if live.weather else None,
                "observation_time": live.observation_time_iso,
                "measurement_type": live.measurement_type,
                "data_source": live.data_source,
                "data_availability_status": live.data_availability_status,
                "is_stale": live.is_stale,
                "last_queried": live.query_timestamp_iso
            })
        return results

aggregator = EnvironmentalAggregator()
