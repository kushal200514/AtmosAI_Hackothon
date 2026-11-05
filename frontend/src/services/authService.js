/**
 * AtmosAI Authentication Service
 * Interfaces with Supabase Auth for identity management, session tokens, and password operations.
 */

import { supabase, isSupabaseConfigured } from './supabaseClient';
import { apiLogin, apiSignup } from './api';

const DEMO_STORAGE_KEY = 'atmosai_active_session';

export const authService = {
  isConfigured() {
    return isSupabaseConfigured();
  },

  /**
   * Registers a new user with Supabase Auth.
   * Attaches full_name in user metadata so the database trigger on_auth_user_created
   * can populate public.profiles automatically.
   */
  async signUp({ email, password, fullName }) {
    const cleanEmail = email.trim().toLowerCase();

    if (isSupabaseConfigured() && supabase) {
      const { data, error } = await supabase.auth.signUp({
        email: cleanEmail,
        password,
        options: {
          data: {
            full_name: fullName
          }
        }
      });
      if (error) throw error;
      return {
        user: data.user,
        session: data.session,
        needsEmailVerification: !data.session && Boolean(data.user)
      };
    }

    // Demo Mode fallback for development without Supabase credentials
    const res = await apiSignup({
      email: cleanEmail,
      password,
      full_name: fullName
    });

    const demoUser = {
      id: res.user_id,
      email: cleanEmail,
      user_metadata: { full_name: fullName },
      full_name: fullName,
      onboarding_completed: false,
      onboarding_step: 1
    };

    localStorage.setItem(DEMO_STORAGE_KEY, JSON.stringify(demoUser));
    return {
      user: demoUser,
      session: { access_token: `demo_token_${demoUser.id}`, user: demoUser },
      needsEmailVerification: false
    };
  },

  /**
   * Signs in an existing user with Supabase Auth.
   */
  async signIn({ email, password, rememberMe = true }) {
    const cleanEmail = email.trim().toLowerCase();

    if (isSupabaseConfigured() && supabase) {
      const { data, error } = await supabase.auth.signInWithPassword({
        email: cleanEmail,
        password
      });
      if (error) throw error;
      return {
        user: data.user,
        session: data.session
      };
    }

    // Demo Mode fallback
    const res = await apiLogin({
      email: cleanEmail,
      password,
      remember_me: rememberMe
    });

    const demoUser = {
      id: res.user_id,
      email: res.user.email,
      user_metadata: { full_name: res.user.full_name },
      full_name: res.user.full_name,
      onboarding_completed: res.onboarding_completed,
      onboarding_step: res.user.onboarding_step
    };

    if (rememberMe) {
      localStorage.setItem(DEMO_STORAGE_KEY, JSON.stringify(demoUser));
      sessionStorage.removeItem(DEMO_STORAGE_KEY);
    } else {
      sessionStorage.setItem(DEMO_STORAGE_KEY, JSON.stringify(demoUser));
      localStorage.removeItem(DEMO_STORAGE_KEY);
    }

    return {
      user: demoUser,
      session: { access_token: `demo_token_${demoUser.id}`, user: demoUser }
    };
  },

  /**
   * Signs out the current user and clears active sessions.
   */
  async signOut() {
    if (isSupabaseConfigured() && supabase) {
      const { error } = await supabase.auth.signOut();
      if (error) console.warn('Supabase signOut notice:', error.message);
    }
    localStorage.removeItem(DEMO_STORAGE_KEY);
    sessionStorage.removeItem(DEMO_STORAGE_KEY);
  },

  /**
   * Fetches the current authenticated session.
   */
  async getSession() {
    if (isSupabaseConfigured() && supabase) {
      const { data, error } = await supabase.auth.getSession();
      if (error) {
        console.warn('Error fetching Supabase session:', error.message);
        return null;
      }
      return data.session;
    }

    const stored = localStorage.getItem(DEMO_STORAGE_KEY) || sessionStorage.getItem(DEMO_STORAGE_KEY);
    if (stored) {
      const user = JSON.parse(stored);
      return { access_token: `demo_token_${user.id}`, user };
    }
    return null;
  },

  /**
   * Fetches the current user.
   */
  async getUser() {
    const session = await this.getSession();
    return session?.user || null;
  },

  /**
   * Dispatches a password reset email via Supabase.
   */
  async resetPassword(email) {
    if (isSupabaseConfigured() && supabase) {
      const { error } = await supabase.auth.resetPasswordForEmail(email.trim().toLowerCase(), {
        redirectTo: `${window.location.origin}/settings`
      });
      if (error) throw error;
      return { success: true, message: 'Password reset link sent to your email.' };
    }

    return {
      success: true,
      message: `DEMO MODE: Password reset link simulated for ${email}.`
    };
  },

  /**
   * Subscribes to auth state changes.
   */
  onAuthStateChange(callback) {
    if (isSupabaseConfigured() && supabase) {
      const { data: { subscription } } = supabase.auth.onAuthStateChange(callback);
      return () => subscription.unsubscribe();
    }
    return () => {};
  }
};

export default authService;

