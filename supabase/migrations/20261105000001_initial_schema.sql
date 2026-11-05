-- ========================================================
-- AtmosAI Initial Database Schema Migration
-- Database: Supabase PostgreSQL with Row Level Security (RLS)
-- Target: Bengaluru, India Air Quality & Forecasting Intelligence
-- ========================================================

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- --------------------------------------------------------
-- 1. PROFILES
-- --------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.profiles (
    id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    email TEXT,
    full_name TEXT,
    profile_type TEXT NOT NULL DEFAULT 'general_public' CHECK (
        profile_type IN (
            'runner',
            'respiratory_sensitive',
            'parent',
            'delivery_worker',
            'office_commuter',
            'general_public'
        )
    ),
    avatar_url TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc', now()),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc', now())
);

-- --------------------------------------------------------
-- 2. USER PREFERENCES
-- --------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.user_preferences (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL UNIQUE REFERENCES public.profiles(id) ON DELETE CASCADE,
    aqi_threshold INTEGER NOT NULL DEFAULT 100,
    enable_push_alerts BOOLEAN NOT NULL DEFAULT true,
    enable_email_alerts BOOLEAN NOT NULL DEFAULT false,
    wearable_connected BOOLEAN NOT NULL DEFAULT false,
    wearable_device_name TEXT,
    favorite_locations JSONB NOT NULL DEFAULT '[]'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc', now()),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc', now())
);

-- --------------------------------------------------------
-- 3. LOCATIONS (Bengaluru monitoring stations & regions)
-- --------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.locations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL UNIQUE,
    display_name TEXT NOT NULL,
    city TEXT NOT NULL DEFAULT 'Bengaluru',
    state TEXT NOT NULL DEFAULT 'Karnataka',
    country TEXT NOT NULL DEFAULT 'India',
    latitude DOUBLE PRECISION NOT NULL,
    longitude DOUBLE PRECISION NOT NULL,
    station_code TEXT,
    is_active BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc', now())
);

-- --------------------------------------------------------
-- 4. AIR QUALITY OBSERVATIONS
-- --------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.air_quality_observations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    location_id UUID NOT NULL REFERENCES public.locations(id) ON DELETE CASCADE,
    timestamp TIMESTAMPTZ NOT NULL,
    pm25 DOUBLE PRECISION NOT NULL,
    pm10 DOUBLE PRECISION,
    aqi INTEGER,
    no2 DOUBLE PRECISION,
    so2 DOUBLE PRECISION,
    o3 DOUBLE PRECISION,
    co DOUBLE PRECISION,
    data_source TEXT NOT NULL, -- 'openaq', 'open-meteo', 'cpcb', 'iot_core'
    data_type TEXT NOT NULL DEFAULT 'measured' CHECK (
        data_type IN ('measured', 'model_forecast', 'estimated', 'simulated')
    ),
    raw_metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc', now())
);

-- --------------------------------------------------------
-- 5. WEATHER OBSERVATIONS
-- --------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.weather_observations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    location_id UUID NOT NULL REFERENCES public.locations(id) ON DELETE CASCADE,
    timestamp TIMESTAMPTZ NOT NULL,
    temperature DOUBLE PRECISION,
    relative_humidity DOUBLE PRECISION,
    wind_speed DOUBLE PRECISION,
    wind_direction DOUBLE PRECISION,
    surface_pressure DOUBLE PRECISION,
    precipitation DOUBLE PRECISION,
    data_source TEXT NOT NULL DEFAULT 'open-meteo',
    created_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc', now())
);

-- --------------------------------------------------------
-- 6. FORECASTS (LightGBM Regression Horizons: 3, 4, 5, 6 Hours)
-- --------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.forecasts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    location_id UUID NOT NULL REFERENCES public.locations(id) ON DELETE CASCADE,
    generated_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc', now()),
    horizon_hours INTEGER NOT NULL CHECK (horizon_hours IN (3, 4, 5, 6)),
    target_timestamp TIMESTAMPTZ NOT NULL,
    predicted_pm25 DOUBLE PRECISION NOT NULL,
    confidence_lower DOUBLE PRECISION,
    confidence_upper DOUBLE PRECISION,
    model_name TEXT NOT NULL DEFAULT 'lightgbm_pm25',
    model_version TEXT NOT NULL DEFAULT '1.0.0',
    is_surge_warning BOOLEAN NOT NULL DEFAULT false,
    surge_reason TEXT,
    input_features JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc', now())
);

-- --------------------------------------------------------
-- 7. ALERTS
-- --------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.alerts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES public.profiles(id) ON DELETE CASCADE,
    location_id UUID REFERENCES public.locations(id) ON DELETE SET NULL,
    alert_type TEXT NOT NULL CHECK (
        alert_type IN (
            'high_pollution',
            'moderate_pollution',
            'improving_pollution',
            'surge_warning',
            'profile_risk'
        )
    ),
    severity TEXT NOT NULL CHECK (severity IN ('low', 'medium', 'high', 'critical')),
    title TEXT NOT NULL,
    message TEXT NOT NULL,
    profile_category TEXT,
    is_read BOOLEAN NOT NULL DEFAULT false,
    created_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc', now())
);

-- --------------------------------------------------------
-- 8. TRAVEL EXPOSURE
-- --------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.travel_exposure (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES public.profiles(id) ON DELETE CASCADE,
    origin_name TEXT NOT NULL,
    origin_lat DOUBLE PRECISION NOT NULL,
    origin_lon DOUBLE PRECISION NOT NULL,
    destination_name TEXT NOT NULL,
    destination_lat DOUBLE PRECISION NOT NULL,
    destination_lon DOUBLE PRECISION NOT NULL,
    duration_minutes INTEGER NOT NULL,
    average_pm25 DOUBLE PRECISION NOT NULL,
    total_exposure_index DOUBLE PRECISION NOT NULL,
    route_waypoints JSONB DEFAULT '[]'::jsonb,
    calculation_note TEXT NOT NULL DEFAULT 'Time-weighted environmental concentration estimate: E = Σ(Ci × Δti) / ΣΔti. Not a measured biological inhaled dose.',
    created_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc', now())
);

-- --------------------------------------------------------
-- INDEXES FOR FAST QUERYING
-- --------------------------------------------------------
CREATE INDEX IF NOT EXISTS idx_aq_obs_loc_time 
    ON public.air_quality_observations(location_id, timestamp DESC);

CREATE INDEX IF NOT EXISTS idx_weather_obs_loc_time 
    ON public.weather_observations(location_id, timestamp DESC);

CREATE INDEX IF NOT EXISTS idx_forecasts_loc_gen 
    ON public.forecasts(location_id, generated_at DESC, horizon_hours);

CREATE INDEX IF NOT EXISTS idx_alerts_user_unread 
    ON public.alerts(user_id, is_read, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_travel_user 
    ON public.travel_exposure(user_id, created_at DESC);

-- --------------------------------------------------------
-- AUTOMATIC TIMESTAMPS TRIGGER FUNCTION
-- --------------------------------------------------------
CREATE OR REPLACE FUNCTION public.handle_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = timezone('utc', now());
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trigger_profiles_updated_at ON public.profiles;
CREATE TRIGGER trigger_profiles_updated_at
    BEFORE UPDATE ON public.profiles
    FOR EACH ROW EXECUTE FUNCTION public.handle_updated_at();

DROP TRIGGER IF EXISTS trigger_user_preferences_updated_at ON public.user_preferences;
CREATE TRIGGER trigger_user_preferences_updated_at
    BEFORE UPDATE ON public.user_preferences
    FOR EACH ROW EXECUTE FUNCTION public.handle_updated_at();

-- --------------------------------------------------------
-- ROW LEVEL SECURITY (RLS)
-- --------------------------------------------------------
ALTER TABLE public.profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.user_preferences ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.locations ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.air_quality_observations ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.weather_observations ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.forecasts ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.alerts ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.travel_exposure ENABLE ROW LEVEL SECURITY;

-- Profiles: Users can view and update their own profile; public read for basic display
CREATE POLICY "Users can view own profile" 
    ON public.profiles FOR SELECT 
    USING (auth.uid() = id);

CREATE POLICY "Users can update own profile" 
    ON public.profiles FOR UPDATE 
    USING (auth.uid() = id);

CREATE POLICY "Users can insert own profile" 
    ON public.profiles FOR INSERT 
    WITH CHECK (auth.uid() = id);

-- Preferences: Private to the authenticated user
CREATE POLICY "Users can view own preferences" 
    ON public.user_preferences FOR SELECT 
    USING (auth.uid() = user_id);

CREATE POLICY "Users can manage own preferences" 
    ON public.user_preferences FOR ALL 
    USING (auth.uid() = user_id);

-- Environmental observations & forecasts: Readable by everyone (public knowledge)
CREATE POLICY "Public read for locations" 
    ON public.locations FOR SELECT 
    TO PUBLIC 
    USING (is_active = true);

CREATE POLICY "Public read for air quality" 
    ON public.air_quality_observations FOR SELECT 
    TO PUBLIC 
    USING (true);

CREATE POLICY "Public read for weather observations" 
    ON public.weather_observations FOR SELECT 
    TO PUBLIC 
    USING (true);

CREATE POLICY "Public read for forecasts" 
    ON public.forecasts FOR SELECT 
    TO PUBLIC 
    USING (true);

-- Alerts & Travel: User scoped
CREATE POLICY "Users view own alerts or system-broadcast alerts" 
    ON public.alerts FOR SELECT 
    USING (user_id IS NULL OR auth.uid() = user_id);

CREATE POLICY "Users update own alerts" 
    ON public.alerts FOR UPDATE 
    USING (auth.uid() = user_id);

CREATE POLICY "Users manage own travel exposures" 
    ON public.travel_exposure FOR ALL 
    USING (auth.uid() = user_id);

-- --------------------------------------------------------
-- SEED INITIAL BENGALURU MONITORING STATIONS
-- --------------------------------------------------------
INSERT INTO public.locations (name, display_name, city, state, country, latitude, longitude, station_code)
VALUES
    ('bengaluru_central', 'Bengaluru Central ', 'Bengaluru', 'Karnataka', 'India', 12.9716, 77.5946, 'BLR-CEN-01'),
    ('yelahanka', 'Yelahanka Satellite Town', 'Bengaluru', 'Karnataka', 'India', 13.1007, 77.5963, 'BLR-YLH-02'),
    ('hebbal', 'Hebbal Flyover Junction', 'Bengaluru', 'Karnataka', 'India', 13.0358, 77.5970, 'BLR-HBL-03'),
    ('peenya', 'Peenya Industrial Area', 'Bengaluru', 'Karnataka', 'India', 13.0285, 77.5197, 'BLR-PNY-04'),
    ('koramangala', 'Koramangala 4th Block', 'Bengaluru', 'Karnataka', 'India', 12.9352, 77.6245, 'BLR-KRM-05'),
    ('silk_board', 'Central Silk Board Junction', 'Bengaluru', 'Karnataka', 'India', 12.9177, 77.6238, 'BLR-CSB-06'),
    ('electronic_city', 'Electronic City Phase 1', 'Bengaluru', 'Karnataka', 'India', 12.8452, 77.6602, 'BLR-ELC-07')
ON CONFLICT (name) DO UPDATE SET
    display_name = EXCLUDED.display_name,
    latitude = EXCLUDED.latitude,
    longitude = EXCLUDED.longitude,
    station_code = EXCLUDED.station_code;

