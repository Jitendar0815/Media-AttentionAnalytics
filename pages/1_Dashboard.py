"""
pages/1_Dashboard.py
Main analytics dashboard: KPIs, trends, retention, heatmap, leaderboard.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import pandas as pd  # noqa: E402
import streamlit as st  # noqa: E402

from src import analytics_engine as ae  # noqa: E402
from src import components as ui  # noqa: E402
from src import data_generator as dg  # noqa: E402
from src import utils  # noqa: E402
from src import visualizations as viz  # noqa: E402

utils.configure_page("Dashboard", icon="📊")
utils.sidebar_nav(active="dashboard")

ui.page_header(
    "Analytics Dashboard",
    "Track attention, retention and engagement across every connected platform.",
    kicker="live overview",
)

# --------------------------------------------------------------------------- #
# Controls
# --------------------------------------------------------------------------- #
df_all = utils.load_timeseries()

cc1, cc2 = st.columns([2, 1], gap="large")
with cc1:
    selected = st.multiselect(
        "Platforms", options=dg.PLATFORMS, default=dg.PLATFORMS,
        help="Choose which platforms to include.",
    )
with cc2:
    window = st.select_slider(
        "Time window", options=[30, 60, 90, 120, 180], value=90,
        help="Number of most-recent days to analyse.",
    )

if not selected:
    st.warning("Select at least one platform to see analytics.")
    ui.footer()
    st.stop()

cutoff = df_all["date"].max() - pd.Timedelta(days=window - 1)
df = df_all[(df_all["platform"].isin(selected)) & (df_all["date"] >= cutoff)].copy()

# --------------------------------------------------------------------------- #
# KPIs
# --------------------------------------------------------------------------- #
k = ae.summarise(df)
ui.section_title("Key metrics", hint=f"{window}-day window")
ui.metric_row([
    {"label": "Views", "value": utils.human(k["total_views"]),
     "delta": ae.period_delta(df, "views"), "icon": "👁️", "accent": "var(--cyan)"},
    {"label": "Watch hours", "value": utils.human(k["total_watch_hours"]),
     "icon": "⏱️", "accent": "var(--violet)"},
    {"label": "Avg attention", "value": f"{k['avg_attention']:.1f}",
     "delta": ae.period_delta(df, "attention_score"), "icon": "📡",
     "accent": "var(--accent)"},
    {"label": "Avg retention", "value": f"{k['avg_retention'] * 100:.0f}%",
     "icon": "🎯", "accent": "var(--magenta)"},
])

# --------------------------------------------------------------------------- #
# Trend + leaderboard
# --------------------------------------------------------------------------- #
left, right = st.columns([1.6, 1], gap="large")

with left:
    ui.section_title("Attention trend")
    metric = st.radio(
        "Metric", ["attention_score", "views", "engagements"],
        horizontal=True, label_visibility="collapsed",
        format_func=lambda m: m.replace("_", " ").title(),
    )
    st.plotly_chart(
        viz.attention_timeseries(df, metric=metric, animate=True),
        width="stretch", config={"displayModeBar": False},
    )

with right:
    ui.section_title("Leaderboard")
    board = ae.platform_leaderboard(df)
    st.plotly_chart(
        viz.platform_bar(board),
        width="stretch", config={"displayModeBar": False},
    )
    top = board.iloc[0]
    ui.insight(
        f"<b>{top['platform']}</b> leads with an attention-weighted score of "
        f"{utils.human(top['score'])}.", tone="accent",
    )

# --------------------------------------------------------------------------- #
# Retention curves + heatmap
# --------------------------------------------------------------------------- #
ui.section_title("Audience retention", hint="how long viewers stay")
curves = utils.load_retention()
curves = curves[curves["platform"].isin(selected)]
st.plotly_chart(viz.retention_curves(curves), width="stretch",
                config={"displayModeBar": False})

ui.section_title("When attention peaks", hint="weekday × hour intensity")
hm_platform = st.selectbox("Heatmap platform", selected, index=0)
heat = utils.load_heatmap(hm_platform)
hc1, hc2 = st.columns([2, 1], gap="large")
with hc1:
    st.plotly_chart(viz.attention_heatmap(heat), width="stretch",
                    config={"displayModeBar": False})
with hc2:
    st.markdown("**Best posting windows**")
    for _, row in ae.best_posting_windows(heat, 4).iterrows():
        ui.insight(
            f"{row['weekday']} · {int(row['hour']):02d}:00 — intensity "
            f"{row['intensity']:.0f}", tone="cyan",
        )

ui.footer()
