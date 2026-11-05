"""
AI Explanation Service.
Enforces the core principle: CODE DECIDES. AI ONLY EXPLAINS.
Coordinates deterministic recommendation engine execution, Gemini structured prompt construction,
and rigorous response validation against ground-truth environmental facts.
"""
import json
import logging
from typing import Dict, Any, Optional
from datetime import datetime, timezone

from app.core.config import settings
from app.services.ai.base import BaseAIProvider
from app.services.recommendations.recommendation_engine import recommendation_engine
from app.services.recommendations.ai_response_validator import ai_response_validator
from app.schemas.ai import PersonalizedRiskAdvisorResponse, ActivityGuidance

logger = logging.getLogger("atmosai.explanation")

SYSTEM_INSTRUCTION = """
You are AtmosAI, an expert environmental intelligence and communication assistant for Bengaluru, India.
CORE PRINCIPLE: CODE DECIDES. AI ONLY EXPLAINS.

You are provided with:
1. VERIFIED ENVIRONMENTAL FACTS (AQI, PM2.5, Category, Freshness, Source).
2. RULE-ENGINE DECISION (Suggested Action, General Guidance, Reason, Constraints).
3. USER CONTEXT (Persona, Activities, Sensitivity, Language).

YOUR MANDATORY RULES:
1. Explain the rule-engine recommendation clearly, politely, and evidence-based.
2. NEVER change the AQI category or invent an AQI value. If AQI is Unavailable, state that it is unavailable.
3. NEVER override the rule-engine suggested action or change outdoor_exercise_allowed or mask advice.
4. NEVER provide medical diagnosis, treatment, or prescribe drugs.
5. Respect user preferred language: 'en' for English, 'hi' for Hindi, 'kn' for Kannada.
6. Acknowledge telemetry uncertainty if data is aging or stale.
7. Return strictly valid JSON conforming to keys:
   - headline_summary: string
   - current_environmental_status: string
   - recommended_action: string (must align with rule-engine decision)
   - evidence_based_explanation: string (explains physical dispersion, traffic, wind)
   - profile_specific_recommendations: list of 2-3 specific guidance strings
   - outdoor_exercise_allowed: boolean (must match rule-engine decision)
   - best_time_window: string
   - recommended_duration_minutes: integer
   - mask_recommendation: string
   - indoor_ventilation_advice: string
"""

class AIExplanationService(BaseAIProvider):
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
                logger.info(f"Initialized GenAI client with model {self.model_name}")
            except Exception as e:
                logger.warning(f"Could not initialize GenAI client: {e}")
                self._client = None

    @property
    def provider_name(self) -> str:
        return "AtmosAI Deterministic Rule Engine + Google Gemini Explanation"

    async def generate_advice(self, context: Dict[str, Any]) -> PersonalizedRiskAdvisorResponse:
        """
        Main entry point for generating explainable environmental advice.
        Executes code-driven decision first, then generates or validates explanation.
        """
        live = context["live"]
        forecast = context["forecast"]
        raw_pt = context.get("profile_type")
        raw_cat = context.get("user_category")
        pt_str = str(raw_pt.value if hasattr(raw_pt, "value") else (raw_pt or "")).lower()
        cat_str = str(raw_cat.value if hasattr(raw_cat, "value") else (raw_cat or "")).lower()
        active_persona = pt_str or cat_str or "general_public"

        lang: str = context.get("preferred_language", "en")
        activities = context.get("preferred_activities", ["walking", "outdoor_commute"])
        outdoor_time = context.get("outdoor_time_duration", "1-2 hours")
        sens_pref = str(context.get("sensitivity_preference", "none"))

        pm25 = live.pm25
        aqi = live.aqi
        aqi_std = "CPCB National AQI (India)"
        freshness_status = getattr(live, "reliability_metadata", None)
        freshness_str = (
            str(freshness_status.freshness_status.value if hasattr(freshness_status, "freshness_status") else freshness_status)
            if freshness_status
            else ("STALE" if live.is_stale else ("FRESH" if pm25 is not None else "UNAVAILABLE"))
        )

        forecast_points = forecast.forecast_points if forecast else []
        surge = forecast.surge_detected if forecast else False
        forecast_trend = "steady"
        if forecast_points and len(forecast_points) > 0 and pm25 is not None:
            delta = forecast_points[-1].predicted_pm25 - pm25
            if delta > 3.0 or surge:
                forecast_trend = "rising"
            elif delta < -3.0:
                forecast_trend = "improving"

        # -------------------------------------------------------------
        # STEP 1: CODE DECIDES (Deterministic Rule-Based Evaluation)
        # -------------------------------------------------------------
        rule_decision = recommendation_engine.evaluate(
            aqi=aqi,
            pm25=pm25,
            freshness_status=freshness_str,
            forecast_trend=forecast_trend,
            forecast_points=forecast_points,
            surge_detected=surge,
            user_category=active_persona,
            preferred_activities=activities,
            sensitivity_preference=sens_pref,
            location_name=live.display_name,
            data_source=live.data_source
        )

        verified_facts = {
            "aqi": aqi,
            "pm25": pm25,
            "aqi_category": rule_decision.aqi_category,
            "aqi_standard": aqi_std,
            "freshness_status": freshness_str,
            "data_source": live.data_source,
            "forecast_trend": forecast_trend,
            "surge_detected": surge
        }

        user_context = {
            "user_category": active_persona,
            "preferred_activities": activities,
            "sensitivity_preference": sens_pref,
            "preferred_language": lang,
            "location_name": live.display_name
        }

        # -------------------------------------------------------------
        # STEP 2: AI EXPLAINS (Structured Gemini Query & Validation)
        # -------------------------------------------------------------
        ai_data = None
        validation_passed = True
        validation_details = "Verified Deterministic Rule Engine"

        if self._client:
            prompt = f"""
VERIFIED ENVIRONMENTAL FACTS:
- Location: {live.display_name} (Lat: {live.latitude}, Lon: {live.longitude})
- Current CPCB AQI: {aqi if aqi is not None else 'Unavailable (Sub-indices missing)'}
- Current CPCB Category: {rule_decision.aqi_category}
- Current PM2.5: {pm25 if pm25 is not None else 'Unavailable'} ug/m3
- Telemetry Freshness: {freshness_str}
- Data Source: {live.data_source}
- Forecast Trend (3–6h): {forecast_trend}
- Surge Detected: {surge}

RULE-ENGINE AUTHORITATIVE DECISION:
- Suggested Action: {rule_decision.suggested_action}
- General Guidance: {rule_decision.general_guidance}
- Reason: {rule_decision.reason_for_recommendation}
- Forecast Context: {rule_decision.forecast_context}
- Outdoor Exercise Allowed: {rule_decision.outdoor_exercise_allowed}
- Mask Advised: {rule_decision.mask_advised}
- Best Time Window: {rule_decision.best_time_window}
- Duration Minutes: {rule_decision.recommended_duration_mins}
- Ventilation Advice: {rule_decision.ventilation_advice}

USER CONTEXT:
- Persona: {active_persona}
- Preferred Activities: {activities}
- Outdoor Exposure Time: {outdoor_time}
- Sensitivity Preference: {sens_pref}
- Preferred Language: {lang}

Explain why AtmosAI recommends this decision based on physical and meteorological factors.
Do not change the category or suggested action. Return JSON only.
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
                parsed = json.loads(response.text)

                # STEP 3: RIGOROUS RESPONSE VALIDATION
                is_valid, fail_reason = ai_response_validator.validate(
                    ai_data=parsed,
                    verified_facts=verified_facts,
                    rule_decision=rule_decision
                )

                if is_valid:
                    ai_data = parsed
                    validation_passed = True
                    validation_details = "Gemini explanation verified against deterministic facts."
                else:
                    logger.warning(f"AI response rejected by validator: {fail_reason}. Using safe fallback.")
                    ai_data = ai_response_validator.build_safe_fallback(
                        rule_decision=rule_decision,
                        verified_facts=verified_facts,
                        user_context=user_context,
                        rejection_reason=fail_reason
                    )
                    validation_passed = False
                    validation_details = f"Gemini response rejected: {fail_reason}. Rule-engine explanation served."

            except Exception as e:
                logger.warning(f"Gemini explanation failed: {e}. Using deterministic fallback.")
                ai_data = ai_response_validator.build_safe_fallback(
                    rule_decision=rule_decision,
                    verified_facts=verified_facts,
                    user_context=user_context,
                    rejection_reason=str(e)
                )
                validation_passed = False
                validation_details = "Deterministic Rule Engine (Gemini service unavailable)"

        if ai_data is None:
            # Fallback if client uninitialized
            ai_data = ai_response_validator.build_safe_fallback(
                rule_decision=rule_decision,
                verified_facts=verified_facts,
                user_context=user_context
            )
            validation_passed = True
            validation_details = "Verified Deterministic Rule Engine (Local Offline Mode)"

        activity = ActivityGuidance(
            outdoor_exercise_allowed=bool(ai_data.get("outdoor_exercise_allowed", rule_decision.outdoor_exercise_allowed)),
            best_time_window=str(ai_data.get("best_time_window", rule_decision.best_time_window)),
            recommended_duration_minutes=int(ai_data.get("recommended_duration_minutes", rule_decision.recommended_duration_mins)),
            mask_recommendation=str(ai_data.get("mask_recommendation", "N95 Advised" if rule_decision.mask_advised else "Optional")),
            indoor_ventilation_advice=str(ai_data.get("indoor_ventilation_advice", rule_decision.ventilation_advice))
        )

        out_type = raw_pt if raw_pt is not None else active_persona
        now_iso = datetime.now(timezone.utc).isoformat()

        return PersonalizedRiskAdvisorResponse(
            user_category=str(raw_cat.value if hasattr(raw_cat, "value") else (raw_cat or active_persona)),
            profile_type=str(out_type.value if hasattr(out_type, "value") else out_type),
            location_name=live.location_name,
            display_name=live.display_name,
            timestamp_iso=getattr(live, "observation_time_iso", None) or now_iso,
            current_environmental_status=str(ai_data.get("current_environmental_status", f"Air quality is {rule_decision.aqi_category} in {live.display_name}.")),
            current_aqi=aqi,
            current_pm25=round(pm25, 1) if pm25 is not None else None,
            aqi_category=rule_decision.aqi_category,
            potential_forecast_deterioration=surge or (forecast_trend == "rising"),
            deterioration_details=rule_decision.forecast_context,
            recommended_action=str(ai_data.get("recommended_action", rule_decision.suggested_action)),
            explanation=str(ai_data.get("evidence_based_explanation", rule_decision.general_guidance)),
            data_source=f"{live.data_source} & AtmosAI Rule Engine",
            confidence_status=f"{rule_decision.confidence_level} ({rule_decision.data_quality_status})",
            headline_summary=str(ai_data.get("headline_summary", f"{rule_decision.aqi_category} Air Quality Advisory")),
            evidence_based_explanation=str(ai_data.get("evidence_based_explanation", rule_decision.reason_for_recommendation)),
            profile_specific_recommendations=(
                ai_data.get("profile_specific_recommendations")
                if ai_data.get("profile_specific_recommendations") and isinstance(ai_data.get("profile_specific_recommendations"), list) and len(ai_data.get("profile_specific_recommendations")) > 0
                else (rule_decision.profile_specific_recommendations or [rule_decision.suggested_action])
            ),
            activity_guidance=activity,
            environmental_drivers_cited=forecast.primary_driving_factors if forecast else ["Local meteorological conditions"],
            ai_provider=self.provider_name if validation_passed else "AtmosAI Deterministic Engine (Validator Guard Active)",
            disclaimer=(
                "AtmosAI मार्गदर्शन केवल पर्यावरणीय जानकारी और जोखिम कम करने के लिए है। यह चिकित्सा सलाह या बीमारी का निदान नहीं है।" if lang == "hi"
                else "AtmosAI ಮಾರ್ಗದರ್ಶನವು ಪರಿಸರ ಜಾಗೃತಿ ಮತ್ತು ಅಪಾಯ ತಗ್ಗಿಸುವಿಕೆಗಾಗಿ ಮಾತ್ರ. ಇದು ವೈದ್ಯಕೀಯ ಸಲಹೆ ಅಥವಾ ರೋಗನಿರ್ಣಯವಲ್ಲ." if lang == "kn"
                else "AtmosAI guidance is for environmental intelligence and risk reduction only. It does not constitute medical advice or disease diagnosis."
            ),
            preferred_activities=activities,
            outdoor_time_context=outdoor_time,
            sensitivity_preference=sens_pref,
            forecast_trend=forecast_trend
        )

# Global singleton
ai_explanation_service = AIExplanationService()
