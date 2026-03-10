"""
Version Manager — Data & system versioning with rollback support.

Two independent version axes:
1. DATA versions  — when census/external data updates trigger re-synthesis
2. SYSTEM versions — when engine code changes (life rules, prob models, etc.)

Each version bump creates a full snapshot. Rollback restores both agent
population and the configuration that generated it.
"""

import json
import shutil
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict
import pandas as pd

logger = logging.getLogger(__name__)


class DataVersion:
    """Represents one data version entry."""
    def __init__(self, version: str, created_at: str,
                 description: str, data_sources: dict,
                 agent_count: int = 0,
                 population_file: str = "",
                 synthesis_config: dict = None,
                 is_active: bool = False):
        self.version = version
        self.created_at = created_at
        self.description = description
        self.data_sources = data_sources
        self.agent_count = agent_count
        self.population_file = population_file
        self.synthesis_config = synthesis_config or {}
        self.is_active = is_active

    def to_dict(self) -> dict:
        return {
            "version": self.version,
            "created_at": self.created_at,
            "description": self.description,
            "data_sources": self.data_sources,
            "agent_count": self.agent_count,
            "population_file": self.population_file,
            "synthesis_config": self.synthesis_config,
            "is_active": self.is_active,
        }


class VersionManager:
    """
    Manages data versions and system versions with rollback.

    Directory structure:
      versions/
        manifest.json        — version history
        v1.0.0/
          population.csv     — agent population snapshot
          data_sources/      — census CSV copies used for this version
          config.json        — synthesis parameters
          summary.json       — validation summary
        v1.1.0/
          ...
    """

    def __init__(self, versions_dir: str = "versions",
                 data_dir: str = "data"):
        self.versions_dir = Path(versions_dir)
        self.versions_dir.mkdir(parents=True, exist_ok=True)
        self.data_dir = Path(data_dir)
        self.manifest = self._load_manifest()

    def _manifest_path(self) -> Path:
        return self.versions_dir / "manifest.json"

    def _load_manifest(self) -> dict:
        mp = self._manifest_path()
        if mp.exists():
            with open(mp) as f:
                return json.load(f)
        return {
            "current_version": None,
            "versions": [],
            "rollback_history": [],
        }

    def _save_manifest(self):
        with open(self._manifest_path(), "w") as f:
            json.dump(self.manifest, f, indent=2, ensure_ascii=False,
                      default=str)

    @property
    def current_version(self) -> Optional[str]:
        return self.manifest.get("current_version")

    def list_versions(self) -> List[dict]:
        """List all available versions."""
        return self.manifest.get("versions", [])

    def get_version(self, version: str) -> Optional[dict]:
        """Get details for a specific version."""
        for v in self.manifest["versions"]:
            if v["version"] == version:
                return v
        return None

    def _next_version(self, bump: str = "minor") -> str:
        """Calculate next version number."""
        current = self.current_version
        if not current:
            return "1.0.0"

        parts = current.split(".")
        major, minor, patch = int(parts[0]), int(parts[1]), int(parts[2])

        if bump == "major":
            return f"{major + 1}.0.0"
        elif bump == "minor":
            return f"{major}.{minor + 1}.0"
        else:  # patch
            return f"{major}.{minor}.{patch + 1}"

    def create_version(self, description: str,
                       data_sources: dict,
                       population_df: pd.DataFrame = None,
                       population_file: str = None,
                       synthesis_config: dict = None,
                       bump: str = "minor") -> str:
        """
        Create a new data version.

        Args:
            description: Human-readable description of what changed
            data_sources: Dict of {dataset_key: {file, last_modified, records}}
            population_df: Agent DataFrame (if available)
            population_file: Path to existing population CSV
            synthesis_config: Parameters used for synthesis
            bump: Version bump type (major/minor/patch)

        Returns:
            New version string (e.g., "1.1.0")
        """
        new_ver = self._next_version(bump)
        ver_dir = self.versions_dir / f"v{new_ver}"
        ver_dir.mkdir(parents=True, exist_ok=True)

        # 1. Save population snapshot
        pop_path = ver_dir / "population.csv"
        agent_count = 0
        if population_df is not None:
            population_df.to_csv(pop_path, index=False)
            agent_count = len(population_df)
        elif population_file:
            src = Path(population_file)
            if src.exists():
                shutil.copy2(src, pop_path)
                agent_count = sum(1 for _ in open(pop_path)) - 1  # minus header

        # 2. Copy census data sources
        ds_dir = ver_dir / "data_sources"
        ds_dir.mkdir(exist_ok=True)
        for key, info in data_sources.items():
            src_file = info.get("file") or info.get("download_path", "")
            if src_file and Path(src_file).exists():
                shutil.copy2(src_file, ds_dir / Path(src_file).name)

        # 3. Save config
        config = {
            "synthesis_config": synthesis_config or {},
            "data_sources": data_sources,
            "created_at": datetime.now().isoformat(),
            "description": description,
        }
        with open(ver_dir / "config.json", "w") as f:
            json.dump(config, f, indent=2, ensure_ascii=False, default=str)

        # 4. Update manifest
        entry = DataVersion(
            version=new_ver,
            created_at=datetime.now().isoformat(),
            description=description,
            data_sources=data_sources,
            agent_count=agent_count,
            population_file=str(pop_path) if pop_path.exists() else "",
            synthesis_config=synthesis_config or {},
            is_active=True,
        ).to_dict()

        # Deactivate previous version
        for v in self.manifest["versions"]:
            v["is_active"] = False

        self.manifest["versions"].append(entry)
        self.manifest["current_version"] = new_ver
        self._save_manifest()

        logger.info(f"Version {new_ver} created: {description} "
                    f"({agent_count} agents)")
        return new_ver

    def rollback(self, target_version: str) -> Optional[dict]:
        """
        Rollback to a previous version.

        Returns:
            {"version": str, "population_df": DataFrame, "config": dict}
            or None if version not found
        """
        ver_entry = self.get_version(target_version)
        if not ver_entry:
            logger.error(f"Version {target_version} not found")
            return None

        ver_dir = self.versions_dir / f"v{target_version}"
        if not ver_dir.exists():
            logger.error(f"Version directory not found: {ver_dir}")
            return None

        # Load population
        pop_path = ver_dir / "population.csv"
        population_df = None
        if pop_path.exists():
            population_df = pd.read_csv(pop_path)

        # Load config
        config_path = ver_dir / "config.json"
        config = {}
        if config_path.exists():
            with open(config_path) as f:
                config = json.load(f)

        # Restore data sources to active data directory
        ds_dir = ver_dir / "data_sources"
        if ds_dir.exists():
            census_dir = self.data_dir / "census"
            census_dir.mkdir(parents=True, exist_ok=True)
            for f in ds_dir.iterdir():
                if f.suffix == ".csv":
                    shutil.copy2(f, census_dir / f.name)

        # Copy population to output dir
        output_dir = self.data_dir / "output"
        if population_df is not None and output_dir.exists():
            population_df.to_csv(
                output_dir / "agents_20k_v2.csv", index=False)

        # Update manifest
        for v in self.manifest["versions"]:
            v["is_active"] = (v["version"] == target_version)

        self.manifest["current_version"] = target_version
        self.manifest["rollback_history"].append({
            "from_version": self.current_version,
            "to_version": target_version,
            "rolled_back_at": datetime.now().isoformat(),
        })
        self._save_manifest()

        logger.info(f"Rolled back to version {target_version}")

        return {
            "version": target_version,
            "population_df": population_df,
            "config": config,
            "agent_count": len(population_df) if population_df is not None else 0,
        }

    def compare_versions(self, v1: str, v2: str) -> dict:
        """Compare two versions to show what changed."""
        entry1 = self.get_version(v1)
        entry2 = self.get_version(v2)
        if not entry1 or not entry2:
            return {"error": "Version not found"}

        ds1 = set(entry1.get("data_sources", {}).keys())
        ds2 = set(entry2.get("data_sources", {}).keys())

        # Check which data sources changed
        changed_sources = {}
        for key in ds1 | ds2:
            s1 = entry1.get("data_sources", {}).get(key, {})
            s2 = entry2.get("data_sources", {}).get(key, {})
            if s1.get("last_modified") != s2.get("last_modified"):
                changed_sources[key] = {
                    f"v{v1}": s1.get("last_modified", "N/A"),
                    f"v{v2}": s2.get("last_modified", "N/A"),
                }

        return {
            "v1": v1,
            "v2": v2,
            "agent_count_change": (
                entry2.get("agent_count", 0) - entry1.get("agent_count", 0)),
            "data_sources_added": list(ds2 - ds1),
            "data_sources_removed": list(ds1 - ds2),
            "data_sources_changed": changed_sources,
            "v1_created": entry1.get("created_at"),
            "v2_created": entry2.get("created_at"),
        }

    def get_status(self) -> dict:
        """Get version manager status for dashboard."""
        versions = self.manifest.get("versions", [])
        return {
            "current_version": self.current_version,
            "total_versions": len(versions),
            "versions": [
                {
                    "version": v["version"],
                    "created_at": v["created_at"],
                    "description": v["description"],
                    "agent_count": v.get("agent_count", 0),
                    "is_active": v.get("is_active", False),
                }
                for v in versions
            ],
            "rollback_history": self.manifest.get("rollback_history", [])[-10:],
        }
