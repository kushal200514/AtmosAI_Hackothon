from typing import Dict, Any, List
from datetime import datetime, timezone

from app.services.ai.base import BaseAIProvider
from app.schemas.ai import PersonalizedRiskAdvisorResponse, ActivityGuidance
from app.schemas.profile import UserCategory, SensitivityPreference, ProfileType

# Multilingual Translations for Common Headlines & Disclaimers
TRANSLATIONS = {
    "hi": {
        "disclaimer": "AtmosAI मार्गदर्शन केवल पर्यावरणीय जानकारी और जोखिम कम करने के लिए है। यह चिकित्सा सलाह या बीमारी का निदान नहीं है।",
        "good_air": "वर्तमान में वायु गुणवत्ता अच्छी है। बाहरी गतिविधियों के लिए उपयुक्त।",
        "moderate_air": "मध्यम वायु प्रदूषण दर्ज किया गया है। संवेदनशील समूहों को सावधानी बरतने की सलाह दी जाती है।",
        "poor_air": "खराब वायु गुणवत्ता चेतावनी। लंबे समय तक बाहर रहने से बचें।"
    },
    "kn": {
        "disclaimer": "AtmosAI ಮಾರ್ಗದರ್ಶನವು ಪರಿಸರ ಜಾಗೃತಿ ಮತ್ತು ಅಪಾಯ ತಗ್ಗಿಸುವಿಕೆಗಾಗಿ ಮಾತ್ರ. ಇದು ವೈದ್ಯಕೀಯ ಸಲಹೆ ಅಥವಾ ರೋಗನಿರ್ಣಯವಲ್ಲ.",
        "good_air": "ಪ್ರಸ್ತುತ ವಾಯು ಗುಣಮಟ್ಟ ಉತ್ತಮವಾಗಿದೆ. ಹೊರಾಂಗಣ ಚಟುವಟಿಕೆಗಳಿಗೆ ಸೂಕ್ತವಾಗಿದೆ.",
        "moderate_air": "ಮಧ್ಯಮ ವಾಯು ಮಾಲಿನ್ಯ ಕಂಡುಬಂದಿದೆ. ಸೂಕ್ಷ್ಮ ವ್ಯಕ್ತಿಗಳು ಎಚ್ಚರ ವಹಿಸಬೇಕು.",
        "poor_air": "ಕಳಪೆ ವಾಯು ಗುಣಮಟ್ಟದ ಎಚ್ಚರಿಕೆ. ದೀರ್ಘಾವಧಿಯ ಹೊರಾಂಗಣ ಚಟುವಟಿಕೆಗಳನ್ನು ಮಿತಿಗೊಳಿಸಿ."
    }
}

class RuleBasedFallbackProvider(BaseAIProvider):
    @property
    def provider_name(self) -> str:
        return "AtmosAI Personalized Risk Engine (Expert Rule Fallback)"

    async def generate_advice(self, context: Dict[str, Any]) -> PersonalizedRiskAdvisorResponse:
        live = context["live"]
        forecast = context["forecast"]
        
        raw_pt = context.get("profile_type")
        raw_cat = context.get("user_category")
        pt_str = str(raw_pt.value if hasattr(raw_pt, "value") else (raw_pt or "")).lower()
        cat_str = str(raw_cat.value if hasattr(raw_cat, "value") else (raw_cat or "")).lower()
        active_persona = pt_str or cat_str or "general_public"

        lang: str = context.get("preferred_language", "en")
        cautious_mode: bool = context.get("cautious_mode", False) or (active_persona == "respiratory_sensitive")
        activities: List[str] = context.get("preferred_activities", ["walking", "outdoor_commute"])
        outdoor_time = context.get("outdoor_time_duration", "1-2 hours")
        sens_pref = context.get("sensitivity_preference", "none")

        pm25 = live.pm25 if live.pm25 is not None else 25.0
        aqi = live.aqi if live.aqi is not None else 45
        aqi_cat = live.aqi_category or "Satisfactory"
        weather = live.weather
        wind_speed = weather.wind_speed_kmh if weather and weather.wind_speed_kmh is not None else 8.5
        temp = weather.temperature_c if weather and weather.temperature_c is not None else 24.0

        # Determine dominant trend & potential forecast deterioration from ML forecast
        forecast_points = forecast.forecast_points if forecast else []
        trend = "stable"
        is_deteriorating = False
        deterioration_text = "Atmospheric conditions are projected to remain steady over the next 3–6 hours."

        if forecast_points:
            delta = forecast_points[-1].predicted_pm25 - pm25
            if delta > 3.0 or (forecast and forecast.surge_detected):
                trend = "rising"
                is_deteriorating = True
                deterioration_text = (
                    f"Forecast warning: PM2.5 projected to deteriorate from {pm25:.1f} µg/m³ to "
                    f"{forecast_points[-1].predicted_pm25:.1f} µg/m³ (+{delta:.1f} µg/m³) over the next 3–6 hours."
                )
            elif delta < -3.0:
                trend = "improving"
                is_deteriorating = False
                deterioration_text = (
                    f"Favorable forecast trend: PM2.5 projected to improve from {pm25:.1f} µg/m³ down to "
                    f"{forecast_points[-1].predicted_pm25:.1f} µg/m³ assisted by {wind_speed} km/h wind dispersion."
                )

        # Confidence & Data Quality Status (Stale Data Protection)
        rel_meta = getattr(live, "reliability_metadata", None)
        is_stale_data = getattr(live, "is_stale", False) or (rel_meta and str(getattr(rel_meta, "freshness_status", "")).upper() == "STALE")
        is_unavail = (live.pm25 is None) or (rel_meta and str(getattr(rel_meta, "freshness_status", "")).upper() == "UNAVAILABLE")

        if is_unavail:
            confidence = "NONE (Environmental Telemetry Offline)"
        elif is_stale_data:
            confidence = "LOW (Stale Telemetry - Current Conditions Uncertain)"
        elif getattr(live, "measurement_type", "") in ("measured", "MEASURED") or (rel_meta and str(getattr(rel_meta, "source_type", "")).upper() == "MEASURED"):
            confidence = "HIGH (Verified Ground Telemetry + Validated Model)"
        else:
            confidence = "MEDIUM (Regional Atmospheric Chemistry Model)"

        # 1. Current Environmental Status String
        env_status = f"Current air quality is {aqi_cat} (AQI {aqi}, PM2.5 {pm25:.1f} µg/m³) in {live.display_name}."

        # 2. Headline Summary
        if lang == "hi":
            headline = TRANSLATIONS["hi"]["good_air"] if aqi <= 75 else (TRANSLATIONS["hi"]["moderate_air"] if aqi <= 150 else TRANSLATIONS["hi"]["poor_air"])
        elif lang == "kn":
            headline = TRANSLATIONS["kn"]["good_air"] if aqi <= 75 else (TRANSLATIONS["kn"]["moderate_air"] if aqi <= 150 else TRANSLATIONS["kn"]["poor_air"])
        else:
            if aqi <= 50:
                headline = f"Air quality is Good in {live.display_name}. Optimal conditions for outdoor activities."
            elif aqi <= 100:
                headline = f"Satisfactory atmospheric conditions in {live.display_name}. Minor sensitivity awareness advised."
            elif aqi <= 200:
                headline = f"Moderate air pollution detected. Fine particulates may cause irritation during prolonged exertion."
            elif aqi <= 300:
                headline = f"Poor air quality alert for {live.display_name}. Reduce strenuous outdoor exposure."
            else:
                headline = f"Very Poor to Severe pollution levels. High particulate concentration warning."

        # 3. Evidence-Based Explanation
        evidence_parts = []
        if is_deteriorating:
            evidence_parts.append(
                f"Multi-horizon machine learning models indicate rising PM2.5 reaching {forecast_points[-1].predicted_pm25:.1f} µg/m³."
            )
            if wind_speed < 8.0:
                evidence_parts.append(f"Low surface wind ventilation ({wind_speed} km/h) is trapping emissions near ground level.")
            else:
                evidence_parts.append("Evening traffic surge combined with boundary layer cooling will restrict particulate dispersion.")
        elif trend == "improving":
            evidence_parts.append(
                f"Atmospheric dispersion is favorable. Active surface winds of {wind_speed} km/h are ventilating urban corridors."
            )
        else:
            evidence_parts.append(
                f"Local particulate concentration remains steady near {pm25:.1f} µg/m³ with balanced meteorological dispersion."
            )
        explanation = " ".join(evidence_parts)

        # 4. Persona-Specific Recommendations & Action
        recommendations: List[str] = []
        primary_action = ""
        exercise_allowed = True
        mask_recommendation = "Optional under present conditions."
        best_time_window = "Early morning or mid-afternoon"
        duration_mins = 60
        ventilation_advice = "Natural ventilation recommended during midday hours."

        # --- PERSONA 1: STUDENT ---
        if active_persona == "student":
            primary_action = "Schedule campus outdoor walks and field sports before peak evening traffic; use shaded tree canopy pathways."
            recommendations.append("Campus conditions are favorable for study and outdoor walks; utilize shaded interior campus paths rather than arterial boundary roads.")
            recommendations.append("If participating in outdoor campus sports, schedule sessions between 11:00 AM and 03:30 PM before evening commuter particulate spikes.")
            recommendations.append("Keep campus hostel and dormitory windows closed during peak 05:00 PM – 08:00 PM traffic hours.")
            best_time_window = "Midday between classes (11:00 AM - 03:30 PM)"
            duration_mins = 60

        # --- PERSONA 2: RUNNER / ATHLETE ---
        elif active_persona == "runner":
            if aqi > 100 or is_deteriorating or cautious_mode:
                exercise_allowed = aqi < 180
                duration_mins = 35 if aqi < 180 else 0
                best_time_window = "Early morning (05:30 - 07:00 AM) or indoor treadmill"
                mask_recommendation = "Sports particulate mask advised for outdoor cardio, or train indoors."
                primary_action = "Shift intense aerobic endurance training indoors or to the early morning window before commuter traffic builds."
                recommendations.append("High ventilation rates during running dramatically increase particulate deposition; shift strenuous intervals indoors.")
                recommendations.append("If running outdoors, maintain low-to-moderate heart rate zones away from high-traffic corridors like Outer Ring Road.")
                recommendations.append("Hydrate well; ambient temperature of {temp}°C and rising PM2.5 increase airway strain.")
            else:
                primary_action = "Atmospheric conditions are optimal for outdoor running and athletic conditioning."
                recommendations.append("Favorable dispersion allows outdoor tempo and long runs; maintain hydration and check 3-hour forecast prior to departure.")
                recommendations.append("Choose park routes (Cubbon Park, Lalbagh) with natural vegetation barriers.")
                best_time_window = "06:00 AM - 08:30 AM"

        # --- PERSONA 3: OFFICE COMMUTER ---
        elif active_persona == "office_commuter":
            primary_action = "Switch vehicle AC to internal recirculation mode when passing congested junctions (Silk Board, Hebbal) to block exhaust particulates."
            recommendations.append("Corridor traffic congestion leads to localized PM2.5 spikes; keep vehicle windows rolled up with AC recirculation engaged.")
            recommendations.append("Plan evening departure slightly before 17:30 or after 20:00 to avoid peak particulate congestion corridors.")
            recommendations.append("If commuting by two-wheeler or walking from metro stations, wear an anti-pollution N95 mask during peak hours.")
            ventilation_advice = "Keep car windows rolled up during transit along major arterial corridors."
            best_time_window = "Off-peak travel before 08:30 AM or between 11:00 AM - 04:00 PM"

        # --- PERSONA 4: OUTDOOR / DELIVERY WORKER ---
        elif active_persona in ("outdoor_worker", "delivery_worker"):
            primary_action = "Equip an N95 respirator during continuous street-level shifts; take scheduled 15-minute rest breaks in filtered indoor environments."
            recommendations.append("Continuous on-road exposure creates cumulative particulate intake; wear a fitted N95 respirator during motorcycle or street shifts.")
            recommendations.append("Schedule 15-minute breaks in air-conditioned or filtered indoor rest points every 2 hours.")
            recommendations.append("Hydrate frequently to support airway mucosal clearance against road dust and fine particulates.")
            mask_recommendation = "N95 respirator strongly recommended during on-road shifts."
            duration_mins = 45

        # --- PERSONA 5: PARENT / GUARDIAN ---
        elif active_persona == "parent":
            primary_action = "Plan children's playground visits and stroller walks during midday dispersion hours (11:00 AM - 03:30 PM); keep home windows closed by 17:00."
            recommendations.append("Children breathe faster and closer to the ground; schedule outdoor playground trips between 11:00 AM and 03:30 PM when vertical air mixing is best.")
            recommendations.append("Limit strenuous outdoor games for young children during evening traffic rush hours when vehicular particulates accumulate.")
            recommendations.append("Ensure indoor play areas are protected; close street-facing windows before evening traffic builds up.")
            ventilation_advice = "Ensure indoor play spaces maintain filtered air; close road-facing windows by 5 PM."
            best_time_window = "11:00 AM to 03:30 PM"
            duration_mins = 40

        # --- PERSONA 6: GENERAL PUBLIC ---
        else:
            if aqi > 120 or cautious_mode:
                primary_action = "Moderate pollution present; sensitive individuals should reduce prolonged outdoor exertion and consider an N95 mask near traffic."
                recommendations.append("Fine particulate concentrations are elevated; sensitive individuals should reduce prolonged outdoor exertion.")
                recommendations.append("Run indoor air filtration and keep windows facing busy roads closed during evening rush hours.")
            else:
                primary_action = "Air quality is favorable for routine outdoor daily activities; check multi-horizon forecast before evening gatherings."
                recommendations.append("Standard daily activities and outdoor plans can proceed without special environmental restrictions.")
                recommendations.append("Ventilate homes during midday hours when urban particulate dispersion is most effective.")

        # Sensitivity additions
        if cautious_mode or str(sens_pref).lower() != "none":
            recommendations.insert(0, f"Sensitivity precaution ({sens_pref}): Keep prescribed inhalers and preventive care accessible when outside.")

        # Stale data protection: attach advisory warning if measurements are outdated
        if is_stale_data:
            recommendations.insert(0, "DATA STALE WARNING: Ground readings are older than 3 hours. Atmospheric dispersion or sudden local emissions may have changed actual air quality. Exercise caution.")

        disclaimer_text = TRANSLATIONS.get(lang, {}).get("disclaimer", (
            "AtmosAI guidance is for environmental intelligence and risk reduction only. "
            "It does not constitute medical advice or disease diagnosis."
        ))

        activity = ActivityGuidance(
            outdoor_exercise_allowed=exercise_allowed,
            best_time_window=best_time_window,
            recommended_duration_minutes=duration_mins,
            mask_recommendation=mask_recommendation,
            indoor_ventilation_advice=ventilation_advice
        )

        out_type = raw_pt if raw_pt is not None else active_persona

        now_iso = datetime.now(timezone.utc).isoformat()
        data_src = f"{getattr(live, 'data_source', 'CPCB Ground Station')} & AtmosAI Multi-Horizon LightGBM"

        return PersonalizedRiskAdvisorResponse(
            user_category=str(raw_cat.value if hasattr(raw_cat, "value") else (raw_cat or active_persona)),
            profile_type=str(out_type.value if hasattr(out_type, "value") else out_type),
            location_name=live.location_name,
            display_name=live.display_name,
            timestamp_iso=getattr(live, "observation_time_iso", None) or now_iso,
            
            # Required outputs
            current_environmental_status=env_status,
            current_aqi=aqi,
            current_pm25=pm25,
            aqi_category=aqi_cat,
            potential_forecast_deterioration=is_deteriorating,
            deterioration_details=deterioration_text,
            recommended_action=primary_action,
            explanation=explanation,
            data_source=data_src,
            confidence_status=confidence,
            
            # Detailed guidance
            headline_summary=headline,
            evidence_based_explanation=explanation,
            profile_specific_recommendations=recommendations,
            activity_guidance=activity,
            environmental_drivers_cited=forecast.primary_driving_factors if forecast else ["Local meteorological conditions"],
            ai_provider=self.provider_name,
            disclaimer=disclaimer_text,
            preferred_activities=activities,
            outdoor_time_context=outdoor_time,
            sensitivity_preference=str(sens_pref),
            forecast_trend=trend
        )

rule_fallback_provider = RuleBasedFallbackProvider()
