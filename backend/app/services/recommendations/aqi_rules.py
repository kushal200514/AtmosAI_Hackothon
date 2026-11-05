"""
CPCB National Air Quality Index (India) Rules and Standard Categories.
Enforces that AQI categories are deterministically mapped and validated strictly per CPCB methodology.
"""
from typing import Optional, Dict, Any

CPCB_AQI_CATEGORIES = {
    "Good": {
        "min": 0,
        "max": 50,
        "color": "#10b981",
        "risk_level": "Low",
        "general_guidance": "Air quality is favourable; ambient atmospheric conditions pose minimal risk to healthy and sensitive individuals.",
        "base_action": "Routine outdoor activities, ventilation, and outdoor recreation can proceed without restrictions.",
        "exercise_allowed": True,
        "mask_advised": False
    },
    "Satisfactory": {
        "min": 51,
        "max": 100,
        "color": "#06b6d4",
        "risk_level": "Low-Moderate",
        "general_guidance": "Air quality is acceptable; unusually sensitive individuals should remain aware of potential minor respiratory sensitivity.",
        "base_action": "Standard outdoor exertion is acceptable; monitor multi-horizon forecast before strenuous evening sessions.",
        "exercise_allowed": True,
        "mask_advised": False
    },
    "Moderate": {
        "min": 101,
        "max": 200,
        "color": "#f59e0b",
        "risk_level": "Moderate",
        "general_guidance": "Elevated particulate concentrations; sensitive individuals may experience breathing discomfort during prolonged exertion.",
        "base_action": "Sensitive individuals should consider reducing prolonged outdoor exertion; exercise in shaded or low-traffic zones.",
        "exercise_allowed": True,
        "mask_advised": False
    },
    "Poor": {
        "min": 201,
        "max": 300,
        "color": "#f97316",
        "risk_level": "High",
        "general_guidance": "Pollution levels likely to cause breathing discomfort to most individuals on prolonged outdoor exposure.",
        "base_action": "Reduce prolonged outdoor exertion; consider an N95 particulate mask near busy road corridors.",
        "exercise_allowed": False,
        "mask_advised": True
    },
    "Very Poor": {
        "min": 301,
        "max": 400,
        "color": "#ef4444",
        "risk_level": "Very High",
        "general_guidance": "Significant atmospheric contamination; prolonged exposure can trigger acute respiratory symptoms.",
        "base_action": "Avoid prolonged outdoor activities where possible; shift workouts indoors and seal living spaces.",
        "exercise_allowed": False,
        "mask_advised": True
    },
    "Severe": {
        "min": 401,
        "max": 500,
        "color": "#7f1d1d",
        "risk_level": "Critical",
        "general_guidance": "Hazardous pollution levels affecting healthy people and severely impacting vulnerable populations.",
        "base_action": "Avoid unnecessary outdoor exposure; activate high-efficiency indoor air filtration and follow official advisories.",
        "exercise_allowed": False,
        "mask_advised": True
    }
}

def get_cpcb_category_info(aqi: Optional[int]) -> Dict[str, Any]:
    """
    Returns deterministic CPCB NAQI metadata.
    If aqi is None or out of valid range (0-500), reports category as Unavailable.
    """
    if aqi is None:
        return {
            "category": "Unavailable",
            "risk_level": "Unknown",
            "risk_category": "Unknown",
            "color": "#94a3b8",
            "general_guidance": "Overall multi-pollutant AQI is unavailable due to missing sub-indices.",
            "base_action": "Rely on specific pollutant concentrations (e.g. PM2.5) where available.",
            "exercise_allowed": True,
            "mask_advised": False
        }
        
    for cat_name, info in CPCB_AQI_CATEGORIES.items():
        if info["min"] <= aqi <= info["max"]:
            return {
                "category": cat_name,
                "risk_level": info["risk_level"],
                "risk_category": info["risk_level"],
                "color": info["color"],
                "general_guidance": info["general_guidance"],
                "base_action": info["base_action"],
                "exercise_allowed": info["exercise_allowed"],
                "mask_advised": info["mask_advised"]
            }
            
    # For severe spikes > 500
    if aqi > 500:
        return {
            "category": "Severe",
            "risk_level": "Critical",
            "risk_category": "Critical",
            "color": "#7f1d1d",
            "general_guidance": CPCB_AQI_CATEGORIES["Severe"]["general_guidance"],
            "base_action": CPCB_AQI_CATEGORIES["Severe"]["base_action"],
            "exercise_allowed": False,
            "mask_advised": True
        }
        
    return {
        "category": "Unavailable",
        "risk_level": "Unknown",
        "risk_category": "Unknown",
        "color": "#94a3b8",
        "general_guidance": "Uncalibrated AQI reading.",
        "base_action": "Exercise general environmental awareness.",
        "exercise_allowed": True,
        "mask_advised": False
    }

def get_cpcb_category_from_value(aqi: int) -> str:
    """Returns the exact CPCB category string for a valid integer AQI."""
    return get_cpcb_category_info(aqi)["category"]
