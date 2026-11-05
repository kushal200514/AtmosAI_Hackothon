# AtmosAI REST API Documentation

Base URL: `http://localhost:8000` (or `https://atmosai-backend.onrender.com`)

Interactive Swagger UI: `/docs`  
OpenAPI Specification: `/openapi.json`

---

## 1. System Endpoints

### `GET /health`
Returns system health, service version, environment, active AI provider, and ML engine status.

**Response (200 OK):**
```json
{
  "status": "healthy",
  "service": "AtmosAI Environmental API",
  "version": "1.0.0",
  "environment": "development",
  "timestamp": "2026-11-05T09:36:02.772047+00:00",
  "ai_provider": "gemini",
  "ml_engine": "LightGBM + Time-series persistence benchmark"
}
```

---

## 2. Environmental & Locations

### `GET /api/locations`
Retrieves all 7 active monitoring stations in the Bengaluru metropolitan area.

### `GET /api/forecast/live`
Fetches live environmental telemetry, trace gases, meteorological conditions, and calculated CPCB NAQI.

**Query Parameters:**
- `location` (string, optional, default: `"bengaluru_central"`): Station slug.

**Response (200 OK):**
```json
{
  "location_id": "11111111-1111-1111-1111-111111111101",
  "location_name": "bengaluru_central",
  "display_name": "Bengaluru Central ",
  "latitude": 12.9716,
  "longitude": 77.5946,
  "pm25": 11.8,
  "pm10": 12.1,
  "aqi": 20,
  "aqi_category": "Good",
  "risk_level": "Low",
  "weather": {
    "temperature_c": 26.7,
    "relative_humidity_pct": 60.0,
    "wind_speed_kmh": 8.9,
    "wind_direction_deg": 118.0
  },
  "measurement_type": "model_forecast",
  "data_source": "Open-Meteo (Copernicus CAMS European Atmospheric Model)",
  "data_availability_status": "live",
  "is_stale": false
}
```

### `GET /api/map/data`
Returns spatial air quality records across all monitoring stations for Leaflet rendering.

---

## 3. Machine Learning Forecasting

### `GET /api/forecast/predict`
Generates $3\text{h}$, $4\text{h}$, $5\text{h}$, and $6\text{h}$ PM2.5 predictions via LightGBM regression.

**Query Parameters:**
- `location` (string, default: `"bengaluru_central"`)

**Response (200 OK):**
```json
{
  "location_name": "bengaluru_central",
  "model_version": "lightgbm_pm25_v1.0",
  "model_name": "LightGBM Gradient Boosted Decision Trees",
  "forecast_points": [
    {
      "horizon_hours": 3,
      "target_time_label": "+3h (12:18)",
      "predicted_pm25": 10.2,
      "confidence_lower": 0.0,
      "confidence_upper": 26.2,
      "trend": "stable",
      "risk_level": "Low",
      "surge_warning": false
    }
  ],
  "primary_driving_factors": ["Moderate wind dispersion (8.6 km/h)"],
  "surge_detected": false
}
```

---

## 4. Explainable AI & Recommendations

### `GET /api/profiles`
Returns the 6 supported user profile categories (`runner`, `respiratory_sensitive`, `parent`, `delivery_worker`, `office_commuter`, `general_public`).

### `GET /api/advice`
Generates evidence-based explanations and profile-tailored activity recommendations.

**Query Parameters:**
- `location` (string, default: `"bengaluru_central"`)
- `profile` (string, default: `"general_public"`)

### `POST /api/advice`
POST alternative accepting `{ "location": "...", "profile_type": "..." }`.

---

## 5. Travel Exposure Intelligence

### `POST /api/travel/exposure`
Calculates time-weighted environmental exposure for corridor transit.

**Payload:**
```json
{
  "origin": "yelahanka",
  "destination": "silk_board",
  "mode": "commute"
}
```

**Response (200 OK):**
```json
{
  "origin": "Yelahanka Satellite Town",
  "destination": "Central Silk Board Junction",
  "estimated_duration_minutes": 55,
  "total_exposure_index": 28.4,
  "risk_level": "Low",
  "advisory": "Corridor environmental quality is currently favorable.",
  "disclaimer": "Time-weighted environmental concentration estimate: E = Σ(Ci * Δti) / ΣΔti. Not a measured biological inhaled dose."
}
```

---

## 6. Alerts & Telemetry

### `GET /api/alerts`
Returns active pollution surge warnings and air quality advisories.

### `POST /api/telemetry`
Ingests contextual wearable prototype telemetry (`heart_rate`, `step_count`, `ambient_pm25`).

### `POST /api/user/profile`
Updates user preferences and active profile archetype.

