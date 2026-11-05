"""
AtmosAI Indian National Air Quality Index (NAQI) Calculator
Calculates sub-indices and overall AQI based on Central Pollution Control Board (CPCB) standards.
Supports multi-pollutant index derivation (PM2.5, PM10, NO2, SO2, CO, O3) and safety recommendations.
"""
from typing import Tuple, Dict, Optional, Any, List

# CPCB Standard Breakpoints: (C_low, C_high, I_low, I_high)
PM25_BREAKPOINTS = [
    (0.0, 30.0, 0, 50),        # Good
    (31.0, 60.0, 51, 100),     # Satisfactory
    (61.0, 90.0, 101, 200),    # Moderate
    (91.0, 120.0, 201, 300),   # Poor
    (121.0, 250.0, 301, 400),  # Very Poor
    (250.1, 500.0, 401, 500),  # Severe
]

PM10_BREAKPOINTS = [
    (0.0, 50.0, 0, 50),
    (51.0, 100.0, 51, 100),
    (101.0, 250.0, 101, 200),
    (251.0, 350.0, 201, 300),
    (351.0, 430.0, 301, 400),
    (430.1, 600.0, 401, 500),
]

NO2_BREAKPOINTS = [
    (0.0, 40.0, 0, 50),
    (41.0, 80.0, 51, 100),
    (81.0, 180.0, 101, 200),
    (181.0, 280.0, 201, 300),
    (281.0, 400.0, 301, 400),
    (400.1, 1000.0, 401, 500),
]

SO2_BREAKPOINTS = [
    (0.0, 40.0, 0, 50),
    (41.0, 80.0, 51, 100),
    (81.0, 380.0, 101, 200),
    (381.0, 800.0, 201, 300),
    (801.0, 1600.0, 301, 400),
    (1600.1, 2500.0, 401, 500),
]

# CO in ug/m3 (1 mg/m3 = 1000 ug/m3)
CO_BREAKPOINTS_UGM3 = [
    (0.0, 1000.0, 0, 50),
    (1001.0, 2000.0, 51, 100),
    (2001.0, 10000.0, 101, 200),
    (10001.0, 17000.0, 201, 300),
    (17001.0, 34000.0, 301, 400),
    (34001.0, 50000.0, 401, 500),
]

O3_BREAKPOINTS = [
    (0.0, 50.0, 0, 50),
    (51.0, 100.0, 51, 100),
    (101.0, 168.0, 101, 200),
    (169.0, 208.0, 201, 300),
    (209.0, 748.0, 301, 400),
    (748.1, 1000.0, 401, 500),
]

# Official CPCB standard categories and safety recommendations
CPCB_CATEGORIES = [
    {
        "category": "Good",
        "aqi_min": 0,
        "aqi_max": 50,
        "risk_level": "Low",
        "color": "#10b981",
        "recommendation": "Generally favourable outdoor conditions."
    },
    {
        "category": "Satisfactory",
        "aqi_min": 51,
        "aqi_max": 100,
        "risk_level": "Low-Moderate",
        "color": "#06b6d4",
        "recommendation": "Generally acceptable; sensitive individuals should remain aware."
    },
    {
        "category": "Moderate",
        "aqi_min": 101,
        "aqi_max": 200,
        "risk_level": "Moderate",
        "color": "#f59e0b",
        "recommendation": "Sensitive individuals should consider reducing prolonged outdoor exertion."
    },
    {
        "category": "Poor",
        "aqi_min": 201,
        "aqi_max": 300,
        "risk_level": "High",
        "color": "#f97316",
        "recommendation": "Reduce prolonged outdoor exertion."
    },
    {
        "category": "Very Poor",
        "aqi_min": 301,
        "aqi_max": 400,
        "risk_level": "Very High",
        "color": "#ef4444",
        "recommendation": "Avoid prolonged outdoor activities where possible."
    },
    {
        "category": "Severe",
        "aqi_min": 401,
        "aqi_max": 500,
        "risk_level": "Critical",
        "color": "#991b1b",
        "recommendation": "Avoid unnecessary outdoor exposure and follow official advisories."
    }
]

MEDICAL_DISCLAIMER = (
    "AtmosAI environmental guidance is for informational and risk reduction purposes only "
    "and does not constitute personalized medical diagnosis or treatment advice."
)

def calculate_sub_index(conc: Optional[float], breakpoints: list) -> int:
    if conc is None or conc < 0:
        return 0
    for c_low, c_high, i_low, i_high in breakpoints:
        if c_low <= conc <= c_high:
            sub = i_low + ((i_high - i_low) / (c_high - c_low)) * (conc - c_low)
            return round(sub)
    if conc > breakpoints[-1][1]:
        return 500
    return 0

def get_aqi_category_and_risk(aqi: int) -> Tuple[str, str, str]:
    """
    Returns (Category, Risk Level, Hex Color) strictly following CPCB standards.
    """
    for cat in CPCB_CATEGORIES:
        if cat["aqi_min"] <= aqi <= cat["aqi_max"]:
            return (cat["category"], cat["risk_level"], cat["color"])
    if aqi > 500:
        return ("Severe", "Critical", "#991b1b")
    return ("Good", "Low", "#10b981")

def get_cpcb_safety_recommendation(
    aqi: int, 
    user_category: Optional[str] = None, 
    sensitivity: Optional[str] = None
) -> Dict[str, Any]:
    """
    Generates CPCB-aligned safety recommendations enriched with user lifestyle
    context and health sensitivity notes, accompanied by a non-medical disclaimer.
    """
    category, risk, color = get_aqi_category_and_risk(aqi)
    base_rec = next((c["recommendation"] for c in CPCB_CATEGORIES if c["category"] == category), "Generally favourable outdoor conditions.")

    # Persona-specific actionable advice
    persona_rec = None
    u_cat = str(user_category or "").lower()
    if u_cat == "runner":
        if aqi > 100:
            persona_rec = "Shift endurance training indoors or schedule light runs before morning traffic peaks."
        else:
            persona_rec = "Favourable conditions for outdoor training and aerobic sessions."
    elif u_cat == "parent":
        if aqi > 100:
            persona_rec = "Plan children's outdoor playground visits during midday hours; avoid road-facing play areas during evening rush."
        else:
            persona_rec = "Conditions are suitable for family outdoor walks and playground outings."
    elif u_cat == "office_commuter":
        if aqi > 100:
            persona_rec = "Switch vehicle AC to internal recirculation mode when navigating congested corridors like Silk Board."
        else:
            persona_rec = "Corridor air quality is satisfactory for standard commute routines."
    elif u_cat in ("outdoor_worker", "delivery_worker"):
        if aqi > 100:
            persona_rec = "Wear an N95 respirator during high-traffic shifts and take rest breaks in filtered indoor locations."
        else:
            persona_rec = "Shift conditions are clear; stay hydrated during extended field hours."
    elif u_cat == "student":
        if aqi > 100:
            persona_rec = "Use shaded campus pathways away from perimeter traffic and prioritize indoor study halls."
        else:
            persona_rec = "Optimal conditions for campus walks, open-air study, and university sports."

    # Sensitivity-specific proactive note
    sens_note = None
    sens_str = str(sensitivity or "").lower()
    if sens_str in ("asthma_respiratory", "allergies"):
        sens_note = "Sensitive profile alert: Keep prescribed rescue inhalers or allergy relief medication readily accessible."
    elif sens_str == "elderly_child_care":
        sens_note = "High vulnerability alert: Limit prolonged outdoor exertion for infants, young children, and elderly residents."
    elif sens_str == "cardiovascular":
        sens_note = "Cardiovascular alert: Moderate physical pace; avoid sudden high-stress exertion in elevated particulate conditions."

    return {
        "aqi": aqi,
        "category": category,
        "risk_level": risk,
        "color": color,
        "base_recommendation": base_rec,
        "persona_recommendation": persona_rec,
        "sensitivity_note": sens_note,
        "disclaimer": MEDICAL_DISCLAIMER
    }

def compute_naqi(
    pm25: Optional[float] = None, 
    pm10: Optional[float] = None,
    no2: Optional[float] = None,
    so2: Optional[float] = None,
    co: Optional[float] = None,
    o3: Optional[float] = None
) -> Dict[str, Any]:
    """
    Computes overall Indian NAQI using valid CPCB methodology.
    Calculates sub-indices across all supplied pollutants and returns the maximum.
    Strictly avoids computing NAQI from PM2.5 alone when other pollutants are present.
    """
    sub_indices: Dict[str, int] = {}
    
    if pm25 is not None:
        sub_indices["PM2.5"] = calculate_sub_index(pm25, PM25_BREAKPOINTS)
    if pm10 is not None:
        sub_indices["PM10"] = calculate_sub_index(pm10, PM10_BREAKPOINTS)
    if no2 is not None:
        sub_indices["NO2"] = calculate_sub_index(no2, NO2_BREAKPOINTS)
    if so2 is not None:
        sub_indices["SO2"] = calculate_sub_index(so2, SO2_BREAKPOINTS)
    if co is not None:
        sub_indices["CO"] = calculate_sub_index(co, CO_BREAKPOINTS_UGM3)
    if o3 is not None:
        sub_indices["O3"] = calculate_sub_index(o3, O3_BREAKPOINTS)

    if not sub_indices:
        return {
            "aqi": 0,
            "category": "Good",
            "risk_level": "Low",
            "color": "#10b981",
            "dominant_pollutant": "None",
            "sub_indices": {}
        }

    # Find dominant pollutant with maximum sub-index
    dominant = max(sub_indices, key=sub_indices.get)
    overall_aqi = sub_indices[dominant]
    category, risk, color = get_aqi_category_and_risk(overall_aqi)

    return {
        "aqi": overall_aqi,
        "category": category,
        "risk_level": risk,
        "color": color,
        "dominant_pollutant": dominant,
        "sub_indices": sub_indices,
        # Backward compatibility fields
        "sub_index_pm25": sub_indices.get("PM2.5"),
        "sub_index_pm10": sub_indices.get("PM10")
    }
