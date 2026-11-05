import pytest
from unittest.mock import patch, MagicMock
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.services.recommendations.aqi_rules import get_cpcb_category_info, get_cpcb_category_from_value
from app.services.recommendations.recommendation_engine import recommendation_engine
from app.services.recommendations.ai_response_validator import ai_response_validator
from app.services.recommendations.ai_explanation_service import ai_explanation_service

def test_good_aqi_cpcb():
    """Test Good AQI (0–50) maps correctly and allows full outdoor exertion."""
    res = recommendation_engine.evaluate(aqi=35, pm25=12.0, user_category="general_public")
    assert res.aqi_category == "Good"
    assert res.risk_category == "Low"
    assert res.outdoor_exercise_allowed is True
    assert res.mask_advised is False
    assert "favourable" in res.general_guidance.lower()

def test_satisfactory_aqi_cpcb():
    """Test Satisfactory AQI (51–100) generates acceptable baseline guidance."""
    res = recommendation_engine.evaluate(aqi=75, pm25=28.0, user_category="runner")
    assert res.aqi_category == "Satisfactory"
    assert res.risk_category == "Low-Moderate"
    assert res.outdoor_exercise_allowed is True
    assert "acceptable" in res.general_guidance.lower()

def test_moderate_aqi_cpcb():
    """Test Moderate AQI (101–200) advises sensitive individuals to reduce prolonged exertion."""
    res = recommendation_engine.evaluate(aqi=145, pm25=55.0, user_category="student")
    assert res.aqi_category == "Moderate"
    assert res.risk_category == "Moderate"
    assert "sensitive" in res.suggested_action.lower() or "moderate" in res.suggested_action.lower()

def test_poor_aqi_cpcb():
    """Test Poor AQI (201–300) restricts prolonged exertion and recommends masks near roads."""
    res = recommendation_engine.evaluate(aqi=240, pm25=110.0, user_category="office_commuter")
    assert res.aqi_category == "Poor"
    assert res.risk_category == "High"
    assert res.mask_advised is True
    assert "recirculation" in res.suggested_action.lower() or "mask" in res.suggested_action.lower()

def test_very_poor_aqi_cpcb():
    """Test Very Poor AQI (301–400) advises avoiding prolonged outdoor activity."""
    res = recommendation_engine.evaluate(aqi=340, pm25=190.0, user_category="runner")
    assert res.aqi_category == "Very Poor"
    assert res.risk_category == "Very High"
    assert res.outdoor_exercise_allowed is False
    assert res.mask_advised is True
    assert "indoor" in res.suggested_action.lower()

def test_severe_aqi_cpcb():
    """Test Severe AQI (401–500) triggers critical emergency warning."""
    res = recommendation_engine.evaluate(aqi=450, pm25=310.0, user_category="outdoor_worker")
    assert res.aqi_category == "Severe"
    assert res.risk_category == "Critical"
    assert res.outdoor_exercise_allowed is False
    assert res.mask_advised is True
    assert "mandatory" in res.suggested_action.lower() or "avoid" in res.suggested_action.lower()

def test_missing_aqi_handled_without_inventing_category():
    """When overall AQI is missing, category must be Unavailable; PM2.5 is kept separate."""
    res = recommendation_engine.evaluate(aqi=None, pm25=28.5, user_category="general_public")
    assert res.aqi_category == "Unavailable"
    assert res.is_aqi_available is False
    assert "PM2.5 Only" in res.data_quality_status

def test_stale_measurement_handling():
    """Stale data (>3h) must not be called live; confidence is downgraded."""
    res = recommendation_engine.evaluate(
        aqi=80, 
        pm25=30.0, 
        freshness_status="STALE",
        user_category="general_public"
    )
    assert res.is_stale is True
    assert res.confidence_level == "LOW"
    assert "outdated" in res.suggested_action.lower() or "stale" in res.suggested_action.lower()

def test_missing_forecast_handling():
    """When forecast points are absent, forecast context explicitly notes unavailability."""
    res = recommendation_engine.evaluate(
        aqi=65, 
        pm25=22.0, 
        forecast_points=[],
        user_category="runner"
    )
    assert res.is_forecast_available is False
    assert "unavailable" in res.forecast_context.lower()

def test_validator_rejects_hallucinated_aqi_category():
    """AIResponseValidator must reject an AI response that contradicts code's AQI category."""
    rule_dec = recommendation_engine.evaluate(aqi=40, pm25=12.0, user_category="general_public")
    assert rule_dec.aqi_category == "Good"

    # Hallucinated response claiming "Severe"
    fake_ai = {
        "headline_summary": "Dangerous Severe Pollution Alert Today!",
        "current_environmental_status": "Current air category is severe in Bengaluru.",
        "recommended_action": "Avoid all outdoor activities.",
        "evidence_based_explanation": "Particulate matter is dangerously high.",
        "outdoor_exercise_allowed": False
    }

    is_valid, fail_reason = ai_response_validator.validate(
        ai_data=fake_ai,
        verified_facts={"aqi": 40, "pm25": 12.0, "aqi_category": "Good"},
        rule_decision=rule_dec
    )
    assert is_valid is False
    assert "Category mismatch" in fail_reason

def test_validator_rejects_hallucinated_aqi_number_when_missing():
    """AIResponseValidator must reject invented numerical AQI when actual AQI is None."""
    rule_dec = recommendation_engine.evaluate(aqi=None, pm25=35.0, user_category="general_public")
    assert rule_dec.aqi_category == "Unavailable"

    fake_ai = {
        "headline_summary": "Current AQI is 185 in Indiranagar.",
        "current_environmental_status": "AQI level 185 recorded.",
        "recommended_action": "Check conditions.",
        "evidence_based_explanation": "Moderate dust."
    }

    is_valid, fail_reason = ai_response_validator.validate(
        ai_data=fake_ai,
        verified_facts={"aqi": None, "pm25": 35.0, "aqi_category": "Unavailable"},
        rule_decision=rule_dec
    )
    assert is_valid is False
    assert "Hallucinated AQI" in fail_reason

def test_validator_rejects_exercise_safety_contradiction():
    """Validator rejects AI that permits exercise when code strictly disallowed it."""
    rule_dec = recommendation_engine.evaluate(aqi=420, pm25=280.0, user_category="runner")
    assert rule_dec.outdoor_exercise_allowed is False

    fake_ai = {
        "headline_summary": "Severe air quality today.",
        "current_environmental_status": "Severe air.",
        "recommended_action": "Go for a long morning marathon run.",
        "evidence_based_explanation": "Exertion is fine.",
        "outdoor_exercise_allowed": True # Contradicts code!
    }

    is_valid, fail_reason = ai_response_validator.validate(
        ai_data=fake_ai,
        verified_facts={"aqi": 420, "pm25": 280.0, "aqi_category": "Severe"},
        rule_decision=rule_dec
    )
    assert is_valid is False
    assert "Safety contradiction" in fail_reason

def test_validator_rejects_medical_diagnosis_claims():
    """Validator rejects AI generating medical diagnoses or prescribing drugs."""
    rule_dec = recommendation_engine.evaluate(aqi=150, pm25=60.0, user_category="student")
    
    fake_ai = {
        "headline_summary": "Moderate air quality.",
        "current_environmental_status": "Moderate air.",
        "recommended_action": "You have asthma and need prescribed antibiotics for this infection.",
        "evidence_based_explanation": "Medical diagnosis proves acute bronchitis.",
        "outdoor_exercise_allowed": True
    }

    is_valid, fail_reason = ai_response_validator.validate(
        ai_data=fake_ai,
        verified_facts={"aqi": 150, "pm25": 60.0, "aqi_category": "Moderate"},
        rule_decision=rule_dec
    )
    assert is_valid is False
    assert "Medical boundary violation" in fail_reason

def test_safe_fallback_construction():
    """When validation fails, build_safe_fallback produces authoritative, uncorrupted output."""
    rule_dec = recommendation_engine.evaluate(aqi=70, pm25=25.0, user_category="parent")
    fallback = ai_response_validator.build_safe_fallback(
        rule_decision=rule_dec,
        verified_facts={"aqi": 70, "pm25": 25.0},
        user_context={"preferred_language": "en", "location_name": "Bengaluru"},
        rejection_reason="Hallucination detected"
    )
    assert fallback["ai_validation_passed"] is False
    assert "Rule Engine Fallback active" in fallback["ai_validation_details"]
    assert "Satisfactory" in fallback["current_environmental_status"]
    assert fallback["recommended_action"] == rule_dec.suggested_action

def test_all_six_user_personas_deterministic_rules():
    """Verify distinct, customized actionable output for all six personas."""
    personas = ["student", "runner", "office_commuter", "outdoor_worker", "parent", "general_public"]
    actions = set()

    for p in personas:
        res = recommendation_engine.evaluate(aqi=160, pm25=65.0, user_category=p)
        assert res.suggested_action not in actions
        actions.add(res.suggested_action)
        assert res.relevant_activity is not None
        assert res.reason_for_recommendation is not None
