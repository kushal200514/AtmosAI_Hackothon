/**
 * AtmosAI Profile & User Preferences Service
 * Directly interacts with Supabase PostgreSQL tables protected by Row Level Security (RLS).
 * Falls back to FastAPI backend when Supabase is not configured.
 */

import { supabase, isSupabaseConfigured } from './supabaseClient';
import { fetchUserProfile, updateUserProfile, createSavedLocation, fetchSavedLocations } from './api';

export const profileService = {
  /**
   * Fetches user profile from Supabase profiles table.
   */
  async getProfile(userId) {
    if (isSupabaseConfigured() && supabase) {
      const { data, error } = await supabase
        .from('profiles')
        .select('*')
        .eq('id', userId)
        .maybeSingle();

      if (error) {
        console.warn('Supabase profile fetch error:', error.message);
      }
      if (data) return data;
    }

    // Fallback to FastAPI backend
    const res = await fetchUserProfile(userId).catch(() => null);
    return res?.profile || null;
  },

  /**
   * Updates user profile in Supabase profiles table.
   */
  async updateProfile(userId, updates) {
    if (isSupabaseConfigured() && supabase) {
      const { data, error } = await supabase
        .from('profiles')
        .update({
          ...updates,
          updated_at: new Date().toISOString()
        })
        .eq('id', userId)
        .select()
        .single();

      if (error) throw error;
      // Also sync to FastAPI backend in background
      updateUserProfile(updates, userId).catch(() => {});
      return data;
    }

    const res = await updateUserProfile(updates, userId);
    return res?.profile || null;
  },

  /**
   * Fetches user preferences from Supabase user_preferences table.
   */
  async getPreferences(userId) {
    if (isSupabaseConfigured() && supabase) {
      const { data, error } = await supabase
        .from('user_preferences')
        .select('*')
        .eq('user_id', userId)
        .maybeSingle();

      if (error) console.warn('Supabase preferences fetch error:', error.message);
      if (data) return data;
    }
    return null;
  },

  /**
   * Updates or upserts user preferences in Supabase user_preferences table.
   */
  async updatePreferences(userId, prefs) {
    if (isSupabaseConfigured() && supabase) {
      const { data, error } = await supabase
        .from('user_preferences')
        .upsert({
          user_id: userId,
          ...prefs,
          updated_at: new Date().toISOString()
        }, { onConflict: 'user_id' })
        .select()
        .single();

      if (error) throw error;
      return data;
    }
    return prefs;
  },

  /**
   * Fetches saved locations for the user.
   */
  async getSavedLocations(userId) {
    if (isSupabaseConfigured() && supabase) {
      const { data, error } = await supabase
        .from('saved_locations')
        .select('*')
        .eq('user_id', userId)
        .order('is_primary', { ascending: false });

      if (error) console.warn('Supabase saved_locations fetch error:', error.message);
      if (data && data.length > 0) return data;
    }

    return fetchSavedLocations(userId, true).catch(() => []);
  },

  /**
   * Adds a new saved location.
   */
  async addSavedLocation(userId, location) {
    if (isSupabaseConfigured() && supabase) {
      // If setting as primary, clear any existing primary
      if (location.is_primary) {
        await supabase
          .from('saved_locations')
          .update({ is_primary: false })
          .eq('user_id', userId);
      }

      const { data, error } = await supabase
        .from('saved_locations')
        .insert([{
          user_id: userId,
          location_name: location.location_name,
          location_type: location.location_type || 'favourite_place',
          address: location.address || null,
          latitude: location.latitude,
          longitude: location.longitude,
          is_primary: Boolean(location.is_primary)
        }])
        .select()
        .single();

      if (error) throw error;
      return data;
    }

    return createSavedLocation(location, userId);
  },

  /**
   * Saves complete onboarding data into Supabase (profiles, preferences, saved_locations).
   */
  async saveOnboardingData(userId, payload) {
    const {
      full_name,
      age_group,
      city,
      locality,
      preferred_language,
      lifestyle_category,
      activities,
      outdoor_time,
      environmental_preferences,
      sensitivity_preference,
      notifications,
      aqi_alert_threshold,
      primary_location,
      onboarding_completed = true,
      onboarding_step = 5
    } = payload;

    // 1. Update Profiles table
    const profileUpdates = {
      full_name,
      age_group,
      city,
      locality,
      preferred_language,
      lifestyle_category,
      onboarding_completed,
      updated_at: new Date().toISOString()
    };

    let updatedProfile = null;
    if (isSupabaseConfigured() && supabase) {
      const { data, error } = await supabase
        .from('profiles')
        .upsert({
          id: userId,
          ...profileUpdates
        })
        .select()
        .single();

      if (error) console.error('Failed to update Supabase profile:', error.message);
      else updatedProfile = data;

      // 2. Upsert user_preferences table
      const { error: prefError } = await supabase
        .from('user_preferences')
        .upsert({
          user_id: userId,
          activities: activities || ['walking', 'commuting'],
          outdoor_time: outdoor_time || '1_to_3h',
          environmental_preferences: environmental_preferences || ['pm25_focus', 'deterioration_alerts'],
          sensitivity_preference: sensitivity_preference || 'none',
          notification_preferences: notifications || {},
          aqi_alert_threshold: aqi_alert_threshold || 101,
          updated_at: new Date().toISOString()
        }, { onConflict: 'user_id' });

      if (prefError) console.error('Failed to update Supabase preferences:', prefError.message);

      // 3. Insert primary location if supplied
      if (primary_location) {
        // Look up default coordinates for primary location
        const coordsMap = {
          bengaluru_central: { lat: 12.9716, lon: 77.5946, name: 'Bengaluru Central' },
          silk_board: { lat: 12.9177, lon: 77.6238, name: 'Central Silk Board' },
          electronic_city: { lat: 12.8452, lon: 77.6602, name: 'Electronic City' },
          hebbal: { lat: 13.0358, lon: 77.5970, name: 'Hebbal Flyover' },
          koramangala: { lat: 12.9352, lon: 77.6245, name: 'Koramangala' },
          peenya: { lat: 13.0285, lon: 77.5197, name: 'Peenya Industrial Area' },
          yelahanka: { lat: 13.1007, lon: 77.5963, name: 'Yelahanka' }
        };
        const locInfo = coordsMap[primary_location] || { lat: 12.9716, lon: 77.5946, name: primary_location };

        await this.addSavedLocation(userId, {
          location_name: locInfo.name,
          location_type: 'home',
          latitude: locInfo.lat,
          longitude: locInfo.lon,
          is_primary: true
        }).catch(() => {});
      }
    }

    // Always synchronize with FastAPI backend to resolve dynamic personalization rules
    const fastApiPayload = {
      full_name,
      age_group,
      city,
      locality,
      preferred_language,
      user_category: lifestyle_category,
      preferred_activities: activities,
      outdoor_time_duration: outdoor_time,
      environmental_info_preferences: environmental_preferences,
      sensitivity_preference,
      notifications,
      primary_location,
      onboarding_completed,
      onboarding_step
    };

    const backendRes = await updateUserProfile(fastApiPayload, userId).catch(() => null);

    return {
      profile: updatedProfile || backendRes?.profile,
      personalization: backendRes?.personalization
    };
  }
};

export default profileService;

