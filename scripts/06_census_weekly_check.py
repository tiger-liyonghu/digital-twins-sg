"""
Script 06: Weekly Census Data Check & Auto-Version

Designed to run as a cron job (every Sunday at 02:00):
  crontab -e
  0 2 * * 0 cd /path/to/project && python scripts/06_census_weekly_check.py >> logs/census_check.log 2>&1

What it does:
1. Scan data.gov.sg for updates to 14 monitored datasets
2. If new data found → download CSV → create new data version
3. Optionally trigger re-synthesis of the 20K agent population
4. Print summary report

Flags:
  --force           Force check even if checked recently
  --dry-run         Scan only, don't download or create versions
  --re-synthesize   Also run population re-synthesis on new data
  --status          Just print current monitor status
"""

import sys
import os
import json
import argparse
from datetime import datetime
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from engine.pipeline.collectors.census_monitor import (
    CensusMonitor, MONITORED_DATASETS
)
from engine.pipeline.version_manager import VersionManager


def print_header(text: str):
    width = 60
    print("=" * width)
    print(f"  {text}")
    print("=" * width)


def print_monitor_status(monitor: CensusMonitor, vm: VersionManager):
    """Print current status of monitor and versions."""
    status = monitor.get_monitor_status()
    vm_status = vm.get_status()

    print_header("Census Data Monitor Status")

    print(f"\nLast check:         {status['last_check'] or 'Never'}")
    print(f"Check interval:     Every {status['check_interval_days']} days")
    print(f"Should check now:   {'Yes' if status['should_check_now'] else 'No'}")
    print(f"Datasets tracked:   {status['datasets_tracked']}")
    print(f"Datasets with data: {status['datasets_with_data']}")

    print(f"\n--- Monitored Datasets ({status['datasets_tracked']}) ---")
    for key, info in status["datasets"].items():
        marker = "[OK]" if info["has_data"] else "[--]"
        print(f"  {marker} {info['name']}")
        print(f"       Category: {info['category']}  "
              f"Freq: {info['frequency']}  "
              f"Modified: {info['last_modified']}")

    print(f"\n--- Version Manager ---")
    print(f"Current version:  {vm_status['current_version'] or 'None'}")
    print(f"Total versions:   {vm_status['total_versions']}")
    if vm_status["versions"]:
        print("\nVersion History:")
        for v in vm_status["versions"]:
            active = " [ACTIVE]" if v["is_active"] else ""
            print(f"  v{v['version']}{active}  "
                  f"{v['created_at'][:19]}  "
                  f"{v['agent_count']:,} agents  "
                  f"{v['description']}")

    if vm_status["rollback_history"]:
        print("\nRollback History:")
        for rb in vm_status["rollback_history"]:
            print(f"  {rb['rolled_back_at'][:19]}: "
                  f"v{rb['from_version']} -> v{rb['to_version']}")


def run_check(monitor: CensusMonitor, vm: VersionManager,
              force: bool = False, dry_run: bool = False,
              re_synthesize: bool = False):
    """Run the weekly data check."""
    print_header("Weekly Census Data Check")
    print(f"Time:           {datetime.now().isoformat()}")
    print(f"Force:          {force}")
    print(f"Dry run:        {dry_run}")
    print(f"Re-synthesize:  {re_synthesize}")

    if not monitor.should_check() and not force:
        print(f"\nSkipping — last check was recent. Use --force to override.")
        return

    # Step 1: Scan for updates
    print(f"\nStep 1: Scanning data.gov.sg for updates...")
    if force:
        events = monitor.force_check()
    else:
        events = monitor.fetch(str(datetime.now().date()))

    if not events:
        print("  No updates found. All datasets are current.")
        return

    # Step 2: Report findings
    print(f"\n  Found {len(events)} dataset update(s):")
    for ev in events:
        payload = ev.payload
        print(f"    - {payload['dataset_name']} ({payload['dataset_key']})")
        prev = payload.get('previous_record_count', 0)
        new = payload.get('new_record_count', 0)
        if prev and new:
            print(f"      Records: {prev:,} -> {new:,}")

    if dry_run:
        print("\n  [DRY RUN] Stopping here. No version created.")
        return

    # Step 3: Create new data version
    print(f"\nStep 2: Creating new data version...")

    # Build data_sources dict from events
    data_sources = {}
    descriptions = []
    for ev in events:
        p = ev.payload
        data_sources[p["dataset_key"]] = {
            "name": p["dataset_name"],
            "last_modified": datetime.now().isoformat(),
            "record_count": p.get("new_record_count", 0),
            "download_path": p.get("download_path", ""),
        }
        descriptions.append(p["dataset_name"])

    # Also include unchanged datasets from current version
    current = vm.current_version
    if current:
        current_entry = vm.get_version(current)
        if current_entry:
            for key, info in current_entry.get("data_sources", {}).items():
                if key not in data_sources:
                    data_sources[key] = info

    description = f"Data update: {', '.join(descriptions)}"

    # Load current population (if exists) as baseline
    pop_file = PROJECT_ROOT / "data" / "output" / "agents_20k_v2.csv"
    if not pop_file.exists():
        pop_file = PROJECT_ROOT / "data" / "output" / "agents_20k.csv"

    new_ver = vm.create_version(
        description=description,
        data_sources=data_sources,
        population_file=str(pop_file) if pop_file.exists() else None,
        bump="minor",
    )
    print(f"  Created version: v{new_ver}")

    # Step 4: Re-synthesis (optional)
    if re_synthesize:
        print(f"\nStep 3: Re-synthesizing population with updated data...")
        try:
            # Import and run synthesis
            from scripts.synthesize_population import synthesize
            new_pop_path = synthesize()
            print(f"  New population: {new_pop_path}")

            # Update the version with new population
            import pandas as pd
            new_pop = pd.read_csv(new_pop_path)
            vm.create_version(
                description=f"Re-synthesized population from v{new_ver} data",
                data_sources=data_sources,
                population_df=new_pop,
                bump="patch",
            )
            print(f"  Population re-synthesis complete.")
        except Exception as e:
            print(f"  Re-synthesis failed: {e}")
            print(f"  Population NOT updated. Manual re-synthesis needed:")
            print(f"    python scripts/03_synthesize_v2_mathematical.py")

    # Summary
    print(f"\n{'=' * 60}")
    print(f"Check complete. Current version: v{vm.current_version}")
    print(f"{'=' * 60}")


def rollback_version(vm: VersionManager, target: str):
    """Rollback to a specific version."""
    print_header(f"Rollback to v{target}")

    current = vm.current_version
    if current == target:
        print(f"Already at version v{target}. Nothing to do.")
        return

    result = vm.rollback(target)
    if result:
        print(f"  Rolled back: v{current} -> v{target}")
        print(f"  Agents restored: {result['agent_count']:,}")
        print(f"  Population file updated in data/output/")
    else:
        print(f"  Rollback FAILED. Version v{target} not found.")
        print(f"  Available versions:")
        for v in vm.list_versions():
            print(f"    v{v['version']}  {v['description']}")


def main():
    parser = argparse.ArgumentParser(
        description="Weekly Census Data Check & Version Manager")
    parser.add_argument("--force", action="store_true",
                        help="Force check even if checked recently")
    parser.add_argument("--dry-run", action="store_true",
                        help="Scan only, don't download or version")
    parser.add_argument("--re-synthesize", action="store_true",
                        help="Re-synthesize population after data update")
    parser.add_argument("--status", action="store_true",
                        help="Print current status")
    parser.add_argument("--rollback", type=str, default=None,
                        help="Rollback to version (e.g., 1.0.0)")
    parser.add_argument("--compare", nargs=2, metavar=("V1", "V2"),
                        help="Compare two versions")
    parser.add_argument("--init", action="store_true",
                        help="Initialize v1.0.0 from current population")

    args = parser.parse_args()

    # Initialize
    data_dir = str(PROJECT_ROOT / "data")
    monitor = CensusMonitor(data_dir=os.path.join(data_dir, "census"))
    vm = VersionManager(
        versions_dir=str(PROJECT_ROOT / "versions"),
        data_dir=data_dir,
    )

    if args.status:
        print_monitor_status(monitor, vm)
    elif args.rollback:
        rollback_version(vm, args.rollback)
    elif args.compare:
        diff = vm.compare_versions(args.compare[0], args.compare[1])
        print(json.dumps(diff, indent=2, ensure_ascii=False))
    elif args.init:
        print_header("Initialize Version 1.0.0")
        pop_file = PROJECT_ROOT / "data" / "output" / "agents_20k_v2.csv"
        if not pop_file.exists():
            pop_file = PROJECT_ROOT / "data" / "output" / "agents_20k.csv"
        ver = vm.create_version(
            description="Initial population (Census 2020 base data)",
            data_sources={"census_2020": {
                "name": "Singapore Census of Population 2020",
                "last_modified": "2021-06-16",
            }},
            population_file=str(pop_file) if pop_file.exists() else None,
            bump="major",
        )
        print(f"  Created version: v{ver}")
        if pop_file.exists():
            import pandas as pd
            n = len(pd.read_csv(pop_file))
            print(f"  Population: {n:,} agents")
    else:
        run_check(monitor, vm, force=args.force, dry_run=args.dry_run,
                  re_synthesize=args.re_synthesize)


if __name__ == "__main__":
    main()
