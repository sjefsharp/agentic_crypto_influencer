import logging
from typing import Any, Dict, List, Optional

import requests
from config.key_constants import X_PERSONALIZED_TRENDS_ENDPOINT, X_URL


class TrendsHandler:
    def __init__(self, access_token: str):
        self.access_token = access_token

    def get_personalized_trends(
        self, user_id: str, max_results: int = 10, exclude: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        trends_url = f"{X_URL}{X_PERSONALIZED_TRENDS_ENDPOINT}"
        headers = {"Authorization": f"Bearer {self.access_token}"}

        try:
            resp = requests.get(trends_url, headers=headers, timeout=15)
            logging.info("Trends response status: %d", resp.status_code)
            if resp.status_code != 200:
                logging.error(
                    "Trends request failed: %d %s", resp.status_code, resp.text
                )
                raise Exception(
                    f"Trends request returned an error: {resp.status_code} {resp.text}"
                )
            return resp.json()
        except Exception as e:
            logging.error("Trends request error: %s", str(e))
            raise RuntimeError(f"Error fetching personalized trends: {str(e)}")
