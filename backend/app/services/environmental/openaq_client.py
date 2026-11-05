import httpx
import logging
from typing import Dict, Any, Optional, List
from app.core.config import settings

logger = logging.getLogger("atmosai.openaq")

class OpenAQClient:
    def __init__(self):
        self.base_url = settings.OPENAQ_BASE_URL.rstrip('/')
        self.api_key = settings.OPENAQ_API_KEY

    def _get_headers(self) -> Dict[str, str]:
        headers = {"Accept": "application/json"}
        if self.api_key:
            headers["X-API-Key"] = self.api_key
        return headers

    async def get_latest_measurements(self, lat: float, lon: float, radius_meters: int = 25000) -> Optional[Dict[str, Any]]:
        """
        Queries OpenAQ API v3 for real physical sensor stations around the given latitude & longitude.
        """
        headers = self._get_headers()
        params = {
            "coordinates": f"{lat},{lon}",
            "radius": radius_meters,
            "limit": 5
        }
        try:
            async with httpx.AsyncClient(timeout=6.0) as client:
                res = await client.get(f"{self.base_url}/locations", headers=headers, params=params)
                if res.status_code == 200:
                    data = res.json()
                    results = data.get("results", [])
                    if results:
                        # Extract sensors from first station
                        return results[0]
                elif res.status_code == 401 or res.status_code == 403:
                    logger.info("OpenAQ API key required or unauthorized; deferring to atmospheric models.")
                else:
                    logger.warning(f"OpenAQ returned status {res.status_code}")
        except Exception as e:
            logger.error(f"OpenAQ request exception: {e}")
        return None

openaq_client = OpenAQClient()

