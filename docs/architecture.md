# AtmosAI System Architecture

## 1. Executive Summary
**AtmosAI** is an AI-powered environmental forecasting and personal environmental intelligence platform targeting the Bengaluru metropolitan area. Unlike static AQI dashboards that merely display historical or current sensor values, AtmosAI predicts future particulate concentrations ($3\text{--}6$ hours ahead) via a LightGBM multi-horizon regression engine and generates tailored health and activity guidance via Google Gemini.

```mermaid
flowchart TD
    subgraph Data Sources
        OAQ[OpenAQ v3 Ground Sensors]
        OM[Open-Meteo Atmospheric Chemistry & Weather]
        IOT[Simulated IoT & Wearable PulseWear]
    end

    subgraph Backend Engine [FastAPI Service]
        AGG[Environmental Aggregator & CPCB NAQI Engine]
        TTL[In-Memory 300s TTL Cache]
        ML[LightGBM Multi-Horizon Regression Engine]
        AI[AI Recommendation Engine: Gemini + Rule Fallback]
        TRV[Travel Exposure Matrix]
    end

    subgraph Storage [Supabase PostgreSQL]
        DB_PROF[User Profiles & Sensitivity Criteria]
        DB_LOC[Bengaluru Monitoring Stations]
        DB_RLS[Row Level Security Layer]
    end

    subgraph Frontend [React 19 + Vite PWA]
        DASH[Main Real-Time Dashboard]
        MAP[Leaflet Bengaluru Monitoring Map]
        FC[Forecast Details & Benchmark Explorer]
        AIV[Explainable AI Activity & Mask Schedule]
        TRVV[Travel Exposure Corridor Calculator]
        WEAR[AtmosAI Wear Smartwatch Prototype]
        ALT[Alerts & Web Push Notification Center]
    end

    OAQ --> AGG
    OM --> AGG
    IOT --> AGG

    AGG <--> TTL
    AGG --> ML
    ML --> AI
    AGG --> AI
    AGG --> TRV

    Backend Engine <--> Storage
    Backend Engine <--> Frontend
```

## 2. Core Architectural Pillars

### A. Environmental Telemetry & Normalization
- Concurrently queries ground stations (OpenAQ v3) and European Copernicus atmospheric transport models (Open-Meteo).
- Calculates standard Indian National Air Quality Index (NAQI) based on Central Pollution Control Board (CPCB) breakpoint tables.
- Enforces strict data provenance tags: `measured`, `model_forecast`, `estimated`, `simulated`.

### B. Machine Learning Forecasting
- **Engine**: LightGBM Multi-Horizon Gradient Boosted Decision Trees (`lgbm_pm25_3h`, `4h`, `5h`, `6h`).
- **Data Partitioning**: Strictly forward chronological split ($70\%$ Train, $15\%$ Validation, $15\%$ Out-of-sample Test). Zero future data leakage.
- **Input Features**: $23$ engineered covariates including diurnal sine/cosine hour encoding, Bengaluru rush-hour congestion flags, autoregressive lags ($t-1$ through $t-24$), rolling statistics, and meteorological drivers.
- **Persistence Benchmark**: Evaluated against persistence $\hat{y}_{t+h} = y_t$, demonstrating up to $+9.2\%$ MAE improvement at $+6\text{h}$.

### C. Explainable AI & Activity Guidance
- **Provider Abstraction**: Pluggable interface supporting Google Gemini, AWS Bedrock, and an Expert Rule Engine fallback.
- **Conservative Guardrails**: Strictly non-medical. Does not diagnose diseases or claim wearable heart-rate telemetry proves biological pollution damage.
- **Profile Customization**: Adapts advice to $6$ distinct user archetypes: Runner, Respiratory-Sensitive, Parent, Delivery Worker, Office Commuter, and General Public.

### D. Travel Exposure Intelligence
- Point-to-point exposure model using time-weighted environmental concentration:
  $$E = \frac{\sum (C_i \times \Delta t_i)}{\sum \Delta t_i}$$
- Clearly documented as an environmental ambient exposure estimate rather than an inhaled biological dose.

