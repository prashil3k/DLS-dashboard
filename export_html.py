import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import plotly.io as pio
from sample_data import CLUSTER_SUMMARY, POSITION_DISTRIBUTION, MONTHLY_TRENDS, TOP_QUERIES

charts = []

def chart_html(fig, title=""):
    return f"<h2>{title}</h2>" + pio.to_html(fig, full_html=False, include_plotlyjs=False)

# ── 1. Cluster table ──────────────────────────────────────────────────────────
def ctr_bg(val):
    if val >= 1.5: return "background:#d4edda;color:#155724"
    if val >= 0.5: return "background:#fff3cd;color:#856404"
    return "background:#f8d7da;color:#721c24"

rows = ""
for _, r in CLUSTER_SUMMARY.iterrows():
    style = ctr_bg(r.ctr)
    rows += (
        f"<tr><td>{r.cluster}</td>"
        f"<td>{r.clicks:,.0f}</td>"
        f"<td>{r.impressions:,.0f}</td>"
        f"<td style='{style};padding:4px 8px;border-radius:4px'>{r.ctr:.2f}%</td>"
        f"<td>{r.avg_position:.1f}</td></tr>"
    )

table_html = f"""
<h2>All Clusters · Last 3 Months</h2>
<table style="width:100%;border-collapse:collapse;font-family:sans-serif;font-size:14px">
  <thead style="background:#f1f3f5">
    <tr>
      {''.join(f'<th style="text-align:left;padding:8px;border-bottom:2px solid #dee2e6">{h}</th>'
               for h in ['Cluster','Clicks','Impressions','CTR','Avg Position'])}
    </tr>
  </thead>
  <tbody>{rows}</tbody>
</table>
<p style="font-size:12px;color:#888">🟢 CTR ≥ 1.5% &nbsp; 🟡 0.5–1.5% &nbsp; 🔴 &lt; 0.5%</p>
"""

# ── 2. Clicks bar chart ───────────────────────────────────────────────────────
fig_clicks = px.bar(
    CLUSTER_SUMMARY.sort_values("clicks", ascending=True),
    x="clicks", y="cluster", orientation="h",
    color="ctr", color_continuous_scale=["#dc3545","#ffc107","#28a745"],
    range_color=[0,3],
    title="Clicks by Cluster (color = CTR health)",
    labels={"clicks":"Clicks","cluster":"","ctr":"CTR %"},
)
fig_clicks.update_layout(height=480, margin=dict(l=0,r=20,t=40,b=0))
charts.append(chart_html(fig_clicks, ""))

# ── 3. CTR vs Impressions bubble ──────────────────────────────────────────────
fig_bubble = px.scatter(
    CLUSTER_SUMMARY, x="impressions", y="ctr",
    size="clicks", color="cluster",
    hover_name="cluster",
    title="CTR vs Impressions · Bubble size = Clicks",
    labels={"impressions":"Impressions","ctr":"CTR (%)"},
    size_max=50,
)
fig_bubble.add_hline(y=1.5, line_dash="dash", line_color="green", annotation_text="Healthy CTR (1.5%)")
fig_bubble.add_hline(y=0.5, line_dash="dash", line_color="red",   annotation_text="Danger zone (0.5%)")
fig_bubble.update_layout(height=460, margin=dict(l=0,r=0,t=40,b=0))
charts.append(chart_html(fig_bubble, ""))

# ── 4. Position health — top 1.5 now vs peak ─────────────────────────────────
fig_pos = go.Figure()
fig_pos.add_bar(name="Peak", x=POSITION_DISTRIBUTION["cluster"],
                y=POSITION_DISTRIBUTION["peak_top_1_5"], marker_color="#6c757d")
fig_pos.add_bar(name="Now",  x=POSITION_DISTRIBUTION["cluster"],
                y=POSITION_DISTRIBUTION["top_1_5"],      marker_color="#0d6efd")
fig_pos.update_layout(barmode="group", height=380, title="Top 1.5 Queries (Absolute #1) — Now vs Peak",
                      yaxis_title="Query count", margin=dict(l=0,r=0,t=40,b=0))
charts.append(chart_html(fig_pos, ""))

# ── 5. Retention table ────────────────────────────────────────────────────────
pos_df = POSITION_DISTRIBUTION.copy()
pos_df["retention_pct"] = (pos_df["top_1_5"] / pos_df["peak_top_1_5"] * 100).round(0).astype(int)

def ret_bg(pct):
    if pct >= 70: return "background:#d4edda;color:#155724"
    if pct >= 40: return "background:#fff3cd;color:#856404"
    return "background:#f8d7da;color:#721c24"

ret_rows = ""
for _, r in pos_df.iterrows():
    s = ret_bg(r.retention_pct)
    ret_rows += (
        f"<tr><td>{r.cluster}</td><td>{r.peak_top_1_5}</td><td>{r.top_1_5}</td>"
        f"<td style='{s};padding:4px 8px;border-radius:4px'>{r.retention_pct}%</td></tr>"
    )

retention_html = f"""
<h2>Position Retention · Top 1.5 Queries Kept vs Peak</h2>
<p style="color:#555;font-size:13px">A small shift from rank 1.2 → 2.1 on high-volume queries causes most click loss.
Average position hides this — this table shows it directly.</p>
<table style="width:60%;border-collapse:collapse;font-family:sans-serif;font-size:14px">
  <thead style="background:#f1f3f5">
    <tr>{''.join(f'<th style="text-align:left;padding:8px;border-bottom:2px solid #dee2e6">{h}</th>'
                 for h in ['Cluster','Peak #1s','Current #1s','Retention'])}</tr>
  </thead>
  <tbody>{ret_rows}</tbody>
</table>
"""

# ── 6. AIO signature — Notion ─────────────────────────────────────────────────
for cluster_name in ["Notion", "Canva"]:
    df = MONTHLY_TRENDS[cluster_name]
    fig_aio = make_subplots(
        rows=3, cols=1, shared_xaxes=True,
        subplot_titles=("Clicks", "CTR (%) and Avg Position", "Impressions"),
        vertical_spacing=0.1,
    )
    fig_aio.add_trace(go.Scatter(x=df["month"], y=df["clicks"], name="Clicks",
        line=dict(color="#0d6efd",width=2), fill="tozeroy",
        fillcolor="rgba(13,110,253,0.1)"), row=1, col=1)
    fig_aio.add_trace(go.Scatter(x=df["month"], y=df["ctr"], name="CTR %",
        line=dict(color="#dc3545",width=2)), row=2, col=1)
    fig_aio.add_trace(go.Scatter(x=df["month"], y=df["avg_position"], name="Avg Position",
        line=dict(color="#198754",width=2,dash="dash")), row=2, col=1)
    fig_aio.add_trace(go.Scatter(x=df["month"], y=df["impressions"], name="Impressions",
        line=dict(color="#6c757d",width=2), fill="tozeroy",
        fillcolor="rgba(108,117,125,0.1)"), row=3, col=1)
    fig_aio.update_layout(height=560, hovermode="x unified",
                          title=f"{cluster_name} · AIO Signature Check",
                          margin=dict(l=0,r=0,t=40,b=0))
    charts.append(chart_html(fig_aio, ""))

# ── 7. Query deep dive — Confluence ──────────────────────────────────────────
for cluster_name in ["Grok", "Confluence", "Linear", "NotebookLM"]:
    qdf = TOP_QUERIES[cluster_name].copy()
    signal_colors = {"Healthy":"#28a745","AIO":"#dc3545","Displaced":"#fd7e14"}
    fig_q = px.scatter(
        qdf, x="impressions", y="ctr", size="clicks",
        color="signal", color_discrete_map=signal_colors,
        hover_name="query",
        hover_data={"clicks":True,"impressions":True,"position":True},
        title=f"{cluster_name} · Query Signals",
        labels={"impressions":"Impressions","ctr":"CTR (%)","signal":"Signal"},
        size_max=40,
    )
    fig_q.add_hline(y=5,  line_dash="dot", line_color="green", annotation_text="Strong CTR (5%+)")
    fig_q.add_hline(y=1,  line_dash="dot", line_color="red",   annotation_text="Weak CTR (1%)")
    fig_q.update_layout(height=400, margin=dict(l=0,r=0,t=40,b=0))
    charts.append(chart_html(fig_q, ""))

# ── Assemble HTML ─────────────────────────────────────────────────────────────
sections = [
    ("Cluster Overview", table_html + charts[0] + charts[1]),
    ("Position Health · Top 1.5 Tracking", charts[2] + retention_html),
    ("AIO Signature · Notion", charts[3]),
    ("AIO Signature · Canva", charts[4]),
    ("Query Deep Dive", "".join(charts[5:])),
]

nav_links = "".join(
    f'<a href="#s{i}" style="margin-right:20px;color:#0d6efd;text-decoration:none;font-weight:500">{t}</a>'
    for i, (t, _) in enumerate(sections)
)

body = ""
for i, (title, content) in enumerate(sections):
    body += f"""
    <section id="s{i}" style="margin-bottom:60px">
      <h1 style="border-bottom:2px solid #dee2e6;padding-bottom:8px;color:#212529">{title}</h1>
      {content}
    </section>
    """

html = f"""<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <title>Storylane · SEO Dashboard</title>
  <script src="https://cdn.plot.ly/plotly-2.27.0.min.js"></script>
  <style>
    body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            max-width: 1200px; margin: 0 auto; padding: 24px; background: #f8f9fa; color: #212529; }}
    nav  {{ background: white; padding: 16px 24px; border-radius: 8px;
            box-shadow: 0 1px 4px rgba(0,0,0,.1); margin-bottom: 32px; position: sticky; top: 0; z-index: 10; }}
    section {{ background: white; padding: 28px; border-radius: 8px;
               box-shadow: 0 1px 4px rgba(0,0,0,.08); }}
    table td, table th {{ padding: 8px 12px; border-bottom: 1px solid #dee2e6; }}
    h2 {{ color: #343a40; margin-top: 28px; }}
  </style>
</head>
<body>
  <h1 style="margin-bottom:4px">📊 Storylane · Demo-led SEO Dashboard</h1>
  <p style="color:#6c757d;margin-bottom:24px">Phase 1 + Phase 2 cluster performance · Sample data from GSC audit</p>
  <nav>{nav_links}</nav>
  {body}
</body>
</html>"""

with open("dashboard.html", "w") as f:
    f.write(html)

print("✅ Saved: dashboard/dashboard.html")
