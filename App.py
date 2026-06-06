"""
App.py — AttentionLab
=====================
Main entry point & landing page for the Media Attention Analytics app.

Run with:  streamlit run App.py
"""
from __future__ import annotations

import sys
from pathlib import Path

# Make the project root importable no matter where Streamlit is launched from.
ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import streamlit as st  # noqa: E402

from src import analytics_engine as ae  # noqa: E402
from src import components as ui  # noqa: E402
from src import utils  # noqa: E402
from src import visualizations as viz  # noqa: E402

# --------------------------------------------------------------------------- #
# Page setup
# --------------------------------------------------------------------------- #
utils.configure_page("Home", icon=utils.APP_CONFIG["icon"])
utils.sidebar_nav(active="home")

# --------------------------------------------------------------------------- #
# Hero
# --------------------------------------------------------------------------- #
ui.hero(
    title_lines=["Where does", "attention go?"],
    subtitle=(
        "AttentionLab tracks the rise, peak and decay of audience attention "
        "across five major platforms — then forecasts where it heads next."
    ),
    lottie_name="hero_attention",
)

# --------------------------------------------------------------------------- #
# Headline KPIs
# --------------------------------------------------------------------------- #
df = utils.load_timeseries()
kpis = ae.summarise(df)
views_delta = ae.period_delta(df, "views")
attn_delta = ae.period_delta(df, "attention_score")
engage_delta = ae.period_delta(df, "engagements")

ui.section_title("Network pulse", hint="last 180 days · all platforms")
ui.metric_row([
    {"label": "Total views", "value": utils.human(kpis["total_views"]),
     "delta": views_delta, "icon": "👁️", "accent": "var(--cyan)"},
    {"label": "Watch time (hrs)", "value": utils.human(kpis["total_watch_hours"]),
     "icon": "⏱️", "accent": "var(--violet)"},
    {"label": "Avg attention", "value": f"{kpis['avg_attention']:.1f}",
     "delta": attn_delta, "icon": "📡", "accent": "var(--accent)"},
    {"label": "Engagements", "value": utils.human(kpis["total_engagements"]),
     "delta": engage_delta, "icon": "💬", "accent": "var(--magenta)"},
])

# --------------------------------------------------------------------------- #
# Teaser chart (animated)
# --------------------------------------------------------------------------- #
ui.section_title("Attention over time", hint="press ▶ to replay the build-up")
fig = viz.attention_timeseries(df, metric="attention_score", animate=True)
st.plotly_chart(fig, width="stretch", config={"displayModeBar": False})

# --------------------------------------------------------------------------- #
# Navigation cards → other pages
# --------------------------------------------------------------------------- #
ui.section_title("Explore the lab")
c1, c2, c3 = st.columns(3, gap="medium")

with c1:
    st.markdown(
        "<div class='metric-card' style='--card-accent:var(--cyan)'>"
        "<div class='metric-icon'>📊</div>"
        "<div class='metric-value' style='font-size:1.15rem'>Dashboard</div>"
        "<div class='metric-label' style='margin-top:.4rem'>"
        "Retention curves, heatmaps & platform leaderboards.</div></div>",
        unsafe_allow_html=True,
    )
    st.page_link(utils.PAGES["dashboard"]["path"], label="Open dashboard", icon="📊")

with c2:
    st.markdown(
        "<div class='metric-card' style='--card-accent:var(--accent)'>"
        "<div class='metric-icon'>🔮</div>"
        "<div class='metric-value' style='font-size:1.15rem'>Predictions</div>"
        "<div class='metric-label' style='margin-top:.4rem'>"
        "30/60/90-day attention forecasts with confidence bands.</div></div>",
        unsafe_allow_html=True,
    )
    st.page_link(utils.PAGES["predictions"]["path"], label="See forecasts", icon="🔮")

with c3:
    st.markdown(
        "<div class='metric-card' style='--card-accent:var(--magenta)'>"
        "<div class='metric-icon'>📁</div>"
        "<div class='metric-value' style='font-size:1.15rem'>Data Explorer</div>"
        "<div class='metric-label' style='margin-top:.4rem'>"
        "Filter the raw content table & export to CSV.</div></div>",
        unsafe_allow_html=True,
    )
    st.page_link(utils.PAGES["explorer"]["path"], label="Browse data", icon="📁")

ui.footer()
