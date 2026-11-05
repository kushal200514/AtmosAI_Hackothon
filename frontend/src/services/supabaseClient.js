/**
 * AtmosAI Supabase Client Configuration
 * Manages Supabase Auth and Database connection using client-safe publishable credentials.
 * Never exposes the Supabase service-role key in frontend bundles.
 */

import { createClient } from '@supabase/supabase-js';

const supabaseUrl = import.meta.env.VITE_SUPABASE_URL;
// Supports both VITE_SUPABASE_PUBLISHABLE_KEY and legacy VITE_SUPABASE_ANON_KEY
const supabaseKey = import.meta.env.VITE_SUPABASE_PUBLISHABLE_KEY || import.meta.env.VITE_SUPABASE_ANON_KEY;

export function isSupabaseConfigured() {
  return Boolean(
    supabaseUrl && 
    supabaseKey && 
    !supabaseUrl.includes('your-project') &&
    supabaseKey !== 'your-supabase-anon-or-publishable-key'
  );
}

export function getSupabaseConfig() {
  return {
    url: supabaseUrl || null,
    isConfigured: isSupabaseConfigured()
  };
}

export const supabase = isSupabaseConfigured()
  ? createClient(supabaseUrl, supabaseKey, {
      auth: {
        autoRefreshToken: true,
        persistSession: true,
        detectSessionInUrl: true,
        storage: window.localStorage
      }
    })
  : null;

export default supabase;

