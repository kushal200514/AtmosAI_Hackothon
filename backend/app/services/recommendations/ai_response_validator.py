"""
AI Response Validator.
Enforces the core principle: CODE DECIDES. AI ONLY EXPLAINS.
Validates Gemini explanations against deterministic environmental facts.
Rejects hallucinated numbers, altered AQI categories, medical diagnoses, and action contradictions.
"""
import re
import logging
from typing import Dict, Any, Tuple, Optional, List

from app.services.recommendations.recommendation_engine import DeterministicRecommendation

logger = logging.getLogger("atmosai.validator")

ALL_AQI_CATEGORIES = ["Good", "Satisfactory", "Moderate", "Poor", "Very Poor", "Severe"]

FORBIDDEN_MEDICAL_PATTERNS = [
    r"\bdiagnos(?:ed|is|ing)\b",
    r"\bprescrib(?:ed|tion|ing)\b",
    r"\bcure(?:s|d|ing)?\b",
    r"\btreat(?:ment|ing)?\s+disease\b",
    r"\bmedical\s+advice\b",
    r"\byou\s+have\s+(?:asthma|copd|bronchitis|pneumonia)\b"
]

class AIResponseValidator:
    """
    Validates that Gemini responses adhere strictly to verified environmental telemetry
    and deterministic rule-engine decisions without fabrication.
    """

    def validate(
        self,
        ai_data: Dict[str, Any],
        verified_facts: Dict[str, Any],
        rule_decision: DeterministicRecommendation
    ) -> Tuple[bool, Optional[str]]:
        """
        Validates LLM generated explanation against ground truth.
        Returns (is_valid: bool, failure_reason: Optional[str]).
        """
        if not isinstance(ai_data, dict):
            return False, "AI response is not a valid JSON dictionary."

        headline = str(ai_data.get("headline_summary", ""))
        explanation = str(ai_data.get("evidence_based_explanation", ""))
        status = str(ai_data.get("current_environmental_status", ""))
        action = str(ai_data.get("recommended_action", ""))
        combined_text = f"{headline} {explanation} {status} {action}".lower()

        # 1. AQI Category Contradiction Check
        expected_cat = rule_decision.aqi_category
        if expected_cat and expected_cat != "Unavailable":
            conflicting_cats = [c for c in ALL_AQI_CATEGORIES if c.lower() != expected_cat.lower()]
            for wrong_cat in conflicting_cats:
                w = wrong_cat.lower()
                wrong_patterns = [
                    rf"\bcategory\s+(?:is\s+)?{w}\b",
                    rf"\bair\s+(?:quality\s+)?(?:is\s+)?{w}\b",
                    rf"\baqi\s+(?:category\s+)?(?:is\s+)?{w}\b",
                    rf"\b{w}\s+(?:pollution|air|alert|condition|category|weather)\b",
                    rf"\bcurrent\s+(?:air\s+)?(?:category\s+is\s+|quality\s+is\s+|conditions?\s+are\s+)?{w}\b",
                ]
                if any(re.search(p, combined_text) for p in wrong_patterns):
                    return False, f"Category mismatch: Code determined '{expected_cat}', but AI asserted '{wrong_cat}'."

        # 2. Hallucinated AQI when True AQI is Unavailable
        true_aqi = verified_facts.get("aqi")
        if true_aqi is None:
            # Check if AI hallucinated an AQI number (e.g. "aqi 150", "aqi is 75")
            aqi_hallucination = re.search(r"\baqi\s+(?:is\s+|of\s+|level\s+)?(\d{1,3})\b", combined_text)
            if aqi_hallucination:
                return False, f"Hallucinated AQI: Code has missing AQI, but AI invented '{aqi_hallucination.group(0)}'."

        # 3. Numeric Divergence Check on Verified PM2.5
        true_pm25 = verified_facts.get("pm25")
        if true_pm25 is not None:
            # Look for explicit claims of PM2.5 concentration in AI text
            pm_matches = re.findall(r"pm2\.?5\s*(?:is|of|concentration|level)?\s*[:=]?\s*(\d+(?:\.\d+)?)", combined_text)
            for m in pm_matches:
                try:
                    val = float(m)
                    # If AI cited a PM2.5 value differing by more than 50% from verified ground truth
                    if abs(val - true_pm25) > max(15.0, true_pm25 * 0.5):
                        return False, f"Numeric distortion: Verified PM2.5 is {true_pm25} µg/m³, but AI claimed {val} µg/m³."
                except ValueError:
                    continue

        # 4. Action Contradiction Check
        # If code strictly disallowed outdoor exercise, but AI says outdoor exercise allowed
        ai_exercise = ai_data.get("outdoor_exercise_allowed")
        if rule_decision.outdoor_exercise_allowed is False and ai_exercise is True:
            return False, "Safety contradiction: Rule engine restricted outdoor exercise, but AI permitted it."

        # If code advised particulate masks (Severe / Very Poor / Poor), but AI says masks not needed
        if rule_decision.mask_advised is True:
            ai_mask = str(ai_data.get("mask_recommendation", "")).lower()
            if "no mask" in ai_mask or "not required" in ai_mask:
                return False, "Mask recommendation contradiction: Code advised particulate mask, but AI dismissed it."

        # 5. Medical Diagnosis & Treatment Prohibitions
        for pattern in FORBIDDEN_MEDICAL_PATTERNS:
            if re.search(pattern, combined_text):
                return False, f"Medical boundary violation: Forbidden pattern '{pattern}' detected in explanation."

        return True, None

    def build_safe_fallback(
        self,
        rule_decision: DeterministicRecommendation,
        verified_facts: Dict[str, Any],
        user_context: Dict[str, Any],
        rejection_reason: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Builds a robust, deterministic, transparent fallback explanation when Gemini
        fails validation, is unavailable, or introduces hallucinations.
        """
        lang = user_context.get("preferred_language", "en")
        loc_name = user_context.get("location_name", "Bengaluru")
        aqi_str = f"AQI {verified_facts.get('aqi')}" if verified_facts.get('aqi') is not None else "AQI Unavailable"
        pm_str = f"PM2.5 {verified_facts.get('pm25')} µg/m³" if verified_facts.get('pm25') is not None else "PM2.5 Unavailable"

        headline = f"Air Quality Status: {rule_decision.aqi_category} ({aqi_str}) in {loc_name}"
        
        explanation_parts = [
            rule_decision.general_guidance,
            f"Why AtmosAI recommends this: {rule_decision.reason_for_recommendation}",
            f"Forecast context: {rule_decision.forecast_context}"
        ]
        if rule_decision.is_stale:
            explanation_parts.append("Note: Telemetry is older than 3 hours. Exercise conservative awareness.")

        explanation = " ".join(explanation_parts)

        if rule_decision.profile_specific_recommendations:
            profile_recs = list(rule_decision.profile_specific_recommendations)
        else:
            profile_recs = [
                rule_decision.suggested_action,
                f"Recommended window: {rule_decision.best_time_window} (limit to {rule_decision.recommended_duration_mins} mins).",
                f"Ventilation: {rule_decision.ventilation_advice}."
            ]

        val_details = (
            f"Rule Engine Fallback active ({rejection_reason})"
            if rejection_reason
            else "Verified Deterministic Rule Engine (Gemini bypassed or offline)"
        )

        return {
            "current_environmental_status": f"Current air quality is {rule_decision.aqi_category} ({aqi_str}, {pm_str}) in {loc_name}.",
            "recommended_action": rule_decision.suggested_action,
            "headline_summary": headline,
            "evidence_based_explanation": explanation,
            "profile_specific_recommendations": profile_recs,
            "outdoor_exercise_allowed": rule_decision.outdoor_exercise_allowed,
            "best_time_window": rule_decision.best_time_window,
            "recommended_duration_minutes": rule_decision.recommended_duration_mins,
            "mask_recommendation": "N95 Particulate Mask Advised" if rule_decision.mask_advised else "Optional",
            "indoor_ventilation_advice": rule_decision.ventilation_advice,
            "ai_validation_passed": False if rejection_reason else True,
            "ai_validation_details": val_details
        }

# Global singleton
ai_response_validator = AIResponseValidator()
