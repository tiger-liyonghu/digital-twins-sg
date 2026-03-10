"""RSS/News collector — ingests Singapore news and classifies relevance."""

from typing import List, Optional
import logging

from .base import BaseCollector, ExternalEvent

logger = logging.getLogger(__name__)

# Singapore news category → relevance tags mapping
NEWS_CATEGORY_TAGS = {
    "property": ["housing:HDB_3", "housing:HDB_4", "housing:HDB_5_EC",
                  "housing:Condo", "housing:Landed"],
    "hdb": ["housing:HDB_3", "housing:HDB_4", "housing:HDB_5_EC"],
    "transport": ["transport:mrt", "transport:bus", "transport:vehicle"],
    "erp": ["transport:vehicle"],
    "employment": ["age:working"],
    "retirement": ["age:senior"],
    "cpf": ["age:working", "age:senior"],
    "education": ["age:young"],
    "healthcare": [],  # affects everyone
    "gst": [],  # affects everyone
    "budget": [],  # affects everyone
    "ns": ["age:young"],
}


class RSSCollector(BaseCollector):
    """Collects news from Singapore RSS feeds and classifies into events."""

    # Singapore news RSS feeds
    DEFAULT_FEEDS = [
        "https://www.channelnewsasia.com/api/v1/rss-outbound-feed?_format=xml&category=6511",  # SG news
        "https://www.straitstimes.com/news/singapore/rss.xml",
        "https://www.todayonline.com/feed",
    ]

    def __init__(self, feeds: Optional[List[str]] = None,
                 enabled: bool = True):
        super().__init__("rss_news", enabled)
        self.feeds = feeds or self.DEFAULT_FEEDS

    def fetch(self, sim_date: str) -> List[ExternalEvent]:
        """Fetch and parse RSS feeds for Singapore news."""
        events = []

        try:
            import feedparser
        except ImportError:
            logger.warning("feedparser not installed, using mock data")
            return self._mock_events(sim_date)

        for feed_url in self.feeds:
            try:
                feed = feedparser.parse(feed_url)
                for entry in feed.entries[:10]:  # limit per feed
                    event = self._parse_entry(entry, sim_date)
                    if event:
                        events.append(event)
            except Exception as e:
                logger.warning(f"Failed to parse feed {feed_url}: {e}")

        return events

    def _parse_entry(self, entry, sim_date: str) -> Optional[ExternalEvent]:
        """Parse an RSS entry into an ExternalEvent."""
        title = entry.get("title", "")
        summary = entry.get("summary", "")
        link = entry.get("link", "")
        text = (title + " " + summary).lower()

        # Classify by keywords
        relevance_tags = []
        event_type = "news_general"

        for category, tags in NEWS_CATEGORY_TAGS.items():
            if category in text:
                event_type = f"news_{category}"
                relevance_tags.extend(tags)

        # Policy-specific detection
        if any(kw in text for kw in ["gst", "tax", "levy"]):
            event_type = "policy_tax"
        elif any(kw in text for kw in ["interest rate", "mortgage", "loan"]):
            event_type = "policy_finance"
            relevance_tags.extend(["housing:Condo", "housing:Landed"])
        elif any(kw in text for kw in ["mrt", "bus", "lrt", "train"]):
            event_type = "infrastructure_transport"
        elif any(kw in text for kw in ["bto", "hdb", "resale flat"]):
            event_type = "policy_housing"

        return ExternalEvent(
            source="rss",
            event_type=event_type,
            payload={
                "title": title,
                "summary": summary[:500],
                "url": link,
                "sim_date": sim_date,
            },
            relevance_tags=list(set(relevance_tags)),
        )

    def _mock_events(self, sim_date: str) -> List[ExternalEvent]:
        """Generate mock news events for testing without RSS feeds."""
        import random
        mock_news = [
            {
                "type": "policy_housing",
                "title": "BTO launch in Tengah with 4,000 units",
                "tags": ["housing:HDB_4", "housing:HDB_5_EC"],
            },
            {
                "type": "policy_finance",
                "title": "MAS holds interest rate steady at 3.5%",
                "tags": ["housing:Condo", "housing:Landed", "age:working"],
            },
            {
                "type": "infrastructure_transport",
                "title": "Cross Island Line Phase 1 on track for 2030",
                "tags": ["transport:mrt"],
            },
            {
                "type": "policy_tax",
                "title": "GST vouchers for lower-income households",
                "tags": [],
            },
            {
                "type": "news_employment",
                "title": "Tech sector sees 5% growth in hiring",
                "tags": ["age:working", "industry:ICT"],
            },
        ]
        # Return 1-3 random mock events per tick
        chosen = random.sample(mock_news, k=min(random.randint(1, 3), len(mock_news)))
        return [
            ExternalEvent(
                source="rss_mock",
                event_type=item["type"],
                payload={"title": item["title"], "sim_date": sim_date},
                relevance_tags=item["tags"],
            )
            for item in chosen
        ]
