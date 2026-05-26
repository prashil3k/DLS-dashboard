# DLS SEO performance dashboard

This is Storylane's demo-led SEO diagnostic dashboard tracking ~9,000+ tutorial pages on `storylane.io`. Claude Code is the conversational query layer — open any chat in this directory and start asking questions about clusters, keywords, position health, or traffic patterns.

The Streamlit dashboard (`streamlit run app.py`) is the visual layer. This file exists so Claude Code can query the same data directly via SQL.

## Database

- **Path:** `storylane_seo.db` (this directory)
- **Query method:** `sqlite3 storylane_seo.db "YOUR SQL HERE"` via Bash
- For tabular output: `sqlite3 -header -column storylane_seo.db "..."`
- For CSV output: `sqlite3 -header -csv storylane_seo.db "..."`
- Current data: 18 months (2024-12 through 2026-05), 7,200 page rows, 7,200 keyword rows, 38 clusters

## Schema reference

### `pages_monthly` — one row per page per month
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
| is_estimated | 1 = backfilled from Ahrefs (thin data, 100 rows/month), 0 = full GSC export |

### `keywords_monthly` — one row per keyword per month
| Column | Meaning |
|--------|---------|
| keyword | Search query from GSC |
| month | `YYYY-MM` format |
| top_url | Best-performing URL for this keyword |
| cluster | SaaS tool cluster |
| urls_count | Number of URLs ranking for this keyword |
| clicks, impressions, ctr, position | GSC metrics |
| is_estimated | Same as above |

### `keyword_volumes` — search volume enrichment from Ahrefs
| Column | Meaning |
|--------|---------|
| keyword | Search query (joins to keywords_monthly.keyword) |
| volume | Monthly search volume |
| cpc | Cost per click (cents) |
| difficulty | Keyword difficulty score |

### `organic_competitors` — domains competing for the same keywords
| Column | Meaning |
|--------|---------|
| competitor_domain | Domain name |
| keywords_common | Keywords shared with storylane.io |
| traffic, domain_rating, share | Competitor metrics from Ahrefs |

### `serp_snapshots` — point-in-time SERP results for select keywords
| Column | Meaning |
|--------|---------|
| keyword | Search query |
| position | Rank in SERP |
| url, domain | Who ranks there |
| domain_rating, traffic | Domain metrics |

Currently limited to ~9 keywords, 107 results. Used for "lost to" competitor analysis.

### `cluster_config` — cluster-to-URL-pattern mapping
Stores the slug patterns and parent domains used to assign pages to clusters.

## What is a cluster

A "cluster" is a SaaS tool that Storylane has tutorial pages about. There are 38 clusters (canva, notion, chatgpt, claude, github, figma, slack, hubspot, salesforce, etc.). Each cluster maps to URL slug patterns — e.g. any page with "canva" in the URL belongs to the canva cluster. The parent domain (canva.com, notion.so) is the original brand that may be reclaiming rankings.

Cluster assignment logic is in `cluster.py` — first checks the URL slug, then falls back to keyword matching. About 89.5% of clicks are classified into a cluster.

## The metric that matters

**"Top 1.5 count"** — the number of keywords ranking at position <= 1.5. This is the north star metric, NOT average position.

Average position is misleading because gaining 50 keywords at position 15 inflates the average even though those keywords drive zero clicks. Top 1.5 count directly correlates with clicks.

Example of what this reveals:
- Canva peak: 299 top-1.5 keywords → now 18
- Notion peak: 114 top-1.5 keywords → now 61

Query to check:
```sql
SELECT month, cluster,
  COUNT(DISTINCT CASE WHEN position <= 1.5 THEN keyword END) as top_1_5,
  COUNT(DISTINCT CASE WHEN position <= 3.0 THEN keyword END) as top_3,
  COUNT(DISTINCT keyword) as total
FROM keywords_monthly
WHERE cluster IS NOT NULL AND month NOT LIKE '%_to_%'
GROUP BY month, cluster
ORDER BY cluster, month;
```

## Diagnostic patterns

### AIO signature (AI Overview stealing clicks)
- Position stable or improving + CTR dropping
- Means Google is answering the query directly in the SERP via AI Overview
- The page still ranks but users never click through
- Detection: compare position trend vs CTR trend for the same keyword/cluster

### Brand displacement
- Position dropping (not just CTR)
- The original brand (canva.com, notion.so, etc.) is reclaiming its rankings
- `cluster_config.parent_domain` tells you which domain is the threat
- Canva and Notion are the clearest examples of this pattern

### Content staleness
- Impressions dropping (Google showing the page less often)
- This is the most fixable problem — refresh the content
- Different from AIO (impressions stay, clicks drop) or displacement (position drops)

### Concentration risk
- Top 2 pages as % of total cluster clicks
- High concentration = fragile. If those pages drop, the whole cluster collapses
- Grok is the highest-risk cluster (~50% from 2 pages)
```sql
-- Concentration risk for latest month
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

### Page 2 trap
- Position 5-15, high impressions, low CTR
- Keywords that are visible but not generating clicks — opportunity or lost cause depending on context
```sql
SELECT keyword, cluster, position, impressions, clicks, ctr
FROM keywords_monthly
WHERE month = (SELECT MAX(month) FROM keywords_monthly WHERE month NOT LIKE '%_to_%')
  AND position >= 5.0 AND position <= 15.0
  AND impressions >= 50
ORDER BY impressions DESC LIMIT 50;
```

## Useful starting queries

### Top declining clusters (compare peak to current)
```sql
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
) b ON a.cluster = b.cluster
ORDER BY delta ASC;
```

### Keyword movers (biggest position changes between two months)
```sql
SELECT a.keyword, a.cluster, a.position as pos_before, b.position as pos_after,
  ROUND(b.position - a.position, 1) as pos_delta, b.impressions
FROM keywords_monthly a
JOIN keywords_monthly b ON a.keyword = b.keyword
WHERE a.month = '2026-04' AND b.month = '2026-05'
  AND a.cluster IS NOT NULL
ORDER BY ABS(pos_delta) DESC LIMIT 30;
```

### AIO candidates (position stable, CTR dropping)
```sql
SELECT a.cluster,
  ROUND(AVG(a.ctr), 4) as old_ctr, ROUND(AVG(b.ctr), 4) as new_ctr,
  ROUND(AVG(a.position), 1) as old_pos, ROUND(AVG(b.position), 1) as new_pos
FROM keywords_monthly a
JOIN keywords_monthly b ON a.keyword = b.keyword AND a.cluster = b.cluster
WHERE a.month = '2025-03' AND b.month = '2026-04'
  AND a.cluster IS NOT NULL
GROUP BY a.cluster
HAVING ABS(new_pos - old_pos) < 2.0 AND new_ctr < old_ctr * 0.8
ORDER BY (old_ctr - new_ctr) DESC;
```

### Cluster health snapshot (latest month)
```sql
SELECT cluster,
  SUM(clicks) as clicks, SUM(impressions) as impressions,
  ROUND(SUM(clicks) * 100.0 / NULLIF(SUM(impressions), 0), 2) as ctr_pct,
  ROUND(AVG(position), 1) as avg_pos,
  COUNT(DISTINCT page) as pages
FROM pages_monthly
WHERE month = (SELECT MAX(month) FROM pages_monthly WHERE month NOT LIKE '%_to_%')
  AND cluster IS NOT NULL
GROUP BY cluster ORDER BY clicks DESC;
```

### High-volume opportunity keywords (ranking poorly on high-demand queries)
```sql
SELECT k.keyword, k.cluster, k.position, v.volume, v.difficulty,
  ROUND(v.volume / k.position, 0) as opportunity_score
FROM keywords_monthly k
JOIN keyword_volumes v ON k.keyword = v.keyword
WHERE k.month = (SELECT MAX(month) FROM keywords_monthly WHERE month NOT LIKE '%_to_%')
  AND v.volume >= 100 AND k.position >= 4.0 AND k.position <= 20.0
ORDER BY opportunity_score DESC LIMIT 30;
```

## Known healthy clusters

GitLab, Bitbucket, Confluence, Linear, NotebookLM — these hold rankings because their official docs are weak or the integration workflows are complex enough that tutorials retain value.

## Known structurally losing clusters

Canva, Notion — losing both clicks AND impressions. The original brands have reclaimed rankings and AIO compounds the damage.

## Streamlit dashboard

- Run locally: `streamlit run app.py`
- Deployed on Streamlit Cloud from the `main` branch
- 7 tabs: cluster scorecard, cluster trends, position filter, query deep dive, page 2 trap, opportunities, lost-to analysis

## Data constraints

- **Estimated rows**: months backfilled via Ahrefs MCP have only ~100 rows each (pages and keywords). These are flagged with `is_estimated = 1`. Full GSC exports have ~1,000 rows per month.
- **Full GSC months**: Feb-Apr 2025, Feb-Apr 2026 (6 months). The rest may be thinner.
- **Current coverage**: 18 months from Dec 2024 to May 2026
- **Aggregate rows**: some rows have month values like `YYYY-MM_to_YYYY-MM` — always exclude these with `month NOT LIKE '%_to_%'` in queries
- **Search volume**: ~497 keywords have volume data from Ahrefs keyword explorer. Most keywords are unmatched — volume queries should use LEFT JOIN and handle NULLs.

## Python query layer

The `db.py` module has pre-built query functions that return pandas DataFrames. Useful if running Python instead of raw SQL:
- `db.cluster_summary()` — multi-period cluster comparison
- `db.cluster_monthly_trends(cluster)` — monthly time series for one or all clusters
- `db.query_position_counts(cluster)` — top 1/3/5/10 keyword counts by month
- `db.concentration_risk(month)` — top-2 page concentration per cluster
- `db.page2_trap(cluster, month)` — keywords stuck on page 2
- `db.keyword_movers(cluster, month_a, month_b)` — biggest position changes
- `db.keywords_with_volume(cluster, month)` — keywords enriched with search volume
- `db.top_opportunity_keywords(month)` — high-volume keywords we rank poorly for
- `db.top3_cohort_ctr(cluster)` — retention tracking for keywords that ever reached top 3
- `db.lost_to_summary()` — who ranks above Storylane on SERP-tracked keywords
- `db.serp_domain_analysis()` — which domains appear most in SERPs across tracked keywords
