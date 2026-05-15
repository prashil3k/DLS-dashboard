# DLS Dashboard — Session Handoff Context

This file was created to hand off context between Claude sessions. The project
began in a local Claude instance (with Ahrefs MCP connected) and continued in
a Claude Code web session (without Ahrefs). Git is the shared source of truth.

---

## Where This Project Came From

The project started in a **local Claude session** that had the Ahrefs MCP
connected. In that session:
- The Ahrefs GSC tools (0 units cost, free/unlimited) were confirmed working
- Project: Storylane (ID 9000301), GSC connected
- A backfill of 17 months of page + keyword data was started via MCP
- 6 months of page data were pulled but the session hit its API rate limit
  **before any JSON files were saved to disk**
- Infrastructure files (`schema.sql`, `ingest.py`, `cluster.py`, `db.py`,
  `save_json.py`, `app.py`) were created in that session
- Those files were pushed to the user's local folder:
  `/Users/prashil3k/Documents/Claude Code/DLS performance dashboard`

---

## How Files Got Into This Repo

The user manually pushed the local folder to GitHub via Terminal:
```
cd "/Users/prashil3k/Documents/Claude Code/DLS performance dashboard"
git init
git remote add origin https://github.com/prashil3k/DLS-dashboard.git
git add .
git commit -m "Initial commit: DLS performance dashboard"
git push -u origin main
```

This web session then pulled from GitHub to continue the work.

---

## What This Session Built

### 1. Rewrote `app.py` — real data, not sample data
- The original `app.py` used hardcoded `sample_data.py` (fake numbers)
- Rewrote it to read entirely from SQLite via `db.py`
- Added a graceful empty-state warning when no DB exists yet
- All 4 tabs now use real queries:
  - **Tab 1 Cluster Overview**: period selector, sortable table, bar + scatter charts
  - **Tab 2 Position Health**: per-cluster position bucket tracker over time + retention table
  - **Tab 3 AIO Signature**: signal grid for ALL clusters (AIO / Displaced / Declining / Healthy) + per-cluster drill-down with 3-panel trend chart + auto-diagnosis
  - **Tab 4 Query Deep Dive**: keyword scatter + table with auto-assigned signals

### 2. Built `ingest_gsc.py` — GSC XLSX ingestion pipeline
The Ahrefs backfill wasn't available, so a manual GSC export pipeline was built.
- Reads `.xlsx` files from `data/gsc-exports/`
- Parses period from **month names in filename** (e.g. "March 2026", "feb 2025",
  "Jan 2025 - May 2026") — GSC exports in this format have no Dates tab
- CTR is exported as decimal (0.0722 = 7.22%) — parsed correctly
- Tabs used: `Queries` (Top queries | Clicks | Impressions | CTR | Position)
  and `Pages` (Top pages | Clicks | Impressions | CTR | Position)
- Single-month files → stored as `YYYY-MM`
- Multi-month range files → stored as `YYYY-MM_to_YYYY-MM` (aggregate only,
  excluded from monthly trend selectors)
- Run with: `python ingest_gsc.py`

### 3. Expanded `cluster.py` — 17 → 37 clusters
Added: Figma, Zoom, Teams (fixed slug from "teams-dark" to "teams"),
Google Forms, Mailchimp, WordPress, Webflow, Dropbox, Upwork, Perplexity,
Gemini, Replit, MS Access, Asana, Google Analytics, Semrush.
Result: **89.5% of clicks classified** on the loaded data.

### 4. Fixed `db.py`
- `available_months()` now excludes range period keys (those containing `_to_`)
  so they don't pollute monthly trend dropdowns

### 5. Created `data/gsc-exports/` folder
Drop `.xlsx` GSC exports here. The ingestion script picks them up automatically.

---

## User's Manual Data Plan (Current Approach)

Since Ahrefs MCP is not connected in the web session, the user proposed
exporting data manually from Google Search Console:

**Export format:**
- XLSX file with default GSC filename (contains date info)
- Tabs that matter: `Queries`, `Pages` (and `Dates` if present)
- Filtered to the tutorials folder on Storylane's GSC property

**Files uploaded so far (in `data/gsc-exports/`):**
| File | Period |
|------|--------|
| storylane.io-Performance Jan 2025 - May 2026 (16 months).xlsx | 2025-01_to_2026-05 (aggregate) |
| storylane.io-Performance-on-Search feb 2025.xlsx | 2025-02 |
| storylane.io-Performance-on-Search march 2025.xlsx | 2025-03 |
| storylane.io-Performance-on-Search- April - 2025xlsx.xlsx | 2025-04 |
| storylane.io-Performance-on-Search feb 2026.xlsx | 2026-02 |
| storylane.io-Performance-on-Search - March 2026.xlsx | 2026-03 |
| storylane.io-Performance-on-Search April 2026.xlsx | 2026-04 |

**Monthly periods in DB:** 2025-02, 2025-03, 2025-04, 2026-02, 2026-03, 2026-04
**Gap:** May 2025 → Jan 2026 (missing). Trend charts will have a jump here.
The "Post-peak Q1'25" (Feb–Apr 2025) vs current (Feb–Apr 2026) comparison
works correctly with what's loaded.

**To add more months:** export from GSC, drop in `data/gsc-exports/`, re-run
`python ingest_gsc.py` (it uses INSERT OR REPLACE so safe to re-run).

---

## What the Next Session Should Pick Up

### Immediate — already designed, not yet built
1. **Concentration risk metric** — top 2 pages as % of cluster total clicks
   (the "Grok problem": 2 pages = ~50% of cluster clicks, high fragility)
2. **Page 2 trap view** — queries with impressions > threshold and position
   5–15, low CTR. These are close to page 1 and worth targeting. Jira is the
   prime example per user notes.
3. **Top-3 cohort CTR tracking** — track CTR specifically for queries that
   were ever in top 3 positions, not overall average CTR

### Needs Ahrefs MCP (backlog)
4. **"Lost to" buckets** — who outranks you per query:
   - Lost to AIO (AI Overview)
   - Lost to parent domain + YouTube
   - Lost to unbranded / Reddit / forums
   Requires knowing what's ranking above you — GSC alone can't provide this.
   This is the highest-value missing feature.
5. **Search volume patching** — add monthly search volume per keyword.
   Also requires Ahrefs.

### When Ahrefs MCP is reconnected
The original plan was to use these tools (confirmed working, 0 unit cost):
- `ahrefs_gsc_pages` → article-level snapshots per month
- `ahrefs_gsc_keywords` → keyword-level detail per cluster
- `ahrefs_gsc_keyword_history` → time-series trends

Backfill target: 17 months (Dec 2024 → Apr 2026), month by month.
Save format: `data/pages/pages_YYYY-MM.json` and `data/keywords/keywords_YYYY-MM.json`
Then run `python ingest.py` (the original JSON-based ingester, separate from
`ingest_gsc.py` which handles XLSX).

---

## Key Business Context (From User Notes)

- **12,000+ tutorial pages** driving SEO traffic, declining for months
- **Three distinct problems** (not one):
  1. AIO stealing clicks — position stable, CTR collapsed
  2. Brand displacement — original brands (Canva, Notion) reclaimed top spots
  3. Content staleness — fixable, unlike AIO
- **The metric that matters**: "Top 1.5" count (queries ranking at position ≤1.5)
  NOT average position. Average position is misleading.
  - Notion peak: 114 top-1.5 queries → now 61
  - Canva peak: 299 top-1.5 queries → now 18
- **Healthy clusters** (weak official docs or complex integrations):
  GitLab, Bitbucket, Confluence, Linear, NotebookLM
- **High-risk cluster**: Grok — 2 pages drive ~50% of cluster clicks
- **Watch**: Claude, GitHub (per user)
- **Clusters structurally losing**: Canva (losing clicks AND impressions),
  Notion (same pattern)
- **Global signal**: Leads stopped dipping April 2026, slight click lift
  (8,158 → 9,135 over 3 months)

---

## How to Run Locally

```bash
git clone https://github.com/prashil3k/DLS-dashboard.git
cd DLS-dashboard
pip install -r requirements.txt

# If GSC exports are already in data/gsc-exports/:
python ingest_gsc.py

# Launch dashboard:
streamlit run app.py
```

The `.db` file is gitignored — it must be built locally from the exports.
