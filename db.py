"""SQLite query layer for the DLS dashboard."""

import os
import sqlite3

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
    rows = conn.execute(
        "SELECT DISTINCT month FROM pages_monthly WHERE month NOT LIKE '%_to_%' ORDER BY month"
    ).fetchall()
    conn.close()
    return [r[0] for r in rows]


def estimated_months():
    conn = get_connection()
    rows = conn.execute(
        "SELECT DISTINCT month FROM pages_monthly WHERE is_estimated = 1 ORDER BY month"
    ).fetchall()
    conn.close()
    return set(r[0] for r in rows)


def available_clusters():
    conn = get_connection()
    rows = conn.execute(
        "SELECT DISTINCT cluster FROM pages_monthly "
        "WHERE cluster IS NOT NULL AND month NOT LIKE '%_to_%' "
        "ORDER BY cluster"
    ).fetchall()
    conn.close()
    return [r[0] for r in rows]


def cluster_summary(periods: dict | None = None) -> pd.DataFrame:
    if periods is None:
        periods = _default_periods()

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
                      COUNT(DISTINCT page) as pages,
                      MAX(is_estimated) as is_estimated
               FROM pages_monthly
               WHERE cluster IS NOT NULL
                 AND month >= ? AND month <= ?
                 AND month NOT LIKE '%_to_%'
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


def _default_periods():
    months = available_months()
    if not months:
        return {}
    return {
        "Peak (Feb–Apr '25)": ("2025-02", "2025-04"),
        months[-3] if len(months) >= 3 else months[0]: (
            months[-3] if len(months) >= 3 else months[0],
            months[-3] if len(months) >= 3 else months[0],
        ),
        months[-2] if len(months) >= 2 else months[0]: (
            months[-2] if len(months) >= 2 else months[0],
            months[-2] if len(months) >= 2 else months[0],
        ),
        f"{months[-1]} (current)": (months[-1], months[-1]),
    }


def cluster_monthly_trends(cluster: str | None = None) -> pd.DataFrame:
    conn = get_connection()
    where = "cluster = ?" if cluster else "cluster IS NOT NULL"
    params = (cluster,) if cluster else ()
    df = pd.read_sql_query(
        f"""SELECT month,
                  SUM(clicks) as clicks,
                  SUM(impressions) as impressions,
                  CASE WHEN SUM(impressions) > 0
                       THEN ROUND(SUM(clicks) * 100.0 / SUM(impressions), 2)
                       ELSE 0 END as ctr,
                  ROUND(AVG(position), 1) as avg_position,
                  COUNT(DISTINCT page) as pages,
                  MAX(is_estimated) as is_estimated
           FROM pages_monthly
           WHERE {where} AND month NOT LIKE '%_to_%'
           GROUP BY month
           ORDER BY month""",
        conn,
        params=params,
    )
    conn.close()
    return df


def query_position_counts(cluster: str | None = None) -> pd.DataFrame:
    conn = get_connection()
    where = "cluster = ?" if cluster else "cluster IS NOT NULL"
    params = (cluster,) if cluster else ()
    df = pd.read_sql_query(
        f"""SELECT month,
               COUNT(DISTINCT CASE WHEN position <= 1.5 THEN keyword END) as top_1,
               COUNT(DISTINCT CASE WHEN position <= 3.0 THEN keyword END) as top_3,
               COUNT(DISTINCT CASE WHEN position <= 5.0 THEN keyword END) as top_5,
               COUNT(DISTINCT CASE WHEN position <= 10.0 THEN keyword END) as top_10,
               COUNT(DISTINCT keyword) as total,
               MAX(is_estimated) as is_estimated
           FROM keywords_monthly
           WHERE {where} AND month NOT LIKE '%_to_%'
           GROUP BY month
           ORDER BY month""",
        conn,
        params=params,
    )
    conn.close()
    return df


def page_position_counts(cluster: str | None = None) -> pd.DataFrame:
    conn = get_connection()
    where = "cluster = ?" if cluster else "cluster IS NOT NULL"
    params = (cluster,) if cluster else ()
    df = pd.read_sql_query(
        f"""SELECT month,
               COUNT(DISTINCT CASE WHEN position <= 1.5 THEN page END) as top_1,
               COUNT(DISTINCT CASE WHEN position <= 3.0 THEN page END) as top_3,
               COUNT(DISTINCT CASE WHEN position <= 5.0 THEN page END) as top_5,
               COUNT(DISTINCT CASE WHEN position <= 10.0 THEN page END) as top_10,
               COUNT(DISTINCT page) as total,
               MAX(is_estimated) as is_estimated
           FROM pages_monthly
           WHERE {where} AND month NOT LIKE '%_to_%'
           GROUP BY month
           ORDER BY month""",
        conn,
        params=params,
    )
    conn.close()
    return df


def all_clusters_position_summary(bucket: str = "top_3") -> pd.DataFrame:
    pos_threshold = {"top_1": 1.5, "top_3": 3.0, "top_5": 5.0, "top_10": 10.0}[bucket]
    conn = get_connection()
    df = pd.read_sql_query(
        """SELECT month, cluster,
               COUNT(DISTINCT CASE WHEN position <= ? THEN keyword END) as in_bucket,
               COUNT(DISTINCT keyword) as total,
               SUM(clicks) as clicks,
               SUM(impressions) as impressions,
               CASE WHEN SUM(impressions) > 0
                    THEN ROUND(SUM(clicks) * 100.0 / SUM(impressions), 2)
                    ELSE 0 END as ctr,
               ROUND(AVG(position), 1) as avg_position,
               MAX(is_estimated) as is_estimated
           FROM keywords_monthly
           WHERE cluster IS NOT NULL AND month NOT LIKE '%_to_%'
           GROUP BY month, cluster
           ORDER BY month, cluster""",
        conn,
        params=(pos_threshold,),
    )
    conn.close()
    return df


def scorecard_data() -> pd.DataFrame:
    months = available_months()
    if not months:
        return pd.DataFrame()

    periods = _default_periods()
    return cluster_summary(periods)


def keywords_for_cluster(cluster: str, month: str, limit: int = 300) -> pd.DataFrame:
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
