"""Base collector and registry for external data sources."""

from abc import ABC, abstractmethod
from typing import List, Dict, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class ExternalEvent:
    """An event from an external data source that may affect agents."""

    def __init__(self, source: str, event_type: str, payload: dict,
                 relevance_tags: Optional[List[str]] = None,
                 timestamp: Optional[datetime] = None):
        self.source = source
        self.event_type = event_type
        self.payload = payload
        self.relevance_tags = relevance_tags or []
        self.timestamp = timestamp or datetime.now()

    def to_dict(self) -> dict:
        return {
            "source": self.source,
            "event_type": self.event_type,
            "payload": self.payload,
            "relevance_tags": self.relevance_tags,
            "timestamp": self.timestamp.isoformat(),
        }

    def affects_agent(self, agent: dict) -> bool:
        """Check if this event is relevant to a specific agent."""
        if not self.relevance_tags:
            return True  # global event

        agent_tags = set()
        # Build agent tag set from attributes
        if agent.get("planning_area"):
            agent_tags.add(f"area:{agent['planning_area']}")
        if agent.get("housing_type"):
            agent_tags.add(f"housing:{agent['housing_type']}")
        if agent.get("industry"):
            agent_tags.add(f"industry:{agent['industry']}")
        if agent.get("age"):
            age = agent["age"]
            if age < 30:
                agent_tags.add("age:young")
            elif age < 55:
                agent_tags.add("age:working")
            else:
                agent_tags.add("age:senior")
        if agent.get("has_vehicle"):
            agent_tags.add("transport:vehicle")
        if agent.get("commute_mode"):
            agent_tags.add(f"transport:{agent['commute_mode'].lower()}")

        return bool(set(self.relevance_tags) & agent_tags)


class BaseCollector(ABC):
    """Abstract base class for external data collectors."""

    def __init__(self, name: str, enabled: bool = True):
        self.name = name
        self.enabled = enabled
        self.last_fetch: Optional[datetime] = None
        self.fetch_count = 0
        self.error_count = 0

    @abstractmethod
    def fetch(self, sim_date: str) -> List[ExternalEvent]:
        """Fetch events from the external source. Returns list of events."""
        pass

    def safe_fetch(self, sim_date: str) -> List[ExternalEvent]:
        """Fetch with error handling."""
        if not self.enabled:
            return []
        try:
            events = self.fetch(sim_date)
            self.last_fetch = datetime.now()
            self.fetch_count += 1
            logger.info(f"[{self.name}] Fetched {len(events)} events")
            return events
        except Exception as e:
            self.error_count += 1
            logger.warning(f"[{self.name}] Fetch failed: {e}")
            return []

    def get_stats(self) -> dict:
        return {
            "name": self.name,
            "enabled": self.enabled,
            "last_fetch": self.last_fetch.isoformat() if self.last_fetch else None,
            "fetch_count": self.fetch_count,
            "error_count": self.error_count,
        }


class CollectorRegistry:
    """Registry of all external data collectors."""

    def __init__(self):
        self.collectors: Dict[str, BaseCollector] = {}

    def register(self, collector: BaseCollector):
        self.collectors[collector.name] = collector
        logger.info(f"Registered collector: {collector.name}")

    def fetch_all(self, sim_date: str) -> List[ExternalEvent]:
        """Fetch from all registered collectors."""
        all_events = []
        for collector in self.collectors.values():
            events = collector.safe_fetch(sim_date)
            all_events.extend(events)
        return all_events

    def get_stats(self) -> List[dict]:
        return [c.get_stats() for c in self.collectors.values()]
