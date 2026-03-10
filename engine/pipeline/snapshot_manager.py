"""
Snapshot Manager — Time rollback mechanism for the Digital Twin.

Supports:
1. Periodic snapshots of full agent state (every N ticks)
2. Rollback to any saved snapshot
3. Event log pruning on rollback
4. Differential snapshots for storage efficiency
"""

import pandas as pd
import numpy as np
import json
import os
from pathlib import Path
from typing import Optional, List, Dict
from datetime import date
import logging

logger = logging.getLogger(__name__)


class SnapshotManager:
    """Manages simulation state snapshots for time travel."""

    def __init__(self, snapshot_dir: str = "snapshots",
                 auto_interval: int = 30):
        """
        Args:
            snapshot_dir: Directory to store snapshot files
            auto_interval: Auto-snapshot every N ticks (default: 30 = monthly)
        """
        self.snapshot_dir = Path(snapshot_dir)
        self.snapshot_dir.mkdir(parents=True, exist_ok=True)
        self.auto_interval = auto_interval
        self.manifest: List[dict] = []
        self._load_manifest()

    def _manifest_path(self) -> Path:
        return self.snapshot_dir / "manifest.json"

    def _load_manifest(self):
        """Load existing manifest if present."""
        mp = self._manifest_path()
        if mp.exists():
            with open(mp) as f:
                self.manifest = json.load(f)
            logger.info(f"Loaded {len(self.manifest)} snapshots from manifest")
        else:
            self.manifest = []

    def _save_manifest(self):
        with open(self._manifest_path(), "w") as f:
            json.dump(self.manifest, f, indent=2)

    def save_snapshot(self, agents_df: pd.DataFrame, tick: int,
                      sim_date: str, event_log: List[dict],
                      metadata: Optional[dict] = None) -> str:
        """
        Save a full snapshot of simulation state.

        Args:
            agents_df: Current agent DataFrame
            tick: Current tick number
            sim_date: Current simulation date
            event_log: Accumulated event log up to this tick
            metadata: Optional extra metadata

        Returns:
            Snapshot ID (filename stem)
        """
        snap_id = f"tick_{tick:06d}"
        snap_path = self.snapshot_dir / f"{snap_id}.parquet"
        log_path = self.snapshot_dir / f"{snap_id}_events.json"

        # Save agent state as parquet (efficient columnar storage)
        try:
            agents_df.to_parquet(snap_path, index=False)
        except ImportError:
            # Fallback to CSV if parquet engines not available
            snap_path = self.snapshot_dir / f"{snap_id}.csv"
            agents_df.to_csv(snap_path, index=False)

        # Save event log
        with open(log_path, "w") as f:
            json.dump(event_log, f)

        entry = {
            "snap_id": snap_id,
            "tick": tick,
            "sim_date": sim_date,
            "agent_count": len(agents_df),
            "alive_count": int((agents_df.get("is_alive", pd.Series([True] * len(agents_df))) == True).sum()),
            "event_count": len(event_log),
            "file_size_kb": round(snap_path.stat().st_size / 1024, 1),
            "metadata": metadata or {},
        }
        self.manifest.append(entry)
        self._save_manifest()

        logger.info(f"Snapshot saved: {snap_id} ({entry['file_size_kb']} KB, "
                    f"{entry['agent_count']} agents)")
        return snap_id

    def load_snapshot(self, snap_id: str) -> Optional[dict]:
        """
        Load a snapshot by ID.

        Returns:
            {"agents_df": DataFrame, "tick": int, "sim_date": str,
             "event_log": list, "metadata": dict}
            or None if not found
        """
        parquet_path = self.snapshot_dir / f"{snap_id}.parquet"
        csv_path = self.snapshot_dir / f"{snap_id}.csv"
        log_path = self.snapshot_dir / f"{snap_id}_events.json"

        if parquet_path.exists():
            try:
                agents_df = pd.read_parquet(parquet_path)
            except ImportError:
                if csv_path.exists():
                    agents_df = pd.read_csv(csv_path)
                else:
                    logger.error(f"Cannot read parquet and no CSV fallback: {snap_id}")
                    return None
        elif csv_path.exists():
            agents_df = pd.read_csv(csv_path)
        else:
            logger.error(f"Snapshot not found: {snap_id}")
            return None
        event_log = []
        if log_path.exists():
            with open(log_path) as f:
                event_log = json.load(f)

        # Find manifest entry
        entry = next((e for e in self.manifest if e["snap_id"] == snap_id), {})

        logger.info(f"Loaded snapshot: {snap_id} ({len(agents_df)} agents)")
        return {
            "agents_df": agents_df,
            "tick": entry.get("tick", 0),
            "sim_date": entry.get("sim_date", ""),
            "event_log": event_log,
            "metadata": entry.get("metadata", {}),
        }

    def rollback(self, target_tick: int) -> Optional[dict]:
        """
        Rollback to the nearest snapshot at or before target_tick.

        Also prunes snapshots and event logs after the target tick.

        Returns:
            Loaded snapshot dict, or None if no valid snapshot found
        """
        # Find nearest snapshot <= target_tick
        candidates = [e for e in self.manifest if e["tick"] <= target_tick]
        if not candidates:
            logger.error(f"No snapshot found at or before tick {target_tick}")
            return None

        best = max(candidates, key=lambda e: e["tick"])
        logger.info(f"Rolling back to {best['snap_id']} (tick {best['tick']})")

        # Load the snapshot
        result = self.load_snapshot(best["snap_id"])
        if result is None:
            return None

        # Prune future snapshots
        future = [e for e in self.manifest if e["tick"] > best["tick"]]
        for entry in future:
            sid = entry["snap_id"]
            for ext in [".parquet", ".csv", "_events.json"]:
                p = self.snapshot_dir / f"{sid}{ext}"
                if p.exists():
                    p.unlink()
            logger.info(f"Pruned future snapshot: {sid}")

        self.manifest = [e for e in self.manifest if e["tick"] <= best["tick"]]
        self._save_manifest()

        return result

    def should_auto_snapshot(self, tick: int) -> bool:
        """Check if an auto-snapshot should be taken at this tick."""
        return tick > 0 and tick % self.auto_interval == 0

    def list_snapshots(self) -> List[dict]:
        """List all available snapshots."""
        return list(self.manifest)

    def get_storage_stats(self) -> dict:
        """Get storage usage statistics."""
        total_size = sum(
            f.stat().st_size
            for f in self.snapshot_dir.iterdir()
            if f.suffix in (".parquet", ".json")
        )
        return {
            "snapshot_count": len(self.manifest),
            "total_size_mb": round(total_size / 1024 / 1024, 2),
            "snapshot_dir": str(self.snapshot_dir),
            "auto_interval": self.auto_interval,
        }
