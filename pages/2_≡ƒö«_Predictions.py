"""
pages/2_🔮_Predictions.py
AI-style attention forecasting with confidence bands and trend read-outs.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import streamlit as st  # noqa: E402

from src import analytics_engine as ae  # noqa: E402
from src import components as ui  # noqa: E402
from src import data_generator as dg  # noqa: E402
from src import utils  # noqa: E402
from src import visualizations as viz  # noqa: E402

utils.configure_page("Predictions", icon="🔮")
utils.sidebar_nav(active="predictions")

ui.page_header(
    "Attention Forecasts",
    "Project where each platform's attention is heading using a trend model "
    "with a residual-based confidence band.",
    kicker="forward signal",
)

df_all = utils.load_timeseries()

# --------------------------------------------------------------------------- #
# Controls
# --------------------------------------------------------------------------- #
c1, c2, c3 = st.columns(3, gap="large")
with c1:
    platform = st.selectbox("Platform", dg.PLATFORMS, index=0)
with c2:
    metric = st.selectbox(
        "Metric", ["attention_score", "views", "engagements"],
        format_func=lambda m: m.replace("_", " ").title(),
    )
with c3:
    horizon = st.select_slider("Forecast horizon (days)",
                               options=[14, 30, 60, 90], value=30)

# --------------------------------------------------------------------------- #
# Build forecast
# --------------------------------------------------------------------------- #
series = (
    df_all[df_all["platform"] == platform]
    .sort_values("date")
    .set_index("date")[metric]
)
fc = ae.forecast(series, horizon=horizon, degree=2)
trend = ae.detect_trend(series)
confidence = ae.forecast_confidence(series, horizon)

last_obs = float(series.iloc[-1])
proj_end = float(fc["yhat"].iloc[-1])
change = (proj_end - last_obs) / last_obs * 100 if last_obs else 0.0
color = viz.PLATFORM_COLORS.get(platform, viz.ACCENT)

# --------------------------------------------------------------------------- #
# Forecast readout cards
# --------------------------------------------------------------------------- #
ui.section_title("Forecast read-out", hint=f"{platform} · next {horizon} days")
ui.metric_row([
    {"label": "Current", "value": utils.human(last_obs),
     "icon": "📍", "accent": "var(--cyan)"},
    {"label": f"Projected (+{horizon}d)", "value": utils.human(proj_end),
     "delta": round(change, 1), "icon": "🎯", "accent": "var(--accent)"},
    {"label": "Trend", "value": trend["direction"].title(),
     "icon": {"rising": "📈", "falling": "📉", "stable": "➡️"}[trend["direction"]],
     "accent": "var(--violet)"},
    {"label": "Model confidence", "value": f"{confidence:.0f}%",
     "icon": "🧪", "accent": "var(--magenta)"},
])

# --------------------------------------------------------------------------- #
# Forecast chart + gauge
# --------------------------------------------------------------------------- #
left, right = st.columns([1.7, 1], gap="large")
with left:
    ui.section_title("Projection")
    st.plotly_chart(
        viz.forecast_chart(series, fc, color=color),
        width="stretch", config={"displayModeBar": False},
    )
with right:
    ui.section_title("Confidence")
    st.plotly_chart(
        viz.radial_gauge(confidence, "Confidence", color=color),
        width="stretch", config={"displayModeBar": False},
    )
    tone = "accent" if trend["direction"] == "rising" else (
        "magenta" if trend["direction"] == "falling" else "cyan")
    ui.insight(
        f"Momentum is <b>{trend['direction']}</b> "
        f"(strength {trend['strength']:.2f}). Projected change over the next "
        f"{horizon} days: <b>{change:+.1f}%</b>.", tone=tone,
    )

# --------------------------------------------------------------------------- #
# Cross-platform outlook table
# --------------------------------------------------------------------------- #
ui.section_title("All-platform outlook", hint=f"projected {metric.replace('_',' ')} change")
rows = []
for p in dg.PLATFORMS:
    s = df_all[df_all["platform"] == p].sort_values("date").set_index("date")[metric]
    f = ae.forecast(s, horizon=horizon, degree=2)
    cur, end = float(s.iloc[-1]), float(f["yhat"].iloc[-1])
    rows.append({
        "Platform": p,
        "Current": round(cur, 1),
        f"Projected (+{horizon}d)": round(end, 1),
        "Change %": round((end - cur) / cur * 100 if cur else 0, 1),
        "Trend": ae.detect_trend(s)["direction"],
        "Confidence %": ae.forecast_confidence(s, horizon),
    })

import pandas as pd  # noqa: E402

outlook = pd.DataFrame(rows)
st.dataframe(
    outlook,
    width="stretch",
    hide_index=True,
    column_config={
        "Change %": st.column_config.NumberColumn(format="%.1f%%"),
        "Confidence %": st.column_config.ProgressColumn(
            min_value=0, max_value=100, format="%.0f%%"),
    },
)

st.caption(
    "Forecasts use a degree-2 ordinary-least-squares trend with a 95% "
    "residual confidence band — illustrative, not investment advice."
)

ui.footer()
