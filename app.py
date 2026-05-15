import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

import db

st.set_page_config(page_title="Storylane SEO Dashboard", layout="wide", page_icon="📊")
st.title("Storylane · Demo-led SEO Dashboard")
st.caption("Phase 1 + Phase 2 cluster performance · Google Search Console data")

# ── Guard ─────────────────────────────────────────────────────────────────────
if not db.has_data():
    st.warning(
        "No data in database yet. "
        "Populate `data/pages/` and `data/keywords/` with monthly JSON files, "
        "then run `python ingest.py`."
    )
    st.stop()

# ── Shared state ──────────────────────────────────────────────────────────────
months   = db.available_months()
clusters = db.available_clusters()
latest   = months[-1]
earliest = months[0]


def _ctr_color(val):
    try:
        v = float(str(val).replace("%", ""))
    except Exception:
        return ""
    if v >= 1.5:
        return "background-color: #d4edda; color: #155724"
    elif v >= 0.5:
        return "background-color: #fff3cd; color: #856404"
    return "background-color: #f8d7da; color: #721c24"


tab1, tab2, tab3, tab4 = st.tabs([
    "📊 Cluster Overview",
    "🎯 Position Health",
    "📉 AIO Signature",
    "🔍 Query Deep Dive",
])

# ─────────────────────────────────────────────────────────────────────────────
# TAB 1 — Cluster Overview
# ─────────────────────────────────────────────────────────────────────────────
with tab1:
    st.subheader("Cluster Overview")

    last3_start = months[-3] if len(months) >= 3 else earliest
    period_options = {
        "Post-peak Q1'25":  ("2025-01", "2025-04"),
        "Q1'26":            ("2026-01", "2026-03"),
        f"Last 3 months ({last3_start} – {latest})": (last3_start, latest),
        f"Current ({latest})": (latest, latest),
    }

    selected_period = st.selectbox("Period", list(period_options.keys()), index=2)
    start, end = period_options[selected_period]

    summary = db.cluster_summary(periods={selected_period: (start, end)})
    summary = summary[summary["period"] == selected_period].drop(columns=["period"])

    if summary.empty:
        st.info(f"No data for the selected period ({start} → {end}).")
    else:
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Total Clicks",      f"{summary['clicks'].sum():,.0f}")
        col2.metric("Total Impressions", f"{summary['impressions'].sum() / 1e6:.1f}M")
        total_ctr = (
            summary["clicks"].sum() / summary["impressions"].sum() * 100
            if summary["impressions"].sum() > 0 else 0.0
        )
        col3.metric("Avg CTR",          f"{total_ctr:.2f}%")
        col4.metric("Clusters Tracked", len(summary))

        st.divider()

        disp = summary.copy()
        disp["CTR"]          = disp["ctr"].apply(lambda x: f"{x:.2f}%")
        disp["Impressions"]  = disp["impressions"].apply(lambda x: f"{x:,.0f}")
        disp["Clicks"]       = disp["clicks"].apply(lambda x: f"{x:,.0f}")
        disp["Avg Position"] = disp["avg_position"].apply(lambda x: f"{x:.1f}")

        styled = (
            disp[["cluster", "Clicks", "Impressions", "CTR", "Avg Position", "pages"]]
            .rename(columns={"cluster": "Cluster", "pages": "Pages"})
            .style.applymap(_ctr_color, subset=["CTR"])
        )
        st.dataframe(styled, use_container_width=True, hide_index=True)

        st.divider()
        col_a, col_b = st.columns(2)

        with col_a:
            st.markdown("**Clicks by Cluster**")
            fig = px.bar(
                summary.sort_values("clicks", ascending=True),
                x="clicks", y="cluster", orientation="h",
                color="ctr",
                color_continuous_scale=["#dc3545", "#ffc107", "#28a745"],
                range_color=[0, 3],
                labels={"clicks": "Clicks", "cluster": "", "ctr": "CTR %"},
            )
            fig.update_layout(
                height=500, margin=dict(l=0, r=0, t=0, b=0),
                coloraxis_colorbar=dict(title="CTR %"),
            )
            st.plotly_chart(fig, use_container_width=True)

        with col_b:
            st.markdown("**CTR vs Impressions · Bubble = Clicks**")
            plot_df = summary[summary["clicks"] > 0].copy()
            fig2 = px.scatter(
                plot_df,
                x="impressions", y="ctr",
                size="clicks", color="cluster",
                hover_name="cluster",
                labels={"impressions": "Impressions", "ctr": "CTR (%)"},
                size_max=50,
            )
            fig2.add_hline(y=1.5, line_dash="dash", line_color="green",
                           annotation_text="Healthy CTR (1.5%)")
            fig2.add_hline(y=0.5, line_dash="dash", line_color="red",
                           annotation_text="Danger zone (0.5%)")
            fig2.update_layout(height=500, margin=dict(l=0, r=0, t=0, b=0))
            st.plotly_chart(fig2, use_container_width=True)

# ─────────────────────────────────────────────────────────────────────────────
# TAB 2 — Position Health
# ─────────────────────────────────────────────────────────────────────────────
with tab2:
    st.subheader("Position Health · Ranking Tracker")
    st.caption("Number of queries in each ranking bucket, tracked month by month.")

    t2_cluster = st.selectbox("Cluster", clusters, key="t2_cluster")
    pos_df = db.position_distribution_over_time(t2_cluster)

    if pos_df.empty:
        st.info("No keyword data for this cluster yet.")
    else:
        fig = go.Figure()
        bucket_cfg = [
            ("top_1",  "Top 1.5 (absolute #1)", "#0d6efd"),
            ("top_3",  "Top 3",                 "#198754"),
            ("top_5",  "Top 5",                 "#ffc107"),
            ("top_10", "Top 10",                "#6c757d"),
        ]
        for col, label, color in bucket_cfg:
            if col in pos_df.columns:
                fig.add_trace(go.Scatter(
                    x=pos_df["month"], y=pos_df[col],
                    name=label,
                    line=dict(color=color, width=2),
                    mode="lines+markers",
                ))

        fig.update_layout(
            height=380, hovermode="x unified",
            margin=dict(l=0, r=0, t=0, b=0),
            yaxis_title="Query count",
            legend=dict(orientation="h", y=-0.18),
        )
        st.plotly_chart(fig, use_container_width=True)

        st.divider()
        st.markdown("**Peak vs Current · Retention by Bucket**")

        peak_row = pos_df.loc[pos_df["top_1"].idxmax()]
        curr_row = pos_df.iloc[-1]

        ret_rows = []
        for col, label in [("top_1", "Top 1.5"), ("top_3", "Top 3"),
                            ("top_5", "Top 5"),   ("top_10", "Top 10")]:
            peak_val = int(peak_row[col])
            curr_val = int(curr_row[col])
            pct = round(curr_val / peak_val * 100, 1) if peak_val > 0 else 100.0
            ret_rows.append({
                "Bucket":    label,
                "Peak":      peak_val,
                "Current":   curr_val,
                "Retention": f"{pct:.0f}%",
            })

        def _ret_color(val):
            try:
                v = float(str(val).replace("%", ""))
            except Exception:
                return ""
            if v >= 70:   return "background-color: #d4edda; color: #155724"
            elif v >= 40: return "background-color: #fff3cd; color: #856404"
            return "background-color: #f8d7da; color: #721c24"

        st.dataframe(
            pd.DataFrame(ret_rows).style.applymap(_ret_color, subset=["Retention"]),
            use_container_width=True, hide_index=True,
        )

# ─────────────────────────────────────────────────────────────────────────────
# TAB 3 — AIO Signature Detector (all clusters summary + drill-down)
# ─────────────────────────────────────────────────────────────────────────────
with tab3:
    st.subheader("AIO Signature Detector")
    st.caption(
        "Position stable + CTR collapsed → AI Overview stealing clicks.  "
        "Both dropped → brand displacement. Select a cluster to see the full trend."
    )

    peak_period = ("2025-01", "2025-04")
    curr_period = (latest, latest)

    aio_raw = db.cluster_summary(periods={
        "Peak Q1'25": peak_period,
        "Current":    curr_period,
    })

    if aio_raw.empty:
        st.info("Not enough data to compute AIO signals.")
    else:
        peak_df = aio_raw[aio_raw["period"] == "Peak Q1'25"].set_index("cluster")
        curr_df = aio_raw[aio_raw["period"] == "Current"].set_index("cluster")

        signal_rows = []
        for c in curr_df.index:
            curr = curr_df.loc[c]
            peak = peak_df.loc[c] if c in peak_df.index else None

            ctr_drop  = 0.0
            pos_delta = 0.0
            if peak is not None and peak["ctr"] > 0:
                ctr_drop = (peak["ctr"] - curr["ctr"]) / peak["ctr"] * 100
            if peak is not None:
                pos_delta = curr["avg_position"] - peak["avg_position"]

            if ctr_drop > 40 and pos_delta <= 2:
                signal = "🔴 AIO"
            elif ctr_drop > 40 and pos_delta > 2:
                signal = "🟡 Displaced"
            elif ctr_drop > 20:
                signal = "🟠 Declining"
            else:
                signal = "🟢 Healthy"

            signal_rows.append({
                "cluster":      c,
                "Signal":       signal,
                "Clicks":       int(curr["clicks"]),
                "CTR":          f"{curr['ctr']:.2f}%",
                "CTR Drop":     f"-{ctr_drop:.0f}%" if ctr_drop > 0 else "—",
                "Position Δ":   f"+{pos_delta:.1f}" if pos_delta > 0 else f"{pos_delta:.1f}",
            })

        sig_df = (
            pd.DataFrame(signal_rows)
            .sort_values("Clicks", ascending=False)
            .rename(columns={"cluster": "Cluster"})
        )

        def _sig_color(val):
            if "AIO"       in str(val): return "background-color: #f8d7da"
            if "Displaced" in str(val): return "background-color: #fff3cd"
            if "Declining" in str(val): return "background-color: #fff9e6"
            return "background-color: #d4edda"

        st.dataframe(
            sig_df[["Cluster", "Signal", "Clicks", "CTR", "CTR Drop", "Position Δ"]]
            .style.applymap(_sig_color, subset=["Signal"]),
            use_container_width=True, hide_index=True,
        )

        st.divider()
        st.markdown("**Cluster Deep-Dive**")
        t3_cluster = st.selectbox("Select cluster", clusters, key="t3_cluster")
        trend_df   = db.cluster_monthly_trends(t3_cluster)

        if trend_df.empty:
            st.info("No monthly data for this cluster.")
        else:
            fig = make_subplots(
                rows=3, cols=1, shared_xaxes=True,
                subplot_titles=("Clicks", "CTR (%) vs Avg Position", "Impressions"),
                vertical_spacing=0.08,
            )
            fig.add_trace(go.Scatter(
                x=trend_df["month"], y=trend_df["clicks"],
                name="Clicks", line=dict(color="#0d6efd", width=2),
                fill="tozeroy", fillcolor="rgba(13,110,253,0.1)",
            ), row=1, col=1)
            fig.add_trace(go.Scatter(
                x=trend_df["month"], y=trend_df["ctr"],
                name="CTR %", line=dict(color="#dc3545", width=2),
            ), row=2, col=1)
            fig.add_trace(go.Scatter(
                x=trend_df["month"], y=trend_df["avg_position"],
                name="Avg Position", line=dict(color="#198754", width=2, dash="dash"),
            ), row=2, col=1)
            fig.add_trace(go.Scatter(
                x=trend_df["month"], y=trend_df["impressions"],
                name="Impressions", line=dict(color="#6c757d", width=2),
                fill="tozeroy", fillcolor="rgba(108,117,125,0.1)",
            ), row=3, col=1)

            fig.update_layout(
                height=580, hovermode="x unified",
                margin=dict(l=0, r=0, t=30, b=0),
                legend=dict(orientation="h", y=-0.05),
            )
            fig.update_yaxes(title_text="Clicks",      row=1, col=1)
            fig.update_yaxes(title_text="CTR %",       row=2, col=1)
            fig.update_yaxes(title_text="Impressions", row=3, col=1)
            st.plotly_chart(fig, use_container_width=True)

            latest_row = trend_df.iloc[-1]
            peak_ctr   = trend_df["ctr"].max()
            peak_pos   = trend_df["avg_position"].min()
            ctr_drop_v = (peak_ctr - latest_row["ctr"]) / peak_ctr * 100 if peak_ctr > 0 else 0
            pos_chg_v  = latest_row["avg_position"] - peak_pos

            d1, d2, d3 = st.columns(3)
            d1.metric("CTR drop from peak",        f"-{ctr_drop_v:.0f}%",  delta_color="inverse")
            d2.metric("Position change from peak", f"+{pos_chg_v:.1f}",    delta_color="inverse")
            d3.metric("Impressions (latest)",      f"{latest_row['impressions']:,.0f}")

            if pos_chg_v <= 2 and ctr_drop_v > 40:
                st.error("🔴 AIO Interception — position held but CTR collapsed. Content changes won't fix this.")
            elif pos_chg_v > 4 and ctr_drop_v > 40:
                st.warning("🟡 Brand displacement + possible AIO — both position and CTR declined.")
            else:
                st.success("🟢 Cluster appears healthy or early-stage decline.")

# ─────────────────────────────────────────────────────────────────────────────
# TAB 4 — Query Deep Dive
# ─────────────────────────────────────────────────────────────────────────────
with tab4:
    st.subheader("Query Deep Dive · Per Cluster")

    col_c, col_m = st.columns(2)
    with col_c:
        q_cluster = st.selectbox("Cluster", clusters, key="t4_cluster")
    with col_m:
        q_month = st.selectbox("Month", list(reversed(months)), key="t4_month")

    kw_df = db.keywords_for_cluster(q_cluster, q_month, limit=300)

    if kw_df.empty:
        st.info(f"No keyword data for {q_cluster} in {q_month}.")
    else:
        def _assign_signal(row):
            if row["position"] <= 5 and row["ctr"] < 1.0:
                return "AIO"
            elif row["position"] > 5:
                return "Displaced"
            return "Healthy"

        kw_df["signal"] = kw_df.apply(_assign_signal, axis=1)

        signal_colors = {"Healthy": "#28a745", "AIO": "#dc3545", "Displaced": "#fd7e14"}

        plot_kw = kw_df.copy()
        plot_kw["_size"] = plot_kw["clicks"].clip(lower=1)

        fig = px.scatter(
            plot_kw,
            x="impressions", y="ctr",
            size="_size",
            color="signal",
            color_discrete_map=signal_colors,
            hover_name="keyword",
            hover_data={"clicks": True, "impressions": True, "position": True, "_size": False},
            labels={"impressions": "Impressions", "ctr": "CTR (%)", "signal": "Signal"},
            size_max=40,
        )
        fig.add_hline(y=5.0, line_dash="dot", line_color="green",
                      annotation_text="Strong CTR (5%+)")
        fig.add_hline(y=1.0, line_dash="dot", line_color="red",
                      annotation_text="Weak CTR (1%)")
        fig.update_layout(height=400, margin=dict(l=0, r=0, t=0, b=0))
        st.plotly_chart(fig, use_container_width=True)

        col_f, col_t = st.columns([3, 1])
        with col_f:
            signal_filter = st.multiselect(
                "Filter by signal",
                ["Healthy", "AIO", "Displaced"],
                default=["Healthy", "AIO", "Displaced"],
            )
        with col_t:
            st.metric("Total queries", len(kw_df))

        disp_kw = kw_df[kw_df["signal"].isin(signal_filter)].copy()
        disp_kw["ctr"]      = disp_kw["ctr"].apply(lambda x: f"{x:.2f}%")
        disp_kw["position"] = disp_kw["position"].apply(lambda x: f"{x:.1f}")

        def _sig_style(val):
            bg = {"Healthy": "#d4edda", "AIO": "#f8d7da", "Displaced": "#fff3cd"}
            return f"background-color: {bg.get(val, 'white')}"

        st.dataframe(
            disp_kw[["keyword", "clicks", "impressions", "ctr", "position", "signal"]]
            .rename(columns={
                "keyword": "Keyword", "clicks": "Clicks", "impressions": "Impressions",
                "ctr": "CTR", "position": "Position", "signal": "Signal",
            })
            .style.applymap(_sig_style, subset=["Signal"]),
            use_container_width=True, hide_index=True,
        )

        st.divider()
        st.markdown(
            "🟢 **Healthy** — specific enough that AIO can't intercept  \n"
            "🔴 **AIO** — ranks well but CTR collapsed, AI Overview answers above  \n"
            "🟠 **Displaced** — pushed to page 2+ by brand or competitor"
        )
