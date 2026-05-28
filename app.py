import os
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

import db

st.set_page_config(page_title="Storylane SEO Dashboard", layout="wide", page_icon="📊")
st.title("Storylane · Demo-led SEO dashboard")

# DB version gate: if the on-disk DB is stale, nuke and rebuild from repo copy
DB_VERSION = 7  # bump this to force a rebuild on Streamlit Cloud
db.ensure_db_version(DB_VERSION)

if not db.has_data():
    with st.spinner("Building database from JSON backfill data..."):
        import ingest
        ingest.main()
    if not db.has_data():
        st.warning("No data found. Check data/pages/ and data/keywords/ directories.")
        st.stop()

months = db.available_months()
clusters = db.available_clusters()
est_months = db.estimated_months()
latest = months[-1]

ESTIMATED_DASH = "dot"
ESTIMATED_COLOR = "rgba(180,180,180,0.3)"


def _add_estimated_bands(fig, months_list, est_set, row=None, col=None):
    """Add shaded vertical bands for estimated months."""
    for m in months_list:
        if m in est_set:
            kwargs = dict(
                x0=m, x1=m,
                fillcolor=ESTIMATED_COLOR, opacity=0.4,
                layer="below", line_width=0,
            )
            if row and col:
                fig.add_vrect(**kwargs, row=row, col=col)
            else:
                fig.add_vrect(**kwargs)


def _format_month_label(m: str) -> str:
    """2026-04 → Apr '26"""
    parts = m.split("-")
    month_names = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]
    return f"{month_names[int(parts[1])-1]} '{parts[0][2:]}"


# ═══════════════════════════════════════════════════════════════════════════
tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
    "📊 Cluster scorecard",
    "📈 Cluster trends",
    "🔀 Position filter",
    "🔍 Query deep dive",
    "🎯 Page 2 trap",
    "💎 Opportunities",
    "⚔️ Lost to",
])

# ═══════════════════════════════════════════════════════════════════════════
# TAB 1 — Cluster scorecard
# ═══════════════════════════════════════════════════════════════════════════
with tab1:
    st.subheader("Cluster scorecard")
    st.caption(
        "Peak (Feb–Apr 2025) vs last 3 individual months. "
        "Columns with a * contain estimated data."
    )

    score_df = db.scorecard_data()
    if score_df.empty:
        st.info("No data available.")
    else:
        period_labels = score_df["period"].unique().tolist()

        pivot_clicks = score_df.pivot_table(
            index="cluster", columns="period", values="clicks", aggfunc="sum"
        ).reindex(columns=period_labels).fillna(0).astype(int)

        pivot_imp = score_df.pivot_table(
            index="cluster", columns="period", values="impressions", aggfunc="sum"
        ).reindex(columns=period_labels).fillna(0).astype(int)

        pivot_ctr = score_df.pivot_table(
            index="cluster", columns="period", values="ctr", aggfunc="mean"
        ).reindex(columns=period_labels).fillna(0).round(2)

        pivot_pos = score_df.pivot_table(
            index="cluster", columns="period", values="avg_position", aggfunc="mean"
        ).reindex(columns=period_labels).fillna(0).round(1)

        peak_label = period_labels[0]
        current_label = period_labels[-1]

        display_rows = []
        for cluster in pivot_clicks.index:
            peak_clicks = pivot_clicks.loc[cluster, peak_label]
            curr_clicks = pivot_clicks.loc[cluster, current_label]
            delta_pct = (
                round((curr_clicks - peak_clicks) / peak_clicks * 100)
                if peak_clicks > 0 else None
            )

            row = {"Cluster": cluster}
            for p in period_labels:
                row[f"Clicks {p}"] = f"{int(pivot_clicks.loc[cluster, p]):,}"
                row[f"Impr {p}"] = f"{int(pivot_imp.loc[cluster, p]):,}"
                row[f"CTR {p}"] = f"{pivot_ctr.loc[cluster, p]:.2f}%"
                row[f"Pos {p}"] = f"{pivot_pos.loc[cluster, p]:.1f}"

            row["Δ Clicks"] = f"{delta_pct:+d}%" if delta_pct is not None else "New"
            display_rows.append(row)

        display_df = pd.DataFrame(display_rows).sort_values(
            f"Clicks {current_label}",
            key=lambda s: s.str.replace(",", "").astype(int),
            ascending=False,
        )

        click_cols = ["Cluster"] + [f"Clicks {p}" for p in period_labels] + ["Δ Clicks"]
        ctr_cols = ["Cluster"] + [f"CTR {p}" for p in period_labels]
        pos_cols = ["Cluster"] + [f"Pos {p}" for p in period_labels]

        metric_view = st.radio(
            "Show", ["Clicks", "CTR", "Avg position", "Impressions"],
            horizontal=True, key="scorecard_metric",
        )

        if metric_view == "Clicks":
            cols_show = click_cols
        elif metric_view == "CTR":
            cols_show = ctr_cols
        elif metric_view == "Avg position":
            cols_show = pos_cols
        else:
            cols_show = ["Cluster"] + [f"Impr {p}" for p in period_labels]

        def _delta_color(val):
            try:
                v = int(str(val).replace("%", "").replace("+", ""))
            except Exception:
                return ""
            if v >= 0:
                return "background-color: #d4edda; color: #155724"
            elif v >= -30:
                return "background-color: #fff3cd; color: #856404"
            return "background-color: #f8d7da; color: #721c24"

        styled = display_df[cols_show].style
        if "Δ Clicks" in cols_show:
            styled = styled.map(_delta_color, subset=["Δ Clicks"])
        st.dataframe(styled, use_container_width=True, hide_index=True, height=600)

        st.divider()
        st.markdown("**Clicks by cluster — current month**")
        curr_data = score_df[score_df["period"] == current_label].sort_values("clicks", ascending=True)
        fig = px.bar(
            curr_data, x="clicks", y="cluster", orientation="h",
            color="ctr", color_continuous_scale=["#dc3545", "#ffc107", "#28a745"],
            range_color=[0, 3],
            labels={"clicks": "Clicks", "cluster": "", "ctr": "CTR %"},
        )
        fig.update_layout(height=500, margin=dict(l=0, r=0, t=0, b=0))
        st.plotly_chart(fig, use_container_width=True)

        # ── Concentration risk ──────────────────────────────────────────
        st.divider()
        st.markdown("**Concentration risk — top 2 pages as % of cluster clicks**")
        st.caption(
            "Clusters where 2 pages drive most of the clicks are fragile. "
            "If those pages lose rank, the entire cluster collapses. "
            "Anything above 60% is high risk."
        )

        conc_df = db.concentration_risk(latest)
        if not conc_df.empty:
            conc_df["top_page_short"] = conc_df["top_page"].apply(
                lambda x: x.split("/")[-2] + "/" if pd.notna(x) and "/" in str(x) else str(x)
            )

            def _conc_color(val):
                try:
                    v = float(str(val).replace("%", ""))
                except Exception:
                    return ""
                if v >= 60:
                    return "background-color: #f8d7da; color: #721c24"
                elif v >= 40:
                    return "background-color: #fff3cd; color: #856404"
                return "background-color: #d4edda; color: #155724"

            conc_display = conc_df[["cluster", "total_clicks", "top2_clicks", "top2_pct"]].copy()
            conc_display.columns = ["Cluster", "Total clicks", "Top 2 clicks", "Top 2 %"]
            conc_display["Total clicks"] = conc_display["Total clicks"].apply(lambda x: f"{int(x):,}")
            conc_display["Top 2 clicks"] = conc_display["Top 2 clicks"].apply(lambda x: f"{int(x):,}")
            conc_display["Top 2 %"] = conc_display["Top 2 %"].apply(lambda x: f"{x:.1f}%")

            st.dataframe(
                conc_display.style.map(_conc_color, subset=["Top 2 %"]),
                use_container_width=True, hide_index=True, height=400,
            )

            fig_conc = px.bar(
                conc_df.sort_values("top2_pct", ascending=True),
                x="top2_pct", y="cluster", orientation="h",
                color="top2_pct",
                color_continuous_scale=["#28a745", "#ffc107", "#dc3545"],
                range_color=[20, 80],
                labels={"top2_pct": "Top 2 pages %", "cluster": ""},
            )
            fig_conc.add_vline(x=60, line_dash="dot", line_color="red",
                               annotation_text="High risk (60%)")
            fig_conc.update_layout(height=500, margin=dict(l=0, r=0, t=0, b=0))
            st.plotly_chart(fig_conc, use_container_width=True)


# ═══════════════════════════════════════════════════════════════════════════
# TAB 2 — Cluster trends (the big one)
# ═══════════════════════════════════════════════════════════════════════════
with tab2:
    st.subheader("Cluster trends — month over month")

    t2_cluster = st.selectbox("Cluster", clusters, key="t2_cluster")

    st.caption(
        "Shaded columns = estimated data (will be replaced when real data is backfilled). "
        "Dashed lines = estimated segments."
    )

    # ── Query position counts ────────────────────────────────────────────
    st.markdown("### Queries by ranking position")
    st.markdown(
        "> **What this shows**: how many of your queries sit in each ranking bucket each month. "
        "A shrinking top-3 line means you're losing the queries that actually drive clicks."
    )

    bucket_cfg = [
        ("top_1", "Top 1 (position ≤1.5)", "#0d6efd", 3),
        ("top_3", "Top 3",                  "#198754", 2.5),
        ("top_5", "Top 5",                  "#fd7e14", 2),
        ("top_10", "Top 10",                "#6c757d", 1.5),
    ]

    qpc = db.query_position_counts(t2_cluster)
    if not qpc.empty:
        fig_q = go.Figure()
        for col, label, color, width in bucket_cfg:
            est_mask = qpc["is_estimated"] == 1
            # Real segments
            real = qpc.copy()
            real.loc[est_mask, col] = None
            fig_q.add_trace(go.Scatter(
                x=real["month"], y=real[col], name=label,
                line=dict(color=color, width=width), mode="lines+markers",
                marker=dict(size=5),
            ))
            # Estimated segments (dashed)
            est = qpc.copy()
            est.loc[~est_mask, col] = None
            fig_q.add_trace(go.Scatter(
                x=est["month"], y=est[col], name=f"{label} (est.)",
                line=dict(color=color, width=width, dash="dot"),
                mode="lines", showlegend=False, opacity=0.6,
            ))

        _add_estimated_bands(fig_q, qpc["month"].tolist(), est_months)
        fig_q.update_layout(
            height=380, hovermode="x unified",
            margin=dict(l=0, r=0, t=10, b=0),
            yaxis_title="Number of queries",
            legend=dict(orientation="h", y=-0.18),
        )
        st.plotly_chart(fig_q, use_container_width=True)

    # ── Page position counts ─────────────────────────────────────────────
    st.markdown("### Pages by ranking position")
    st.markdown(
        "> **What this shows**: how many of your tutorial pages hold top positions. "
        "Pages falling out of top 5 = fewer entry points for organic traffic."
    )

    ppc = db.page_position_counts(t2_cluster)
    if not ppc.empty:
        fig_p = go.Figure()
        for col, label, color, width in bucket_cfg:
            est_mask = ppc["is_estimated"] == 1
            real = ppc.copy()
            real.loc[est_mask, col] = None
            fig_p.add_trace(go.Scatter(
                x=real["month"], y=real[col], name=label,
                line=dict(color=color, width=width), mode="lines+markers",
                marker=dict(size=5),
            ))
            est = ppc.copy()
            est.loc[~est_mask, col] = None
            fig_p.add_trace(go.Scatter(
                x=est["month"], y=est[col], name=f"{label} (est.)",
                line=dict(color=color, width=width, dash="dot"),
                mode="lines", showlegend=False, opacity=0.6,
            ))

        _add_estimated_bands(fig_p, ppc["month"].tolist(), est_months)
        fig_p.update_layout(
            height=380, hovermode="x unified",
            margin=dict(l=0, r=0, t=10, b=0),
            yaxis_title="Number of pages",
            legend=dict(orientation="h", y=-0.18),
        )
        st.plotly_chart(fig_p, use_container_width=True)

    # ── Clicks + Impressions + Divergence ────────────────────────────────
    st.markdown("### Clicks vs impressions")
    st.markdown(
        "> **What to look for**: if impressions stay flat or grow while clicks drop, "
        "people are seeing your result but not clicking — a strong signal that AI Overviews "
        "or featured snippets are answering the query above you. "
        "If both drop together, you're losing visibility entirely (brand displacement)."
    )

    trend = db.cluster_monthly_trends(t2_cluster)
    if not trend.empty:
        fig_ci = make_subplots(specs=[[{"secondary_y": True}]])

        est_mask = trend["is_estimated"] == 1

        for is_est, dash, opacity in [(False, "solid", 1.0), (True, "dot", 0.6)]:
            mask = est_mask if is_est else ~est_mask
            subset = trend.copy()
            subset.loc[~mask, ["clicks", "impressions"]] = None

            fig_ci.add_trace(go.Scatter(
                x=subset["month"], y=subset["clicks"],
                name="Clicks" if not is_est else "Clicks (est.)",
                line=dict(color="#0d6efd", width=2.5, dash=dash),
                opacity=opacity, showlegend=not is_est,
                fill="tozeroy" if not is_est else None,
                fillcolor="rgba(13,110,253,0.08)" if not is_est else None,
            ), secondary_y=False)

            fig_ci.add_trace(go.Scatter(
                x=subset["month"], y=subset["impressions"],
                name="Impressions" if not is_est else "Impressions (est.)",
                line=dict(color="#6c757d", width=2, dash=dash),
                opacity=opacity, showlegend=not is_est,
            ), secondary_y=True)

        _add_estimated_bands(fig_ci, trend["month"].tolist(), est_months)
        fig_ci.update_layout(
            height=350, hovermode="x unified",
            margin=dict(l=0, r=0, t=10, b=0),
            legend=dict(orientation="h", y=-0.15),
        )
        fig_ci.update_yaxes(title_text="Clicks", secondary_y=False)
        fig_ci.update_yaxes(title_text="Impressions", secondary_y=True)
        st.plotly_chart(fig_ci, use_container_width=True)

        # Divergence detection
        real_trend = trend[trend["is_estimated"] == 0]
        if len(real_trend) >= 3:
            first_real = real_trend.iloc[0]
            last_real = real_trend.iloc[-1]
            imp_change = (last_real["impressions"] - first_real["impressions"]) / first_real["impressions"] * 100 if first_real["impressions"] > 0 else 0
            click_change = (last_real["clicks"] - first_real["clicks"]) / first_real["clicks"] * 100 if first_real["clicks"] > 0 else 0

            col_d1, col_d2, col_d3 = st.columns(3)
            col_d1.metric("Impressions change", f"{imp_change:+.0f}%")
            col_d2.metric("Clicks change", f"{click_change:+.0f}%")

            if imp_change > -10 and click_change < -30:
                col_d3.error("⚠ Divergence: impressions held but clicks collapsed → likely AIO interception")
            elif imp_change < -20 and click_change < -20:
                col_d3.warning("📉 Both declining → losing visibility (displacement or demand drop)")
            elif imp_change > 10 and click_change > 0:
                col_d3.success("📈 Growing — both impressions and clicks trending up")
            else:
                col_d3.info("→ Mixed signals — monitor next month")

    # ── CTR trend ────────────────────────────────────────────────────────
    st.markdown("### CTR trend")
    st.markdown(
        "> **What this shows**: your click-through rate over time. "
        "CTR dropping while position holds = the clearest AIO signal. "
        "CTR dropping with position = displacement."
    )

    if not trend.empty:
        fig_ctr = go.Figure()
        est_mask = trend["is_estimated"] == 1

        for is_est, dash, opacity in [(False, "solid", 1.0), (True, "dot", 0.6)]:
            mask = est_mask if is_est else ~est_mask
            subset = trend.copy()
            subset.loc[~mask, "ctr"] = None
            fig_ctr.add_trace(go.Scatter(
                x=subset["month"], y=subset["ctr"],
                name="CTR %" if not is_est else "CTR % (est.)",
                line=dict(color="#dc3545", width=2.5, dash=dash),
                opacity=opacity, showlegend=not is_est,
                mode="lines+markers" if not is_est else "lines",
            ))

        _add_estimated_bands(fig_ctr, trend["month"].tolist(), est_months)
        fig_ctr.update_layout(
            height=280, hovermode="x unified",
            margin=dict(l=0, r=0, t=10, b=0),
            yaxis_title="CTR %",
            legend=dict(orientation="h", y=-0.2),
        )
        st.plotly_chart(fig_ctr, use_container_width=True)

    # ── Average position trend ───────────────────────────────────────────
    st.markdown("### Average position")
    st.markdown(
        "> **What this shows**: the cluster's overall average ranking. "
        "Lower = better. A rising line means you're drifting off page 1."
    )

    if not trend.empty:
        fig_pos = go.Figure()
        est_mask = trend["is_estimated"] == 1

        for is_est, dash, opacity in [(False, "solid", 1.0), (True, "dot", 0.6)]:
            mask = est_mask if is_est else ~est_mask
            subset = trend.copy()
            subset.loc[~mask, "avg_position"] = None
            fig_pos.add_trace(go.Scatter(
                x=subset["month"], y=subset["avg_position"],
                name="Avg position" if not is_est else "Avg position (est.)",
                line=dict(color="#198754", width=2.5, dash=dash),
                opacity=opacity, showlegend=not is_est,
                mode="lines+markers" if not is_est else "lines",
            ))

        _add_estimated_bands(fig_pos, trend["month"].tolist(), est_months)
        fig_pos.update_layout(
            height=280, hovermode="x unified",
            margin=dict(l=0, r=0, t=10, b=0),
            yaxis_title="Average position",
            yaxis_autorange="reversed",
            legend=dict(orientation="h", y=-0.2),
        )
        st.plotly_chart(fig_pos, use_container_width=True)

    # ── Top-3 cohort CTR tracking ───────────────────────────────────────
    st.markdown("### Top-3 cohort CTR")
    st.markdown(
        "> **What this shows**: tracks CTR over time for queries that were *ever* in top 3 for this cluster. "
        "If these high-value queries lose CTR while holding position, that's the AIO tax in action. "
        "The 'still in top 3' count shows retention."
    )

    cohort_df = db.top3_cohort_ctr(t2_cluster)
    if cohort_df.empty:
        st.info("No queries were ever in top 3 for this cluster.")
    else:
        col_c1, col_c2, col_c3 = st.columns(3)
        first_row = cohort_df.iloc[0]
        last_row = cohort_df.iloc[-1]
        col_c1.metric(
            "Cohort size",
            f"{int(last_row['cohort_size'])} queries",
            help="Queries that were ever in top 3 for this cluster",
        )
        col_c2.metric(
            "Still in top 3",
            f"{int(last_row['still_top3'])}",
            delta=f"{int(last_row['still_top3'] - first_row['still_top3']):+d}" if len(cohort_df) > 1 else None,
        )
        col_c3.metric(
            "Cohort CTR",
            f"{last_row['cohort_ctr']:.2f}%",
            delta=f"{last_row['cohort_ctr'] - first_row['cohort_ctr']:+.2f}%" if len(cohort_df) > 1 else None,
        )

        fig_cohort = make_subplots(specs=[[{"secondary_y": True}]])

        est_mask = cohort_df["is_estimated"] == 1

        for is_est, dash, opacity in [(False, "solid", 1.0), (True, "dot", 0.6)]:
            mask = est_mask if is_est else ~est_mask
            subset = cohort_df.copy()
            subset.loc[~mask, ["cohort_ctr", "still_top3"]] = None

            fig_cohort.add_trace(go.Scatter(
                x=subset["month"], y=subset["cohort_ctr"],
                name="Cohort CTR %" if not is_est else "Cohort CTR % (est.)",
                line=dict(color="#dc3545", width=2.5, dash=dash),
                opacity=opacity, showlegend=not is_est,
                mode="lines+markers" if not is_est else "lines",
            ), secondary_y=False)

            fig_cohort.add_trace(go.Scatter(
                x=subset["month"], y=subset["still_top3"],
                name="Still in top 3" if not is_est else "Still in top 3 (est.)",
                line=dict(color="#0d6efd", width=2, dash=dash),
                opacity=opacity, showlegend=not is_est,
                mode="lines+markers" if not is_est else "lines",
            ), secondary_y=True)

        _add_estimated_bands(fig_cohort, cohort_df["month"].tolist(), est_months)
        fig_cohort.update_layout(
            height=350, hovermode="x unified",
            margin=dict(l=0, r=0, t=10, b=0),
            legend=dict(orientation="h", y=-0.15),
        )
        fig_cohort.update_yaxes(title_text="CTR %", secondary_y=False)
        fig_cohort.update_yaxes(title_text="Queries still in top 3", secondary_y=True)
        st.plotly_chart(fig_cohort, use_container_width=True)

        # Retention table
        st.markdown("**Cohort retention by month**")
        cohort_table = cohort_df[["month", "cohort_size", "still_top3", "cohort_ctr", "clicks", "impressions", "avg_position"]].copy()
        cohort_table.columns = ["Month", "Cohort size", "Still top 3", "CTR %", "Clicks", "Impressions", "Avg position"]
        cohort_table["Retention %"] = (cohort_table["Still top 3"] / cohort_table["Cohort size"] * 100).round(1)
        cohort_table["Clicks"] = cohort_table["Clicks"].apply(lambda x: f"{int(x):,}")
        cohort_table["Impressions"] = cohort_table["Impressions"].apply(lambda x: f"{int(x):,}")
        cohort_table["CTR %"] = cohort_table["CTR %"].apply(lambda x: f"{x:.2f}%")
        cohort_table["Retention %"] = cohort_table["Retention %"].apply(lambda x: f"{x:.1f}%")
        st.dataframe(cohort_table, use_container_width=True, hide_index=True)


# ═══════════════════════════════════════════════════════════════════════════
# TAB 3 — Position filter view (pick bucket, see all clusters)
# ═══════════════════════════════════════════════════════════════════════════
with tab3:
    st.subheader("All clusters by position bucket")
    st.caption(
        "Choose a ranking bucket, then see how every cluster's query count in that bucket "
        "has changed month over month. Good for spotting which clusters are gaining vs losing "
        "top positions across the board."
    )

    bucket = st.radio(
        "Position bucket",
        ["top_1", "top_3", "top_5"],
        format_func={"top_1": "Top 1 (≤1.5)", "top_3": "Top 3", "top_5": "Top 5"}.get,
        horizontal=True,
        key="t3_bucket",
    )

    all_data = db.all_clusters_position_summary(bucket)
    if all_data.empty:
        st.info("No data.")
    else:
        # Line chart: one line per cluster
        st.markdown(f"#### Queries in {bucket.replace('_', ' ')} — all clusters")
        top_clusters = (
            all_data.groupby("cluster")["in_bucket"].sum()
            .nlargest(12).index.tolist()
        )
        plot_data = all_data[all_data["cluster"].isin(top_clusters)]

        fig_all = px.line(
            plot_data, x="month", y="in_bucket", color="cluster",
            markers=True,
            labels={"in_bucket": "Queries in bucket", "month": "", "cluster": "Cluster"},
        )
        _add_estimated_bands(fig_all, plot_data["month"].unique().tolist(), est_months)
        fig_all.update_layout(
            height=450, hovermode="x unified",
            margin=dict(l=0, r=0, t=10, b=0),
            legend=dict(orientation="h", y=-0.15),
        )
        st.plotly_chart(fig_all, use_container_width=True)

        # Scorecard table: peak vs current for this bucket
        st.markdown(f"#### Peak vs current — queries in {bucket.replace('_', ' ')}")
        peak_months = ["2025-02", "2025-03", "2025-04"]
        peak_data = all_data[all_data["month"].isin(peak_months)]
        curr_data_t3 = all_data[all_data["month"] == latest]

        peak_agg = peak_data.groupby("cluster").agg(
            peak_queries=("in_bucket", "max"),
            peak_clicks=("clicks", "sum"),
        ).reset_index()

        curr_agg = curr_data_t3.groupby("cluster").agg(
            current_queries=("in_bucket", "max"),
            current_clicks=("clicks", "sum"),
            current_ctr=("ctr", "mean"),
            current_pos=("avg_position", "mean"),
        ).reset_index()

        merged = peak_agg.merge(curr_agg, on="cluster", how="outer").fillna(0)
        merged["Δ Queries"] = (merged["current_queries"] - merged["peak_queries"]).astype(int)
        merged["Δ Clicks"] = (merged["current_clicks"] - merged["peak_clicks"]).astype(int)

        display_t3 = merged.rename(columns={
            "cluster": "Cluster",
            "peak_queries": f"Peak queries ({bucket.replace('_',' ')})",
            "current_queries": f"Current queries ({bucket.replace('_',' ')})",
            "peak_clicks": "Peak clicks",
            "current_clicks": "Current clicks",
            "current_ctr": "Current CTR",
            "current_pos": "Current avg pos",
        })

        pk_col = f"Peak queries ({bucket.replace('_',' ')})"
        ck_col = f"Current queries ({bucket.replace('_',' ')})"
        display_t3[pk_col] = display_t3[pk_col].apply(lambda x: int(x))
        display_t3[ck_col] = display_t3[ck_col].apply(lambda x: int(x))
        display_t3["Current CTR"] = display_t3["Current CTR"].apply(lambda x: f"{x:.2f}%")
        display_t3["Current avg pos"] = display_t3["Current avg pos"].apply(lambda x: f"{x:.1f}")
        display_t3["Peak clicks"] = display_t3["Peak clicks"].apply(lambda x: f"{int(x):,}")
        display_t3["Current clicks"] = display_t3["Current clicks"].apply(lambda x: f"{int(x):,}")

        show_cols = [
            "Cluster",
            f"Peak queries ({bucket.replace('_',' ')})",
            f"Current queries ({bucket.replace('_',' ')})",
            "Δ Queries",
            "Peak clicks", "Current clicks", "Δ Clicks",
            "Current CTR", "Current avg pos",
        ]

        def _delta_q_color(val):
            try:
                v = int(val)
            except Exception:
                return ""
            if v >= 0:
                return "background-color: #d4edda; color: #155724"
            elif v >= -5:
                return "background-color: #fff3cd; color: #856404"
            return "background-color: #f8d7da; color: #721c24"

        st.dataframe(
            display_t3[show_cols]
            .sort_values("Δ Queries")
            .style.map(_delta_q_color, subset=["Δ Queries"]),
            use_container_width=True, hide_index=True, height=500,
        )

        # Clicks trend: all clusters
        st.markdown("#### Clicks trend — all clusters")
        fig_clicks = px.line(
            plot_data, x="month", y="clicks", color="cluster",
            markers=True,
            labels={"clicks": "Clicks", "month": "", "cluster": "Cluster"},
        )
        _add_estimated_bands(fig_clicks, plot_data["month"].unique().tolist(), est_months)
        fig_clicks.update_layout(
            height=400, hovermode="x unified",
            margin=dict(l=0, r=0, t=10, b=0),
            legend=dict(orientation="h", y=-0.15),
        )
        st.plotly_chart(fig_clicks, use_container_width=True)

        # CTR trend: all clusters
        st.markdown("#### CTR trend — all clusters")
        fig_ctr_all = px.line(
            plot_data, x="month", y="ctr", color="cluster",
            markers=True,
            labels={"ctr": "CTR %", "month": "", "cluster": "Cluster"},
        )
        _add_estimated_bands(fig_ctr_all, plot_data["month"].unique().tolist(), est_months)
        fig_ctr_all.update_layout(
            height=400, hovermode="x unified",
            margin=dict(l=0, r=0, t=10, b=0),
            legend=dict(orientation="h", y=-0.15),
        )
        st.plotly_chart(fig_ctr_all, use_container_width=True)


# ═══════════════════════════════════════════════════════════════════════════
# TAB 4 — Query deep dive
# ═══════════════════════════════════════════════════════════════════════════
with tab4:
    st.subheader("Query deep dive")

    col_c, col_m = st.columns(2)
    with col_c:
        q_cluster = st.selectbox("Cluster", clusters, key="t4_cluster")
    with col_m:
        q_month = st.selectbox("Month", list(reversed(months)), key="t4_month")

    is_est_month = q_month in est_months
    if is_est_month:
        st.warning(f"⚠ {q_month} contains estimated data — numbers are interpolated, not from GSC.")

    kw_df = db.keywords_for_cluster(q_cluster, q_month, limit=300)

    if kw_df.empty:
        st.info(f"No keyword data for {q_cluster} in {q_month}.")
    else:
        def _assign_signal(row):
            if row["position"] <= 5 and row["ctr"] < 1.0:
                return "AIO suspect"
            elif row["position"] > 5:
                return "Displaced"
            return "Healthy"

        kw_df["signal"] = kw_df.apply(_assign_signal, axis=1)

        signal_colors = {"Healthy": "#28a745", "AIO suspect": "#dc3545", "Displaced": "#fd7e14"}

        plot_kw = kw_df.copy()
        plot_kw["_size"] = plot_kw["clicks"].clip(lower=1)

        fig = px.scatter(
            plot_kw, x="impressions", y="ctr",
            size="_size", color="signal",
            color_discrete_map=signal_colors,
            hover_name="keyword",
            hover_data={"clicks": True, "impressions": True, "position": True, "_size": False},
            labels={"impressions": "Impressions", "ctr": "CTR (%)", "signal": "Signal"},
            size_max=40,
        )
        fig.add_hline(y=5.0, line_dash="dot", line_color="green",
                      annotation_text="Strong CTR (5%+)")
        fig.add_hline(y=1.0, line_dash="dot", line_color="red",
                      annotation_text="Weak CTR (<1%)")
        fig.update_layout(height=400, margin=dict(l=0, r=0, t=0, b=0))
        st.plotly_chart(fig, use_container_width=True)

        col_f, col_t = st.columns([3, 1])
        with col_f:
            signal_filter = st.multiselect(
                "Filter by signal",
                ["Healthy", "AIO suspect", "Displaced"],
                default=["Healthy", "AIO suspect", "Displaced"],
            )
        with col_t:
            st.metric("Total queries", len(kw_df))

        disp_kw = kw_df[kw_df["signal"].isin(signal_filter)].copy()
        disp_kw["ctr"] = disp_kw["ctr"].apply(lambda x: f"{x:.2f}%")
        disp_kw["position"] = disp_kw["position"].apply(lambda x: f"{x:.1f}")

        def _sig_style(val):
            bg = {"Healthy": "#d4edda", "AIO suspect": "#f8d7da", "Displaced": "#fff3cd"}
            return f"background-color: {bg.get(val, 'white')}"

        st.dataframe(
            disp_kw[["keyword", "clicks", "impressions", "ctr", "position", "signal"]]
            .rename(columns={
                "keyword": "Keyword", "clicks": "Clicks", "impressions": "Impressions",
                "ctr": "CTR", "position": "Position", "signal": "Signal",
            })
            .style.map(_sig_style, subset=["Signal"]),
            use_container_width=True, hide_index=True,
        )

        st.divider()
        st.markdown(
            "**Signal legend**\n\n"
            "- 🟢 **Healthy** — ranking well with good CTR; query is specific enough that AIO can't easily answer it\n"
            "- 🔴 **AIO suspect** — position ≤5 but CTR below 1%. AI Overview or featured snippet is likely "
            "answering the query above your result, stealing the click even though you rank well\n"
            "- 🟠 **Displaced** — pushed below position 5; the original brand, YouTube, or a competitor "
            "has reclaimed the top spot"
        )

        # Movers
        if len(months) >= 2:
            st.divider()
            st.markdown("**Biggest position movers** (impact = impressions × position change)")
            prev_month = months[-2] if q_month == latest else months[max(0, months.index(q_month) - 1)]
            movers = db.keyword_movers(q_cluster, prev_month, q_month, limit=30)
            if not movers.empty:
                movers["pos_delta"] = movers["pos_delta"].apply(
                    lambda x: f"+{x:.1f}" if x > 0 else f"{x:.1f}"
                )
                movers["impact_score"] = movers["impact_score"].apply(lambda x: f"{x:,.0f}")
                st.dataframe(
                    movers[["keyword", "pos_before", "pos_after", "pos_delta", "impressions", "clicks", "impact_score"]]
                    .rename(columns={
                        "keyword": "Keyword", "pos_before": "Pos before",
                        "pos_after": "Pos after", "pos_delta": "Δ Position",
                        "impressions": "Impressions", "clicks": "Clicks",
                        "impact_score": "Impact score",
                    }),
                    use_container_width=True, hide_index=True,
                )


# ═══════════════════════════════════════════════════════════════════════════
# TAB 5 — Page 2 trap (opportunity finder)
# ═══════════════════════════════════════════════════════════════════════════
with tab5:
    st.subheader("Page 2 trap — near-miss opportunities")
    st.caption(
        "Queries ranking position 5–15 with decent impressions but low CTR. "
        "These are close to page 1 or on the edge — a small push (content refresh, "
        "internal link, schema markup) could move them into click-driving positions."
    )

    col_p2c, col_p2m = st.columns(2)
    with col_p2c:
        p2_cluster = st.selectbox(
            "Cluster", ["All clusters"] + clusters, key="t5_cluster"
        )
    with col_p2m:
        p2_month = st.selectbox("Month", list(reversed(months)), key="t5_month")

    col_pos, col_imp = st.columns(2)
    with col_pos:
        p2_pos_range = st.slider(
            "Position range", 3.0, 20.0, (5.0, 15.0), step=0.5, key="t5_pos"
        )
    with col_imp:
        p2_min_imp = st.number_input(
            "Min impressions", min_value=0, value=50, step=10, key="t5_imp"
        )

    cluster_arg = None if p2_cluster == "All clusters" else p2_cluster
    trap_df = db.page2_trap(
        cluster_arg, p2_month,
        pos_min=p2_pos_range[0], pos_max=p2_pos_range[1],
        min_impressions=p2_min_imp, limit=300,
    )

    if trap_df.empty:
        st.info("No queries match these filters.")
    else:
        st.metric("Queries in the trap", len(trap_df))

        # Scatter: impressions vs position, sized by clicks
        plot_trap = trap_df.copy()
        plot_trap["_size"] = plot_trap["impressions"].clip(lower=10)

        fig_trap = px.scatter(
            plot_trap, x="position", y="impressions",
            size="_size", color="cluster",
            hover_name="keyword",
            hover_data={"clicks": True, "ctr": True, "position": ":.1f", "_size": False},
            labels={"position": "Position", "impressions": "Impressions", "cluster": "Cluster"},
            size_max=35,
        )
        fig_trap.add_vline(x=10, line_dash="dot", line_color="gray",
                           annotation_text="Page 1 cutoff")
        fig_trap.update_layout(height=450, margin=dict(l=0, r=0, t=0, b=0))
        st.plotly_chart(fig_trap, use_container_width=True)

        # Table
        disp_trap = trap_df.copy()
        disp_trap["ctr"] = disp_trap["ctr"].apply(lambda x: f"{x:.2f}%")
        disp_trap["position"] = disp_trap["position"].apply(lambda x: f"{x:.1f}")
        disp_trap["top_url_short"] = disp_trap["top_url"].apply(
            lambda x: "/".join(str(x).split("/")[-2:]) if pd.notna(x) and "/" in str(x) else str(x)
        )

        st.dataframe(
            disp_trap[["keyword", "cluster", "clicks", "impressions", "ctr", "position", "top_url_short"]]
            .rename(columns={
                "keyword": "Keyword", "cluster": "Cluster", "clicks": "Clicks",
                "impressions": "Impressions", "ctr": "CTR", "position": "Position",
                "top_url_short": "URL",
            }),
            use_container_width=True, hide_index=True, height=500,
        )

        st.divider()
        st.markdown(
            "**How to use this**\n\n"
            "- Queries at position 5–10 with high impressions → quick wins with a content refresh\n"
            "- Queries at position 10–15 → need a stronger push (new section, internal links, better title)\n"
            "- Sort by impressions to prioritize highest-opportunity queries first\n"
            "- Cross-reference with the query deep dive tab to check if AIO is also suppressing CTR"
        )


# ═══════════════════════════════════════════════════════════════════════════
# TAB 6 — Opportunities (volume-enriched)
# ═══════════════════════════════════════════════════════════════════════════
with tab6:
    st.subheader("Keyword opportunities — ranked by search volume")

    vol_stats = db.volume_coverage_stats()
    st.caption(
        f"Volume data: {vol_stats['with_volume']}/{vol_stats['total']} keywords enriched "
        f"({vol_stats['high_volume']} with volume > 1K). "
        "Opportunity score = volume ÷ current position (higher = bigger upside)."
    )

    col_o1, col_o2 = st.columns(2)
    with col_o1:
        opp_month = st.selectbox("Month", list(reversed(months)), key="t6_month")
    with col_o2:
        opp_min_vol = st.number_input(
            "Min search volume", min_value=0, value=100, step=50, key="t6_vol"
        )

    col_o3, col_o4 = st.columns(2)
    with col_o3:
        opp_pos_range = st.slider(
            "Position range", 1.0, 30.0, (4.0, 20.0), step=0.5, key="t6_pos"
        )
    with col_o4:
        opp_limit = st.number_input(
            "Max results", min_value=10, value=50, step=10, key="t6_limit"
        )

    opp_df = db.top_opportunity_keywords(
        month=opp_month, min_volume=opp_min_vol,
        pos_min=opp_pos_range[0], pos_max=opp_pos_range[1],
        limit=opp_limit,
    )

    if opp_df.empty:
        st.info("No opportunities match these filters. Try lowering the min volume or widening the position range.")
    else:
        col_m1, col_m2, col_m3 = st.columns(3)
        col_m1.metric("Opportunities found", len(opp_df))
        col_m2.metric("Total search volume", f"{opp_df['search_volume'].sum():,.0f}")
        col_m3.metric("Avg position", f"{opp_df['position'].mean():.1f}")

        # Bubble chart: volume vs position, sized by opportunity score
        fig_opp = px.scatter(
            opp_df, x="position", y="search_volume",
            size="opportunity_score", color="cluster",
            hover_name="keyword",
            hover_data={"clicks": True, "impressions": True, "difficulty": True,
                        "opportunity_score": ":.0f", "search_volume": ":,"},
            labels={"position": "Current position", "search_volume": "Monthly search volume",
                    "cluster": "Cluster"},
            size_max=40,
        )
        fig_opp.update_layout(
            height=500, margin=dict(l=0, r=0, t=30, b=0),
            yaxis_type="log",
        )
        fig_opp.add_vline(x=10, line_dash="dot", line_color="gray",
                          annotation_text="Page 1 cutoff")
        st.plotly_chart(fig_opp, use_container_width=True)

        # Table
        disp_opp = opp_df.copy()
        disp_opp["position"] = disp_opp["position"].apply(lambda x: f"{x:.1f}")
        disp_opp["search_volume"] = disp_opp["search_volume"].apply(lambda x: f"{x:,}")
        disp_opp["opportunity_score"] = disp_opp["opportunity_score"].apply(lambda x: f"{x:,.0f}")
        disp_opp["url_short"] = disp_opp["top_url"].apply(
            lambda x: "/".join(str(x).split("/")[-2:]) if pd.notna(x) and "/" in str(x) else str(x)
        )

        st.dataframe(
            disp_opp[["keyword", "cluster", "search_volume", "position", "difficulty",
                       "clicks", "impressions", "opportunity_score", "url_short"]]
            .rename(columns={
                "keyword": "Keyword", "cluster": "Cluster", "search_volume": "Volume",
                "position": "Position", "difficulty": "KD", "clicks": "Clicks",
                "impressions": "Impressions", "opportunity_score": "Opp. score",
                "url_short": "URL",
            }),
            use_container_width=True, hide_index=True, height=500,
        )

        st.divider()
        st.markdown(
            "**How to use this**\n\n"
            "- **High volume + position 4–10**: Quick wins — already on page 1, improve content to climb\n"
            "- **High volume + position 11–20**: Need a bigger push — content refresh, internal links, schema\n"
            "- **Low difficulty + high volume**: Best ROI — easier to rank for with less effort\n"
            "- Sort by opportunity score to find the highest-impact keywords to prioritize"
        )

    # Volume-enriched keyword table
    st.divider()
    st.subheader("All keywords with search volume")

    vol_cluster = st.selectbox(
        "Filter by cluster", ["All clusters"] + clusters, key="t6_vol_cluster"
    )
    vol_cluster_arg = None if vol_cluster == "All clusters" else vol_cluster
    vol_kw_df = db.keywords_with_volume(cluster=vol_cluster_arg, month=opp_month, limit=500)

    if not vol_kw_df.empty:
        disp_vol = vol_kw_df.copy()
        disp_vol["position"] = disp_vol["position"].apply(lambda x: f"{x:.1f}")
        disp_vol["ctr"] = disp_vol["ctr"].apply(lambda x: f"{x:.2f}%")
        disp_vol["search_volume"] = disp_vol["search_volume"].apply(lambda x: f"{x:,}")

        st.dataframe(
            disp_vol[["keyword", "cluster", "search_volume", "position", "clicks",
                       "impressions", "ctr"]]
            .rename(columns={
                "keyword": "Keyword", "cluster": "Cluster", "search_volume": "Volume",
                "position": "Position", "clicks": "Clicks", "impressions": "Impressions",
                "ctr": "CTR",
            }),
            use_container_width=True, hide_index=True, height=400,
        )


# ═══════════════════════════════════════════════════════════════════════════
# TAB 7 — Lost to (competitor analysis)
# ═══════════════════════════════════════════════════════════════════════════
with tab7:
    st.subheader("Lost to — who's outranking Storylane")
    st.caption(
        "Competitor analysis based on organic keyword overlap and SERP position data. "
        "Shows which domains consistently rank above Storylane tutorials."
    )

    # ── Organic competitors overview ──
    comp_df = db.organic_competitors_summary()
    if not comp_df.empty:
        st.markdown("#### Organic competitors (by shared keywords)")

        fig_comp = px.bar(
            comp_df.head(15),
            x="keywords_common", y="competitor_domain",
            orientation="h",
            color="domain_rating",
            color_continuous_scale="RdYlGn",
            hover_data={"traffic": ":,", "share": ":.1f", "domain_rating": ":.0f"},
            labels={"keywords_common": "Shared keywords", "competitor_domain": "",
                    "domain_rating": "DR"},
        )
        fig_comp.update_layout(
            height=400, margin=dict(l=0, r=0, t=10, b=0),
            yaxis=dict(autorange="reversed"),
        )
        st.plotly_chart(fig_comp, use_container_width=True)

        disp_comp = comp_df.copy()
        disp_comp["traffic"] = disp_comp["traffic"].apply(lambda x: f"{x:,}")
        disp_comp["share"] = disp_comp["share"].apply(lambda x: f"{x:.1f}%")
        disp_comp["domain_rating"] = disp_comp["domain_rating"].apply(lambda x: f"{x:.0f}")
        st.dataframe(
            disp_comp.rename(columns={
                "competitor_domain": "Domain", "keywords_common": "Shared KWs",
                "keywords_competitor": "Their total KWs", "traffic": "Their traffic",
                "domain_rating": "DR", "share": "KW share",
            }),
            use_container_width=True, hide_index=True,
        )

    # ── SERP domain breakdown ──
    st.divider()
    st.markdown("#### SERP competitors (who appears in top 10 for our keywords)")

    serp_domains = db.serp_domain_analysis()
    if not serp_domains.empty:
        fig_serp = px.scatter(
            serp_domains,
            x="avg_position", y="keywords_covered",
            size="appearances", color="avg_dr",
            hover_name="domain",
            hover_data={"top3_count": True, "page1_count": True, "avg_dr": ":.0f"},
            color_continuous_scale="RdYlGn",
            labels={"avg_position": "Avg SERP position", "keywords_covered": "Keywords covered",
                    "avg_dr": "Avg DR"},
            size_max=40,
        )
        fig_serp.update_layout(height=400, margin=dict(l=0, r=0, t=10, b=0))
        st.plotly_chart(fig_serp, use_container_width=True)

        st.dataframe(
            serp_domains.rename(columns={
                "domain": "Domain", "appearances": "Appearances",
                "keywords_covered": "Keywords", "avg_position": "Avg pos",
                "top3_count": "Top 3", "page1_count": "Page 1", "avg_dr": "DR",
            }),
            use_container_width=True, hide_index=True,
        )

    # ── "Lost to" detail ──
    st.divider()
    st.markdown("#### Who ranks above us (per keyword)")

    lost_df = db.lost_to_summary()
    if not lost_df.empty:
        col_l1, col_l2 = st.columns(2)
        col_l1.metric("Keywords with competitors above us", lost_df["keyword"].nunique())
        col_l2.metric("Domains beating us", lost_df["domain"].nunique())

        # Aggregate: which domains beat us most
        domain_beats = (
            lost_df.groupby("domain")
            .agg(keywords_beating=("keyword", "nunique"),
                 avg_positions_ahead=("positions_ahead", "mean"),
                 total_volume=("search_volume", "sum"))
            .sort_values("keywords_beating", ascending=False)
            .reset_index()
        )
        domain_beats["avg_positions_ahead"] = domain_beats["avg_positions_ahead"].round(1)

        fig_beats = px.bar(
            domain_beats.head(10),
            x="keywords_beating", y="domain",
            orientation="h",
            color="avg_positions_ahead",
            color_continuous_scale="Reds_r",
            hover_data={"total_volume": ":,"},
            labels={"keywords_beating": "Keywords where they beat us", "domain": "",
                    "avg_positions_ahead": "Avg positions ahead"},
        )
        fig_beats.update_layout(
            height=350, margin=dict(l=0, r=0, t=10, b=0),
            yaxis=dict(autorange="reversed"),
        )
        st.plotly_chart(fig_beats, use_container_width=True)

        # Detail table
        disp_lost = lost_df.copy()
        disp_lost["search_volume"] = disp_lost["search_volume"].fillna(0).astype(int).apply(lambda x: f"{x:,}")
        st.dataframe(
            disp_lost[["keyword", "domain", "their_position", "our_position",
                        "positions_ahead", "search_volume", "domain_rating"]]
            .rename(columns={
                "keyword": "Keyword", "domain": "Beating domain",
                "their_position": "Their pos", "our_position": "Our pos",
                "positions_ahead": "Gap", "search_volume": "Volume",
                "domain_rating": "Their DR",
            }),
            use_container_width=True, hide_index=True, height=500,
        )
    else:
        st.info("No SERP snapshot data with Storylane rankings found. "
                "Run more SERP pulls to populate this view.")

    # ── SERP deep dive per keyword ──
    st.divider()
    st.markdown("#### SERP deep dive")
    serp_keywords = db.available_serp_keywords()
    if serp_keywords:
        selected_kw = st.selectbox("Keyword", serp_keywords, key="t7_kw")
        kw_serp = db.serp_keyword_detail(selected_kw)
        if not kw_serp.empty:
            kw_serp["highlight"] = kw_serp["is_storylane"].apply(
                lambda x: "🟢 Storylane" if x == 1 else ""
            )
            kw_serp["url_short"] = kw_serp["url"].apply(
                lambda x: x[:80] + "..." if len(str(x)) > 80 else x
            )
            st.dataframe(
                kw_serp[["position", "domain", "highlight", "domain_rating", "traffic", "url_short"]]
                .rename(columns={
                    "position": "Pos", "domain": "Domain", "highlight": "",
                    "domain_rating": "DR", "traffic": "Traffic", "url_short": "URL",
                }),
                use_container_width=True, hide_index=True,
            )

    st.divider()
    st.markdown(
        "**How to use this**\n\n"
        "- **Organic competitors**: shows who competes for the same keywords at the domain level\n"
        "- **SERP competitors**: shows who actually appears in top 10 for our tracked keywords\n"
        "- **Lost to detail**: for each keyword, exactly which domains rank above Storylane\n"
        "- Focus on domains with low DR that outrank you — they're beatable with better content\n"
        "- High-volume keywords where we're behind are the best targets for content refreshes"
    )


# ── Footer ───────────────────────────────────────────────────────────────
st.divider()
vol_stats = db.volume_coverage_stats()
st.caption(
    f"📊 Data covers {months[0]} to {months[-1]} · All data from GSC exports · "
    f"{vol_stats['with_volume']} keywords enriched with search volume"
)
