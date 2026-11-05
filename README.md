# AtmosAI — Environmental Intelligence & Air Quality Forecasting

> **Tagline:** Breathe Smarter, Live Safer.  
> **Initial Target Location:** Bengaluru, India.  
> **Category:** AI + Machine Learning + Environmental Intelligence Progressive Web Application.

---

## Overview

Traditional air quality apps merely display past or current pollution readings. **AtmosAI** goes further by combining real atmospheric telemetry, multi-horizon **LightGBM machine learning regression** ($3\text{--}6$ hours ahead), and **Explainable AI recommendations via Google Gemini** to help individuals, athletes, parents, and commuters make informed decisions.

---

## Key Features

1. **Live Atmospheric Telemetry & CPCB NAQI:**
   - Real-time PM2.5, PM10, trace gases, temperature, relative humidity, wind speed, wind direction, and surface pressure across 7 Bengaluru stations.
   - Strict data provenance tags: `measured`, `model_forecast`, `estimated`, `simulated`.
2. **Multi-Horizon LightGBM Forecasting ($3\text{h}$, $4\text{h}$, $5\text{h}$, $6\text{h}$):**
   - Trained on historical observations with chronological splitting (zero data leakage).
   - Generates empirical 90% confidence intervals and out-of-sample persistence baseline comparisons.
3. **Pollution Surge Warnings:**
   - Automatically detects impending particulate spikes caused by atmospheric boundary stagnation or traffic rush hours.
4. **Explainable AI Recommendation Engine:**
   - Dual-provider abstraction (Google Gemini API primary + Expert Rule Fallback).
   - Tailors practical, conservative, non-medical advice across 6 user archetypes:
     - Runner / Athlete
     - Respiratory-Sensitive Individual
     - Parent / Guardian
     - Delivery Worker / Field Professional
     - Office Commuter
     - General Public
5. **Interactive Bengaluru Pollution Map (Leaflet):**
   - Custom color-coded pollution markers, station telemetry popups, and spatial rankings across Bengaluru Central, Yelahanka, Hebbal, Peenya, Koramangala, Silk Board, and Electronic City.
6. **Travel Exposure Intelligence:**
   - Evaluates corridor transit exposure via the time-weighted formula:
     $$E = \frac{\sum (C_i \times \Delta t_i)}{\sum \Delta t_i}$$
7. **AtmosAI Wear (Prototype):**
   - Interactive smartwatch prototype simulating heart rate, step count, and ambient PM2.5 exposure synchronization.
8. **Web Push Alerts & PWA Offline Capability:**
   - Installable Progressive Web App with service worker asset precaching and customizable AQI alert thresholds.

---

## Technology Stack

- **Frontend:** React 19, Vite, Tailwind CSS v4, Lucide React, Recharts, Leaflet, Vite PWA Plugin
- **Backend:** Python 3, FastAPI, Uvicorn, Pydantic v2, Pandas, NumPy, Scikit-learn, LightGBM
- **Database:** Supabase PostgreSQL with Row Level Security (RLS)
- **AI / LLM:** Google Gemini API (with pluggable AWS Bedrock and Expert Rule fallback)
- **Deployment:** Render (`render.yaml` blueprint)

---

## Directory Structure

```text
AtmosAI/
  frontend/                # React 19 + Vite + Tailwind v4 PWA
    public/                # Icons and PWA manifests
    src/
      components/          # Dashboard, Map, Forecast, AI, Travel, Wear, Alerts
      services/            # Centralized API client
  backend/                 # FastAPI REST Service
    app/
      api/                 # API route endpoints
      core/                # Settings & configurations
      database/            # Supabase client & in-memory repository
      schemas/             # Pydantic data contracts
      services/            # Environmental, ML forecasting, AI advice, Travel, IoT
    tests/                 # Automated pytest suite (25 tests)
  ml/
    data/                  # Raw and engineered historical datasets
    preprocessing/         # Feature engineering pipeline
    training/              # LightGBM training & persistence benchmark
    evaluation/            # Out-of-sample evaluation reports
    artifacts/             # Saved joblib models & metrics
  supabase/
    migrations/            # PostgreSQL schema & RLS policies
  docs/                    # Architecture, API docs, schema, and deployment
  render.yaml              # Render production deployment blueprint
  .env.example             # Configuration template
  README.md
```

---

## Quick Start Guide

### 1. Backend Setup

```powershell
# Create & activate virtual environment
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# Install dependencies
pip install -r backend/requirements.txt

# Start FastAPI server
cd backend
..\.venv\Scripts\uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```
- API Health Check: [http://localhost:8000/health](http://localhost:8000/health)
- Swagger Documentation: [http://localhost:8000/docs](http://localhost:8000/docs)

### 2. Frontend Setup

```powershell
cd frontend
npm install
npm run dev
```
- Open in Browser: [http://localhost:5173/](http://localhost:5173/)

### 3. Running Automated Tests

```powershell
.\.venv\Scripts\pytest backend\tests
```
All **25 tests** pass verifying database schemas, environmental normalization, LightGBM multi-horizon forecasting, AI advice, and travel intelligence.

