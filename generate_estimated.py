"""
Generate estimated data for gap months (May 2025 – Jan 2026).

Interpolates between the last real month before the gap (Apr 2025)
and the first real month after (Feb 2026) for each cluster.
All generated rows are tagged with is_estimated=1.

Safe to re-run: deletes all estimated rows first, then regenerates.
"""

import math
import random
import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "storylane_seo.db")

GAP_MONTHS = [
    "2025-05", "2025-06", "2025-07", "2025-08", "2025-09",
    "2025-10", "2025-11", "2025-12", "2026-01",
]

BEFORE_MONTH = "2025-04"
AFTER_MONTH = "2026-02"


def _lerp(a: float, b: float, t: float, noise: float = 0.05) -> float:
    base = a + (b - a) * t
    jitter = base * random.uniform(-noise, noise)
    return base + jitter


def _lerp_int(a: int, b: int, t: float, noise: float = 0.05) -> int:
    return max(0, round(_lerp(float(a), float(b), t, noise)))


def generate_pages(conn):
    conn.execute("DELETE FROM pages_monthly WHERE is_estimated = 1")

    before = conn.execute(
        "SELECT page, cluster, clicks, impressions, ctr, position "
        "FROM pages_monthly WHERE month = ? AND cluster IS NOT NULL",
        (BEFORE_MONTH,),
    ).fetchall()

    after_map = {}
    for row in conn.execute(
        "SELECT page, cluster, clicks, impressions, ctr, position "
        "FROM pages_monthly WHERE month = ? AND cluster IS NOT NULL",
        (AFTER_MONTH,),
    ).fetchall():
        after_map[row[0]] = row

    total = 0
    for i, month in enumerate(GAP_MONTHS):
        t = (i + 1) / (len(GAP_MONTHS) + 1)
        rows = []
        for page, cluster, clicks_b, imp_b, ctr_b, pos_b in before:
            if page in after_map:
                _, _, clicks_a, imp_a, ctr_a, pos_a = after_map[page]
            else:
                clicks_a = max(0, int(clicks_b * 0.7))
                imp_a = max(0, int(imp_b * 0.85))
                ctr_a = max(0, ctr_b * 0.8)
                pos_a = pos_b + 2.0

            rows.append((
                page, month, cluster,
                None, None,
                _lerp_int(clicks_b, clicks_a, t),
                _lerp_int(imp_b, imp_a, t),
                round(max(0, _lerp(ctr_b, ctr_a, t, 0.03)), 2),
                round(max(0.1, _lerp(pos_b, pos_a, t, 0.03)), 1),
                None, 1,
            ))

        conn.executemany(
            """INSERT OR REPLACE INTO pages_monthly
               (page, month, cluster, keywords_count, top_keyword,
                clicks, impressions, ctr, position, traffic_value, is_estimated)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            rows,
        )
        total += len(rows)

    conn.commit()
    return total


def generate_keywords(conn):
    conn.execute("DELETE FROM keywords_monthly WHERE is_estimated = 1")

    before = conn.execute(
        "SELECT keyword, top_url, cluster, clicks, impressions, ctr, position "
        "FROM keywords_monthly WHERE month = ? AND cluster IS NOT NULL",
        (BEFORE_MONTH,),
    ).fetchall()

    after_map = {}
    for row in conn.execute(
        "SELECT keyword, top_url, cluster, clicks, impressions, ctr, position "
        "FROM keywords_monthly WHERE month = ? AND cluster IS NOT NULL",
        (AFTER_MONTH,),
    ).fetchall():
        after_map[row[0]] = row

    total = 0
    for i, month in enumerate(GAP_MONTHS):
        t = (i + 1) / (len(GAP_MONTHS) + 1)
        rows = []
        for kw, top_url, cluster, clicks_b, imp_b, ctr_b, pos_b in before:
            if kw in after_map:
                _, url_a, _, clicks_a, imp_a, ctr_a, pos_a = after_map[kw]
            else:
                clicks_a = max(0, int(clicks_b * 0.7))
                imp_a = max(0, int(imp_b * 0.85))
                ctr_a = max(0, ctr_b * 0.8)
                pos_a = pos_b + 2.0
                url_a = top_url

            rows.append((
                kw, month, top_url, cluster, None,
                _lerp_int(clicks_b, clicks_a, t),
                _lerp_int(imp_b, imp_a, t),
                round(max(0, _lerp(ctr_b, ctr_a, t, 0.03)), 2),
                round(max(0.1, _lerp(pos_b, pos_a, t, 0.03)), 1),
                1,
            ))

        conn.executemany(
            """INSERT OR REPLACE INTO keywords_monthly
               (keyword, month, top_url, cluster, urls_count,
                clicks, impressions, ctr, position, is_estimated)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            rows,
        )
        total += len(rows)

    conn.commit()
    return total


def main():
    random.seed(42)
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA journal_mode=WAL")

    print("Generating estimated page data for gap months...")
    pages = generate_pages(conn)
    print(f"  {pages} estimated page rows created")

    print("Generating estimated keyword data for gap months...")
    keywords = generate_keywords(conn)
    print(f"  {keywords} estimated keyword rows created")

    months = [r[0] for r in conn.execute(
        "SELECT DISTINCT month FROM pages_monthly WHERE month NOT LIKE '%_to_%' ORDER BY month"
    ).fetchall()]
    est_months = [r[0] for r in conn.execute(
        "SELECT DISTINCT month FROM pages_monthly WHERE is_estimated = 1 ORDER BY month"
    ).fetchall()]
    print(f"\nAll months in DB: {months}")
    print(f"Estimated months: {est_months}")

    conn.close()


if __name__ == "__main__":
    main()
