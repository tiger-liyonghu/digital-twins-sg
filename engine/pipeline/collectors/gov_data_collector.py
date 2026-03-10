"""Singapore Government open data collector."""

from typing import List, Optional, Dict
import logging

from .base import BaseCollector, ExternalEvent

logger = logging.getLogger(__name__)


class GovDataCollector(BaseCollector):
    """Collects data from data.gov.sg and related APIs."""

    # data.gov.sg dataset IDs for key indicators
    DATASETS = {
        "hdb_resale": {
            "id": "d_8b84c4ee58e3cfc0ece0d773c8ca6abc",
            "event_type": "data_hdb_resale",
            "tags": ["housing:HDB_3", "housing:HDB_4", "housing:HDB_5_EC"],
            "frequency": "quarterly",
        },
        "cpi": {
            "id": "d_37c55ecaa tried_4f1b9f7b0e4fd4b0ad1f",
            "event_type": "data_cpi",
            "tags": [],  # affects everyone
            "frequency": "monthly",
        },
        "unemployment": {
            "id": "d_0d45f15f8d3fa0cf0f6b68b68808e0c0",
            "event_type": "data_unemployment",
            "tags": ["age:working"],
            "frequency": "quarterly",
        },
    }

    API_BASE = "https://data.gov.sg/api/action/datastore_search"

    def __init__(self, enabled: bool = True,
                 api_key: Optional[str] = None):
        super().__init__("gov_data", enabled)
        self.api_key = api_key
        self._cache: Dict[str, dict] = {}
        self._last_check_tick: int = 0

    def fetch(self, sim_date: str) -> List[ExternalEvent]:
        """Fetch latest government data indicators."""
        events = []

        try:
            import requests
        except ImportError:
            logger.warning("requests not installed, using mock data")
            return self._mock_events(sim_date)

        for key, ds in self.DATASETS.items():
            try:
                params = {"resource_id": ds["id"], "limit": 5, "sort": "quarter desc"}
                resp = requests.get(self.API_BASE, params=params, timeout=10)
                if resp.status_code == 200:
                    data = resp.json()
                    records = data.get("result", {}).get("records", [])
                    if records:
                        latest = records[0]
                        # Check if this is new data (not in cache)
                        cache_key = f"{key}_{latest.get('quarter', latest.get('month', ''))}"
                        if cache_key not in self._cache:
                            self._cache[cache_key] = latest
                            events.append(ExternalEvent(
                                source="gov_data",
                                event_type=ds["event_type"],
                                payload={
                                    "dataset": key,
                                    "latest_record": latest,
                                    "sim_date": sim_date,
                                },
                                relevance_tags=ds["tags"],
                            ))
            except Exception as e:
                logger.warning(f"Failed to fetch {key}: {e}")

        return events

    def _mock_events(self, sim_date: str) -> List[ExternalEvent]:
        """Mock government data events for offline development."""
        return [
            ExternalEvent(
                source="gov_data_mock",
                event_type="data_hdb_resale",
                payload={
                    "dataset": "hdb_resale",
                    "latest_record": {
                        "quarter": "2025-Q4",
                        "town": "ANG MO KIO",
                        "flat_type": "4 ROOM",
                        "resale_price": "520000",
                    },
                    "sim_date": sim_date,
                },
                relevance_tags=["housing:HDB_4"],
            ),
            ExternalEvent(
                source="gov_data_mock",
                event_type="data_unemployment",
                payload={
                    "dataset": "unemployment",
                    "latest_record": {
                        "quarter": "2025-Q4",
                        "unemployment_rate": "2.1",
                    },
                    "sim_date": sim_date,
                },
                relevance_tags=["age:working"],
            ),
        ]
