# AtmosAI Database Schema & Architecture

## Overview
AtmosAI utilizes PostgreSQL hosted via Supabase with Row Level Security (RLS) enabled. The schema is divided into user identity/personalization domains and public environmental intelligence domains.

## Tables

### 1. `profiles`
Stores user profile types for personalized environmental intelligence recommendations.
- `id` (UUID, PK, references `auth.users(id)`)
- `email` (TEXT)
- `full_name` (TEXT)
- `profile_type` (TEXT: `runner`, `respiratory_sensitive`, `parent`, `delivery_worker`, `office_commuter`, `general_public`)
- `avatar_url` (TEXT)
- `created_at`, `updated_at` (TIMESTAMPTZ)

### 2. `user_preferences`
User-configured alert thresholds and connected wearables.
- `id` (UUID, PK)
- `user_id` (UUID, FK -> `profiles.id`)
- `aqi_threshold` (INT, default 100)
- `enable_push_alerts` (BOOL)
- `enable_email_alerts` (BOOL)
- `wearable_connected` (BOOL)
- `wearable_device_name` (TEXT)
- `favorite_locations` (JSONB)

### 3. `locations`
Monitoring stations across the target metropolitan region (Bengaluru initially).
- `id` (UUID, PK)
- `name` (TEXT, UNIQUE identifier slug)
- `display_name` (TEXT)
- `city`, `state`, `country` (TEXT)
- `latitude`, `longitude` (DOUBLE PRECISION)
- `station_code` (TEXT)
- `is_active` (BOOL)

### 4. `air_quality_observations`
Physical atmospheric measurements and normalized observations.
- `id` (UUID, PK)
- `location_id` (UUID, FK -> `locations.id`)
- `timestamp` (TIMESTAMPTZ)
- `pm25`, `pm10`, `aqi`, `no2`, `so2`, `o3`, `co` (FLOAT / INT)
- `data_source` (TEXT: `openaq`, `open-meteo`, `cpcb`, `iot_core`)
- `data_type` (TEXT: `measured`, `model_forecast`, `estimated`, `simulated`)
- `raw_metadata` (JSONB)

### 5. `weather_observations`
Meteorological covariates driving pollution dispersion.
- `id` (UUID, PK)
- `location_id` (UUID, FK -> `locations.id`)
- `timestamp` (TIMESTAMPTZ)
- `temperature`, `relative_humidity`, `wind_speed`, `wind_direction`, `surface_pressure`, `precipitation`
- `data_source` (TEXT: `open-meteo`)

### 6. `forecasts`
Multi-horizon machine learning predictions produced by the LightGBM regression engine.
- `id` (UUID, PK)
- `location_id` (UUID, FK -> `locations.id`)
- `generated_at` (TIMESTAMPTZ)
- `horizon_hours` (INT: 3, 4, 5, 6)
- `target_timestamp` (TIMESTAMPTZ)
- `predicted_pm25` (DOUBLE PRECISION)
- `confidence_lower`, `confidence_upper` (DOUBLE PRECISION)
- `model_name`, `model_version` (TEXT)
- `is_surge_warning` (BOOL)
- `surge_reason` (TEXT)
- `input_features` (JSONB)

### 7. `alerts`
Targeted risk notifications and actionable recommendations.
- `id` (UUID, PK)
- `user_id` (UUID, FK -> `profiles.id`, nullable for broadcast alerts)
- `location_id` (UUID, FK -> `locations.id`)
- `alert_type` (`high_pollution`, `moderate_pollution`, `improving_pollution`, `surge_warning`, `profile_risk`)
- `severity` (`low`, `medium`, `high`, `critical`)
- `title`, `message`, `profile_category` (TEXT)
- `is_read` (BOOL)

### 8. `travel_exposure`
Point-to-point and route environmental concentration models.
- `id` (UUID, PK)
- `user_id` (UUID, FK -> `profiles.id`)
- `origin_name`, `destination_name` (TEXT)
- `origin_lat`, `origin_lon`, `destination_lat`, `destination_lon` (FLOAT)
- `duration_minutes` (INT)
- `average_pm25` (FLOAT)
- `total_exposure_index` (FLOAT) -> $E = \frac{\sum (C_i \times \Delta t_i)}{\sum \Delta t_i}$
- `calculation_note` (TEXT)

## Row Level Security (RLS)
1. **User tables (`profiles`, `user_preferences`, `alerts`, `travel_exposure`)**: Protected such that users can only read or write records matching their authenticated `auth.uid()`.
2. **Public data (`locations`, `air_quality_observations`, `weather_observations`, `forecasts`)**: Open read access for all clients, restricted write access to server-side service keys or automated ingestion workers.

