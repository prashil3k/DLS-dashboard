# DLS SEO performance dashboard

This is Storylane's demo-led SEO diagnostic dashboard. Claude Code is the conversational query layer — open any chat in this directory and start asking questions about clusters, keywords, position health, or traffic patterns.

Prashil works from two Claude Code accounts (local CLI + a friend's browser account), both connected to `github.com/prashil3k/DLS-dashboard`. GitHub is the bridge. This file is the single context source for the GitHub account.

## Session context

<!-- AUTO-SYNCED FROM PROJECT CARD — DO NOT EDIT MANUALLY -->

## PROJECT SUMMARY

Storylane's demo-led SEO program — ~9,000 tutorial pages across 100+ SaaS tools targeting how-to queries. Prashil is SEO lead. Repo: `github.com/prashil3k/DLS-dashboard`. Ahrefs project_id: 9000301. Streamlit Cloud auto-deploys from main.

The DLS story: grew from 25K→150K monthly clicks (Feb–Aug 2024), 68% Canva-dependent. 7-month publishing halt (Jul–Dec 2025). Restarted at 5x speed (3,320 tutorials May 2026) but clicks haven't stabilized — 7,213 clicks Apr 2026 (-73% from peak). Only Claude (+22%) and Grok (new) grew; everything else down 50-98%.

## WHAT'S BUILT

- **8-tab Streamlit dashboard**: cluster scorecard, cluster trends, position filter, query deep dive, Page 2 trap, opportunities, lost-to analysis, input→output correlation
- **SQLite pipeline**: 15/16 months full GSC exports (1,000 rows each) + 12,315 tutorial metadata records
- **SERP snapshots**: 17 keywords, 155 results across 8 clusters. Every keyword has AI Overview at position 1.
- **Conversational query layer**: CLAUDE.md + `db.py` with 18+ query functions for ad-hoc SQL analysis
- **Data flow**: GSC XLSX → `ingest_gsc.py` / `ingest.py` → SQLite → Streamlit + Claude Code SQL
- **Tutorial metadata**: `ingest_tutorials.py` handles Webflow CSV. 49% mapped to dashboard clusters.

## ACTIVE WORK

Dashboard usability redesign — brainstorming complete, not yet built. The dashboard is metrics-organized (pick a cluster, see lines going down) when it should be decision-organized (where should we point 3,000+ tutorials/month?).

Proposed 4-view redesign:
1. **Allocation map** — scatter: tutorials invested (X) vs clicks returned (Y) per cluster
2. **Health buckets** — auto-classify clusters: 🟢 growing, 🟡 stable, 🟠 declining-recoverable, 🔴 structurally lost
3. **Creation flow** — portfolio-level: where are new tutorials going? Into green or red clusters?
4. **Drill-down** — existing 8 tabs become the deep layer, entered after triage

Three modes: "what's getting worse?", "what should I do this week?", "is my experiment working?"

## BACKLOG

1. **Dashboard usability redesign** — top priority, see ACTIVE WORK above
2. **New cluster discovery** — Ahrefs keywords-explorer for high-volume SaaS tools not yet covered. Need 200+ tutorial-worthy keywords per cluster.
3. **AI diagnostic layer** — future "doctor" mode: auto-diagnosis with CMS context, competitor analysis, actionable recs. Parked — learn from conversational layer first.

## EXPERIMENT IDEAS

- **Query consolidation — Canva to Google Slides**: 19 keyword variants, 10,372 impressions, 120 clicks. Consolidate into one comprehensive page, redirect the rest.
- **Meta regeneration**: top 10 keywords with position ≤5 and CTR <2%. Rewrite formulaic titles to add value signals.
- **Broader Canva consolidation**: superscript (2,671 impr), youtube (2,430), download-image (2,022), stretch (1,713).

On the horizon: Canva keyword-by-keyword audit, Modash competitive analysis (benchmark: higher traffic at similar revenue).

## KEY CONSTRAINTS

- Scale is the binding constraint — no per-page manual work viable across 9,000+ pages
- Ahrefs MCP: GSC tools free (0 units per row), keywords-explorer and SERP tools cost units
- Content team: ~14 people (writers, reviewers, publisher). Publishing hold while reviewer backlog clears.
- Internal linking confirmed working: each page has "related reads" with 3 in-cluster links
- Parent domain displacement (Canva, Notion) is structural — not worth fighting directly
- Our edge is strongest where official docs are weak + workflows are complex (Jira, Confluence, Bitbucket, Linear)

<!-- END SESSION CONTEXT -->

## Operational reference

Everything below this line is the operational manual for doing actual data work. It changes rarely — only when the database schema changes, new query patterns are discovered, or reasoning principles evolve.

### Database

- **Path:** `storylane_seo.db` (this directory)
- **Query method:** `sqlite3 storylane_seo.db "YOUR SQL HERE"` via Bash
- For tabular output: `sqlite3 -header -column storylane_seo.db "..."`
- For CSV output: `sqlite3 -header -csv storylane_seo.db "..."`
- Current data: 16 months (Feb 2025 – May 2026), ~15,100 page rows, ~15,100 keyword rows, 38 clusters

### Schema

#### `pages_monthly` — one row per page per month
| Column | Meaning |
|--------|---------|
| page | Full URL on storylane.io |
| month | `YYYY-MM` format |
| cluster | SaaS tool cluster (canva, notion, grok, etc.) |
| keywords_count | Number of keywords this page ranks for |
| top_keyword | Highest-traffic keyword for this page |
| clicks, impressions | GSC metrics for that month |
| ctr | Click-through rate (decimal, e.g. 0.07 = 7%) |
| position | Average GSC position |
| traffic_value | Estimated traffic value from Ahrefs |
| is_estimated | 1 = backfilled from Ahrefs (thin data), 0 = full GSC export |

#### `keywords_monthly` — one row per keyword per month
| Column | Meaning |
|--------|---------|
| keyword | Search query from GSC |
| month | `YYYY-MM` format |
| top_url | Best-performing URL for this keyword |
| cluster | SaaS tool cluster |
| urls_count | Number of URLs ranking for this keyword |
| clicks, impressions, ctr, position | GSC metrics |
| is_estimated | Same as above |

#### `keyword_volumes` — search volume enrichment from Ahrefs
| Column | Meaning |
|--------|---------|
| keyword | Search query (joins to keywords_monthly.keyword) |
| volume | Monthly search volume |
| cpc | Cost per click (cents) |
| difficulty | Keyword difficulty score |

#### `organic_competitors` — domains competing for the same keywords
| Column | Meaning |
|--------|---------|
| competitor_domain | Domain name |
| keywords_common | Keywords shared with storylane.io |
| traffic, domain_rating, share | Competitor metrics from Ahrefs |

#### `serp_snapshots` — point-in-time SERP results for select keywords
| Column | Meaning |
|--------|---------|
| keyword | Search query |
| position | Rank in SERP |
| url, domain | Who ranks there |
| domain_rating, traffic | Domain metrics |

#### `tutorial_metadata` — Webflow CMS tutorial catalog (INPUT data)
| Column | Meaning |
|--------|---------|
| slug | URL slug (primary key) |
| url | Full URL on storylane.io |
| title | Tutorial title |
| category | CMS category (141 unique) |
| cluster | Dashboard cluster (mapped from category/slug). NULL if no match |
| created_date | YYYY-MM-DD when created in Webflow |
| created_month | YYYY-MM for easy joins |
| is_draft | 0 = live, 1 = draft |

Key: use `created_date` not published/updated — published dates get overwritten on updates.

#### `cluster_config` — cluster-to-URL-pattern mapping
Stores slug patterns and parent domains used to assign pages to clusters.

### What is a cluster

A "cluster" is a SaaS tool that Storylane has tutorial pages about. 38 clusters (canva, notion, chatgpt, claude, github, figma, slack, hubspot, etc.). Each maps to URL slug patterns. Cluster assignment logic is in `cluster.py`.

### The metric that matters

**"Top 1.5 count"** — keywords ranking at position ≤ 1.5. This is the north star, NOT average position. Average position is misleading (gaining 50 keywords at position 15 inflates it but drives zero clicks).

```sql
SELECT month, cluster,
  COUNT(DISTINCT CASE WHEN position <= 1.5 THEN keyword END) as top_1_5,
  COUNT(DISTINCT keyword) as total
FROM keywords_monthly
WHERE cluster IS NOT NULL AND month NOT LIKE '%_to_%'
GROUP BY month, cluster ORDER BY cluster, month;
```

### Diagnostic patterns

**AIO signature:** Position stable + CTR dropping → Google AI Overview answering the query directly.

**Brand displacement:** Position dropping → parent brand reclaiming rankings. Check `cluster_config.parent_domain`.

**Content staleness:** Impressions dropping → Google deprioritizing old content. Most fixable.

**Concentration risk:** Top 2 pages as % of cluster clicks. High = fragile.
```sql
WITH ranked AS (
  SELECT cluster, page, clicks,
    ROW_NUMBER() OVER (PARTITION BY cluster ORDER BY clicks DESC) as rn,
    SUM(clicks) OVER (PARTITION BY cluster) as cluster_total
  FROM pages_monthly
  WHERE cluster IS NOT NULL AND month = (SELECT MAX(month) FROM pages_monthly WHERE month NOT LIKE '%_to_%')
)
SELECT cluster, cluster_total,
  SUM(CASE WHEN rn <= 2 THEN clicks ELSE 0 END) as top2_clicks,
  ROUND(SUM(CASE WHEN rn <= 2 THEN clicks ELSE 0 END) * 100.0 / cluster_total, 1) as top2_pct
FROM ranked GROUP BY cluster ORDER BY top2_pct DESC;
```

**Page 2 trap:** Position 5-15, high impressions, low CTR.

**Input → outcome:** Always check tutorial_metadata before diagnosing a decline — did we stop publishing?
```sql
SELECT cluster, COUNT(*) as tutorials,
  MIN(created_date) as first, MAX(created_date) as last,
  COUNT(CASE WHEN created_month >= '2025-07' AND created_month <= '2025-12' THEN 1 END) as gap_period
FROM tutorial_metadata WHERE cluster = '{cluster}' GROUP BY cluster;
```

### Reasoning principles

1. **Always separate input from outcome** — before diagnosing a decline, check if publishing stopped. A publishing gap explains traffic loss without needing a ranking theory.

2. **Defensibility filter** — our edge is strongest where official docs are weak and workflows are complex (Jira, Confluence, Bitbucket, Linear, NotebookLM, Grok). Weakest where queries are trivially simple or parent brand has reclaimed SEO (Canva, Notion).

3. **Replacer analysis: why > who** — when analyzing who replaced us, focus on: content depth, freshness, schema/structured data, domain authority, UX. Structure as: who → what they have we don't → fixable? → specific action.

4. **Cluster scale bar** — new clusters need 200+ tutorial-worthy keywords to justify investment. Validate with Ahrefs keywords-explorer "how to [action] in [tool]" patterns.

5. **Experiment quality bar** — every experiment needs: what changes, what we measure, what success looks like, scope (one cluster or a few keywords, not "improve everything"). Analysis ≠ experiment.

### Useful queries

```sql
-- Top declining clusters (peak vs current top-1.5)
SELECT a.cluster,
  a.top_1_5 as peak_top1_5, b.top_1_5 as current_top1_5,
  b.top_1_5 - a.top_1_5 as delta
FROM (
  SELECT cluster, COUNT(DISTINCT CASE WHEN position <= 1.5 THEN keyword END) as top_1_5
  FROM keywords_monthly WHERE month BETWEEN '2025-02' AND '2025-04' AND cluster IS NOT NULL
  GROUP BY cluster
) a
JOIN (
  SELECT cluster, COUNT(DISTINCT CASE WHEN position <= 1.5 THEN keyword END) as top_1_5
  FROM keywords_monthly WHERE month = (SELECT MAX(month) FROM keywords_monthly WHERE month NOT LIKE '%_to_%')
    AND cluster IS NOT NULL
  GROUP BY cluster
) b ON a.cluster = b.cluster ORDER BY delta ASC;
```

```sql
-- Keyword movers between two months
SELECT a.keyword, a.cluster, a.position as pos_before, b.position as pos_after,
  ROUND(b.position - a.position, 1) as pos_delta, b.impressions
FROM keywords_monthly a
JOIN keywords_monthly b ON a.keyword = b.keyword
WHERE a.month = '2026-04' AND b.month = '2026-05'
  AND a.cluster IS NOT NULL
ORDER BY ABS(pos_delta) DESC LIMIT 30;
```

```sql
-- AIO candidates (position stable, CTR dropping)
SELECT a.cluster,
  ROUND(AVG(a.ctr), 4) as old_ctr, ROUND(AVG(b.ctr), 4) as new_ctr,
  ROUND(AVG(a.position), 1) as old_pos, ROUND(AVG(b.position), 1) as new_pos
FROM keywords_monthly a
JOIN keywords_monthly b ON a.keyword = b.keyword AND a.cluster = b.cluster
WHERE a.month = '2025-03' AND b.month = '2026-04' AND a.cluster IS NOT NULL
GROUP BY a.cluster
HAVING ABS(new_pos - old_pos) < 2.0 AND new_ctr < old_ctr * 0.8
ORDER BY (old_ctr - new_ctr) DESC;
```

```sql
-- High-volume opportunity keywords
SELECT k.keyword, k.cluster, k.position, v.volume, v.difficulty,
  ROUND(v.volume / k.position, 0) as opportunity_score
FROM keywords_monthly k
JOIN keyword_volumes v ON k.keyword = v.keyword
WHERE k.month = (SELECT MAX(month) FROM keywords_monthly WHERE month NOT LIKE '%_to_%')
  AND v.volume >= 100 AND k.position >= 4.0 AND k.position <= 20.0
ORDER BY opportunity_score DESC LIMIT 30;
```

### Python query layer

`db.py` has pre-built functions returning pandas DataFrames:
- `db.cluster_summary()` — multi-period cluster comparison
- `db.cluster_monthly_trends(cluster)` — monthly time series
- `db.query_position_counts(cluster)` — top 1/3/5/10 keyword counts by month
- `db.concentration_risk(month)` — top-2 page concentration per cluster
- `db.page2_trap(cluster, month)` — keywords stuck on page 2
- `db.keyword_movers(cluster, month_a, month_b)` — biggest position changes
- `db.keywords_with_volume(cluster, month)` — keywords enriched with search volume
- `db.top_opportunity_keywords(month)` — high-volume, poor-ranking keywords
- `db.top3_cohort_ctr(cluster)` — retention for keywords that ever reached top 3
- `db.lost_to_summary()` — who ranks above us on tracked keywords
- `db.serp_domain_analysis()` — most frequent SERP competitors
- `db.tutorial_creation_by_cluster(cluster)` — monthly tutorial creation counts
- `db.input_output_correlation(cluster)` — joins creation with performance
- `db.cluster_tutorial_summary()` — per-cluster tutorial stats

### Data constraints

- **GSC**: 15 full months (Feb 2025–Apr 2026, 1,000 rows each) + 1 thin month (May 2026, 100 rows from Ahrefs)
- **Tutorials**: 12,315 total. 49% mapped to clusters, rest have unmapped categories. Use `category` for full coverage.
- **Search volume**: ~497 keywords have volume data. Most unmatched — handle NULLs in JOINs.
- **SERP snapshots**: 17 keywords, 155 results. Limited for "lost to" analysis.
- **Aggregate rows**: no `_to_` months in DB, but keep the `NOT LIKE '%_to_%'` filter as safety.

### Known cluster status

**Healthy/growing:** Grok (new, high efficiency at 51.9 clicks/tutorial), Claude (+22%)
**Holding:** GitLab, Bitbucket, Confluence, Linear, NotebookLM — official docs weak, tutorials retain value
**Structurally lost:** Canva (-97%), Notion — parent brands reclaimed + AIO compounds damage
