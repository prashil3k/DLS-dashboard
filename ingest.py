"""Reads JSON files from data/pages/ and data/keywords/, assigns clusters, loads into SQLite."""

import json
import os
import sqlite3
import sys

from cluster import assign_cluster, seed_cluster_config

DB_PATH = os.path.join(os.path.dirname(__file__), "storylane_seo.db")
SCHEMA_PATH = os.path.join(os.path.dirname(__file__), "schema.sql")
DATA_DIR = os.path.join(os.path.dirname(__file__), "data")


def init_db(conn):
    with open(SCHEMA_PATH) as f:
        conn.executescript(f.read())
    seed_cluster_config(conn.cursor())
    conn.commit()


def ingest_pages(conn):
    pages_dir = os.path.join(DATA_DIR, "pages")
    if not os.path.isdir(pages_dir):
        print("No data/pages/ directory found.")
        return 0

    total = 0
    for filename in sorted(os.listdir(pages_dir)):
        if not filename.endswith(".json"):
            continue
        month = filename.replace("pages_", "").replace(".json", "")
        filepath = os.path.join(pages_dir, filename)

        with open(filepath) as f:
            data = json.load(f)

        pages = data.get("pages", data) if isinstance(data, dict) else data
        rows = []
        for p in pages:
            page_url = p.get("page", "")
            cluster = assign_cluster(page_url, p.get("top_keyword", ""))
            rows.append((
                page_url,
                month,
                cluster,
                p.get("keywords_count"),
                p.get("top_keyword"),
                p.get("clicks", 0),
                p.get("impressions", 0),
                p.get("ctr", 0),
                p.get("position", 0),
                p.get("traffic_value"),
            ))

        conn.executemany(
            """INSERT OR REPLACE INTO pages_monthly
               (page, month, cluster, keywords_count, top_keyword, clicks, impressions, ctr, position, traffic_value)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            rows,
        )
        conn.commit()
        total += len(rows)
        print(f"  pages {month}: {len(rows)} rows")

    return total


def ingest_keywords(conn):
    kw_dir = os.path.join(DATA_DIR, "keywords")
    if not os.path.isdir(kw_dir):
        print("No data/keywords/ directory found.")
        return 0

    total = 0
    for filename in sorted(os.listdir(kw_dir)):
        if not filename.endswith(".json"):
            continue
        month = filename.replace("keywords_", "").replace(".json", "")
        filepath = os.path.join(kw_dir, filename)

        with open(filepath) as f:
            data = json.load(f)

        keywords = data.get("keywords", data) if isinstance(data, dict) else data
        rows = []
        for kw in keywords:
            top_url = kw.get("top_url", "")
            keyword = kw.get("keyword", "")
            cluster = assign_cluster(top_url, keyword)
            rows.append((
                keyword,
                month,
                top_url,
                cluster,
                kw.get("urls_count"),
                kw.get("clicks", 0),
                kw.get("impressions", 0),
                kw.get("ctr", 0),
                kw.get("position", 0),
            ))

        conn.executemany(
            """INSERT OR REPLACE INTO keywords_monthly
               (keyword, month, top_url, cluster, urls_count, clicks, impressions, ctr, position)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            rows,
        )
        conn.commit()
        total += len(rows)
        print(f"  keywords {month}: {len(rows)} rows")

    return total


def ingest_volumes(conn):
    vol_path = os.path.join(DATA_DIR, "keyword_volumes.json")
    if not os.path.exists(vol_path):
        print("No data/keyword_volumes.json found.")
        return 0

    with open(vol_path) as f:
        data = json.load(f)

    rows = [(kw["keyword"], kw.get("volume"), kw.get("cpc"), kw.get("difficulty")) for kw in data]
    conn.executemany(
        "INSERT OR REPLACE INTO keyword_volumes (keyword, volume, cpc, difficulty) VALUES (?, ?, ?, ?)",
        rows,
    )
    conn.commit()
    print(f"  keyword_volumes: {len(rows)} rows")
    return len(rows)


def ingest_competitors(conn):
    path = os.path.join(DATA_DIR, "organic_competitors.json")
    if not os.path.exists(path):
        print("No data/organic_competitors.json found.")
        return 0

    with open(path) as f:
        data = json.load(f)

    rows = [
        (c["competitor_domain"], c.get("keywords_common"), c.get("keywords_target"),
         c.get("keywords_competitor"), c.get("traffic"), c.get("domain_rating"), c.get("share"))
        for c in data
    ]
    conn.executemany(
        """INSERT OR REPLACE INTO organic_competitors
           (competitor_domain, keywords_common, keywords_target, keywords_competitor, traffic, domain_rating, share)
           VALUES (?, ?, ?, ?, ?, ?, ?)""",
        rows,
    )
    conn.commit()
    print(f"  organic_competitors: {len(rows)} rows")
    return len(rows)


def ingest_serp_snapshots(conn):
    path = os.path.join(DATA_DIR, "serp_snapshots.json")
    if not os.path.exists(path):
        print("No data/serp_snapshots.json found.")
        return 0

    with open(path) as f:
        data = json.load(f)

    from urllib.parse import urlparse
    total = 0
    for keyword, positions in data.items():
        for p in positions:
            url = p.get("url")
            if not url:
                continue
            domain = urlparse(url).netloc.replace("www.", "")
            conn.execute(
                """INSERT OR REPLACE INTO serp_snapshots
                   (keyword, position, url, domain, domain_rating, traffic)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (keyword, p["position"], url, domain, p.get("domain_rating"), p.get("traffic")),
            )
            total += 1
    conn.commit()
    print(f"  serp_snapshots: {total} rows")
    return total


def main():
    print(f"Database: {DB_PATH}")
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA journal_mode=WAL")

    init_db(conn)

    print("\nIngesting pages...")
    page_count = ingest_pages(conn)

    print("\nIngesting keywords...")
    kw_count = ingest_keywords(conn)

    print("\nIngesting keyword volumes...")
    vol_count = ingest_volumes(conn)

    print("\nIngesting competitors...")
    comp_count = ingest_competitors(conn)

    print("\nIngesting SERP snapshots...")
    serp_count = ingest_serp_snapshots(conn)

    print(f"\nDone. {page_count} pages, {kw_count} keywords, {vol_count} volumes, "
          f"{comp_count} competitors, {serp_count} SERP rows loaded.")
    conn.close()


if __name__ == "__main__":
    main()
