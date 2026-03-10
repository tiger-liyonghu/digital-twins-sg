"""
Script 31: Fix agent data quality issues in V4 database.

Fixes:
  1. Ethnicity: extract from cultural_background (not random)
  2. Occupation: restore NVIDIA original (not CPT-resampled)
  3. Industry: restore NVIDIA original
  4. Dialect group: extract from cultural_background (Chinese only)

Only updates adults (data_source='nvidia_nemotron').
Children keep their existing values.

Usage:
    python3 scripts/31_fix_agent_data.py [--dry-run] [--limit N]
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import argparse
import logging
import time
import math
import numpy as np
import pandas as pd
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

DATA_DIR = Path(__file__).parent.parent / "data"
PARQUET_PATH = DATA_DIR / "nvidia_personas_singapore.parquet"

SUPABASE_URL = "https://rndfpyuuredtqncegygi.supabase.co"
SUPABASE_SERVICE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InJuZGZweXV1cmVkdHFuY2VneWdpIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc3MzA4Nzk0NiwiZXhwIjoyMDg4NjYzOTQ2fQ.EMjLfr3N8RDpBPkVftYKCg1Pf6h4rOj8xfCXSuJIxQI"


def extract_ethnicity(text):
    """Extract ethnicity from cultural_background text."""
    if not isinstance(text, str):
        return None
    t = text.lower()
    # Chinese indicators
    if any(kw in t for kw in ['chinese', 'hokkien', 'teochew', 'cantonese',
                               'hakka', 'hainanese', 'mandarin', 'lunar new year',
                               'chinese new year', 'qingming']):
        return 'Chinese'
    # Malay indicators
    if any(kw in t for kw in ['malay', 'melayu', 'hari raya', 'ramadan',
                               'kampong', 'jawi', 'bahasa']):
        return 'Malay'
    # Indian indicators
    if any(kw in t for kw in ['indian', 'tamil', 'hindi', 'sikh', 'punjabi',
                               'deepavali', 'diwali', 'pongal', 'thaipusam']):
        return 'Indian'
    return 'Others'


def extract_dialect(text):
    """Extract Chinese dialect group from cultural_background."""
    if not isinstance(text, str):
        return None
    t = text.lower()
    if 'hokkien' in t:
        return 'Hokkien'
    if 'teochew' in t:
        return 'Teochew'
    if 'cantonese' in t:
        return 'Cantonese'
    if 'hakka' in t:
        return 'Hakka'
    if 'hainanese' in t:
        return 'Hainanese'
    return None


def batch_update_by_value(supabase, table, records, batch_size=500):
    """
    Group records by (ethnicity, occupation, industry, dialect_group) and
    batch update all agent_ids sharing the same values in one call.
    Much faster than per-row updates.
    """
    from collections import defaultdict

    # Group by update values
    groups = defaultdict(list)
    for rec in records:
        key = (rec['ethnicity'], rec['occupation'], rec['industry'], rec.get('dialect_group'))
        groups[key].append(rec['agent_id'])

    logger.info(f"Grouped into {len(groups)} unique value combinations")

    total = len(records)
    success = 0
    errors = 0
    group_count = 0

    for (eth, occ, ind, dial), agent_ids in groups.items():
        update_data = {
            'ethnicity': eth,
            'occupation': occ,
            'industry': ind,
            'dialect_group': dial,
        }
        # Supabase .in_() has a limit, chunk the agent_ids
        for chunk_start in range(0, len(agent_ids), batch_size):
            chunk = agent_ids[chunk_start:chunk_start + batch_size]
            for attempt in range(3):
                try:
                    supabase.table(table).update(update_data).in_('agent_id', chunk).execute()
                    success += len(chunk)
                    break
                except Exception as e:
                    if attempt < 2:
                        time.sleep(2 ** attempt)
                        continue
                    errors += len(chunk)
                    if errors <= 20:
                        logger.error(f"  Batch failed ({eth}/{occ}): {e}")

        group_count += 1
        if group_count % 200 == 0:
            logger.info(f"  Groups processed: {group_count}/{len(groups)}, updated: {success:,}/{total:,}")

    logger.info(f"  Done: {success:,} success, {errors:,} errors ({len(groups)} groups)")
    return success, errors


def main():
    parser = argparse.ArgumentParser(description="Fix agent data quality")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--limit", type=int, default=0)
    args = parser.parse_args()

    # Load NVIDIA parquet
    logger.info(f"Loading NVIDIA parquet...")
    df = pd.read_parquet(PARQUET_PATH)
    logger.info(f"Loaded {len(df):,} adults")

    if args.limit > 0:
        df = df.head(args.limit)
        logger.info(f"Limited to {len(df):,}")

    # === FIX 1: Extract ethnicity ===
    logger.info("Extracting ethnicity from cultural_background...")
    df['ethnicity'] = df['cultural_background'].apply(extract_ethnicity)
    eth_dist = df['ethnicity'].value_counts()
    logger.info(f"Ethnicity distribution:")
    for eth, count in eth_dist.items():
        logger.info(f"  {eth}: {count:,} ({count/len(df)*100:.1f}%)")

    # === FIX 2: Extract dialect group (Chinese only) ===
    logger.info("Extracting dialect group...")
    df['dialect_group'] = df['cultural_background'].apply(extract_dialect)
    dialect_dist = df['dialect_group'].value_counts(dropna=False)
    logger.info(f"Dialect distribution:")
    for d, count in dialect_dist.head(10).items():
        logger.info(f"  {d}: {count:,}")

    # === FIX 3: Keep NVIDIA occupation + industry (already correct) ===
    logger.info("Using NVIDIA original occupation and industry...")
    occ_dist = df['occupation'].value_counts()
    logger.info(f"Top occupations: {dict(occ_dist.head(5))}")

    # === Prepare update records ===
    logger.info("Preparing update records...")
    records = []
    for _, row in df.iterrows():
        rec = {
            'agent_id': row['uuid'],
            'ethnicity': row['ethnicity'],
            'occupation': row['occupation'] if pd.notna(row['occupation']) else '',
            'industry': row['industry'] if pd.notna(row['industry']) else '',
            'dialect_group': row['dialect_group'] if pd.notna(row['dialect_group']) else None,
        }
        records.append(rec)

    logger.info(f"Prepared {len(records):,} update records")

    # === Validation summary ===
    logger.info(f"\n=== VALIDATION ===")
    logger.info(f"Total adults to update: {len(records):,}")
    logger.info(f"Ethnicity: {dict(eth_dist)}")
    logger.info(f"Dialect: {dict(df['dialect_group'].value_counts(dropna=True))}")
    logger.info(f"Occupation (employed): {(~df.occupation.isin(['Retired','Homemaker','Unemployed','Student','National Service'])).sum():,}")

    if args.dry_run:
        logger.info("DRY RUN — skipping upload")
        # Show sample
        for r in records[:5]:
            logger.info(f"  {r}")
        return

    # === Upload ===
    from supabase import create_client
    supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)

    s, e = batch_update_by_value(supabase, "agents", records, batch_size=500)

    print(f"\n{'='*60}")
    print(f"DATA FIX COMPLETE")
    print(f"{'='*60}")
    print(f"Updated: {s:,} agents")
    print(f"Errors:  {e:,}")
    print(f"Fixes applied:")
    print(f"  1. Ethnicity extracted from cultural_background")
    print(f"  2. Occupation restored to NVIDIA original")
    print(f"  3. Industry restored to NVIDIA original")
    print(f"  4. Dialect group extracted (Chinese only)")


if __name__ == "__main__":
    main()
