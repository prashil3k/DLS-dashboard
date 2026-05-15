"""SQLite query layer for the DLS dashboard."""

import os
import sqlite3
from datetime import date, timedelta

import pandas as pd

DB_PATH = os.path.join(os.path.dirname(__file__), "storylane_seo.db")


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.row_factory = sqlite3.Row
    return conn


def has_data():
    if not os.path.exists(DB_PATH):
        return False
    conn = get_connection()
    row = conn.execute("SELECT COUNT(*) FROM pages_monthly").fetchone()
    conn.close()
    return row[0] > 0


def available_months():
    conn = get_connection()
    rows = conn.execute("SELECT DISTINCT month FROM pages_monthly ORDER BY month").fetchall()
    conn.close()
    return [r[0] for r in rows]


def available_clusters():
    conn = get_connection()
    rows = conn.execute(
        "SELECT DISTINCT cluster FROM pages_monthly WHERE cluster IS NOT NULL ORDER BY cluster"
    ).fetchall()
    conn.close()
    return [r[0] for r in rows]


def default_periods():
    """Return the 4 comparison periods based on available data."""
    months = available_months()
    if not months:
        return {}

    return {
        "Post-peak Q1'25": ("2025-01", "2025-04"),
        "Q1'26": ("2026-01", "2026-03"),
        "3 months ago": _rolling_3mo_ago(months[-1]),
        "Current": (months[-1], months[-1]),
    }


def _rolling_3mo_ago(latest_month: str) -> tuple[str, str]:
    year, mo = int(latest_month[:4]), int(latest_month[5:])
    end_mo = mo - 2
    end_yr = year
    if end_mo <= 0:
        end_mo += 12
        end_yr -= 1
    start_mo = end_mo - 2
    start_yr = end_yr
    if start_mo <= 0:
        start_mo += 12
        start_yr -= 1
    return (f"{start_yr}-{start_mo:02d}", f"{end_yr}-{end_mo:02d}")


def cluster_summary(periods: dict | None = None) -> pd.DataFrame:
    if periods is None:
        periods = default_periods()

    conn = get_connection()
    frames = []
    for label, (start, end) in periods.items():
        df = pd.read_sql_query(
            """SELECT cluster,
                      SUM(clicks) as clicks,
                      SUM(impressions) as impressions,
                      CASE WHEN SUM(impressions) > 0
                           THEN ROUND(SUM(clicks) * 100.0 / SUM(impressions), 2)
                           ELSE 0 END as ctr,
                      ROUND(AVG(position), 1) as avg_position,
                      COUNT(DISTINCT page) as pages
               FROM pages_monthly
               WHERE cluster IS NOT NULL
                 AND month >= ? AND month <= ?
               GROUP BY cluster
               ORDER BY clicks DESC""",
            conn,
            params=(start, end),
        )
        df["period"] = label
        frames.append(df)

    conn.close()
    if not frames:
        return pd.DataFrame()
    return pd.concat(frames, ignore_index=True)


def cluster_monthly_trends(cluster: str | None = None) -> pd.DataFrame:
    conn = get_connection()
    if cluster:
        df = pd.read_sql_query(
            """SELECT month,
                      SUM(clicks) as clicks,
                      SUM(impressions) as impressions,
                      CASE WHEN SUM(impressions) > 0
                           THEN ROUND(SUM(clicks) * 100.0 / SUM(impressions), 2)
                           ELSE 0 END as ctr,
                      ROUND(AVG(position), 1) as avg_position,
                      COUNT(DISTINCT page) as pages
               FROM pages_monthly
               WHERE cluster = ?
               GROUP BY month
               ORDER BY month""",
            conn,
            params=(cluster,),
        )
    else:
        df = pd.read_sql_query(
            """SELECT month,
                      SUM(clicks) as clicks,
                      SUM(impressions) as impressions,
                      CASE WHEN SUM(impressions) > 0
                           THEN ROUND(SUM(clicks) * 100.0 / SUM(impressions), 2)
                           ELSE 0 END as ctr,
                      ROUND(AVG(position), 1) as avg_position,
                      COUNT(DISTINCT page) as pages
               FROM pages_monthly
               WHERE cluster IS NOT NULL
               GROUP BY month
               ORDER BY month""",
            conn,
        )
    conn.close()
    return df


def position_distribution(cluster: str, month: str) -> dict:
    conn = get_connection()
    row = conn.execute(
        """SELECT
               COUNT(DISTINCT CASE WHEN position <= 1.5 THEN keyword END) as top_1,
               COUNT(DISTINCT CASE WHEN position <= 3.0 THEN keyword END) as top_3,
               COUNT(DISTINCT CASE WHEN position <= 5.0 THEN keyword END) as top_5,
               COUNT(DISTINCT CASE WHEN position <= 10.0 THEN keyword END) as top_10,
               COUNT(DISTINCT keyword) as total
           FROM keywords_monthly
           WHERE cluster = ? AND month = ?""",
        (cluster, month),
    ).fetchone()
    conn.close()
    return dict(row) if row else {}


def position_distribution_over_time(cluster: str) -> pd.DataFrame:
    conn = get_connection()
    df = pd.read_sql_query(
        """SELECT month,
               COUNT(DISTINCT CASE WHEN position <= 1.5 THEN keyword END) as top_1,
               COUNT(DISTINCT CASE WHEN position <= 3.0 THEN keyword END) as top_3,
               COUNT(DISTINCT CASE WHEN position <= 5.0 THEN keyword END) as top_5,
               COUNT(DISTINCT CASE WHEN position <= 10.0 THEN keyword END) as top_10,
               COUNT(DISTINCT keyword) as total
           FROM keywords_monthly
           WHERE cluster = ?
           GROUP BY month
           ORDER BY month""",
        conn,
        params=(cluster,),
    )
    conn.close()
    return df


def keyword_movers(cluster: str, month_a: str, month_b: str, limit: int = 50) -> pd.DataFrame:
    conn = get_connection()
    df = pd.read_sql_query(
        """SELECT
               a.keyword,
               a.position as pos_before,
               b.position as pos_after,
               ROUND(b.position - a.position, 1) as pos_delta,
               b.impressions,
               b.clicks,
               b.ctr,
               ROUND(b.impressions * ABS(b.position - a.position), 0) as impact_score
           FROM keywords_monthly a
           JOIN keywords_monthly b ON a.keyword = b.keyword
           WHERE a.cluster = ? AND a.month = ? AND b.month = ?
           ORDER BY impact_score DESC
           LIMIT ?""",
        conn,
        params=(cluster, month_a, month_b, limit),
    )
    conn.close()
    return df


def keywords_for_cluster(cluster: str, month: str, limit: int = 200) -> pd.DataFrame:
    conn = get_connection()
    df = pd.read_sql_query(
        """SELECT keyword, top_url, clicks, impressions, ctr, position
           FROM keywords_monthly
           WHERE cluster = ? AND month = ?
           ORDER BY clicks DESC
           LIMIT ?""",
        conn,
        params=(cluster, month, limit),
    )
    conn.close()
    return df
