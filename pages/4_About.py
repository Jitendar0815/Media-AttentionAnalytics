"""
pages/4_About.py
Methodology, metric definitions, tech stack and credits.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import streamlit as st  # noqa: E402

from src import components as ui  # noqa: E402
from src import utils  # noqa: E402

utils.configure_page("About", icon="ℹ️")
utils.sidebar_nav(active="about")

ui.page_header(
    "Methodology & Credits",
    "How AttentionLab models the rise and decay of audience attention.",
    kicker="under the hood",
)

# --------------------------------------------------------------------------- #
# Animated pulse + intro
# --------------------------------------------------------------------------- #
intro, anim = st.columns([2, 1], gap="large")
with intro:
    st.markdown(
        """
AttentionLab is a **demonstration** analytics suite that simulates how
audience attention behaves across multiple media platforms. Every number is
**synthetic and deterministic** — generated from seeded statistical models so
the dashboard, forecasts and explorer always agree.

The goal is to show a clean, production-style Streamlit architecture: a pure
data/analytics core, a reusable component library and animated Plotly
visualizations — all wired together across multiple linked pages.
        """
    )
with anim:
    ui.lottie("pulse", height=200, key="about_pulse")

# --------------------------------------------------------------------------- #
# Metric definitions
# --------------------------------------------------------------------------- #
ui.section_title("Metric definitions")
st.markdown(
    """
| Metric | Definition |
|---|---|
| **Attention score** | Composite 0–100 index combining retention (60% weight) and engagement rate (scaled). |
| **Retention** | Average share of the audience still watching, modelled as exponential decay per platform. |
| **Watch time** | Views × average view duration, expressed in hours. |
| **Engagements** | Likes, comments and shares, derived from retention-driven engagement rates. |
| **Viral index** | Views relative to the platform baseline, weighted by attention score. |
"""
)

# --------------------------------------------------------------------------- #
# How forecasting works
# --------------------------------------------------------------------------- #
ui.section_title("How forecasting works")
st.markdown(
    """
1. **Trend fit** — a degree-2 ordinary-least-squares polynomial is fit to the
   historical series.
2. **Projection** — the fitted model is extrapolated across the chosen horizon
   (14 / 30 / 60 / 90 days).
3. **Confidence band** — a 95% interval is built from the model's residual
   standard deviation and widened the further out the projection runs.
4. **Confidence score** — derived from the in-sample R² and discounted by the
   forecast horizon.
    """
)
ui.insight(
    "Forecasts are illustrative only. Real attention data is noisier and "
    "would warrant seasonality-aware models (e.g. SARIMA / Prophet).",
    tone="magenta",
)

# --------------------------------------------------------------------------- #
# Tech stack & structure
# --------------------------------------------------------------------------- #
ui.section_title("Project structure")
st.code(
    """media-attention-analytics/
├── App.py                  # entry point / landing page
├── src/
│   ├── data_generator.py   # synthetic multi-platform data
│   ├── analytics_engine.py # scoring, trends, forecasting
│   ├── visualizations.py   # animated Plotly charts
│   ├── components.py        # reusable UI widgets
│   └── utils.py            # caching, formatting, config, nav
└── pages/
    ├── 1_Dashboard.py
    ├── 2_Predictions.py
    ├── 3_Data_Explorer.py
    └── 4_About.py""",
    language="text",
)

ui.section_title("Built with")
b1, b2, b3, b4 = st.columns(4)
for col, (name, icon, tone) in zip(
    [b1, b2, b3, b4],
    [("Streamlit", "🎈", "var(--accent)"), ("Plotly", "📈", "var(--cyan)"),
     ("pandas", "🐼", "var(--violet)"), ("NumPy", "🔢", "var(--magenta)")],
):
    with col:
        ui.metric_card(name, icon, icon="", accent=tone)

ui.footer()
