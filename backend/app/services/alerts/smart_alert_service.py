import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone, timedelta
import uuid

from app.schemas.alerts import AlertItem, NotificationSettingsOut, NotificationSettingsUpdate
from app.schemas.profile import UserProfile, UserCategory, SensitivityPreference
from app.services.environmental.aggregator import aggregator
from app.services.environmental.aqi_calculator import (
    get_cpcb_safety_recommendation, 
    get_aqi_category_and_risk,
    CPCB_CATEGORIES,
    MEDICAL_DISCLAIMER
)
from app.services.forecasting.ml_service import ml_forecaster

logger = logging.getLogger("atmosai.smart_alerts")

class SmartAlertService:
    """
    AtmosAI Smart Alert and Safety Recommendation Engine.
    Implements CPCB NAQI categories, threshold crossing detection,
    pollution deterioration warnings, forecast surge advisories,
    location filtering, and alert deduplication.
    """

    def __init__(self):
        # Cache for deduplication: key -> { 'last_aqi': int, 'last_category': str, 'last_alert_time': datetime, 'alert_id': str }
        self._station_previous_state: Dict[str, Dict[str, Any]] = {}
        self._sent_alerts_cache: Dict[str, datetime] = {}
        self._cooldown_minutes = 60

    def compute_recommended_threshold(self, profile: UserProfile) -> Dict[str, Any]:
        """
        Determines the scientifically recommended notification threshold based on
        CPCB NAQI impact bands, user sensitivity, and lifestyle persona.
        """
        sens = profile.sensitivity_preference
        cat = profile.user_category

        if sens in (SensitivityPreference.ASTHMA_RESPIRATORY, SensitivityPreference.ALLERGIES):
            return {
                "threshold": 80,
                "reason": "Strict respiratory precaution: triggers early within the Satisfactory band before Moderate particulate levels induce bronchial irritation."
            }
        elif sens == SensitivityPreference.CARDIOVASCULAR:
            return {
                "threshold": 80,
                "reason": "Cardiovascular precaution: early notice before fine particulates increase systemic cardiovascular strain."
            }
        elif sens == SensitivityPreference.ELDERLY_CHILD_CARE or cat == UserCategory.PARENT:
            return {
                "threshold": 90,
                "reason": "Pediatric & elderly household safety: triggers prior to the Moderate threshold to protect developing and sensitive lungs."
            }
        elif cat == UserCategory.RUNNER:
            return {
                "threshold": 100,
                "reason": "Athletic ventilation threshold: alerts at the boundary of Moderate air where elevated minute-ventilation increases particulate intake."
            }
        elif cat == UserCategory.STUDENT:
            return {
                "threshold": 100,
                "reason": "Campus activity threshold: balances outdoor sports, walking between faculties, and library ventilation."
            }
        elif cat == UserCategory.OUTDOOR_WORKER:
            return {
                "threshold": 120,
                "reason": "Shift protection threshold: prompts N95 respirator donning and indoor hydration breaks during field transit."
            }
        elif cat == UserCategory.OFFICE_COMMUTER:
            return {
                "threshold": 140,
                "reason": "Commute transit threshold: alerts when arterial corridors exceed healthy vehicle cabin infiltration limits."
            }
        else: # GENERAL_PUBLIC
            return {
                "threshold": 150,
                "reason": "Standard CPCB health awareness threshold: alerts when air quality impacts sensitive groups and general outdoor comfort."
            }

    def get_notification_settings(self, profile: UserProfile) -> NotificationSettingsOut:
        rec = self.compute_recommended_threshold(profile)
        notifs = profile.notifications

        effective_threshold = notifs.custom_threshold if not notifs.use_recommended_threshold and notifs.custom_threshold else notifs.high_pollution_threshold

        return NotificationSettingsOut(
            user_id=profile.id,
            user_category=profile.user_category.value,
            sensitivity_preference=profile.sensitivity_preference.value,
            recommended_threshold=rec["threshold"],
            recommended_threshold_reason=rec["reason"],
            current_threshold=effective_threshold,
            use_recommended_threshold=notifs.use_recommended_threshold,
            threshold_crossing_alerts=notifs.threshold_crossing_alerts,
            deterioration_alerts=notifs.deterioration_alerts,
            forecast_alerts=notifs.forecast_alerts,
            surge_warnings=notifs.surge_warnings,
            daily_morning_brief=notifs.daily_morning_brief,
            commute_window_alerts=notifs.commute_window_alerts,
            improving_air_alerts=notifs.improving_air_alerts,
            monitored_locations=notifs.monitored_locations
        )

    async def generate_smart_alerts(
        self, 
        profile: UserProfile, 
        target_location: Optional[str] = None
    ) -> List[AlertItem]:
        """
        Evaluates current station readings, historical transitions, and ML forecasts
        against the user's customized notification settings.
        Avoids duplicate alerts for steady state conditions.
        """
        notifs = profile.notifications
        rec_info = self.compute_recommended_threshold(profile)
        threshold = notifs.custom_threshold if not notifs.use_recommended_threshold and notifs.custom_threshold else (notifs.high_pollution_threshold or rec_info["threshold"])
        
        now = datetime.now(timezone.utc)
        alerts: List[AlertItem] = []

        # 1. Fetch live multi-station summaries
        stations = await aggregator.get_all_locations_summary()
        monitored = notifs.monitored_locations or [s["name"] for s in stations]

        for s in stations:
            loc_slug = s.get("name")
            display_name = s.get("display_name", loc_slug)

            # Location filtering
            if target_location and loc_slug != target_location:
                continue
            if not target_location and loc_slug not in monitored:
                continue

            aqi = s.get("aqi") or 0
            pm25 = s.get("pm25") or 0.0
            category, risk, color = get_aqi_category_and_risk(aqi)

            prev_state = self._station_previous_state.get(loc_slug, {})
            prev_aqi = prev_state.get("aqi", aqi)
            prev_cat = prev_state.get("category", category)

            # Update tracked state
            self._station_previous_state[loc_slug] = {
                "aqi": aqi,
                "category": category,
                "updated_at": now
            }

            cpcb_guidance = get_cpcb_safety_recommendation(
                aqi=aqi, 
                user_category=profile.user_category.value, 
                sensitivity=profile.sensitivity_preference.value
            )

            # --- A. THRESHOLD CROSSING ALERT (Current Measurement) ---
            if notifs.threshold_crossing_alerts and aqi >= threshold:
                dedup_key = f"{profile.id}:{loc_slug}:threshold:{category}"
                last_sent = self._sent_alerts_cache.get(dedup_key)

                # Send if not in cooldown or crossed into higher category
                if not last_sent or (now - last_sent) > timedelta(minutes=self._cooldown_minutes) or category != prev_cat:
                    severity = "critical" if aqi > 300 else ("high" if aqi > 200 else "medium")
                    alerts.append(AlertItem(
                        id=str(uuid.uuid4()),
                        location_id=s.get("id"),
                        location_name=display_name,
                        alert_type="threshold_crossing",
                        alert_source="current_measurement",
                        severity=severity,
                        title=f"AQI Threshold Exceeded: {display_name}",
                        message=f"Current CPCB AQI is {aqi} ({category}), exceeding your alert threshold of {threshold}. {cpcb_guidance['base_recommendation']}",
                        cpcb_category=category,
                        safety_recommendation=cpcb_guidance["base_recommendation"],
                        sensitivity_note=cpcb_guidance["sensitivity_note"] or cpcb_guidance["persona_recommendation"],
                        current_aqi=aqi,
                        profile_category=profile.user_category.value,
                        disclaimer=MEDICAL_DISCLAIMER,
                        timestamp=now,
                        is_read=False
                    ))
                    self._sent_alerts_cache[dedup_key] = now

            # --- B. POLLUTION DETERIORATION ALERT (Current Measurement Transition) ---
            if notifs.deterioration_alerts:
                # Deterioration triggered if AQI spiked by >= 20 or category downgraded
                aqi_delta = aqi - prev_aqi
                is_category_worse = (
                    CPCB_CATEGORIES_RANK.get(category, 0) > CPCB_CATEGORIES_RANK.get(prev_cat, 0)
                )

                if aqi_delta >= 20 or is_category_worse:
                    dedup_key = f"{profile.id}:{loc_slug}:deterioration:{category}"
                    last_sent = self._sent_alerts_cache.get(dedup_key)

                    if not last_sent or (now - last_sent) > timedelta(minutes=self._cooldown_minutes):
                        alerts.append(AlertItem(
                            id=str(uuid.uuid4()),
                            location_id=s.get("id"),
                            location_name=display_name,
                            alert_type="deterioration",
                            alert_source="current_measurement",
                            severity="high" if aqi > 200 else "medium",
                            title=f"Pollution Deterioration Notice: {display_name}",
                            message=f"Air quality has degraded from AQI {prev_aqi} ({prev_cat}) to AQI {aqi} ({category}). Rapid particulate accumulation observed.",
                            cpcb_category=category,
                            safety_recommendation=cpcb_guidance["base_recommendation"],
                            sensitivity_note=cpcb_guidance["persona_recommendation"] or cpcb_guidance["sensitivity_note"],
                            current_aqi=aqi,
                            profile_category=profile.user_category.value,
                            disclaimer=MEDICAL_DISCLAIMER,
                            timestamp=now,
                            is_read=False
                        ))
                        self._sent_alerts_cache[dedup_key] = now

        # --- C. FORECAST-BASED ALERTS (ML Prediction) ---
        if notifs.forecast_alerts or notifs.surge_warnings:
            eval_loc = target_location or (monitored[0] if monitored else "bengaluru_central")
            try:
                forecast = await ml_forecaster.predict(eval_loc)
                if forecast and (forecast.surge_detected or any(pt.trend == "rising" for pt in forecast.forecast_points)):
                    peak_pt = max(forecast.forecast_points, key=lambda p: p.predicted_pm25, default=None)
                    if peak_pt and peak_pt.predicted_pm25 > 45.0:
                        dedup_key = f"{profile.id}:{eval_loc}:forecast_surge"
                        last_sent = self._sent_alerts_cache.get(dedup_key)

                        if not last_sent or (now - last_sent) > timedelta(minutes=self._cooldown_minutes):
                            alerts.append(AlertItem(
                                id=str(uuid.uuid4()),
                                location_name=forecast.display_name or eval_loc.replace("_", " ").title(),
                                alert_type="forecast_surge",
                                alert_source="forecast_prediction",
                                severity="medium" if peak_pt.predicted_pm25 < 60 else "high",
                                title=f"3–6h Forecast Surge Advisory: {forecast.display_name}",
                                message=f"LightGBM ML model projects particulate levels rising to {peak_pt.predicted_pm25:.1f} µg/m³ ({peak_pt.target_time_label}). Plan to conclude outdoor exertion early.",
                                predicted_aqi=round(peak_pt.predicted_pm25 * 1.5),
                                profile_category=profile.user_category.value,
                                safety_recommendation="Consider scheduling outdoor activities before the predicted afternoon particulate surge.",
                                sensitivity_note="Sensitive groups should close road-facing windows prior to the projected surge window.",
                                disclaimer=MEDICAL_DISCLAIMER,
                                timestamp=now,
                                is_read=False
                            ))
                            self._sent_alerts_cache[dedup_key] = now
            except Exception as e:
                logger.warning(f"Could not compute forecast surge alert for {eval_loc}: {e}")

        # --- D. COMMUTE CORRIDOR ADVISORY ---
        if notifs.commute_window_alerts and profile.user_category == UserCategory.OFFICE_COMMUTER:
            dedup_key = f"{profile.id}:commute_corridor"
            last_sent = self._sent_alerts_cache.get(dedup_key)
            if not last_sent or (now - last_sent) > timedelta(minutes=self._cooldown_minutes * 2):
                alerts.append(AlertItem(
                    id=str(uuid.uuid4()),
                    location_name="Silk Board - Marathahalli Arterial Corridor",
                    alert_type="commute_advisory",
                    alert_source="current_measurement",
                    severity="medium",
                    title="Commute Corridor Pollution Notice",
                    message="Outer Ring Road traffic corridor exhibiting elevated particulate concentrations. Set vehicle air conditioning to internal recirculation.",
                    cpcb_category="Moderate",
                    safety_recommendation="Switch vehicle AC to internal recirculation mode when passing congested junctions.",
                    profile_category=profile.user_category.value,
                    disclaimer=MEDICAL_DISCLAIMER,
                    timestamp=now,
                    is_read=False
                ))
                self._sent_alerts_cache[dedup_key] = now

        # --- E. DAILY AIR-QUALITY SUMMARY (Morning Brief) ---
        if notifs.daily_morning_brief and not any(a.alert_type == "daily_summary" for a in alerts):
            dedup_key = f"{profile.id}:daily_brief:{now.strftime('%Y-%m-%d')}"
            last_sent = self._sent_alerts_cache.get(dedup_key)

            if not last_sent:
                avg_aqi = round(sum(s.get("aqi") or 35 for s in stations) / max(1, len(stations)))
                cat, risk, col = get_aqi_category_and_risk(avg_aqi)
                cleanest = min(stations, key=lambda s: s.get("aqi") or 999, default=stations[0] if stations else {})
                cleanest_name = cleanest.get("display_name", "Yelahanka")

                alerts.insert(0, AlertItem(
                    id=str(uuid.uuid4()),
                    location_name="Bengaluru Metropolitan Region",
                    alert_type="daily_summary",
                    alert_source="daily_summary",
                    severity="low",
                    title="Daily Air Quality Brief & Morning Outlook",
                    message=f"Bengaluru metro average AQI is {avg_aqi} ({cat}). Cleanest ambient air currently recorded at {cleanest_name}. Optimal outdoor window is 10:30 AM to 03:00 PM.",
                    cpcb_category=cat,
                    current_aqi=avg_aqi,
                    safety_recommendation=f"Overall conditions are {cat.lower()}. Plan outdoor errands during solar midday hours for best atmospheric dispersion.",
                    profile_category=profile.user_category.value,
                    disclaimer=MEDICAL_DISCLAIMER,
                    timestamp=now,
                    is_read=False
                ))
                self._sent_alerts_cache[dedup_key] = now

        # --- F. BASELINE IMPROVING / CLEAN AIR NOTICE ---
        if not alerts and notifs.improving_air_alerts:
            alerts.append(AlertItem(
                id=str(uuid.uuid4()),
                location_name="Bengaluru Metropolitan",
                alert_type="improving_pollution",
                alert_source="current_measurement",
                severity="low",
                title="Favorable Atmospheric Conditions",
                message="Current particulate concentrations across Bengaluru monitoring stations are within safe CPCB breathing thresholds.",
                cpcb_category="Good",
                safety_recommendation="Generally favourable outdoor conditions for exercise and recreation.",
                profile_category=profile.user_category.value,
                disclaimer=MEDICAL_DISCLAIMER,
                timestamp=now,
                is_read=False
            ))

        return alerts

CPCB_CATEGORIES_RANK = {
    "Good": 1,
    "Satisfactory": 2,
    "Moderate": 3,
    "Poor": 4,
    "Very Poor": 5,
    "Severe": 6
}

smart_alert_service = SmartAlertService()
