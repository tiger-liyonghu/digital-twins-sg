"""
Script 05: Create Supabase tables and seed 20,000 agents.

Steps:
1. Create tables via SQL (if not exist)
2. Read agents_20k_v2.csv
3. Transform to match schema
4. Batch upsert to Supabase
5. Create households table from agent data
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
import numpy as np
from pathlib import Path
import json
import logging
import math

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

# Supabase config
SUPABASE_URL = "https://rndfpyuuredtqncegygi.supabase.co"
SUPABASE_ANON_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InJuZGZweXV1cmVkdHFuY2VneWdpIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzMwODc5NDYsImV4cCI6MjA4ODY2Mzk0Nn0.J6ks7B2Vv3epXLQSeBcO3JMtgJiQaiA7WCCJCuYceqQ"
SUPABASE_SERVICE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InJuZGZweXV1cmVkdHFuY2VneWdpIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc3MzA4Nzk0NiwiZXhwIjoyMDg4NjYzOTQ2fQ.EMjLfr3N8RDpBPkVftYKCg1Pf6h4rOj8xfCXSuJIxQI"


def get_supabase_client():
    """Initialize Supabase client."""
    try:
        from supabase import create_client
        # Use service role key for full access (bypasses RLS)
        return create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
    except ImportError:
        logger.error("supabase-py not installed. Run: pip3 install supabase")
        sys.exit(1)


def create_tables(supabase):
    """Create tables via Supabase SQL editor (RPC or direct)."""
    schema_path = Path(__file__).parent.parent / "supabase" / "schema.sql"
    if not schema_path.exists():
        logger.error(f"Schema file not found: {schema_path}")
        return False

    sql = schema_path.read_text()

    # Execute via REST API
    import urllib.request
    import urllib.error

    url = f"{SUPABASE_URL}/rest/v1/rpc/exec_sql"
    headers = {
        "apikey": SUPABASE_ANON_KEY,
        "Authorization": f"Bearer {SUPABASE_ANON_KEY}",
        "Content-Type": "application/json",
    }

    # Note: Direct SQL exec may not be available via anon key.
    # Tables should be created via Supabase Dashboard SQL Editor instead.
    logger.info("Tables should be created via Supabase Dashboard SQL Editor.")
    logger.info(f"Schema file: {schema_path}")
    return True


def transform_agent(row: dict) -> dict:
    """Transform CSV row to match Supabase agents table schema."""
    def safe_int(v, default=0):
        try:
            if pd.isna(v):
                return default
            return int(float(v))
        except (ValueError, TypeError):
            return default

    def safe_float(v, default=3.0):
        try:
            if pd.isna(v):
                return default
            return round(float(v), 2)
        except (ValueError, TypeError):
            return default

    def safe_str(v, default=''):
        if pd.isna(v):
            return default
        return str(v)

    agent = {
        "agent_id": row["agent_id"],
        "age": safe_int(row.get("age")),
        "age_group": safe_str(row.get("age_group")),
        "gender": row["gender"],
        "ethnicity": row["ethnicity"],
        "residency_status": row["residency_status"],
        "planning_area": row["planning_area"],

        # Education & Career
        "education_level": safe_str(row.get("education_level")),
        "monthly_income": safe_int(row.get("monthly_income")),

        # Family
        "marital_status": safe_str(row.get("marital_status", "Single")),
        "household_id": safe_str(row.get("household_id")),
        "household_role": safe_str(row.get("household_role")),

        # Housing
        "housing_type": safe_str(row.get("housing_type")),

        # Health
        "health_status": safe_str(row.get("health_status", "Healthy")),

        # NS
        "ns_status": safe_str(row.get("ns_status", "Not_Applicable")),

        # Transport
        "commute_mode": safe_str(row.get("commute_mode", "MRT")),
        "has_vehicle": str(row.get("has_vehicle", "False")).lower() == "true",

        # Life state
        "life_phase": safe_str(row.get("life_phase", "establishment")),
        "agent_type": safe_str(row.get("agent_type", "active")),
        "is_alive": True,

        # Personality
        "big5_o": safe_float(row.get("big5_o")),
        "big5_c": safe_float(row.get("big5_c")),
        "big5_e": safe_float(row.get("big5_e")),
        "big5_a": safe_float(row.get("big5_a")),
        "big5_n": safe_float(row.get("big5_n")),

        # Attitudes
        "risk_appetite": safe_float(row.get("risk_appetite")),
        "political_leaning": safe_float(row.get("political_leaning")),
        "social_trust": safe_float(row.get("social_trust")),
        "religious_devotion": safe_float(row.get("religious_devotion")),
    }

    return agent


def build_households(df: pd.DataFrame) -> list:
    """Build household records from agent data."""
    households = []
    grouped = df.groupby("household_id")

    for hh_id, group in grouped:
        if not hh_id or pd.isna(hh_id):
            continue

        head = group[group["household_role"] == "head"]
        if len(head) == 0:
            head = group.iloc[:1]
        else:
            head = head.iloc[:1]

        hh = {
            "household_id": str(hh_id),
            "planning_area": str(head["planning_area"].values[0]),
            "housing_type": str(head["housing_type"].values[0]) if "housing_type" in head.columns else "",
            "household_size": int(len(group)),
            "household_income": int(group["monthly_income"].sum()),
        }
        households.append(hh)

    return households


def batch_upsert(supabase, table: str, records: list, batch_size: int = 500):
    """Upsert records in batches."""
    total = len(records)
    batches = math.ceil(total / batch_size)

    logger.info(f"Upserting {total} records to '{table}' in {batches} batches of {batch_size}")

    success = 0
    errors = 0

    for i in range(batches):
        start = i * batch_size
        end = min(start + batch_size, total)
        batch = records[start:end]

        try:
            result = supabase.table(table).upsert(batch).execute()
            success += len(batch)

            if (i + 1) % 10 == 0 or i == batches - 1:
                logger.info(f"  Batch {i+1}/{batches}: {success}/{total} records uploaded")

        except Exception as e:
            errors += len(batch)
            logger.error(f"  Batch {i+1} failed: {e}")

            # Try smaller batches on failure
            if batch_size > 50:
                logger.info("  Retrying with smaller batch size...")
                for j in range(0, len(batch), 50):
                    mini_batch = batch[j:j+50]
                    try:
                        supabase.table(table).upsert(mini_batch).execute()
                        success += len(mini_batch)
                        errors -= len(mini_batch)
                    except Exception as e2:
                        logger.error(f"  Mini-batch also failed: {e2}")

    logger.info(f"Done: {success} success, {errors} errors")
    return success, errors


def main():
    # Load CSV
    data_dir = Path(__file__).parent.parent / "data" / "output"
    csv_path = data_dir / "agents_20k_v2.csv"
    if not csv_path.exists():
        csv_path = data_dir / "agents_20k.csv"
    if not csv_path.exists():
        logger.error("No agent CSV found")
        return

    df = pd.read_csv(csv_path)
    logger.info(f"Loaded {len(df)} agents from {csv_path.name}")

    # Initialize Supabase
    supabase = get_supabase_client()
    logger.info(f"Connected to Supabase: {SUPABASE_URL}")

    # Transform agents
    logger.info("Transforming agent records...")
    agents = []
    for _, row in df.iterrows():
        agents.append(transform_agent(row.to_dict()))
    logger.info(f"Transformed {len(agents)} agents")

    # Build households
    logger.info("Building household records...")
    households = build_households(df)
    logger.info(f"Built {len(households)} households")

    # Upload households first (agents reference them)
    logger.info("\n=== Uploading Households ===")
    hh_success, hh_errors = batch_upsert(supabase, "households", households)

    # Upload agents
    logger.info("\n=== Uploading Agents ===")
    ag_success, ag_errors = batch_upsert(supabase, "agents", agents)

    # Summary
    print("\n" + "=" * 50)
    print("SEED COMPLETE")
    print("=" * 50)
    print(f"Households: {hh_success} uploaded, {hh_errors} errors")
    print(f"Agents:     {ag_success} uploaded, {ag_errors} errors")
    print(f"Database:   {SUPABASE_URL}")


if __name__ == "__main__":
    main()
