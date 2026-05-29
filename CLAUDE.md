# DLS SEO performance dashboard

This is Storylane's demo-led SEO diagnostic dashboard tracking ~9,000+ tutorial pages on `storylane.io`. Claude Code is the conversational query layer — open any chat in this directory and start asking questions about clusters, keywords, position health, or traffic patterns.

The Streamlit dashboard (`streamlit run app.py`) is the visual layer. This file exists so Claude Code can query the same data directly via SQL.

## Session continuity

Prashil works from two different Claude Code accounts (local CLI + a friend's browser account), both connected to the same GitHub repo (`github.com/prashil3k/DLS-dashboard`). GitHub is the bridge — always push all changes so the next session on either account picks up where this one left off. This file (CLAUDE.md) is the single source of truth that travels with the repo.

## What's built

- **8-tab Streamlit dashboard**: cluster scorecard, cluster trends, position filter, query deep dive, Page 2 trap, opportunities, lost-to analysis, input→output correlation
- **SQLite pipeline**: 15/16 months full GSC exports (1,000 rows each) + tutorial metadata (12,315 tutorials)
- **SERP snapshots**: 17 keywords, 155 results across 8 clusters. Key finding: every single keyword has AI Overview at position 1.
- **Conversational query layer**: this file + `db.py` with 18+ query functions
- **Data flow**: GSC XLSX exports → `ingest_gsc.py` / `ingest.py` → SQLite → Streamlit + Claude Code SQL

## The DLS story (context for any new session)

- **Feb 2024**: started creating tutorials. Ramped from 1→144→226→364/month
- **Aug 2024**: grew from ~25K to ~150K monthly clicks in 6 months
- **Feb 2025** (first month with GSC data in DB): 26,683 clicks, 228 top-1.5 keywords. **68% of traffic was Canva alone** (18,072 clicks)
- **Jul 2025–Dec 2025**: publishing stopped (7-month gap, only 57 tutorials in Jul then nothing)
- **Jan 2026**: restarted at massive scale. 234→707→957→858→3,320 tutorials/month
- **Apr 2026**: clicks at 7,213 (-73% from peak), top-1.5 at 7 (-97%). Restart hasn't stabilized performance yet.
- **Only 2 clusters grew**: Claude (+22%) and Grok (new). Everything else down 50-98%.

## Dashboard usability redesign (ACTIVE — brainstorming, not yet built)

### The problem

The dashboard is organized by metrics and individual clusters. With 100+ clusters of unequal weight, you pick one from a dropdown, see lines going down, pick another, lines going down. After 10 minutes you've looked at 5 clusters and learned nothing except "everything is bad." The dashboard never answers: where should we point our 3,000+ tutorials/month?

### Proposed redesign

**View 1: Allocation map (scatter plot)**
- X = tutorials invested, Y = clicks returned, per cluster
- Quadrants: top-right = working, bottom-right = wasted effort, top-left = underfed opportunity, bottom-left = ignore
- Key data: Grok (51.9 clicks/tutorial), Claude (7.1), NotebookLM (6.9) are high-efficiency. Adobe (0.03), Salesforce (0.04), HubSpot (0.0) are zero-return.

**View 2: Health buckets (auto-classify every cluster)**
- 🟢 Growing — clicks trending up (Grok, Claude)
- 🟡 Stable — holding position (GitLab, Bitbucket, Linear)
- 🟠 Declining but recoverable — still has positions 2-10
- 🔴 Structurally lost — parent brand/AIO killed it (Canva, Notion, Figma)
- Per bucket: total tutorials, total clicks, clicks-per-tutorial efficiency

**View 3: Creation flow at portfolio level**
- Where are new tutorials going month by month? Into green clusters or red ones?
- Input/output tab exists per-cluster — needs a portfolio-level rollup

**View 4: Detailed drill-down**
- Existing 8 tabs become the "dig deeper" layer, entered after triage view tells you where to look

### Three modes the dashboard should serve
1. **"What's getting worse?"** — triage, ranked by actionability not traffic
2. **"What should I do this week?"** — experiment candidates surfaced from data
3. **"Is my experiment working?"** — before/after tracking (needs experiment log, not built yet)

### Principles for the redesign
- Portfolio first, individual cluster second
- Show mismatches (investing where returns are zero, not investing where efficiency is high)
- Auto-classify clusters so the user doesn't have to manually check each one
- The dashboard should tell you where to look — the conversational layer handles the "why" and "what to do"

## Remaining backlog

1. **Dashboard usability redesign** — see above. This is the top priority.
2. **New cluster discovery** — use Ahrefs keywords-explorer to find high-volume SaaS tools not yet covered. Need 200+ tutorial-worthy keywords per cluster to justify investment.
3. **AI diagnostic layer** — future "doctor" mode, parked. Learn from the conversational layer first, then codify.

## Experiment ideas (pinned, not yet run)

- **Query consolidation — Canva to Google Slides**: 19 keyword variants, 10,372 impressions, 120 clicks. Consolidate into one comprehensive page, redirect the rest.
- **Meta regeneration**: top 10 keywords with position ≤5 and CTR <2%. Rewrite formulaic titles to add value signals ("step-by-step", "2026 updated").
- **Broader Canva topic consolidation**: superscript (2,671 impr), youtube (2,430), download-image (2,022), stretch (1,713). Same treatment as slides.

## On the horizon

- Keyword-by-keyword audit of Canva cluster (triage: brand displacement vs AIO vs recoverable)
- Ahrefs analysis of Modash (benchmark: higher traffic at similar revenue)

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

### `tutorial_metadata` — Webflow CMS tutorial catalog (INPUT data)
| Column | Meaning |
|--------|---------|
| slug | URL slug (primary key), e.g. "how-to-curve-text-in-canva" |
| url | Full URL on storylane.io |
| title | Tutorial title, e.g. "How to Curve Text in Canva" |
| category | CMS category (141 unique), e.g. "canva", "ms-powerpoint", "jira" |
| cluster | Dashboard cluster (mapped from category/slug). NULL if no matching cluster |
| created_date | YYYY-MM-DD when the tutorial was created in Webflow |
| created_month | YYYY-MM for easy joins with pages_monthly/keywords_monthly |
| is_draft | 0 = live, 1 = draft |

12,315 tutorials. 49% mapped to a dashboard cluster, rest have categories not yet in the cluster system (Google Slides, PowerPoint, Power BI, etc.). Use `category` for full granularity.

**Key insight:** Use `created_date` (not published/updated) — published dates get overwritten on updates. Created date = when the tutorial was actually built.

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

### Input → outcome analysis (tutorial_metadata + pages_monthly)
- Correlate publishing activity with traffic changes
- Did a batch of tutorials going live precede a traffic lift?
- Did a publishing gap precede a traffic decline?
- Key finding: 7-month publishing halt (Jul 2025–Dec 2025) aligns with steepest traffic decline
```sql
-- Publishing volume vs cluster clicks by month
SELECT t.created_month as month, t.cluster,
  COUNT(*) as tutorials_created,
  COALESCE(p.clicks, 0) as clicks
FROM tutorial_metadata t
LEFT JOIN (
  SELECT month, cluster, SUM(clicks) as clicks
  FROM pages_monthly WHERE cluster IS NOT NULL
  GROUP BY month, cluster
) p ON t.created_month = p.month AND t.cluster = p.cluster
WHERE t.cluster IS NOT NULL
GROUP BY t.created_month, t.cluster
ORDER BY t.created_month, tutorials_created DESC;
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

- **GSC coverage**: 15 full months (Feb 2025–Apr 2026, 1,000 rows each) + 1 thin month (May 2026, 100 rows from Ahrefs). Dec 2024 and Jan 2025 were unavailable from GSC and removed.
- **Tutorial metadata**: 12,315 tutorials (Feb 2024–May 2026). 49% mapped to dashboard clusters, rest are categories without cluster mapping. Use `category` for full coverage.
- **Search volume**: ~497 keywords have volume data from Ahrefs. Most are unmatched — volume queries should LEFT JOIN and handle NULLs.
- **SERP snapshots**: ~9 keywords, 107 results. Limited coverage for "lost to" analysis.
- **Aggregate rows**: removed from DB. No `_to_` months exist, but keep the `NOT LIKE '%_to_%'` filter as a safety habit.

## How to use this tool

This dashboard isn't just for looking at numbers. It's a diagnostic + ideation layer. When Prashil opens a chat, the goal is to come out with **specific experiments to run that week**.

### Diagnostic workflow

1. **Identify the bleeding** — which clusters lost the most top-1.5 keywords or clicks in the last 1-3 months? Focus on clusters that are still worth saving (have meaningful traffic left).

2. **Diagnose the cause** — for each declining cluster, determine which pattern:
   - AIO tax (position stable, CTR collapsing) → can't outrank AI Overview, need to pivot content strategy
   - Brand displacement (position dropping) → the parent domain is reclaiming its turf. Check if the replacer is the parent domain or a third party.
   - Content staleness (impressions dropping) → Google is deprioritizing old content. This is fixable.
   - Publishing gap → did we stop publishing in this cluster? Check tutorial_metadata for creation gaps.

3. **Analyze the replacers** — for keywords where we lost position, who took our spot? Ignore parent domain takeovers (canva.com beating us on "canva" queries is structural, not actionable). Focus on third-party sites that outrank us — analyze their content, schema markup, tech SEO, and domain authority to understand what gave them the edge.

4. **Generate experiment hypotheses** — specific, testable changes:
   - Content refresh experiments (update stale top pages)
   - Schema/structured data additions
   - Internal linking changes
   - New content targeting Page 2 trap keywords
   - Consolidation of thin keyword variants

5. **Find new clusters** — look for SaaS tools with high keyword volume that we haven't covered. Use category distribution in tutorial_metadata to see what's already there vs what's missing. Use Ahrefs keywords-explorer for volume validation.

### Reasoning principles

These govern HOW to think when interpreting data. Without these, raw numbers mislead.

#### Always separate input from outcome

Every trend has two possible explanations: something we did (input) or something that happened to us (outcome). Before diagnosing a decline, ALWAYS check tutorial_metadata first:
- When were tutorials for this cluster created? If creation stopped, traffic dropping is expected, not a mystery.
- If we created 500 tutorials but only 50 show up in GSC, the gap might be indexation or relevance, not ranking loss.
- A page created 2 months ago and a page created 14 months ago cannot be compared on raw traffic — normalize by time in the sun.

```sql
-- Before diagnosing any cluster, run this first
SELECT cluster, COUNT(*) as tutorials,
  MIN(created_date) as first, MAX(created_date) as last,
  COUNT(CASE WHEN created_month >= '2025-07' AND created_month <= '2025-12' THEN 1 END) as gap_period
FROM tutorial_metadata WHERE cluster = '{cluster}' GROUP BY cluster;
```

If the input story explains the output, say so. Don't invent a ranking problem where a publishing gap is the real cause.

#### Defensibility filter

Not all clusters are worth the same effort. Our edge is strongest where:
- **Official docs are weak** (Jira, Confluence, Bitbucket, Linear) — complex workflows where an interactive demo tutorial adds genuine value over text docs
- **The query is multi-step** — AIO can't easily replicate a 10-step workflow with screenshots
- **The parent brand hasn't invested in SEO for this** — e.g. NotebookLM, Grok (newer tools)

Our edge is weakest where:
- **The query is trivially simple** ("how to do X in canva") — AIO answers it in one sentence, parent brand has a dedicated help page
- **The parent brand has reclaimed its SEO** (Canva, Notion) — structural loss, not fixable by content tweaks

When suggesting experiments or new clusters, always apply this filter. Don't recommend investing in structurally indefensible positions.

#### Replacer analysis: the "why" matters more than the "who"

When analyzing who replaced us on a keyword, the "who" is just a database lookup. The value is in the "why":
- **Content depth** — did the replacer write a more comprehensive guide? Check word count, number of steps, visual aids.
- **Content freshness** — is their page more recently updated? Google favors fresh content for how-to queries.
- **Schema/structured data** — do they have FAQ schema, HowTo schema, or video markup that earns SERP features?
- **Domain authority** — is it just a DA gap? If a DR 90 site is outranking us, that's harder to overcome than a DR 40 site with better content.
- **User experience** — do they have interactive elements, video, better mobile experience?

When reporting replacer analysis, always structure as: who → what they have that we don't → is it fixable → specific action if yes.

#### New cluster discovery: scale bar

We have 12,315 tutorials across 100+ tools. Large clusters have 200-500+ tutorials, which means the original keyword pool was 5x+ that size (most keywords are zero-volume long-tail that still drive aggregate traffic). When evaluating a new cluster:
- It must have potential for **at least 200+ tutorial-worthy keywords** to be worth the investment
- Check if the tool already has tutorials in our unclustered categories (tutorial_metadata.category) — partial coverage might exist
- Validate with Ahrefs keywords-explorer: look for "how to [action] in [tool]" pattern volume
- Prefer tools where official documentation is weak or overly technical — that's where our interactive demo format wins

#### Experiment quality bar

An experiment is something we **actually change and measure**. Analysis and discovery are not experiments. For each experiment:
- **What changes**: specific pages, specific meta, specific content structure
- **What we measure**: which metric, over what timeframe (minimum 3-4 weeks)
- **What success looks like**: e.g. "CTR improves from 0.5% to 2%+ on these 10 keywords"
- **Scope**: one cluster or a handful of keywords, not "improve everything"

Types of valid experiments:
- **Meta regeneration** — rewrite formulaic title/description tags to add value signals ("with screenshots", "2026 updated", "step-by-step")
- **Query consolidation** — merge thin pages targeting the same intent into one comprehensive page, redirect the rest
- **Content refresh** — update stale pages with current screenshots, steps, and context
- **Schema additions** — add HowTo or FAQ structured data to existing pages

### Data gaps for this workflow
- **SERP snapshots are thin** (9 keywords). To properly analyze replacers, need to expand to top 3-5 declining keywords per cluster via Ahrefs serp-overview tool (costs units).
- **Competitor page content** is not stored — when analyzing a replacer, Claude Code should fetch and analyze the live page (content structure, schema, headers, word count) on the fly.
- **New cluster discovery** needs keyword explorer data for tools not yet in the system.

### Key principles for experiments
- Parent domain displacement is NOT actionable — don't waste time competing with canva.com on "canva" queries
- AIO displacement requires strategy pivots, not content tweaks
- Content staleness is the most fixable problem
- Focus experiments on clusters where we still have positions 2-10 (recoverable) not clusters we've been pushed off entirely
- Each experiment should be scoped to one cluster or a few keywords, run for 2-4 weeks, then measured

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
