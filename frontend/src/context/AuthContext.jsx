import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { supabase, isSupabaseConfigured, getSupabaseConfig } from '../services/supabaseClient';
import { authService } from '../services/authService';
import { profileService } from '../services/profileService';
import { fetchAuthStatus, fetchUserProfile } from '../services/api';

export const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [session, setSession] = useState(null);
  const [profile, setProfile] = useState(null);
  const [preferences, setPreferences] = useState(null);
  const [personalization, setPersonalization] = useState(null);
  const [loading, setLoading] = useState(true);
  const [authMode, setAuthMode] = useState(isSupabaseConfigured() ? 'supabase' : 'demo');
  const [authDisclaimer, setAuthDisclaimer] = useState(
    isSupabaseConfigured()
      ? null
      : 'DEMO AUTHENTICATION MODE — Simulated secure session for demonstration. Supabase credentials are not configured in environment.'
  );

  const loadUserData = useCallback(async (authUser, authSession) => {
    try {
      setUser(authUser);
      setSession(authSession || null);

      const userId = authUser.id;
      // 1. Fetch profile from Supabase profiles (or FastAPI fallback)
      const prof = await profileService.getProfile(userId);
      // 2. Fetch preferences
      const prefs = await profileService.getPreferences(userId);
      // 3. Fetch personalization rules from FastAPI
      const fastApiData = await fetchUserProfile(userId).catch(() => null);

      if (prof) {
        setProfile(prof);
      } else {
        // Default initialized profile
        setProfile({
          id: userId,
          full_name: authUser.user_metadata?.full_name || authUser.full_name || 'Atmos Citizen',
          email: authUser.email,
          onboarding_completed: authUser.onboarding_completed ?? false,
          lifestyle_category: 'general_public'
        });
      }

      setPreferences(prefs);
      if (fastApiData?.personalization) {
        setPersonalization(fastApiData.personalization);
      }
    } catch (err) {
      console.warn('Error loading user profile & preferences:', err);
    }
  }, []);

  // Initialize Auth state on mount
  useEffect(() => {
    async function initAuth() {
      try {
        // Handshake with backend to inspect server auth config
        const status = await fetchAuthStatus().catch(() => null);
        if (status && status.mode) {
          setAuthMode(status.mode);
          if (status.disclaimer) setAuthDisclaimer(status.disclaimer);
        }

        // Get active session from authService (Supabase or stored demo)
        const activeSession = await authService.getSession();
        if (activeSession?.user) {
          await loadUserData(activeSession.user, activeSession);
        }
      } catch (err) {
        console.error('Auth initialization error:', err);
      } finally {
        setLoading(false);
      }
    }

    initAuth();

    // Listen to real-time Supabase auth state changes
    const unsubscribe = authService.onAuthStateChange(async (event, newSession) => {
      if (event === 'SIGNED_IN' || event === 'TOKEN_REFRESHED' || event === 'USER_UPDATED') {
        if (newSession?.user) {
          await loadUserData(newSession.user, newSession);
        }
      } else if (event === 'SIGNED_OUT') {
        setUser(null);
        setSession(null);
        setProfile(null);
        setPreferences(null);
        setPersonalization(null);
      }
    });

    return () => unsubscribe();
  }, [loadUserData]);

  // Sign up action
  const signUp = async ({ email, password, fullName }) => {
    const result = await authService.signUp({ email, password, fullName });
    if (result.user) {
      await loadUserData(result.user, result.session);
    }
    return result;
  };

  // Sign in action
  const signIn = async ({ email, password, rememberMe = true }) => {
    const result = await authService.signIn({ email, password, rememberMe });
    if (result.user) {
      await loadUserData(result.user, result.session);
    }
    return result.user;
  };

  // Sign out action
  const signOut = async () => {
    await authService.signOut();
    setUser(null);
    setSession(null);
    setProfile(null);
    setPreferences(null);
    setPersonalization(null);
  };

  // Password reset
  const resetPassword = async (email) => {
    return authService.resetPassword(email);
  };

  // Update profile
  const updateProfileData = async (updates) => {
    if (!user) return;
    const userId = user.id;
    const updated = await profileService.updateProfile(userId, updates);
    if (updated) {
      setProfile(prev => ({ ...prev, ...updated }));
    }
    // Refresh personalization rules
    const fastApiData = await fetchUserProfile(userId).catch(() => null);
    if (fastApiData?.personalization) {
      setPersonalization(fastApiData.personalization);
    }
    return updated;
  };

  // Complete onboarding save (updating profiles, preferences, and saved locations)
  const saveOnboarding = async (payload) => {
    if (!user) return;
    const userId = user.id;
    const result = await profileService.saveOnboardingData(userId, payload);
    if (result.profile) {
      setProfile(result.profile);
    }
    if (result.personalization) {
      setPersonalization(result.personalization);
    }
    // Update local user onboarding_completed flag
    setUser(prev => ({
      ...prev,
      onboarding_completed: true
    }));
    return result;
  };

  return (
    <AuthContext.Provider value={{
      user,
      session,
      profile,
      preferences,
      personalization,
      loading,
      authMode,
      authDisclaimer,
      isConfigured: isSupabaseConfigured(),
      signUp,
      signIn,
      signOut,
      resetPassword,
      updateProfileData,
      saveOnboarding,
      refreshProfile: () => user && loadUserData(user, session)
    }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}

export default AuthContext;
