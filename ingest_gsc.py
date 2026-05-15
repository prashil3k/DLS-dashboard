"""
Ingests GSC XLSX exports from data/gsc-exports/ into SQLite.

Expected XLSX structure (standard GSC Performance export):
  Queries tab : Top queries | Clicks | Impressions | CTR | Position
  Pages tab   : Top pages   | Clicks | Impressions | CTR | Position
  Dates tab   : Date        | Clicks | Impressions | CTR | Position

Period is inferred from the Dates tab (min/max date).
Single-month files → stored as YYYY-MM in the monthly tables.
Multi-month files  → stored as YYYY-MM_to_YYYY-MM (used for aggregate views).
"""

import os
import re
import sqlite3

import pandas as pd

from cluster import assign_cluster, seed_cluster_config

DB_PATH      = os.path.join(os.path.dirname(__file__), "storylane_seo.db")
SCHEMA_PATH  = os.path.join(os.path.dirname(__file__), "schema.sql")
EXPORTS_DIR  = os.path.join(os.path.dirname(__file__), "data", "gsc-exports")


# ── DB init ─────────────────────────────────────────────────────────────────────

def init_db(conn):
    with open(SCHEMA_PATH) as f:
        conn.executescript(f.read())
    seed_cluster_config(conn.cursor())
    conn.commit()


# ── Helpers ───────────────────────────────────────────────────────────────────

def _parse_ctr(val) -> float:
    """Accept '2.01%', 0.0201, or 2.01 — always returns percentage float."""
    if isinstance(val, str):
        return float(val.replace("%", "").strip())
    if isinstance(val, float) and val <= 1.0:
        return round(val * 100, 4)
    return float(val)


def _find_tab(xl: pd.ExcelFile, candidates: list[str]) -> pd.DataFrame | None:
    for name in candidates:
        if name in xl.sheet_names:
            return xl.parse(name)
    return None


def _find_col(df: pd.DataFrame, *keywords) -> str | None:
    """Return first column whose name contains any of the given keywords (case-insensitive)."""
    for kw in keywords:
        for col in df.columns:
            if kw.lower() in str(col).lower():
                return col
    return None


def _infer_period(xl: pd.ExcelFile) -> tuple[str, bool]:
    """
    Returns (period_str, is_single_month).
    period_str is either 'YYYY-MM' or 'YYYY-MM_to_YYYY-MM'.
    Falls back to None if the Dates tab is absent or unreadable.
    """
    df = _find_tab(xl, ["Dates", "dates", "Date", "date"])
    if df is None:
        return None, False

    date_col = _find_col(df, "date")
    if date_col is None:
        return None, False

    dates = pd.to_datetime(df[date_col], errors="coerce").dropna()
    if dates.empty:
        return None, False

    lo, hi = dates.min(), dates.max()
    if lo.year == hi.year and lo.month == hi.month:
        return f"{lo.year}-{lo.month:02d}", True
    return f"{lo.strftime('%Y-%m')}_to_{hi.strftime('%Y-%m')}", False


def _period_from_filename(filename: str) -> tuple[str, bool] | tuple[None, bool]:
    """Try to parse YYYY-MM or YYYY_MM from filename as a fallback."""
    m = re.search(r"(\d{4})[-_](\d{2})", filename)
    if m:
        return f"{m.group(1)}-{m.group(2)}", True
    return None, False


# ── Loaders ───────────────────────────────────────────────────────────────────

def _load_queries(conn, df: pd.DataFrame, month: str) -> int:
    kw_col   = _find_col(df, "query", "queries", "top quer", "keyword")
    clk_col  = _find_col(df, "click")
    imp_col  = _find_col(df, "impression")
    ctr_col  = _find_col(df, "ctr")
    pos_col  = _find_col(df, "position")

    missing = [n for n, c in [("keyword", kw_col), ("clicks", clk_col),
                               ("impressions", imp_col), ("ctr", ctr_col),
                               ("position", pos_col)] if c is None]
    if missing:
        print(f"    Queries tab: cannot find columns {missing}. Skipping.")
        print(f"    Available columns: {list(df.columns)}")
        return 0

    rows = []
    for _, row in df.iterrows():
        keyword = str(row[kw_col]).strip()
        if not keyword or keyword.lower() == "nan":
            continue
        cluster = assign_cluster("", keyword)
        try:
            rows.append((
                keyword, month, None, cluster, None,
                int(float(row[clk_col])),
                int(float(row[imp_col])),
                _parse_ctr(row[ctr_col]),
                float(row[pos_col]),
            ))
        except Exception:
            continue

    conn.executemany(
        """INSERT OR REPLACE INTO keywords_monthly
           (keyword, month, top_url, cluster, urls_count, clicks, impressions, ctr, position)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        rows,
    )
    conn.commit()
    return len(rows)


def _load_pages(conn, df: pd.DataFrame, month: str) -> int:
    pg_col   = _find_col(df, "page", "top page", "url", "landing")
    clk_col  = _find_col(df, "click")
    imp_col  = _find_col(df, "impression")
    ctr_col  = _find_col(df, "ctr")
    pos_col  = _find_col(df, "position")

    missing = [n for n, c in [("page", pg_col), ("clicks", clk_col),
                               ("impressions", imp_col), ("ctr", ctr_col),
                               ("position", pos_col)] if c is None]
    if missing:
        print(f"    Pages tab: cannot find columns {missing}. Skipping.")
        print(f"    Available columns: {list(df.columns)}")
        return 0

    rows = []
    for _, row in df.iterrows():
        page_url = str(row[pg_col]).strip()
        if not page_url or page_url.lower() == "nan":
            continue
        cluster = assign_cluster(page_url, "")
        try:
            rows.append((
                page_url, month, cluster,
                None, None,
                int(float(row[clk_col])),
                int(float(row[imp_col])),
                _parse_ctr(row[ctr_col]),
                float(row[pos_col]),
                None,
            ))
        except Exception:
            continue

    conn.executemany(
        """INSERT OR REPLACE INTO pages_monthly
           (page, month, cluster, keywords_count, top_keyword, clicks, impressions, ctr, position, traffic_value)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        rows,
    )
    conn.commit()
    return len(rows)


# ── Per-file processor ────────────────────────────────────────────────────────────

def process_file(conn, filepath: str):
    filename = os.path.basename(filepath)
    print(f"\n{'─'*60}")
    print(f"File: {filename}")

    xl = pd.ExcelFile(filepath)
    print(f"Tabs: {xl.sheet_names}")

    month, is_single = _infer_period(xl)
    if month is None:
        month, is_single = _period_from_filename(filename)
    if month is None:
        print("Could not determine period from Dates tab or filename. Skipping.")
        return

    kind = "single month" if is_single else "range"
    print(f"Period: {month} ({kind})")

    queries_df = _find_tab(xl, ["Queries", "queries", "Top queries", "QUERIES"])
    if queries_df is not None:
        n = _load_queries(conn, queries_df, month)
        print(f"  Queries: {n} rows loaded")
    else:
        print("  Queries tab: not found")

    pages_df = _find_tab(xl, ["Pages", "pages", "Top pages", "PAGES"])
    if pages_df is not None:
        n = _load_pages(conn, pages_df, month)
        print(f"  Pages: {n} rows loaded")
    else:
        print("  Pages tab: not found")


# ── Main ─────────────────────────────────────────────────────────────────────────────

def main():
    if not os.path.isdir(EXPORTS_DIR):
        print(f"Exports directory not found: {EXPORTS_DIR}")
        return

    files = sorted(f for f in os.listdir(EXPORTS_DIR) if f.lower().endswith(".xlsx"))
    if not files:
        print(f"No .xlsx files found in {EXPORTS_DIR}")
        return

    print(f"Found {len(files)} file(s) to process.")

    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA journal_mode=WAL")
    init_db(conn)

    for filename in files:
        process_file(conn, os.path.join(EXPORTS_DIR, filename))

    pages_count = conn.execute("SELECT COUNT(*) FROM pages_monthly").fetchone()[0]
    kw_count    = conn.execute("SELECT COUNT(*) FROM keywords_monthly").fetchone()[0]
    months      = [r[0] for r in conn.execute(
        "SELECT DISTINCT month FROM pages_monthly ORDER BY month"
    ).fetchall()]

    print(f"\n{'='*60}")
    print(f"Done.")
    print(f"  {pages_count:,} page rows  |  {kw_count:,} keyword rows")
    print(f"  Periods loaded: {months}")
    conn.close()


if __name__ == "__main__":
    main()
