"""Market/financial data collector for SGX and MAS indicators."""

from typing import List, Optional
import logging

from .base import BaseCollector, ExternalEvent

logger = logging.getLogger(__name__)


class MarketDataCollector(BaseCollector):
    """Collects market and financial data relevant to agent decisions."""

    def __init__(self, enabled: bool = True):
        super().__init__("market_data", enabled)
        self._last_rates: Optional[dict] = None

    def fetch(self, sim_date: str) -> List[ExternalEvent]:
        """Fetch latest market indicators."""
        events = []

        try:
            import requests
        except ImportError:
            return self._mock_events(sim_date)

        # MAS exchange rate API
        try:
            resp = requests.get(
                "https://eservices.mas.gov.sg/api/action/store/search",
                params={"id": "95932927-c8bc-4e7a-b484-68a66a24edfe", "limit": 1},
                timeout=10,
            )
            if resp.status_code == 200:
                data = resp.json()
                records = data.get("result", {}).get("records", [])
                if records:
                    rate = records[0]
                    if self._last_rates != rate:
                        self._last_rates = rate
                        events.append(ExternalEvent(
                            source="market",
                            event_type="market_exchange_rate",
                            payload={"rate": rate, "sim_date": sim_date},
                            relevance_tags=[],
                        ))
        except Exception as e:
            logger.debug(f"Exchange rate fetch failed: {e}")

        return events or self._mock_events(sim_date)

    def _mock_events(self, sim_date: str) -> List[ExternalEvent]:
        """Mock market events for development."""
        import random
        events = []

        # Simulate STI movement
        sti_change = random.gauss(0, 0.8)  # daily % change
        if abs(sti_change) > 1.5:  # only report significant moves
            events.append(ExternalEvent(
                source="market_mock",
                event_type="market_sti_move",
                payload={
                    "index": "STI",
                    "change_pct": round(sti_change, 2),
                    "direction": "up" if sti_change > 0 else "down",
                    "sim_date": sim_date,
                },
                relevance_tags=["age:working", "age:senior"],
            ))

        # Simulate interest rate changes (rare)
        if random.random() < 0.01:  # ~1% chance per day ≈ quarterly
            rate_delta = random.choice([-0.25, 0.25])
            events.append(ExternalEvent(
                source="market_mock",
                event_type="market_interest_rate",
                payload={
                    "change_bps": int(rate_delta * 100),
                    "sim_date": sim_date,
                },
                relevance_tags=["housing:Condo", "housing:Landed", "age:working"],
            ))

        return events
