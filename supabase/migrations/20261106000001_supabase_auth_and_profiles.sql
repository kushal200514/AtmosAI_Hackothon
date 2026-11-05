-- ========================================================
-- AtmosAI: Supabase Auth, Profiles, Preferences & Saved Locations
-- Migration: 20261106000001_supabase_auth_and_profiles.sql
-- ========================================================

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- --------------------------------------------------------
-- 1. PROFILES TABLE
-- --------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.profiles (
    id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    full_name TEXT,
    age_group TEXT,
    city TEXT DEFAULT 'Bengaluru',
    locality TEXT DEFAULT 'Central',
    preferred_language TEXT DEFAULT 'English',
    lifestyle_category TEXT DEFAULT 'general_public',
    onboarding_completed BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc', now()),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc', now())
);

-- Ensure columns exist if table was previously partially created
ALTER TABLE public.profiles ADD COLUMN IF NOT EXISTS full_name TEXT;
ALTER TABLE public.profiles ADD COLUMN IF NOT EXISTS age_group TEXT;
ALTER TABLE public.profiles ADD COLUMN IF NOT EXISTS city TEXT DEFAULT 'Bengaluru';
ALTER TABLE public.profiles ADD COLUMN IF NOT EXISTS locality TEXT DEFAULT 'Central';
ALTER TABLE public.profiles ADD COLUMN IF NOT EXISTS preferred_language TEXT DEFAULT 'English';
ALTER TABLE public.profiles ADD COLUMN IF NOT EXISTS lifestyle_category TEXT DEFAULT 'general_public';
ALTER TABLE public.profiles ADD COLUMN IF NOT EXISTS onboarding_completed BOOLEAN NOT NULL DEFAULT FALSE;
ALTER TABLE public.profiles ADD COLUMN IF NOT EXISTS created_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc', now());
ALTER TABLE public.profiles ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc', now());

-- --------------------------------------------------------
-- 2. USER PREFERENCES TABLE
-- --------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.user_preferences (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL UNIQUE REFERENCES auth.users(id) ON DELETE CASCADE,
    activities TEXT[] DEFAULT ARRAY['walking', 'commuting']::TEXT[],
    outdoor_time TEXT DEFAULT '1_to_3h',
    environmental_preferences JSONB DEFAULT '["pm25_focus", "deterioration_alerts"]'::jsonb,
    sensitivity_preference TEXT DEFAULT 'none',
    notification_preferences JSONB DEFAULT '{"surge_warnings": true, "daily_morning_brief": true, "threshold_crossing_alerts": true}'::jsonb,
    aqi_alert_threshold INTEGER DEFAULT 101,
    created_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc', now()),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc', now())
);

ALTER TABLE public.user_preferences ADD COLUMN IF NOT EXISTS activities TEXT[] DEFAULT ARRAY['walking', 'commuting']::TEXT[];
ALTER TABLE public.user_preferences ADD COLUMN IF NOT EXISTS outdoor_time TEXT DEFAULT '1_to_3h';
ALTER TABLE public.user_preferences ADD COLUMN IF NOT EXISTS environmental_preferences JSONB DEFAULT '["pm25_focus", "deterioration_alerts"]'::jsonb;
ALTER TABLE public.user_preferences ADD COLUMN IF NOT EXISTS sensitivity_preference TEXT DEFAULT 'none';
ALTER TABLE public.user_preferences ADD COLUMN IF NOT EXISTS notification_preferences JSONB DEFAULT '{"surge_warnings": true, "daily_morning_brief": true, "threshold_crossing_alerts": true}'::jsonb;
ALTER TABLE public.user_preferences ADD COLUMN IF NOT EXISTS aqi_alert_threshold INTEGER DEFAULT 101;

-- --------------------------------------------------------
-- 3. SAVED LOCATIONS TABLE
-- --------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.saved_locations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    location_name TEXT NOT NULL,
    location_type TEXT DEFAULT 'favourite_place',
    address TEXT,
    latitude DOUBLE PRECISION NOT NULL,
    longitude DOUBLE PRECISION NOT NULL,
    is_primary BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc', now())
);

-- --------------------------------------------------------
-- 4. INDEXES FOR PERFORMANCE
-- --------------------------------------------------------
CREATE INDEX IF NOT EXISTS idx_profiles_lifestyle ON public.profiles(lifestyle_category);
CREATE INDEX IF NOT EXISTS idx_user_preferences_user ON public.user_preferences(user_id);
CREATE INDEX IF NOT EXISTS idx_saved_locations_user ON public.saved_locations(user_id);
CREATE INDEX IF NOT EXISTS idx_saved_locations_primary ON public.saved_locations(user_id, is_primary) WHERE is_primary = TRUE;

-- --------------------------------------------------------
-- 5. AUTOMATIC TIMESTAMP TRIGGER
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
-- 6. AUTOMATIC PROFILE & PREFERENCE CREATION TRIGGER
-- --------------------------------------------------------
CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO public.profiles (
        id, 
        full_name, 
        preferred_language, 
        lifestyle_category,
        onboarding_completed, 
        created_at, 
        updated_at
    )
    VALUES (
        NEW.id,
        COALESCE(NEW.raw_user_meta_data->>'full_name', 'Atmos Citizen'),
        'English',
        'general_public',
        FALSE,
        timezone('utc', now()),
        timezone('utc', now())
    )
    ON CONFLICT (id) DO NOTHING;

    INSERT INTO public.user_preferences (
        id, 
        user_id, 
        activities, 
        outdoor_time, 
        environmental_preferences, 
        sensitivity_preference, 
        notification_preferences, 
        aqi_alert_threshold, 
        created_at, 
        updated_at
    )
    VALUES (
        gen_random_uuid(),
        NEW.id,
        ARRAY['walking', 'commuting']::TEXT[],
        '1_to_3h',
        '["pm25_focus", "deterioration_alerts"]'::jsonb,
        'none',
        '{"surge_warnings": true, "daily_morning_brief": true, "threshold_crossing_alerts": true}'::jsonb,
        101,
        timezone('utc', now()),
        timezone('utc', now())
    )
    ON CONFLICT (user_id) DO NOTHING;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

DROP TRIGGER IF EXISTS on_auth_user_created ON auth.users;
CREATE TRIGGER on_auth_user_created
    AFTER INSERT ON auth.users
    FOR EACH ROW EXECUTE FUNCTION public.handle_new_user();

-- --------------------------------------------------------
-- 7. ROW LEVEL SECURITY (RLS) POLICIES
-- --------------------------------------------------------
ALTER TABLE public.profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.user_preferences ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.saved_locations ENABLE ROW LEVEL SECURITY;

-- Profiles: Users can only read, insert, and update their own record
DROP POLICY IF EXISTS "Users can view own profile" ON public.profiles;
CREATE POLICY "Users can view own profile" 
    ON public.profiles FOR SELECT 
    USING (auth.uid() = id);

DROP POLICY IF EXISTS "Users can insert own profile" ON public.profiles;
CREATE POLICY "Users can insert own profile" 
    ON public.profiles FOR INSERT 
    WITH CHECK (auth.uid() = id);

DROP POLICY IF EXISTS "Users can update own profile" ON public.profiles;
CREATE POLICY "Users can update own profile" 
    ON public.profiles FOR UPDATE 
    USING (auth.uid() = id)
    WITH CHECK (auth.uid() = id);

-- User Preferences: Users can only read, insert, and update their own preferences
DROP POLICY IF EXISTS "Users can view own preferences" ON public.user_preferences;
CREATE POLICY "Users can view own preferences" 
    ON public.user_preferences FOR SELECT 
    USING (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can insert own preferences" ON public.user_preferences;
CREATE POLICY "Users can insert own preferences" 
    ON public.user_preferences FOR INSERT 
    WITH CHECK (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can update own preferences" ON public.user_preferences;
CREATE POLICY "Users can update own preferences" 
    ON public.user_preferences FOR UPDATE 
    USING (auth.uid() = user_id)
    WITH CHECK (auth.uid() = user_id);

-- Saved Locations: Full CRUD strictly scoped to auth.uid()
DROP POLICY IF EXISTS "Users can view own saved locations" ON public.saved_locations;
CREATE POLICY "Users can view own saved locations" 
    ON public.saved_locations FOR SELECT 
    USING (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can insert own saved locations" ON public.saved_locations;
CREATE POLICY "Users can insert own saved locations" 
    ON public.saved_locations FOR INSERT 
    WITH CHECK (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can update own saved locations" ON public.saved_locations;
CREATE POLICY "Users can update own saved locations" 
    ON public.saved_locations FOR UPDATE 
    USING (auth.uid() = user_id)
    WITH CHECK (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can delete own saved locations" ON public.saved_locations;
CREATE POLICY "Users can delete own saved locations" 
    ON public.saved_locations FOR DELETE 
    USING (auth.uid() = user_id);

