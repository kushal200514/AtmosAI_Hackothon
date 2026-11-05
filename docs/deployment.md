# AtmosAI Deployment Guide (Render & Supabase)

This document details the production deployment process for the AtmosAI platform using **Render** and **Supabase**.

---

## 1. Prerequisites
- GitHub repository containing this project.
- Render account ([render.com](https://render.com)).
- Supabase project ([supabase.com](https://supabase.com)).
- Google Gemini API key ([aistudio.google.com](https://aistudio.google.com)).

---

## 2. Supabase Database Setup
1. Create a new Supabase project.
2. Open the **SQL Editor** in the Supabase Dashboard.
3. Paste the contents of `supabase/migrations/20261105000001_initial_schema.sql` and execute the migration.
4. Verify that the 8 tables and Row Level Security (RLS) policies are active.
5. In **Project Settings > API**, copy:
   - Project URL (`SUPABASE_URL`)
   - Anon Public Key (`SUPABASE_KEY`)
   - Service Role Secret (`SUPABASE_SERVICE_ROLE_KEY`)

---

## 3. Render Deployment via Blueprint (`render.yaml`)

AtmosAI includes a native `render.yaml` blueprint configuration in the repository root.

1. In the Render Dashboard, click **New > Blueprint**.
2. Connect your AtmosAI GitHub repository.
3. Render will automatically detect the blueprint and configure:
   - **`atmosai-backend`**: Python Web Service running FastAPI.
   - **`atmosai-frontend`**: Static Site building React 19 with Vite.
4. Under Environment Variables for `atmosai-backend`, populate:
   - `GEMINI_API_KEY`: Your Google Gemini API key.
   - `SUPABASE_URL`: Your Supabase project URL.
   - `SUPABASE_KEY`: Your Supabase anon key.
   - `SUPABASE_SERVICE_ROLE_KEY`: Your Supabase service key.
5. Click **Apply**. Render will automatically build and deploy both services.

---

## 4. Production Verification Checklist

1. **Backend Health Check**:
   ```bash
   curl -s https://atmosai-backend.onrender.com/health
   ```
   Should return `{"status": "healthy", ...}`.

2. **Frontend Loading**:
   Open `https://atmosai-frontend.onrender.com`. Verify the responsive dashboard, Leaflet map, and LightGBM forecast charts.

3. **PWA Installability**:
   Open in Google Chrome or mobile Safari. Verify that the install banner appears and the Service Worker registers with offline precache.

