from typing import Dict, Any, List
from app.schemas.profile import (
    UserProfile, 
    UserCategory, 
    PersonalizedViewConfig, 
    ActivityWindowScore,
    SensitivityPreference
)
from app.schemas.forecast import ForecastResponse
from app.schemas.environmental import LiveEnvironmentalData

# All standard reusable dashboard widgets
ALL_WIDGETS = [
    "current_aqi",
    "pm25_forecast",
    "weather",
    "ai_insight",
    "activity_planner",
    "pollution_map",
    "environmental_alerts",
    "local_stations"
]

class PersonalizationEngine:
    """
    Central Personalization Engine mapping user onboarding profiles
    to dynamic widget ordering, activity planner prioritizations,
    alert filter matrices, and AI prompting constraints.
    """

    def resolve_config(self, profile: UserProfile) -> PersonalizedViewConfig:
        cat = profile.user_category
        is_sensitive = profile.sensitivity_preference != SensitivityPreference.NONE

        if cat == UserCategory.STUDENT:
            order = [
                "current_aqi",
                "environmental_alerts",
                "activity_planner",
                "pm25_forecast",
                "weather",
                "ai_insight",
                "local_stations",
                "pollution_map"
            ]
            activities = ["campus_walks", "outdoor_sports", "cycling", "walking"]
            alerts = ["surge_warnings", "high_pollution"]
            headline = "Campus & Student Environmental Intelligence"

        elif cat == UserCategory.RUNNER:
            order = [
                "pm25_forecast",
                "activity_planner",
                "weather",
                "current_aqi",
                "ai_insight",
                "environmental_alerts",
                "local_stations",
                "pollution_map"
            ]
            activities = ["running", "cycling", "interval_training", "walking"]
            alerts = ["surge_warnings", "high_pollution", "improving_air"]
            headline = "Workout Window & Multi-Horizon Trend"

        elif cat == UserCategory.CYCLIST:
            order = [
                "pm25_forecast",
                "activity_planner",
                "weather",
                "current_aqi",
                "pollution_map",
                "environmental_alerts",
                "ai_insight",
                "local_stations"
            ]
            activities = ["cycling", "morning_ride", "evening_ride", "walking"]
            alerts = ["surge_warnings", "high_pollution", "improving_air"]
            headline = "Cycling Exposure & Wind-PM2.5 Route Conditions"

        elif cat == UserCategory.OFFICE_COMMUTER:
            order = [
                "pm25_forecast",
                "environmental_alerts",
                "current_aqi",
                "weather",
                "ai_insight",
                "activity_planner",
                "pollution_map",
                "local_stations"
            ]
            activities = ["commuting", "morning_transit", "evening_transit", "walking"]
            alerts = ["commute_window_alerts", "surge_warnings"]
            headline = "Corridor Transit Pollution & Commute Planner"

        elif cat == UserCategory.OUTDOOR_WORKER:
            order = [
                "current_aqi",
                "environmental_alerts",
                "pm25_forecast",
                "weather",
                "ai_insight",
                "activity_planner",
                "local_stations",
                "pollution_map"
            ]
            activities = ["street_deliveries", "field_transit", "outdoor_shifts", "walking"]
            alerts = ["high_pollution", "surge_warnings"]
            headline = "Shift Safety & On-Road Environmental Telemetry"

        elif cat == UserCategory.PARENT:
            order = [
                "ai_insight",
                "activity_planner",
                "current_aqi",
                "pm25_forecast",
                "environmental_alerts",
                "weather",
                "pollution_map",
                "local_stations"
            ]
            activities = ["playground_trips", "stroller_walks", "park_visits", "school_transit"]
            alerts = ["high_pollution", "surge_warnings"]
            headline = "Family Outdoor Safety & Pediatric Air Quality"

        else: # GENERAL_PUBLIC
            order = [
                "current_aqi",
                "pm25_forecast",
                "weather",
                "ai_insight",
                "pollution_map",
                "environmental_alerts",
                "activity_planner",
                "local_stations"
            ]
            activities = ["walking", "errands", "outdoor_recreation", "cycling"]
            alerts = ["high_pollution", "surge_warnings"]
            headline = " Forecast"

        # Apply user preferred activities if specified
        if profile.preferred_activities and len(profile.preferred_activities) > 0:
            # Merge with high priority to user chosen activities
            custom_acts = [a for a in profile.preferred_activities if a]
            for a in activities:
                if a not in custom_acts:
                    custom_acts.append(a)
            activities = custom_acts

        # Visible widgets based on environmental_info_preferences
        visible = list(order)
        # If user explicitly opted out of map, exclude
        if "no_map" in profile.environmental_info_preferences and "pollution_map" in visible:
            visible.remove("pollution_map")

        cautious = is_sensitive or (cat == UserCategory.PARENT)

        return PersonalizedViewConfig(
            widget_order=order,
            visible_widgets=visible,
            priority_headline=headline,
            primary_alert_types=alerts,
            planner_activities=activities[:4],
            language=profile.preferred_language,
            cautious_mode=cautious
        )

    def evaluate_planner_windows(
        self, 
        profile: UserProfile, 
        forecast: ForecastResponse, 
        live: LiveEnvironmentalData
    ) -> List[ActivityWindowScore]:
        """
        Evaluates forecast windows for preferred activities.
        Compares +3h, +4h, +5h, +6h windows and identifies why a specific window is best.
        """
        config = self.resolve_config(profile)
        activities = config.planner_activities
        results = []

        curr_pm = live.pm25 if live.pm25 is not None else 25.0
        points = forecast.forecast_points if forecast and forecast.forecast_points else []

        # Find the window with the lowest PM2.5
        best_pt = None
        min_pm = curr_pm
        for pt in points:
            if pt.predicted_pm25 < min_pm:
                min_pm = pt.predicted_pm25
                best_pt = pt

        for act in activities:
            act_name = act.replace("_", " ").title()

            # Current Window (Now)
            score_now = max(10, min(100, int(100 - (curr_pm * 1.2))))
            if config.cautious_mode:
                score_now = max(5, score_now - 15)

            status_now = "Optimal" if score_now >= 75 else ("Moderate" if score_now >= 50 else "Challenging")
            results.append(ActivityWindowScore(
                activity_name=act_name,
                horizon_label="Current Window (Now)",
                target_time="Now",
                predicted_pm25=round(curr_pm, 1),
                suitability_score=score_now,
                status=status_now,
                explanation=f"Ambient PM2.5 is {curr_pm:.1f} µg/m³. {status_now} window for {act_name.lower()}."
            ))

            # Future Horizons
            for pt in points:
                pm = pt.predicted_pm25
                score = max(10, min(100, int(100 - (pm * 1.2))))
                if config.cautious_mode:
                    score = max(5, score - 15)

                status = "Optimal" if score >= 75 else ("Moderate" if score >= 50 else "Challenging")
                
                # Explanation of why this window is favorable or challenging
                delta = pm - curr_pm
                if delta < -2.0:
                    why = f"Favorable window: particulate levels drop by {abs(delta):.1f} µg/m³ due to active wind dispersion."
                elif delta > 4.0:
                    why = f"Caution advised: PM2.5 increases by +{delta:.1f} µg/m³ as evening congestion intensifies."
                else:
                    why = f"Stable air quality expected near {pm:.1f} µg/m³."

                results.append(ActivityWindowScore(
                    activity_name=act_name,
                    horizon_label=pt.target_time_label,
                    target_time=pt.target_time_label.split(" ")[0],
                    predicted_pm25=round(pm, 1),
                    suitability_score=score,
                    status=status,
                    explanation=why
                ))

        return results

personalization_engine = PersonalizationEngine()

