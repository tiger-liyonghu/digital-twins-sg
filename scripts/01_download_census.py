"""
Script 01: Download core Census 2020 datasets from data.gov.sg
These are the 12 key cross-tabulation datasets needed for IPF population synthesis.
"""

import requests
import os
import time
import json

DATA_DIR = os.path.join(os.path.dirname(__file__), '..', 'data', 'census')
os.makedirs(DATA_DIR, exist_ok=True)

# data.gov.sg API base
API_BASE = "https://api-production.data.gov.sg/v2/public/api/datasets"

# Key datasets to search for and download
# Each entry: (search_query, description, priority)
DATASETS_TO_FIND = [
    ("resident population planning area age group sex",
     "Population by Planning Area x Age x Sex (Census 2020)", 1),
    ("resident population age group ethnic group sex",
     "Population by Age x Ethnicity x Sex", 2),
    ("resident households monthly household income type dwelling",
     "Households by Income x Housing Type", 3),
    ("resident working persons monthly income occupation sex",
     "Workers by Income x Occupation x Sex", 4),
    ("resident population highest qualification age group sex",
     "Population by Education x Age x Sex", 5),
    ("resident households household living arrangement",
     "Households by Living Arrangement", 6),
    ("resident households household size ethnic group",
     "Households by Size x Ethnicity", 7),
    ("resident population planning area marital status sex",
     "Population by Planning Area x Marital Status x Sex", 8),
    ("employed residents usual mode transport work age",
     "Workers by Transport Mode x Age x Sex", 9),
    ("citizen ever married females age group number children",
     "Married Females by Age x Children Born", 10),
    ("deaths age ethnic group gender",
     "Deaths by Age x Ethnicity x Gender", 11),
    ("hdb resale flat prices",
     "HDB Resale Flat Prices (transaction level)", 12),
]


def search_datasets(query, max_results=5):
    """Search data.gov.sg for datasets matching a query."""
    url = f"{API_BASE}"
    params = {"page": 1}

    try:
        resp = requests.get(url, params=params, timeout=30)
        resp.raise_for_status()
        data = resp.json()

        datasets = data.get("data", {}).get("datasets", [])
        # Simple keyword matching since API search might be limited
        query_words = query.lower().split()

        results = []
        for ds in datasets:
            name = (ds.get("name", "") or "").lower()
            desc = (ds.get("description", "") or "").lower()
            combined = name + " " + desc

            match_count = sum(1 for w in query_words if w in combined)
            if match_count >= len(query_words) * 0.5:
                results.append((match_count, ds))

        results.sort(key=lambda x: -x[0])
        return [r[1] for r in results[:max_results]]
    except Exception as e:
        print(f"  Search error: {e}")
        return []


def download_dataset(dataset_id, filename):
    """Download a dataset CSV from data.gov.sg."""
    url = f"{API_BASE}/{dataset_id}/poll-download"
    filepath = os.path.join(DATA_DIR, filename)

    if os.path.exists(filepath):
        print(f"  Already exists: {filename}")
        return True

    try:
        resp = requests.get(url, timeout=60)
        resp.raise_for_status()
        data = resp.json()

        download_url = data.get("data", {}).get("url")
        if download_url:
            csv_resp = requests.get(download_url, timeout=120)
            csv_resp.raise_for_status()
            with open(filepath, 'wb') as f:
                f.write(csv_resp.content)
            size_kb = len(csv_resp.content) / 1024
            print(f"  Downloaded: {filename} ({size_kb:.1f} KB)")
            return True
        else:
            print(f"  No download URL for {filename}")
            return False
    except Exception as e:
        print(f"  Download error for {filename}: {e}")
        return False


def list_available_datasets(page=1):
    """List datasets from data.gov.sg to explore what's available."""
    url = f"{API_BASE}"
    params = {"page": page}

    try:
        resp = requests.get(url, params=params, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        datasets = data.get("data", {}).get("datasets", [])
        total = data.get("data", {}).get("total", 0)
        return datasets, total
    except Exception as e:
        print(f"  List error: {e}")
        return [], 0


def main():
    print("=" * 60)
    print("Census Data Download Script")
    print("Target: 12 core cross-tabulation datasets for IPF")
    print("=" * 60)

    # First, let's explore what's available
    print("\nStep 1: Exploring data.gov.sg API...")
    datasets_page1, total = list_available_datasets(1)
    print(f"  Total datasets available: {total}")
    print(f"  First page has {len(datasets_page1)} datasets")

    if datasets_page1:
        print("\n  Sample datasets:")
        for ds in datasets_page1[:5]:
            print(f"    - {ds.get('name', 'N/A')} (ID: {ds.get('datasetId', 'N/A')})")

    # Save the full dataset listing for reference
    print("\nStep 2: Fetching full dataset catalog (this may take a while)...")
    all_datasets = []
    page = 1
    while True:
        datasets, total = list_available_datasets(page)
        if not datasets:
            break
        all_datasets.extend(datasets)
        page += 1
        if page > 50:  # Safety limit
            break
        time.sleep(0.5)

    print(f"  Fetched {len(all_datasets)} datasets across {page-1} pages")

    # Save catalog
    catalog_path = os.path.join(DATA_DIR, '_catalog.json')
    with open(catalog_path, 'w') as f:
        json.dump(all_datasets, f, indent=2, ensure_ascii=False)
    print(f"  Catalog saved to {catalog_path}")

    # Search for our target datasets
    print("\nStep 3: Searching for target datasets...")
    found = {}

    for query, description, priority in DATASETS_TO_FIND:
        print(f"\n  [{priority}/12] {description}")
        query_words = query.lower().split()

        matches = []
        for ds in all_datasets:
            name = (ds.get("name", "") or "").lower()
            match_count = sum(1 for w in query_words if w in name)
            if match_count >= len(query_words) * 0.4:
                matches.append((match_count, ds))

        matches.sort(key=lambda x: -x[0])

        if matches:
            best = matches[0][1]
            ds_id = best.get("datasetId", "")
            ds_name = best.get("name", "")
            print(f"    Found: {ds_name}")
            print(f"    ID: {ds_id}")
            found[priority] = {
                "id": ds_id,
                "name": ds_name,
                "description": description,
                "query": query
            }
        else:
            print(f"    NOT FOUND - will need manual search")

    # Save found datasets mapping
    mapping_path = os.path.join(DATA_DIR, '_dataset_mapping.json')
    with open(mapping_path, 'w') as f:
        json.dump(found, f, indent=2, ensure_ascii=False)
    print(f"\nDataset mapping saved to {mapping_path}")

    # Download found datasets
    print("\nStep 4: Downloading datasets...")
    success_count = 0
    for priority, info in sorted(found.items()):
        print(f"\n  [{priority}/12] {info['description']}")
        filename = f"{priority:02d}_{info['id'][:20]}.csv"
        if download_dataset(info['id'], filename):
            success_count += 1
        time.sleep(1)  # Rate limiting

    print(f"\n{'=' * 60}")
    print(f"Download complete: {success_count}/{len(found)} datasets")
    print(f"Found {len(found)}/12 target datasets")
    if len(found) < 12:
        print(f"Missing {12 - len(found)} datasets - may need manual download from:")
        print(f"  https://data.gov.sg")
        print(f"  https://www.singstat.gov.sg/find-data/search-by-theme")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    main()
