"""
Deterministic Rule-Based Environmental Recommendation Engine.
CORE PRINCIPLE: CODE DECIDES. AI ONLY EXPLAINS.
Generates authoritative risk categories, guidance, suggested actions, and reasons
strictly based on deterministic logic and input facts before LLM explanation.
"""
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field

from app.services.recommendations.aqi_rules import get_cpcb_category_info, CPCB_AQI_CATEGORIES

class DeterministicRecommendation(BaseModel):
    risk_category: str
    general_guidance: str
    suggested_action: str
    relevant_activity: str
    reason_for_recommendation: str
    aqi_category: str
    is_stale: bool
    is_aqi_available: bool
    is_forecast_available: bool
    confidence_level: str
    data_quality_status: str
    forecast_context: str
    outdoor_exercise_allowed: bool
    mask_advised: bool
    best_time_window: str
    recommended_duration_mins: int
    ventilation_advice: str
    profile_specific_recommendations: List[str] = Field(default_factory=list)

class RecommendationEngine:
    """
    Authoritative deterministic engine executing rule-based decision trees
    for Indian CPCB NAQI environmental conditions across user personas.
    """

    def evaluate(
        self,
        aqi: Optional[int],
        pm25: Optional[float],
        user_category: str = "general_public",
        forecast_trend: str = "steady",
        surge_detected: bool = False,
        freshness_status: str = "FRESH",
        sensitivity_preference: Optional[str] = "none",
        has_forecast: bool = True,
        is_aqi_available: bool = True,
        location_name: str = "Bengaluru",
        cautious_mode: bool = False,
        forecast_points: Optional[List[Any]] = None,
        preferred_activities: Optional[List[str]] = None,
        data_source: Optional[str] = None,
        **kwargs: Any
    ) -> DeterministicRecommendation:
        """
        Executes strict deterministic decision tree matching Indian CPCB standards.
        """
        if forecast_points is not None:
            has_forecast = len(forecast_points) > 0

        # Normalize category
        raw_cat = (user_category or "general_public").lower().replace(" ", "_")
        if raw_cat in ("outdoor_worker", "delivery_worker", "cyclist"):
            user_cat = "outdoor_worker"
        elif raw_cat in ("runner", "athlete"):
            user_cat = "runner"
        elif raw_cat in ("respiratory_sensitive", "sensitive"):
            user_cat = "respiratory_sensitive"
        elif raw_cat in ("parent", "guardian"):
            user_cat = "parent"
        elif raw_cat in ("student", "college"):
            user_cat = "student"
        elif raw_cat in ("office_commuter", "commuter"):
            user_cat = "office_commuter"
        else:
            user_cat = "general_public"

        sens_pref = (sensitivity_preference or "none").lower()
        has_sensitivity = sens_pref != "none" or cautious_mode or user_cat == "respiratory_sensitive"

        # 1. Base CPCB Category Lookup
        is_stale = (freshness_status or "").upper() == "STALE"
        is_aqi_avail = is_aqi_available and (aqi is not None)

        if is_aqi_avail:
            cat_info = get_cpcb_category_info(aqi)
            base_cat = cat_info["category"]
            base_risk = cat_info.get("risk_category") or cat_info.get("risk_level", "Moderate")
            base_guidance = cat_info["general_guidance"]
        elif pm25 is not None:
            # Multi-pollutant AQI sub-indices missing, fallback to PM2.5-specific guidance only
            base_cat = "Unavailable"
            base_risk = "Moderate" if pm25 > 60 else "Low"
            base_guidance = (
                f"Overall multi-pollutant CPCB AQI is unavailable due to missing sub-indices. "
                f"PM2.5 concentration is {pm25:.1f} µg/m³. Guidance is based on PM2.5 alone."
            )
        else:
            base_cat = "Unavailable"
            base_risk = "Unknown"
            base_guidance = "Environmental telemetry is unavailable from upstream monitoring stations. Zero synthetic values fabricated."

        # 2. Data Quality & Reliability Status Evaluation
        data_quality_notes = []
        if is_stale:
            data_quality_notes.append("Telemetry is older than 3 hours; current conditions cannot be assessed confidently.")
            confidence = "LOW"
            data_quality_status = "STALE (Age > 3 hours; relying on multi-horizon forecast)"
        elif not is_aqi_avail and pm25 is not None:
            confidence = "MEDIUM"
            data_quality_status = "PM2.5 Only (Multi-pollutant AQI sub-indices missing)"
        elif not is_aqi_avail and pm25 is None:
            data_quality_notes.append("No valid environmental telemetry received from upstream monitoring stations.")
            confidence = "NONE"
            data_quality_status = "UNAVAILABLE (Sensors unreachable; zero synthetic data fabricated)"
        else:
            confidence = "HIGH"
            data_quality_status = "FRESH (Live ground / CAMS telemetry verified)"

        # 3. Forecast Context Evaluation
        if not has_forecast:
            forecast_context = "Multi-horizon predictive forecast is currently unavailable; avoid planning around assumed future improvements."
        elif surge_detected or forecast_trend == "rising":
            forecast_context = "Multi-horizon forecast projects particulate deterioration over the next 3–6 hours; wrap up outdoor exposure early."
        elif forecast_trend == "improving":
            forecast_context = "Forecast indicates improving dispersion over the next 3–6 hours as surface winds increase."
        else:
            forecast_context = "Atmospheric conditions are projected to remain steady over the next 3–6 hours."

        # Initialize defaults
        exercise_allowed = True
        mask_advised = False
        profile_recs: List[str] = []

        # 4. Persona-Specific Deterministic Rules (Section 4)
        if not is_aqi_avail and pm25 is None:
            # Complete absence of data
            suggested_action = "Environmental sensors are offline for this location. Exercise general environmental awareness."
            relevant_activity = "Indoor & routine transit"
            reason = "No live ground or satellite telemetry could be verified; AtmosAI does not fabricate substitute measurements."
            best_window = "Check back when telemetry restores"
            duration = 30
            ventilation = "Standard indoor ventilation"
            profile_recs = [
                "Environmental sensors are offline; avoid prolonged unmonitored exposure.",
                "Rely on local municipal advisories until station telemetry restores."
            ]

        elif user_cat == "student":
            relevant_activity = "Campus walking, study commutes & outdoor sports"
            if is_stale:
                suggested_action = "Current readings are outdated (>3h old). Rely on multi-horizon forecast and exercise caution during outdoor campus activities."
                reason = "Ground telemetry age exceeds 3 hours. Atmospheric dispersion may have changed conditions across campus pathways."
                best_window = "Midday hours (if forecast indicates favorable wind)"
                duration = 30 if has_sensitivity else 45
                ventilation = "Keep windows facing busy boundary roads closed"
                profile_recs = [
                    "Assess campus conditions conservatively and rely on predictive forecasts before scheduling outdoor sports.",
                    "Choose indoor campus study spaces or shaded courtyards if atmospheric haze is observed.",
                    "Keep dormitory and study hall windows closed during evening traffic rush hours."
                ]
            elif base_cat in ("Good", "Satisfactory"):
                suggested_action = "Campus air quality is favorable; outdoor study groups and campus sports sessions can proceed normally."
                reason = f"Current CPCB AQI is {aqi} ({base_cat}), well within national clean air thresholds for student campus activities."
                best_window = "Any daylight hour"
                duration = 90
                ventilation = "Open classroom and dormitory windows for fresh air exchange"
                profile_recs = [
                    "Campus air is clean; outdoor campus activities and sports sessions can proceed without restriction.",
                    "Open classroom and dormitory windows for fresh natural cross-ventilation.",
                    "Walk or cycle between campus academic blocks freely during daylight hours."
                ]
            elif base_cat == "Moderate":
                suggested_action = "Campus air has moderate dust levels; take shaded campus routes and schedule strenuous sports after midday dispersion."
                reason = f"AQI {aqi} ({base_cat}) indicates particulate buildup that sensitive students or athletes may feel during intense training."
                best_window = "11:00 AM – 3:30 PM (optimal daytime dispersion)"
                duration = 45
                ventilation = "Ventilate study areas during peak daytime wind hours"
                profile_recs = [
                    "Take tree-lined campus paths rather than high-traffic boundary avenues.",
                    "Schedule high-exertion campus athletics between 11:00 AM and 03:30 PM.",
                    "Keep campus library and study space windows closed during peak traffic hours."
                ]
            else: # Poor, Very Poor, Severe
                suggested_action = "Elevated campus pollution warning; relocate physical education and student recreation to indoor facilities."
                reason = f"Severe particulate exposure ({base_cat}, AQI {aqi}) poses acute respiratory discomfort on campus pathways."
                best_window = "Indoor facilities recommended"
                duration = 20
                ventilation = "Keep campus library and classroom windows closed with air filtration"
                exercise_allowed = False
                mask_advised = True
                profile_recs = [
                    "Move campus physical education and student sports into indoor facilities.",
                    "Keep campus library and classroom windows closed; wear an N95 mask between academic blocks.",
                    "Sensitive students should remain indoors with active air purification."
                ]

        elif user_cat == "runner":
            relevant_activity = "Aerobic workouts, distance running & cycling"
            if is_stale:
                suggested_action = "Current readings are outdated (>3h old). Rely on multi-horizon forecast and exercise caution before high-exertion outdoor running."
                reason = "Ground telemetry age exceeds 3 hours. Local atmospheric dispersion may have altered conditions since the last record."
                best_window = "Midday hours (if forecast indicates favorable wind)"
                duration = 30 if has_sensitivity else 45
                ventilation = "Keep windows facing busy roads closed"
                profile_recs = [
                    "Current telemetry is outdated (>3h old). Rely on forecast before high-intensity outdoor running workouts.",
                    "Keep aerobic exertion moderate and monitor local breathing comfort.",
                    "Switch to indoor treadmill training if haze is noticeable on road corridors."
                ]
            elif base_cat == "Good":
                suggested_action = "Optimal conditions for tempo runs, intervals, and extended outdoor distance training."
                reason = f"AQI {aqi} and PM2.5 {pm25} µg/m³ indicate minimal pulmonary resistance and clean airway passage."
                best_window = "Early morning (06:00 – 08:30 AM)"
                duration = 90
                ventilation = "Full home ventilation"
                profile_recs = [
                    "Optimal running window: early morning (06:00 – 08:30 AM) or daytime dispersion hours.",
                    "Air quality supports unrestricted cardiovascular and endurance training.",
                    "Full home and post-workout cross-ventilation."
                ]
            elif base_cat == "Satisfactory":
                if forecast_trend == "rising" or surge_detected:
                    suggested_action = "Run early morning; conclude intense training before forecast pollution rise in the afternoon."
                    reason = f"Current AQI is {aqi} ({base_cat}), but LightGBM forecast detects rising PM2.5 over the next 3–6 hours."
                else:
                    suggested_action = "Favorable running conditions; maintain hydration and check 3h trend before evening sessions."
                    reason = f"AQI {aqi} is acceptable for cardiovascular training without special exertion limits."
                best_window = "06:30 – 08:30 AM"
                duration = 60
                ventilation = "Ventilate living spaces after morning run"
                profile_recs = [
                    "Complete outdoor distance runs during early morning hours before urban road dust accumulates.",
                    "Hydrate thoroughly and monitor multi-horizon forecast before evening sessions.",
                    "Avoid high-density arterial intersections during warm-up."
                ]
            elif base_cat == "Moderate":
                suggested_action = "Limit vigorous anaerobic intervals; stick to moderate aerobic intensity and avoid running along major arterial roads."
                reason = f"PM2.5 concentration of {pm25} µg/m³ increases particulate inhalation 4–6x during high ventilation exercise."
                best_window = "Midday (11:00 AM – 02:00 PM) when thermal lift disperses ground dust"
                duration = 40
                ventilation = "Run indoor HEPA filtration post-workout"
                exercise_allowed = True
                profile_recs = [
                    "Choose park routes with tree canopy over roadside running paths.",
                    "Cap high-intensity cardiovascular sessions to 40 minutes.",
                    "Avoid roadside running routes adjacent to heavy traffic arteries."
                ]
            else: # Poor, Very Poor, Severe
                suggested_action = "Shift training indoors (treadmill / indoor gym); high-volume outdoor aerobic exertion is inadvisable."
                reason = f"Unhealthy particulate density ({base_cat}, AQI {aqi}) causes bronchial inflammation during strenuous exercise."
                best_window = "Indoor treadmill or strength training only"
                duration = 0
                ventilation = "Keep windows sealed and run indoor air cleaner"
                exercise_allowed = False
                mask_advised = True
                profile_recs = [
                    "Suspend outdoor running workouts; heavy aerobic respiration dramatically increases particulate deposition.",
                    "Train indoors with air filtration until ambient AQI improves.",
                    "Wear a particulate mask if warm-up or transit outdoors is necessary."
                ]

        elif user_cat == "office_commuter":
            relevant_activity = "Daily vehicular commute, transit waiting & walking to office"
            if is_stale:
                suggested_action = "Current readings are outdated (>3h old). Rely on multi-horizon forecast and keep cabin air recirculating during transit commutes."
                reason = "Ground station readings exceed 3 hours. Local traffic congestion may have spiked particulate concentrations."
                best_window = "Off-peak travel hours"
                duration = 30 if has_sensitivity else 45
                ventilation = "Keep vehicle windows closed on busy expressways"
                profile_recs = [
                    "Station telemetry is outdated (>3h old). Rely on forecast for commute route planning.",
                    "Maintain vehicle AC in recirculate mode along traffic corridors.",
                    "Two-wheeler and transit commuters should keep a protective mask handy."
                ]
            elif base_cat in ("Good", "Satisfactory"):
                suggested_action = "Clean corridor conditions for daily office commute; standard public transit or two-wheeler travel is favorable."
                reason = f"Corridor air quality is {base_cat} (AQI {aqi}), with low particulate accumulation at road junctions."
                best_window = "Normal commute hours"
                duration = 60
                ventilation = "Open office windows before peak traffic hours"
                profile_recs = [
                    "Commute air quality is clear along main urban corridors.",
                    "Open car windows during midday transit when traffic emissions are dispersed.",
                    "Public transit and two-wheeler commuting can proceed with standard comfort."
                ]
            elif base_cat == "Moderate":
                suggested_action = "Set vehicle AC to internal air recirculation; two-wheeler riders should wear a particulate mask near bottleneck signals."
                reason = f"AQI {aqi} with localized exhaust buildup along arterial roads elevates commuter PM2.5 exposure."
                best_window = "Off-peak travel (prior to 08:30 AM or after 11:00 AM)"
                duration = 45
                ventilation = "Keep vehicle windows closed on busy expressways"
                profile_recs = [
                    "Keep vehicle windows closed and set air conditioning to recirculation mode.",
                    "Two-wheeler commuters should wear a particulate mask near traffic signals.",
                    "Travel outside peak rush hours if flexible schedules permit."
                ]
            else: # Poor, Very Poor, Severe
                suggested_action = "Heavy commute pollution advisory; wear an N95 mask on roads and enable cabin air recirculation."
                reason = f"Dangerous corridor particulate density ({base_cat}, AQI {aqi}) at traffic intersections."
                best_window = "Stagger commute to off-peak or explore remote work if viable"
                duration = 20
                ventilation = "Seal vehicle cabin and use office HEPA filtration"
                mask_advised = True
                profile_recs = [
                    "Keep car windows tightly shut with HEPA/cabin filtration on recirculate.",
                    "Two-wheeler and pedestrian commuters should wear an N95 mask along arterial roads.",
                    "Stagger commute to off-peak or explore remote work if viable."
                ]

        elif user_cat == "outdoor_worker":
            relevant_activity = "Continuous outdoor shift work, delivery & construction"
            if is_stale:
                suggested_action = "Current readings are outdated (>3h old). Outdoor workers should rely on predictive forecast, carry particulate masks, and take indoor rest breaks."
                reason = "Ground station telemetry exceeds 3 hours. Particulate exposure may vary across road corridors."
                best_window = "Midday breaks in shaded, low-dust zones"
                duration = 45
                ventilation = "Rest in indoor or shaded filtered rest areas"
                profile_recs = [
                    "Telemetry is older than 3 hours. Outdoor workers should rely on predictive forecasts.",
                    "Carry an N95 particulate mask and take scheduled rest breaks in clean indoor areas.",
                    "Maintain high hydration to support airway mucosal clearance."
                ]
            elif base_cat in ("Good", "Satisfactory"):
                suggested_action = "Favorable atmospheric conditions for extended outdoor work shifts; maintain standard hydration."
                reason = f"Ambient AQI {aqi} ({base_cat}) does not present occupational environmental hazard today."
                best_window = "Full shift"
                duration = 120
                ventilation = "Standard site ventilation"
                profile_recs = [
                    "Safe atmospheric conditions for outdoor work shifts and deliveries; maintain regular hydration.",
                    "Stay well hydrated during long outdoor work intervals.",
                    "Standard site ventilation is safe."
                ]
            elif base_cat == "Moderate":
                suggested_action = "Take scheduled hydration breaks away from active vehicular traffic; wear dust protection during prolonged shifts."
                reason = f"Prolonged 8-hour exposure at AQI {aqi} ({base_cat}) causes cumulative airway dryness and fatigue."
                best_window = "Midday breaks in shaded, low-dust zones"
                duration = 60
                ventilation = "Rest in indoor or shaded filtered rest areas"
                profile_recs = [
                    "Take rest breaks away from heavy idling traffic in shaded zones.",
                    "Wear a particulate dust mask during peak afternoon traffic shifts.",
                    "Drink water regularly to soothe respiratory passages."
                ]
            else: # Poor, Very Poor, Severe
                suggested_action = "Occupational pollution warning: Mandatory N95 particulate mask, frequent indoor respite breaks, and reduced heavy lifting."
                reason = f"Sustained physical labor in {base_cat} air (AQI {aqi}) poses acute respiratory strain on workers."
                best_window = "Rotate outdoor shifts; rest indoors every 45 minutes"
                duration = 45
                ventilation = "Stay in sealed rest rooms with active air purifiers"
                exercise_allowed = False
                mask_advised = True
                profile_recs = [
                    "Mandatory N95 mask usage during outdoor delivery and road work shifts.",
                    "Rotate shifts into indoor filtered resting areas every 45 minutes.",
                    "Limit high-exertion manual lifting during peak midday particulate stagnation."
                ]

        elif user_cat == "parent":
            relevant_activity = "Children playground activities, stroller walks & school trips"
            if is_stale:
                suggested_action = "Current readings are outdated (>3h old). Rely on multi-horizon forecast before scheduling children's playground play or stroller outings."
                reason = "Telemetry age exceeds 3 hours. Assess child outdoor play conservatively."
                best_window = "11:00 AM – 03:00 PM"
                duration = 30
                ventilation = "Run indoor HEPA purifier in children's bedrooms"
                profile_recs = [
                    "Current readings are outdated (>3h old). Plan children's playground trips during midday dispersion.",
                    "Keep infant strollers away from street curb vehicle exhaust.",
                    "Rely on predictive forecast before planning evening park visits."
                ]
            elif base_cat == "Good":
                suggested_action = "Excellent air quality for infant stroller walks, park visits, and unrestricted children's playground play."
                reason = f"Clean atmospheric readings (AQI {aqi}, PM2.5 {pm25} µg/m³) safeguard developing child lungs."
                best_window = "09:00 – 11:30 AM or 04:00 – 06:00 PM"
                duration = 75
                ventilation = "Aerate children's rooms with fresh outdoor air"
                profile_recs = [
                    "Children can engage in unrestricted outdoor playground play and park games.",
                    "Aerate children's rooms with fresh outdoor air.",
                    "Infant stroller walks are optimal during morning or late afternoon."
                ]
            elif base_cat == "Satisfactory":
                suggested_action = "Family outdoor activities can proceed safely; keep stroller walks in green parks rather than busy traffic streets."
                reason = f"Acceptable air quality ({base_cat}, AQI {aqi}); children inhale more air per kg of body weight near exhaust level."
                best_window = "10:00 AM – 04:00 PM"
                duration = 60
                ventilation = "Ventilate nurseries midday when sun aids dispersion"
                profile_recs = [
                    "Schedule outdoor playground outings between 10:00 AM and 04:00 PM when air mixing is favorable.",
                    "Keep stroller walks in green parks rather than busy traffic streets.",
                    "Ventilate nurseries midday when sunlight aids urban dispersion."
                ]
            elif base_cat == "Moderate":
                suggested_action = "Moderate air quality: Move children's high-energy play to indoor spaces or parks with dense tree foliage."
                reason = f"Developing lungs are sensitive to particulate density at AQI {aqi}; reduce continuous running exertion."
                best_window = "11:00 AM – 03:00 PM"
                duration = 35
                ventilation = "Run indoor HEPA purifier in children's bedrooms"
                exercise_allowed = True
                profile_recs = [
                    "Move children's high-energy play to indoor spaces or parks with dense tree foliage.",
                    "Run indoor HEPA air purifiers in children's bedrooms.",
                    "Close street-facing windows before evening traffic builds up."
                ]
            else: # Poor, Very Poor, Severe
                suggested_action = "Child air safety alert: Keep infants and children indoors; cancel outdoor sports and close home windows."
                reason = f"Hazardous fine dust ({base_cat}, AQI {aqi}) significantly increases risk of acute pediatric cough and wheeze."
                best_window = "Keep children indoors"
                duration = 0
                ventilation = "Seal windows and run indoor air purifiers continuously"
                exercise_allowed = False
                mask_advised = True
                profile_recs = [
                    "Keep infants and young children indoors with windows sealed.",
                    "Cancel outdoor playground trips and school sports activities.",
                    "Run indoor air purifiers continuously in living and sleeping quarters."
                ]

        elif user_cat == "respiratory_sensitive":
            relevant_activity = "Outdoor travel with respiratory sensitivity precaution"
            if is_stale:
                suggested_action = "Current readings are outdated (>3h old). Carry prescribed inhaler / relief medication and rely on predictive forecast before outdoor trips."
                reason = "Readings exceed 3 hours. Sensitive individuals should exercise high precaution."
                best_window = "Midday hours (if forecast is favorable)"
                duration = 20
                ventilation = "Keep windows facing roadways closed"
                mask_advised = True
                profile_recs = [
                    "Readings are outdated (>3h old). Keep prescribed inhaler and preventive care accessible during outdoor travel.",
                    "Wear an N95 particulate mask if traveling along dusty transit corridors.",
                    "Rely on multi-horizon forecast before planning outdoor activities."
                ]
            elif base_cat in ("Good", "Satisfactory"):
                suggested_action = "Air quality is favorable; sensitive individuals can engage in outdoor activities while keeping relief care accessible."
                reason = f"Clean atmospheric readings ({base_cat}, AQI {aqi}) allow comfortable outdoor respiration."
                best_window = "Daylight hours"
                duration = 60
                ventilation = "Natural ventilation"
                profile_recs = [
                    "Outdoor walks are permissible; keep prescribed inhaler accessible as a precaution.",
                    "Wear a light mask or avoid walking along heavy transit corridors.",
                    "Monitor multi-horizon forecast before evening activities."
                ]
            elif base_cat == "Moderate":
                suggested_action = "Moderate particulate density: carry prescribed inhaler / medication and wear an N95 mask near traffic corridors."
                reason = f"AQI {aqi} with particulate matter can trigger bronchial sensitivity or asthma flares."
                best_window = "11:00 AM – 02:00 PM"
                duration = 30
                ventilation = "Run indoor HEPA purifier"
                mask_advised = True
                profile_recs = [
                    "Keep prescribed inhaler or allergy relief medication readily accessible at all times.",
                    "Wear an N95 particulate mask near heavy traffic or during outdoor transit.",
                    "Limit outdoor exertion to 30 minutes during midday dispersion."
                ]
            else: # Poor, Very Poor, Severe
                suggested_action = "Respiratory health warning: stay indoors, keep inhaler / medication ready, and use air purification."
                reason = f"Dangerous particulate levels ({base_cat}, AQI {aqi}) trigger acute airway constriction."
                best_window = "Remain indoors"
                duration = 0
                ventilation = "Seal living spaces and run air purifier continuously"
                exercise_allowed = False
                mask_advised = True
                profile_recs = [
                    "Stay strictly indoors with windows sealed and air filtration running.",
                    "Keep prescribed inhaler immediately accessible; monitor breathing comfort closely.",
                    "Wear an N95 mask for any unavoidable outdoor transit."
                ]

        else: # general_public
            relevant_activity = "Routine daily errands, leisure & household activities"
            if is_stale:
                suggested_action = "Current readings are outdated (>3h old). Rely on multi-horizon forecast and exercise caution before high-exertion outdoor activity."
                reason = "Telemetry age exceeds 3 hours. Local atmospheric dispersion may have altered conditions since the last record."
                best_window = "Midday hours (if forecast indicates favorable wind)"
                duration = 30 if has_sensitivity else 45
                ventilation = "Keep windows facing busy roads closed"
                profile_recs = [
                    "Current readings are outdated (>3h old). Rely on multi-horizon forecast for daily planning.",
                    "Keep windows facing busy roadways closed during evening rush hours."
                ]
            elif base_cat in ("Good", "Satisfactory"):
                suggested_action = f"Air quality is {base_cat.lower()}; standard daily errands, shopping, and outdoor routines can proceed normally."
                reason = f"AQI {aqi} ({base_cat}) indicates safe ambient atmospheric conditions throughout {location_name}."
                best_window = "Any daylight hour"
                duration = 90
                ventilation = "Open windows for natural cross-ventilation"
                profile_recs = [
                    "Air quality is favorable for standard daily errands, shopping, and outdoor routines.",
                    "Open windows for natural cross-ventilation during peak daytime wind hours."
                ]
            elif base_cat == "Moderate":
                suggested_action = "Moderate pollution present; sensitive individuals should reduce prolonged outdoor exertion; ventilate homes midday."
                reason = f"Elevated PM2.5 ({pm25} µg/m³, AQI {aqi}) warrants mindfulness during prolonged street exposure."
                best_window = "11:00 AM – 03:30 PM"
                duration = 45
                ventilation = "Open windows briefly during midday when dispersion is highest"
                profile_recs = [
                    "Moderate air pollution: open windows briefly during midday when dispersion is highest.",
                    "Sensitive individuals should reduce prolonged outdoor exertion along traffic routes."
                ]
            else: # Poor, Very Poor, Severe
                suggested_action = f"High pollution advisory ({base_cat}); minimize unnecessary outdoor exposure and keep living spaces sealed."
                reason = f"Particulate levels (AQI {aqi}) are in the {base_cat} category; continuous breathing can cause throat and eye irritation."
                best_window = "Remain indoors where possible"
                duration = 20
                ventilation = "Keep windows facing roadways closed; use indoor air filtration"
                exercise_allowed = False
                mask_advised = True
                profile_recs = [
                    "Minimize unnecessary outdoor exposure and keep living spaces sealed.",
                    "Wear an N95 particulate mask outdoors and run indoor air filtration."
                ]

        # Attach sensitivity precaution if applicable and not already present
        if has_sensitivity and not any("inhaler" in r.lower() for r in profile_recs):
            profile_recs.insert(0, f"Sensitivity precaution ({sens_pref}): Keep prescribed inhalers and preventive care accessible when outside.")

        # Attach stale telemetry warning if applicable
        if is_stale and not any("older than 3 hours" in r.lower() or "outdated" in r.lower() for r in profile_recs):
            profile_recs.insert(0, "DATA STALE WARNING: Ground readings are older than 3 hours. Atmospheric dispersion or sudden local emissions may have changed actual air quality. Exercise caution.")

        return DeterministicRecommendation(
            risk_category=base_risk,
            general_guidance=base_guidance,
            suggested_action=suggested_action,
            relevant_activity=relevant_activity,
            reason_for_recommendation=reason,
            aqi_category=base_cat,
            is_stale=is_stale,
            is_aqi_available=is_aqi_avail,
            is_forecast_available=has_forecast,
            confidence_level=confidence,
            data_quality_status=data_quality_status,
            forecast_context=forecast_context,
            outdoor_exercise_allowed=exercise_allowed,
            mask_advised=mask_advised,
            best_time_window=best_window,
            recommended_duration_mins=duration,
            ventilation_advice=ventilation,
            profile_specific_recommendations=profile_recs
        )

# Global singleton
recommendation_engine = RecommendationEngine()
