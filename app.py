import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from sample_data import CLUSTER_SUMMARY, POSITION_DISTRIBUTION, MONTHLY_TRENDS, TOP_QUERIES

st.set_page_config(page_title="Storylane SEO Dashboard", layout="wide", page_icon="📊")

st.title("Storylane · Demo-led SEO Dashboard")
st.caption("Phase 1 + Phase 2 cluster performance · Google Search Console data")

# ── Tabs ──────────────────────────────────────────────────────────────────────
tab1, tab2, tab3, tab4 = st.tabs([
    "📊 Cluster Overview",
    "🎯 Position Health",
    "📉 AIO Signature",
    "🔍 Query Deep Dive",
])

# ─────────────────────────────────────────────────────────────────────────────
# TAB 1: Cluster Overview
# ─────────────────────────────────────────────────────────────────────────────
with tab1:
    st.subheader("All Clusters · Last 3 Months")

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Clicks",      f"{CLUSTER_SUMMARY['clicks'].sum():,.0f}")
    col2.metric("Total Impressions", f"{CLUSTER_SUMMARY['impressions'].sum()/1e6:.1f}M")
    col3.metric("Avg CTR",           f"{(CLUSTER_SUMMARY['clicks'].sum() / CLUSTER_SUMMARY['impressions'].sum() * 100):.2f}%")
    col4.metric("Clusters Tracked",  len(CLUSTER_SUMMARY))

    st.divider()

    # Color-code CTR: green > 1.5%, yellow 0.5–1.5%, red < 0.5%
    def ctr_color(val):
        if val >= 1.5:
            return "background-color: #d4edda; color: #155724"
        elif val >= 0.5:
            return "background-color: #fff3cd; color: #856404"
        else:
            return "background-color: #f8d7da; color: #721c24"

    display_df = CLUSTER_SUMMARY.copy()
    display_df["impressions"] = display_df["impressions"].apply(lambda x: f"{x:,.0f}")
    display_df["clicks"]      = display_df["clicks"].apply(lambda x: f"{x:,.0f}")
    display_df["ctr_display"] = display_df["ctr"].apply(lambda x: f"{x:.2f}%")
    display_df["avg_position"] = display_df["avg_position"].apply(lambda x: f"{x:.1f}")

    styled = (
        display_df[["cluster","clicks","impressions","ctr_display","avg_position"]]
        .rename(columns={"cluster":"Cluster","clicks":"Clicks","impressions":"Impressions",
                         "ctr_display":"CTR","avg_position":"Avg Position"})
        .style.applymap(ctr_color, subset=["CTR"])
    )
    st.dataframe(styled, use_container_width=True, hide_index=True)

    st.divider()

    col_a, col_b = st.columns(2)

    with col_a:
        st.markdown("**Clicks by Cluster**")
        fig = px.bar(
            CLUSTER_SUMMARY.sort_values("clicks", ascending=True),
            x="clicks", y="cluster", orientation="h",
            color="ctr",
            color_continuous_scale=["#dc3545","#ffc107","#28a745"],
            range_color=[0, 3],
            labels={"clicks":"Clicks","cluster":"","ctr":"CTR %"},
        )
        fig.update_layout(height=480, margin=dict(l=0,r=0,t=0,b=0),
                          coloraxis_colorbar=dict(title="CTR %"))
        st.plotly_chart(fig, use_container_width=True)

    with col_b:
        st.markdown("**CTR vs Impressions · Bubble = Clicks**")
        fig2 = px.scatter(
            CLUSTER_SUMMARY,
            x="impressions", y="ctr",
            size="clicks", color="cluster",
            hover_name="cluster",
            labels={"impressions":"Impressions","ctr":"CTR (%)"},
            size_max=50,
        )
        fig2.add_hline(y=1.5, line_dash="dash", line_color="green",
                       annotation_text="Healthy CTR (1.5%)")
        fig2.add_hline(y=0.5, line_dash="dash", line_color="red",
                       annotation_text="Danger zone (0.5%)")
        fig2.update_layout(height=480, margin=dict(l=0,r=0,t=0,b=0))
        st.plotly_chart(fig2, use_container_width=True)

# ─────────────────────────────────────────────────────────────────────────────
# TAB 2: Position Health — the key metric
# ─────────────────────────────────────────────────────────────────────────────
with tab2:
    st.subheader("Position Distribution · Now vs Peak")
    st.caption("Top 1.5 = absolute #1 rankings. Small shifts here cause most of the click loss.")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**Top 1.5 Queries (Absolute #1) — Now vs Peak**")
        fig = go.Figure()
        fig.add_bar(
            name="Peak",
            x=POSITION_DISTRIBUTION["cluster"],
            y=POSITION_DISTRIBUTION["peak_top_1_5"],
            marker_color="#6c757d",
        )
        fig.add_bar(
            name="Now",
            x=POSITION_DISTRIBUTION["cluster"],
            y=POSITION_DISTRIBUTION["top_1_5"],
            marker_color="#0d6efd",
        )
        fig.update_layout(barmode="group", height=380,
                          margin=dict(l=0,r=0,t=0,b=0),
                          yaxis_title="Query count")
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.markdown("**Top 3 Queries — Now vs Peak**")
        fig2 = go.Figure()
        fig2.add_bar(
            name="Peak",
            x=POSITION_DISTRIBUTION["cluster"],
            y=POSITION_DISTRIBUTION["peak_top_3"],
            marker_color="#6c757d",
        )
        fig2.add_bar(
            name="Now",
            x=POSITION_DISTRIBUTION["cluster"],
            y=POSITION_DISTRIBUTION["top_3"],
            marker_color="#198754",
        )
        fig2.update_layout(barmode="group", height=380,
                           margin=dict(l=0,r=0,t=0,b=0),
                           yaxis_title="Query count")
        st.plotly_chart(fig2, use_container_width=True)

    st.divider()
    st.markdown("**Retention Rate: Top 1.5 queries kept vs peak**")
    pos_df = POSITION_DISTRIBUTION.copy()
    pos_df["retention_pct"] = (pos_df["top_1_5"] / pos_df["peak_top_1_5"] * 100).round(1)
    pos_df["retention_label"] = pos_df["retention_pct"].apply(lambda x: f"{x:.0f}%")

    def retention_color(val):
        if val >= 70:
            return "background-color: #d4edda; color: #155724"
        elif val >= 40:
            return "background-color: #fff3cd; color: #856404"
        else:
            return "background-color: #f8d7da; color: #721c24"

    ret_display = pos_df[["cluster","peak_top_1_5","top_1_5","retention_label"]].rename(
        columns={"cluster":"Cluster","peak_top_1_5":"Peak #1s",
                 "top_1_5":"Current #1s","retention_label":"Retention"}
    )
    st.dataframe(
        ret_display.style.applymap(retention_color, subset=["Retention"]),
        use_container_width=True, hide_index=True
    )

# ─────────────────────────────────────────────────────────────────────────────
# TAB 3: AIO Signature Detector
# ─────────────────────────────────────────────────────────────────────────────
with tab3:
    st.subheader("AIO Signature Detector")
    st.caption(
        "If position holds or improves while CTR drops → AI Overview interception. "
        "If both position and CTR drop → brand displacement or staleness."
    )

    cluster_choice = st.selectbox("Select cluster", list(MONTHLY_TRENDS.keys()))
    df = MONTHLY_TRENDS[cluster_choice]

    fig = make_subplots(
        rows=3, cols=1, shared_xaxes=True,
        subplot_titles=("Clicks", "CTR (%) vs Avg Position", "Impressions"),
        vertical_spacing=0.08,
    )

    fig.add_trace(go.Scatter(
        x=df["month"], y=df["clicks"],
        name="Clicks", line=dict(color="#0d6efd", width=2),
        fill="tozeroy", fillcolor="rgba(13,110,253,0.1)"
    ), row=1, col=1)

    fig.add_trace(go.Scatter(
        x=df["month"], y=df["ctr"],
        name="CTR %", line=dict(color="#dc3545", width=2)
    ), row=2, col=1)
    fig.add_trace(go.Scatter(
        x=df["month"], y=df["avg_position"],
        name="Avg Position", line=dict(color="#198754", width=2, dash="dash"),
        yaxis="y4"
    ), row=2, col=1)

    fig.add_trace(go.Scatter(
        x=df["month"], y=df["impressions"],
        name="Impressions", line=dict(color="#6c757d", width=2),
        fill="tozeroy", fillcolor="rgba(108,117,125,0.1)"
    ), row=3, col=1)

    fig.update_layout(
        height=580,
        margin=dict(l=0, r=0, t=30, b=0),
        hovermode="x unified",
        legend=dict(orientation="h", y=-0.05),
    )
    fig.update_yaxes(title_text="Clicks", row=1, col=1)
    fig.update_yaxes(title_text="CTR %", row=2, col=1)
    fig.update_yaxes(title_text="Impressions", row=3, col=1)

    st.plotly_chart(fig, use_container_width=True)

    # Diagnosis
    latest = df.iloc[-1]
    peak_ctr = df["ctr"].max()
    peak_pos = df["avg_position"].min()
    ctr_drop = (peak_ctr - latest["ctr"]) / peak_ctr * 100
    pos_change = latest["avg_position"] - peak_pos

    st.divider()
    st.markdown("**Auto-diagnosis**")
    d1, d2, d3 = st.columns(3)
    d1.metric("CTR drop from peak", f"-{ctr_drop:.0f}%", delta_color="inverse")
    d2.metric("Position change from peak", f"+{pos_change:.1f}", delta_color="inverse")
    d3.metric("Impressions (latest)", f"{latest['impressions']:,.0f}")

    if pos_change <= 2 and ctr_drop > 40:
        st.error("🔴 AIO Interception likely — position held but CTR collapsed. Content changes won't fix this.")
    elif pos_change > 4 and ctr_drop > 40:
        st.warning("🟡 Brand displacement + possible AIO — both position and CTR declined. Check who took top 3.")
    else:
        st.success("🟢 Cluster appears healthy or early-stage decline.")

# ─────────────────────────────────────────────────────────────────────────────
# TAB 4: Query Deep Dive
# ─────────────────────────────────────────────────────────────────────────────
with tab4:
    st.subheader("Query Deep Dive · Per Cluster")

    q_cluster = st.selectbox("Select cluster", list(TOP_QUERIES.keys()), key="query_tab")
    qdf = TOP_QUERIES[q_cluster].copy()

    signal_colors = {"Healthy": "#28a745", "AIO": "#dc3545", "Displaced": "#fd7e14"}

    fig = px.scatter(
        qdf,
        x="impressions", y="ctr",
        size="clicks",
        color="signal",
        color_discrete_map=signal_colors,
        hover_name="query",
        hover_data={"clicks": True, "impressions": True, "position": True},
        labels={"impressions": "Impressions", "ctr": "CTR (%)", "signal": "Signal"},
        size_max=40,
    )
    fig.add_hline(y=5, line_dash="dot", line_color="green",
                  annotation_text="Strong CTR (5%+)")
    fig.add_hline(y=1, line_dash="dot", line_color="red",
                  annotation_text="Weak CTR (1%)")
    fig.update_layout(height=400, margin=dict(l=0, r=0, t=0, b=0))
    st.plotly_chart(fig, use_container_width=True)

    st.markdown("**Query table**")
    def signal_style(val):
        colors = {"Healthy": "#d4edda", "AIO": "#f8d7da", "Displaced": "#fff3cd"}
        return f"background-color: {colors.get(val, 'white')}"

    qdf["ctr"] = qdf["ctr"].apply(lambda x: f"{x:.2f}%")
    qdf["position"] = qdf["position"].apply(lambda x: f"{x:.1f}")
    st.dataframe(
        qdf.style.applymap(signal_style, subset=["signal"]),
        use_container_width=True, hide_index=True
    )

    st.divider()
    st.markdown("**Signal legend**")
    st.markdown(
        "🟢 **Healthy** — specific enough that AIO can't intercept, original brand hasn't claimed it  \n"
        "🔴 **AIO** — you rank fine, Google answers above you, clicks gone  \n"
        "🟠 **Displaced** — brand reclaimed position, pushed you to page 2+"
    )
