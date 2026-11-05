import json
import logging
from typing import Dict, Any
from datetime import datetime, timezone

from app.services.ai.base import BaseAIProvider
from app.services.ai.fallback_provider import rule_fallback_provider
from app.schemas.ai import PersonalizedRiskAdvisorResponse, ActivityGuidance
from app.core.config import settings

logger = logging.getLogger("atmosai.gemini")

SYSTEM_INSTRUCTION = """
You are AtmosAI, an expert environmental intelligence and pollution risk reduction assistant for Bengaluru, India.
Explain air quality conditions and provide tailored, evidence-based recommendations based strictly on structured environmental data.

STRICT CONSTRAINTS:
1. Explain available evidence rather than inventing conditions or measurements.
2. Conservative and strictly non-medical: never diagnose diseases or claim wearable heart-rate readings prove pollution damage.
3. Tailor practical activity recommendations to the specific user profile and preferred activities provided:
   - STUDENT: Prioritize campus conditions, shaded pathways, study/sports timing.
   - RUNNER: Prioritize workout-time forecasts, aerobic exertion, morning/evening windows.
   - OFFICE COMMUTER: Prioritize commute-time pollution information, vehicle AC recirculation, congestion points.
   - OUTDOOR WORKER: Prioritize current conditions, continuous street exposure, hydration, rest breaks, N95 masks.
   - PARENT: Prioritize family outdoor activity information, playground/stroller conditions, midday dispersion windows.
   - GENERAL PUBLIC: Prioritize overall air-quality information, daily trends, home ventilation.
4. If cautious_mode is true, adopt more cautious, safety-first wording and highlight protective measures.
5. Respect the preferred language (English: 'en', Hindi: 'hi', Kannada: 'kn').
6. Output valid JSON strictly conforming to the requested schema.
"""

class GeminiProvider(BaseAIProvider):
    def __init__(self):
        self.api_key = settings.GEMINI_API_KEY
        self.model_name = settings.GEMINI_MODEL
        self._client = None
        self._init_client()

    def _init_client(self):
        if self.api_key and "your-gemini" not in self.api_key:
            try:
                from google import genai
                self._client = genai.Client(api_key=self.api_key)
                logger.info(f"Initialized Google GenAI Client with model {self.model_name}")
            except Exception as e:
                logger.warning(f"Could not initialize Google GenAI Client: {e}")
                self._client = None

    @property
    def provider_name(self) -> str:
        return "Google Gemini 2.5 Flash"

    async def generate_advice(self, context: Dict[str, Any]) -> PersonalizedRiskAdvisorResponse:
        if not self._client:
            logger.info("Gemini API key unconfigured; routing through AtmosAI Personalized Risk Engine.")
            return await rule_fallback_provider.generate_advice(context)

        live = context["live"]
        forecast = context["forecast"]
        raw_pt = context.get("profile_type")
        raw_cat = context.get("user_category")
        pt_str = str(raw_pt.value if hasattr(raw_pt, "value") else (raw_pt or "")).lower()
        cat_str = str(raw_cat.value if hasattr(raw_cat, "value") else (raw_cat or "")).lower()
        active_persona = pt_str or cat_str or "general_public"

        lang: str = context.get("preferred_language", "en")
        cautious_mode: bool = context.get("cautious_mode", False) or (active_persona == "respiratory_sensitive")
        activities = context.get("preferred_activities", ["walking", "outdoor_commute"])
        outdoor_time = context.get("outdoor_time_duration", "1-2 hours")
        sens_pref = context.get("sensitivity_preference", "none")

        pm25 = live.pm25 if live.pm25 is not None else 25.0
        aqi = live.aqi if live.aqi is not None else 45
        aqi_cat = live.aqi_category or "Satisfactory"

        # Determine deterioration
        forecast_points = forecast.forecast_points if forecast else []
        is_deteriorating = False
        trend = "stable"
        if forecast_points:
            delta = forecast_points[-1].predicted_pm25 - pm25
            if delta > 3.0 or (forecast and forecast.surge_detected):
                is_deteriorating = True
                trend = "rising"
            elif delta < -3.0:
                trend = "improving"

        prompt = f"""
Location: {live.display_name} (Coordinates: {live.latitude}, {live.longitude})
Current PM2.5: {pm25} ug/m3
Current Indian AQI: {aqi} ({aqi_cat}, Risk Level: {live.risk_level})
Weather: Temperature={live.weather.temperature_c if live.weather else 24}°C, Humidity={live.weather.relative_humidity_pct if live.weather else 70}%, Wind={live.weather.wind_speed_kmh if live.weather else 8} km/h
ML Forecast Points (LightGBM):
{[f"+{p.horizon_hours}h: {p.predicted_pm25} ug/m3 ({p.trend}, risk={p.risk_level})" for p in forecast_points]}
Primary Driving Factors: {forecast.primary_driving_factors if forecast else []}
Surge Warning: {forecast.surge_detected if forecast else False}
User Persona: {active_persona}
Preferred Activities: {activities}
Outdoor Time: {outdoor_time}
Sensitivity Preference: {sens_pref}
Target Language: {lang}
Cautious Mode: {cautious_mode}

Generate a structured environmental explanation and persona-tailored guidance in JSON with keys:
- current_environmental_status: string (concise status sentence)
- recommended_action: string (single most actionable directive for the persona)
- headline_summary: string (in target language)
- evidence_based_explanation: string (in target language explaining physical factors)
- profile_specific_recommendations: list of 2-3 specific actionable strings
- outdoor_exercise_allowed: boolean
- best_time_window: string
- recommended_duration_minutes: integer
- mask_recommendation: string
- indoor_ventilation_advice: string
"""

        try:
            from google.genai import types
            response = self._client.models.generate_content(
                model=self.model_name,
                contents=prompt,
                config=types.GenerateContentConfig(
                    system_instruction=SYSTEM_INSTRUCTION,
                    response_mime_type="application/json",
                    temperature=0.2
                )
            )

            data = json.loads(response.text)
            activity = ActivityGuidance(
                outdoor_exercise_allowed=data.get("outdoor_exercise_allowed", True),
                best_time_window=data.get("best_time_window", "Early morning"),
                recommended_duration_minutes=data.get("recommended_duration_minutes", 45),
                mask_recommendation=data.get("mask_recommendation", "Optional"),
                indoor_ventilation_advice=data.get("indoor_ventilation_advice", "Ventilate during midday hours")
            )

            out_type = raw_pt if raw_pt is not None else active_persona
            now_iso = datetime.now(timezone.utc).isoformat()

            confidence = (
                "HIGH (Verified Ground Telemetry + Validated Model)"
                if getattr(live, "measurement_type", "") in ("measured", "MEASURED")
                else "MEDIUM (Regional Atmospheric Chemistry Model)"
            )

            return PersonalizedRiskAdvisorResponse(
                user_category=str(raw_cat.value if hasattr(raw_cat, "value") else (raw_cat or active_persona)),
                profile_type=str(out_type.value if hasattr(out_type, "value") else out_type),
                location_name=live.location_name,
                display_name=live.display_name,
                timestamp_iso=getattr(live, "observation_time_iso", None) or now_iso,
                current_environmental_status=data.get("current_environmental_status", f"Current air quality is {aqi_cat} (AQI {aqi}) in {live.display_name}."),
                current_aqi=aqi,
                current_pm25=pm25,
                aqi_category=aqi_cat,
                potential_forecast_deterioration=is_deteriorating,
                deterioration_details=f"Conditions projected to {'deteriorate' if is_deteriorating else 'remain stable or improve'} over the next 3–6 hours.",
                recommended_action=data.get("recommended_action", "Check 3–6 hour forecast before prolonged outdoor activities."),
                explanation=data.get("evidence_based_explanation", "Analysis based on multi-horizon forecast and live telemetry."),
                data_source=f"{getattr(live, 'data_source', 'CPCB Ground Station')} & LightGBM Multi-Horizon Predictor",
                confidence_status=confidence,
                headline_summary=data.get("headline_summary", "Air quality report generated."),
                evidence_based_explanation=data.get("evidence_based_explanation", "Analysis based on live observations."),
                profile_specific_recommendations=data.get("profile_specific_recommendations", []),
                activity_guidance=activity,
                environmental_drivers_cited=forecast.primary_driving_factors if forecast else ["Local meteorological conditions"],
                ai_provider=self.provider_name,
                preferred_activities=activities,
                outdoor_time_context=outdoor_time,
                sensitivity_preference=str(sens_pref),
                forecast_trend=trend
            )
        except Exception as e:
            logger.error(f"Gemini API invocation failed: {e}. Falling back to rule engine.")
            return await rule_fallback_provider.generate_advice(context)

gemini_provider = GeminiProvider()
