"""
Census Data Monitor — Weekly scan for updated SingStat / data.gov.sg datasets.

Checks known dataset IDs against their last-modified timestamps.
If new data is found, triggers a data version bump and optional re-synthesis.
"""

import json
import os
import logging
from datetime import datetime, date
from pathlib import Path
from typing import List, Dict, Optional

from .base import BaseCollector, ExternalEvent

logger = logging.getLogger(__name__)

# SingStat / data.gov.sg datasets that feed the digital twin
MONITORED_DATASETS = {
    # Census / population structure
    "pop_age_sex_area": {
        "name": "Resident Population by Planning Area, Age Group and Sex",
        "api_url": "https://api-production.data.gov.sg/v2/public/api/datasets",
        "search_keywords": "resident population planning area age group sex",
        "frequency": "annual",
        "category": "population",
        "priority": 1,
    },
    "pop_ethnicity": {
        "name": "Resident Population by Age Group, Ethnic Group and Sex",
        "search_keywords": "resident population age group ethnic group sex",
        "frequency": "annual",
        "category": "population",
        "priority": 2,
    },
    "household_income_dwelling": {
        "name": "Resident Households by Monthly HH Income and Type of Dwelling",
        "search_keywords": "resident households monthly household income type dwelling",
        "frequency": "annual",
        "category": "income",
        "priority": 3,
    },
    "worker_income_occupation": {
        "name": "Resident Working Persons by Monthly Income, Occupation and Sex",
        "search_keywords": "resident working persons monthly income occupation sex",
        "frequency": "annual",
        "category": "income",
        "priority": 4,
    },
    "education_age_sex": {
        "name": "Resident Population by Qualification, Age Group and Sex",
        "search_keywords": "resident population highest qualification age group sex",
        "frequency": "annual",
        "category": "education",
        "priority": 5,
    },
    "household_arrangement": {
        "name": "Resident Households by Household Living Arrangement",
        "search_keywords": "resident households household living arrangement",
        "frequency": "annual",
        "category": "household",
        "priority": 6,
    },
    "household_size_ethnicity": {
        "name": "Resident Households by Household Size and Ethnic Group",
        "search_keywords": "resident households household size ethnic group",
        "frequency": "annual",
        "category": "household",
        "priority": 7,
    },
    "marital_status_area": {
        "name": "Resident Population by Planning Area, Marital Status and Sex",
        "search_keywords": "resident population planning area marital status sex",
        "frequency": "annual",
        "category": "population",
        "priority": 8,
    },
    "transport_mode": {
        "name": "Employed Residents by Usual Mode of Transport, Age and Sex",
        "search_keywords": "employed residents usual mode transport work age",
        "frequency": "annual",
        "category": "transport",
        "priority": 9,
    },
    "fertility": {
        "name": "Ever-Married Females by Age Group and Number of Children Born",
        "search_keywords": "citizen ever married females age group number children",
        "frequency": "annual",
        "category": "population",
        "priority": 10,
    },
    "mortality": {
        "name": "Deaths by Age, Ethnic Group and Gender",
        "search_keywords": "deaths age ethnic group gender",
        "frequency": "annual",
        "category": "population",
        "priority": 11,
    },
    "hdb_resale": {
        "name": "HDB Resale Flat Prices",
        "search_keywords": "hdb resale flat prices",
        "frequency": "quarterly",
        "category": "housing",
        "priority": 12,
    },
    # Additional real-time indicators
    "cpi": {
        "name": "Consumer Price Index",
        "search_keywords": "consumer price index",
        "frequency": "monthly",
        "category": "economy",
        "priority": 13,
    },
    "unemployment": {
        "name": "Unemployment Rate",
        "search_keywords": "unemployment rate quarterly",
        "frequency": "quarterly",
        "category": "economy",
        "priority": 14,
    },
}


class CensusMonitor(BaseCollector):
    """
    Weekly census data monitor.

    Scans data.gov.sg for updated datasets. When new data is found:
    1. Downloads the updated CSV
    2. Records the change in the version log
    3. Emits an ExternalEvent so the VersionManager can trigger re-synthesis
    """

    CHECK_INTERVAL_DAYS = 7  # weekly check

    def __init__(self, data_dir: str = "data/census",
                 enabled: bool = True):
        super().__init__("census_monitor", enabled)
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)

        # State file: tracks last-known dataset metadata
        self.state_file = self.data_dir / "_monitor_state.json"
        self.state = self._load_state()

    def _load_state(self) -> dict:
        if self.state_file.exists():
            with open(self.state_file) as f:
                return json.load(f)
        return {
            "last_check": None,
            "datasets": {},  # key -> {dataset_id, last_modified, record_count, ...}
            "check_history": [],
        }

    def _save_state(self):
        with open(self.state_file, "w") as f:
            json.dump(self.state, f, indent=2, ensure_ascii=False,
                      default=str)

    def should_check(self) -> bool:
        """Determine if it's time for a weekly check."""
        last = self.state.get("last_check")
        if not last:
            return True
        last_dt = datetime.fromisoformat(last)
        days_since = (datetime.now() - last_dt).days
        return days_since >= self.CHECK_INTERVAL_DAYS

    def fetch(self, sim_date: str) -> List[ExternalEvent]:
        """
        Check for updated census datasets.
        Only runs if CHECK_INTERVAL_DAYS has passed since last check.
        """
        if not self.should_check():
            return []

        logger.info("Census Monitor: Starting weekly data scan...")
        events = []

        try:
            import requests
        except ImportError:
            logger.warning("requests not installed, skipping census check")
            return []

        # Scan data.gov.sg catalog
        updated = self._scan_catalog(requests)

        for key, info in updated.items():
            events.append(ExternalEvent(
                source="census_monitor",
                event_type="census_data_updated",
                payload={
                    "dataset_key": key,
                    "dataset_name": info["name"],
                    "category": info["category"],
                    "new_record_count": info.get("record_count", 0),
                    "previous_record_count": info.get("prev_record_count", 0),
                    "dataset_id": info.get("dataset_id", ""),
                    "download_path": info.get("download_path", ""),
                    "sim_date": sim_date,
                },
                relevance_tags=[],  # census updates are system-level
            ))

        # Update check timestamp
        self.state["last_check"] = datetime.now().isoformat()
        self.state["check_history"].append({
            "date": datetime.now().isoformat(),
            "datasets_checked": len(MONITORED_DATASETS),
            "updates_found": len(updated),
            "updated_keys": list(updated.keys()),
        })
        # Keep last 52 weeks of history
        self.state["check_history"] = self.state["check_history"][-52:]
        self._save_state()

        if updated:
            logger.info(f"Census Monitor: {len(updated)} dataset(s) updated: "
                        f"{list(updated.keys())}")
        else:
            logger.info("Census Monitor: No updates found.")

        return events

    def _scan_catalog(self, requests) -> Dict[str, dict]:
        """Scan data.gov.sg for updated datasets."""
        API_BASE = "https://api-production.data.gov.sg/v2/public/api/datasets"
        updated = {}

        # Fetch full catalog (paginated)
        all_datasets = []
        page = 1
        while page <= 50:
            try:
                resp = requests.get(API_BASE, params={"page": page},
                                    timeout=30)
                if resp.status_code != 200:
                    break
                data = resp.json()
                datasets = data.get("data", {}).get("datasets", [])
                if not datasets:
                    break
                all_datasets.extend(datasets)
                page += 1
            except Exception as e:
                logger.warning(f"Catalog page {page} failed: {e}")
                break

        logger.info(f"Census Monitor: Scanned {len(all_datasets)} datasets "
                    f"in catalog")

        # Match against monitored datasets
        for key, spec in MONITORED_DATASETS.items():
            match = self._find_best_match(all_datasets, spec)
            if not match:
                continue

            ds_id = match.get("datasetId", "")
            last_modified = match.get("lastUpdatedAt", "")
            name = match.get("name", spec["name"])

            # Compare with known state
            prev = self.state["datasets"].get(key, {})
            prev_modified = prev.get("last_modified", "")

            if last_modified and last_modified != prev_modified:
                # Dataset has been updated
                download_path = self._download_dataset(
                    requests, ds_id, key, spec)

                prev_count = prev.get("record_count", 0)
                updated[key] = {
                    "name": name,
                    "category": spec["category"],
                    "dataset_id": ds_id,
                    "last_modified": last_modified,
                    "record_count": match.get("totalRecordCount", 0),
                    "prev_record_count": prev_count,
                    "download_path": str(download_path) if download_path else "",
                }

                # Update state
                self.state["datasets"][key] = {
                    "dataset_id": ds_id,
                    "name": name,
                    "last_modified": last_modified,
                    "record_count": match.get("totalRecordCount", 0),
                    "download_path": str(download_path) if download_path else "",
                    "checked_at": datetime.now().isoformat(),
                }

        return updated

    def _find_best_match(self, catalog: list, spec: dict) -> Optional[dict]:
        """Find the best matching dataset from the catalog."""
        keywords = spec["search_keywords"].lower().split()
        best_score = 0
        best_match = None

        for ds in catalog:
            name = (ds.get("name", "") or "").lower()
            score = sum(1 for kw in keywords if kw in name)
            if score > best_score and score >= len(keywords) * 0.4:
                best_score = score
                best_match = ds

        return best_match

    def _download_dataset(self, requests, dataset_id: str,
                          key: str, spec: dict) -> Optional[Path]:
        """Download updated dataset CSV."""
        url = f"https://api-production.data.gov.sg/v2/public/api/datasets/{dataset_id}/poll-download"

        try:
            resp = requests.get(url, timeout=60)
            if resp.status_code != 200:
                return None

            data = resp.json()
            download_url = data.get("data", {}).get("url")
            if not download_url:
                return None

            csv_resp = requests.get(download_url, timeout=120)
            if csv_resp.status_code != 200:
                return None

            # Save with version timestamp
            timestamp = datetime.now().strftime("%Y%m%d")
            filename = f"{spec['priority']:02d}_{key}_{timestamp}.csv"
            filepath = self.data_dir / filename
            with open(filepath, "wb") as f:
                f.write(csv_resp.content)

            # Also save as "latest" symlink
            latest = self.data_dir / f"{spec['priority']:02d}_{key}_latest.csv"
            if latest.exists() or latest.is_symlink():
                latest.unlink()
            latest.symlink_to(filepath.name)

            size_kb = len(csv_resp.content) / 1024
            logger.info(f"Downloaded {key}: {filename} ({size_kb:.1f} KB)")
            return filepath

        except Exception as e:
            logger.warning(f"Download failed for {key}: {e}")
            return None

    def get_monitor_status(self) -> dict:
        """Get current monitor status for the dashboard."""
        return {
            "last_check": self.state.get("last_check"),
            "datasets_tracked": len(MONITORED_DATASETS),
            "datasets_with_data": len(self.state.get("datasets", {})),
            "check_interval_days": self.CHECK_INTERVAL_DAYS,
            "should_check_now": self.should_check(),
            "recent_checks": self.state.get("check_history", [])[-5:],
            "datasets": {
                key: {
                    "name": spec["name"],
                    "category": spec["category"],
                    "frequency": spec["frequency"],
                    "has_data": key in self.state.get("datasets", {}),
                    "last_modified": self.state.get("datasets", {}).get(
                        key, {}).get("last_modified", "N/A"),
                }
                for key, spec in MONITORED_DATASETS.items()
            },
        }

    def force_check(self, sim_date: str = None) -> List[ExternalEvent]:
        """Force an immediate check regardless of interval."""
        self.state["last_check"] = None  # reset to trigger check
        return self.fetch(sim_date or str(date.today()))
