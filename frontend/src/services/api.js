/**
 * AtmosAI Frontend API Client
 * Centralized service layer communicating with the FastAPI backend
 */

import { supabase, isSupabaseConfigured } from './supabaseClient';

const API_BASE = '/api';

async function getAuthHeaders() {
  const headers = {};
  try {
    if (isSupabaseConfigured() && supabase) {
      const { data: { session } } = await supabase.auth.getSession();
      if (session?.access_token) {
        headers['Authorization'] = `Bearer ${session.access_token}`;
      }
    } else {
      const stored = localStorage.getItem('atmosai_active_session') || sessionStorage.getItem('atmosai_active_session');
      if (stored) {
        const u = JSON.parse(stored);
        if (u?.id) headers['Authorization'] = `Bearer demo_token_${u.id}`;
      }
    }
  } catch {}
  return headers;
}

export async function fetchAuthStatus() {
  const res = await fetch(`${API_BASE}/auth/status`);
  if (!res.ok) throw new Error('Failed to fetch auth status');
  return res.json();
}

export async function apiLogin(credentials) {
  const res = await fetch(`${API_BASE}/auth/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(credentials)
  });
  if (!res.ok) throw new Error('Failed to log in');
  return res.json();
}

export async function apiSignup(userData) {
  const res = await fetch(`${API_BASE}/auth/signup`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(userData)
  });
  if (!res.ok) throw new Error('Failed to sign up');
  return res.json();
}

export async function fetchLocations() {
  const res = await fetch(`${API_BASE}/locations?scope=stations`);
  if (!res.ok) throw new Error('Failed to fetch stations');
  return res.json();
}

export async function fetchSavedLocations(userId = 'default_user', includeAirQuality = true) {
  const res = await fetch(`${API_BASE}/locations?user_id=${encodeURIComponent(userId)}&include_air_quality=${includeAirQuality}`);
  if (!res.ok) throw new Error('Failed to fetch saved locations');
  return res.json();
}

export async function searchLocations(query) {
  const res = await fetch(`${API_BASE}/locations/search?q=${encodeURIComponent(query)}`);
  if (!res.ok) throw new Error('Failed to search locations');
  return res.json();
}

export async function createSavedLocation(locationData, userId = 'default_user') {
  const res = await fetch(`${API_BASE}/locations?user_id=${encodeURIComponent(userId)}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(locationData)
  });
  if (!res.ok) throw new Error('Failed to save location');
  return res.json();
}

export async function updateSavedLocation(locationId, updateData, userId = 'default_user') {
  const res = await fetch(`${API_BASE}/locations/${encodeURIComponent(locationId)}?user_id=${encodeURIComponent(userId)}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(updateData)
  });
  if (!res.ok) throw new Error('Failed to update saved location');
  return res.json();
}

export async function deleteSavedLocation(locationId, userId = 'default_user') {
  const res = await fetch(`${API_BASE}/locations/${encodeURIComponent(locationId)}?user_id=${encodeURIComponent(userId)}`, {
    method: 'DELETE'
  });
  if (!res.ok) throw new Error('Failed to delete saved location');
  return res.json();
}

export async function fetchSavedLocationAirQuality(locationId, userId = 'default_user') {
  const res = await fetch(`${API_BASE}/locations/${encodeURIComponent(locationId)}/air-quality?user_id=${encodeURIComponent(userId)}`);
  if (!res.ok) throw new Error('Failed to fetch saved location air quality');
  return res.json();
}

export async function fetchLiveForecast(location = 'bengaluru_central') {
  const res = await fetch(`${API_BASE}/forecast/live?location=${encodeURIComponent(location)}`);
  if (!res.ok) throw new Error('Failed to fetch live environmental data');
  return res.json();
}

export async function fetchMLPrediction(location = 'bengaluru_central') {
  const res = await fetch(`${API_BASE}/forecast/predict?location=${encodeURIComponent(location)}`);
  if (!res.ok) throw new Error('Failed to fetch ML forecast');
  return res.json();
}

export async function fetchAIAdvice(location = 'bengaluru_central', profile = 'runner', userId = 'default_user') {
  const res = await fetch(`${API_BASE}/advice?location=${encodeURIComponent(location)}&profile=${encodeURIComponent(profile)}&user_id=${encodeURIComponent(userId)}`);
  if (!res.ok) throw new Error('Failed to fetch AI advice');
  return res.json();
}

export async function fetchMapData() {
  const res = await fetch(`${API_BASE}/map/data`);
  if (!res.ok) throw new Error('Failed to fetch map data');
  return res.json();
}

export async function fetchAlerts(profile = 'runner', userId = 'default_user') {
  const res = await fetch(`${API_BASE}/alerts?profile=${encodeURIComponent(profile)}&user_id=${encodeURIComponent(userId)}`);
  if (!res.ok) throw new Error('Failed to fetch alerts');
  return res.json();
}

export async function calculateTravelExposure(origin, destination, mode = 'commute') {
  const res = await fetch(`${API_BASE}/travel/exposure`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ origin, destination, mode })
  });
  if (!res.ok) throw new Error('Failed to compute travel exposure');
  return res.json();
}

export async function postTelemetry(telemetry) {
  const res = await fetch(`${API_BASE}/telemetry`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(telemetry)
  });
  if (!res.ok) throw new Error('Failed to send telemetry');
  return res.json();
}

export async function fetchUserProfile(userId = 'default_user') {
  const authHeaders = await getAuthHeaders();
  const res = await fetch(`${API_BASE}/user/profile?user_id=${encodeURIComponent(userId)}`, {
    headers: { ...authHeaders }
  });
  if (!res.ok) throw new Error('Failed to fetch user profile');
  return res.json();
}

export async function updateUserProfile(profileUpdate, userId = 'default_user') {
  const authHeaders = await getAuthHeaders();
  const res = await fetch(`${API_BASE}/user/profile?user_id=${encodeURIComponent(userId)}`, {
    method: 'POST',
    headers: { 
      'Content-Type': 'application/json',
      ...authHeaders 
    },
    body: JSON.stringify(profileUpdate)
  });
  if (!res.ok) throw new Error('Failed to update profile');
  return res.json();
}

export async function fetchActivityPlanner(location = 'bengaluru_central', userId = 'default_user') {
  const res = await fetch(`${API_BASE}/planner?location=${encodeURIComponent(location)}&user_id=${encodeURIComponent(userId)}`);
  if (!res.ok) throw new Error('Failed to fetch activity planner');
  return res.json();
}

export async function fetchNotificationSettings(userId = 'default_user') {
  const res = await fetch(`${API_BASE}/notifications/settings?user_id=${encodeURIComponent(userId)}`);
  if (!res.ok) throw new Error('Failed to fetch notification settings');
  return res.json();
}

export async function updateNotificationSettings(settings, userId = 'default_user') {
  const res = await fetch(`${API_BASE}/notifications/settings?user_id=${encodeURIComponent(userId)}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(settings)
  });
  if (!res.ok) throw new Error('Failed to update notification settings');
  return res.json();
}

export async function fetchCPCBRecommendations(userId = 'default_user') {
  const res = await fetch(`${API_BASE}/notifications/recommendations?user_id=${encodeURIComponent(userId)}`);
  if (!res.ok) throw new Error('Failed to fetch CPCB recommendations');
  return res.json();
}

export async function fetchForecastAccuracy(location = 'bengaluru_central', horizon = 3, range = 'all', mode = 'real') {
  const res = await fetch(`${API_BASE}/forecast/accuracy?location=${encodeURIComponent(location)}&horizon=${encodeURIComponent(horizon)}&range=${encodeURIComponent(range)}&mode=${encodeURIComponent(mode)}`);
  if (!res.ok) throw new Error('Failed to fetch forecast accuracy metrics');
  return res.json();
}

export async function fetchForecastHistory(location = 'bengaluru_central', horizon = null, limit = 50, mode = 'real') {
  let url = `${API_BASE}/forecast/history?location=${encodeURIComponent(location)}&limit=${encodeURIComponent(limit)}&mode=${encodeURIComponent(mode)}`;
  if (horizon !== null && horizon !== undefined) {
    url += `&horizon=${encodeURIComponent(horizon)}`;
  }
  const res = await fetch(url);
  if (!res.ok) throw new Error('Failed to fetch forecast history');
  return res.json();
}

export async function fetchEvaluationDemoData(horizon = null, limit = 168) {
  let url = `${API_BASE}/evaluation/demo-data?limit=${encodeURIComponent(limit)}`;
  if (horizon !== null && horizon !== undefined) {
    url += `&horizon=${encodeURIComponent(horizon)}`;
  }
  const res = await fetch(url);
  if (!res.ok) throw new Error('Failed to fetch evaluation demo data');
  return res.json();
}

export async function fetchEvaluationMetrics(horizon = 3, range = 'all', mode = 'demo', location = 'bengaluru_central') {
  const res = await fetch(`${API_BASE}/evaluation/metrics?horizon=${encodeURIComponent(horizon)}&range=${encodeURIComponent(range)}&mode=${encodeURIComponent(mode)}&location=${encodeURIComponent(location)}`);
  if (!res.ok) throw new Error('Failed to fetch evaluation metrics');
  return res.json();
}

export async function fetchMapGrid() {
  const res = await fetch(`${API_BASE}/map/grid`);
  if (!res.ok) throw new Error('Failed to fetch atmospheric forecast grid');
  return res.json();
}

export async function fetchMapStationMarkers() {
  const res = await fetch(`${API_BASE}/map/stations`);
  if (!res.ok) throw new Error('Failed to fetch monitoring station markers');
  return res.json();
}

export async function fetchTravelRoutePollution(origin, destination, mode = 'driving') {
  const res = await fetch(`${API_BASE}/map/route`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ origin, destination, mode })
  });
  if (!res.ok) throw new Error('Failed to calculate travel route pollution');
  return res.json();
}
