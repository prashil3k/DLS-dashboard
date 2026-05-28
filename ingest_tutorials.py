"""
Ingest Webflow CMS tutorial export into tutorial_metadata table.

Reads the CSV from data/tutorials/tutorials-export.csv.
Extracts: slug, title, category, created date + month.
Maps category → dashboard cluster where possible, falls back to slug matching.
Skips the Content column entirely — not needed for metadata.

Safe to re-run (INSERT OR REPLACE on slug primary key).
"""

import csv
import os
import sqlite3
from datetime import datetime

from cluster import assign_cluster

DB_PATH = os.path.join(os.path.dirname(__file__), "storylane_seo.db")
SCHEMA_PATH = os.path.join(os.path.dirname(__file__), "schema.sql")
CSV_PATH = os.path.join(os.path.dirname(__file__), "data", "tutorials", "tutorials-export.csv")

BASE_URL = "https://www.storylane.io/tutorials/"

# Map CMS category names → dashboard cluster names
# Only needed where they differ (e.g. "ms-excel" → "excel")
CATEGORY_TO_CLUSTER = {
    "ms-excel": "excel",
    "ms-powerpoint": None,       # no dashboard cluster yet
    "ms-project": None,
    "ms-teams": "teams",
    "adobe-indesign": "adobe",
    "adobe-illustrator": "adobe",
    "adobe-premiere": "adobe",
    "adobe-photoshop": "adobe",
    "adobe-after-effects": "adobe",
    "adobe-lightroom": "adobe",
    "google-slides": None,       # no dashboard cluster yet
    "google-docs": None,
    "google-sheets": None,
    "google-calendar": None,
    "google-drive": None,
    "power-bi": None,
    "ms-access": "ms-access",
    "cisco-webex": None,
    "microsoft-teams": "teams",
    "openai": "chatgpt",
    "chat-gpt": "chatgpt",
    # Direct matches (category == cluster name) don't need mapping
}


def _parse_created_date(raw: str) -> tuple[str, str] | None:
    """Parse 'Thu Jan 29 2026 10:56:56 GMT+0000 (Coordinated Universal Time)' → (date, month)."""
    try:
        dt_str = raw.split("(")[0].strip()
        dt = datetime.strptime(dt_str, "%a %b %d %Y %H:%M:%S GMT%z")
        return dt.strftime("%Y-%m-%d"), dt.strftime("%Y-%m")
    except (ValueError, IndexError):
        return None


def _resolve_cluster(category: str, slug: str) -> str | None:
    """Category → cluster, falling back to slug-based assignment."""
    cat = (category or "").strip().lower()

    # Check explicit mapping first
    if cat in CATEGORY_TO_CLUSTER:
        return CATEGORY_TO_CLUSTER[cat]

    # Try category as cluster name directly (works for canva, notion, jira, etc.)
    from cluster import CLUSTER_RULES
    if cat in CLUSTER_RULES:
        return cat

    # Fall back to slug matching
    url = BASE_URL + slug
    return assign_cluster(url, "")


def main():
    if not os.path.exists(CSV_PATH):
        print(f"Tutorial export not found: {CSV_PATH}")
        return

    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA journal_mode=WAL")

    # Ensure table exists
    with open(SCHEMA_PATH) as f:
        conn.executescript(f.read())

    rows = []
    skipped = 0

    with open(CSV_PATH, "r") as f:
        reader = csv.DictReader(f)
        for row in reader:
            parsed = _parse_created_date(row.get("Created On", ""))
            if parsed is None:
                skipped += 1
                continue

            created_date, created_month = parsed
            slug = (row.get("Slug") or "").strip()
            title = (row.get("Name") or "").strip()
            category = (row.get("Category") or "").strip()
            is_draft = 1 if row.get("Draft", "").lower() == "true" else 0

            if not slug or not title:
                skipped += 1
                continue

            cluster = _resolve_cluster(category, slug)
            url = BASE_URL + slug

            rows.append((
                slug, url, title, category, cluster,
                created_date, created_month, is_draft
            ))

    conn.executemany(
        """INSERT OR REPLACE INTO tutorial_metadata
           (slug, url, title, category, cluster, created_date, created_month, is_draft)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
        rows,
    )
    conn.commit()

    # Stats
    total = len(rows)
    clustered = sum(1 for r in rows if r[4] is not None)
    categories = len(set(r[3] for r in rows if r[3]))

    print(f"Loaded {total:,} tutorials ({skipped} skipped)")
    print(f"  Clustered: {clustered:,} ({clustered*100//total}%)")
    print(f"  Categories: {categories}")
    print(f"  Date range: {rows[-1][5] if rows else '?'} to {rows[0][5] if rows else '?'}")

    # Show cluster distribution
    from collections import Counter
    cluster_counts = Counter(r[4] for r in rows if r[4])
    print(f"\nTop 15 clusters by tutorial count:")
    for c, n in cluster_counts.most_common(15):
        print(f"  {c}: {n}")

    unmapped = Counter(r[3] for r in rows if r[4] is None)
    print(f"\nTop 15 unmapped categories ({sum(unmapped.values())} tutorials):")
    for c, n in unmapped.most_common(15):
        print(f"  {c}: {n}")

    conn.close()


if __name__ == "__main__":
    main()
