# 📡 AttentionLab — Media Attention Analytics

[![Open in Streamlit](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://streamlit.io/cloud)

> Measuring the rise, peak and **half-life of attention** across every major media platform — and forecasting where it heads next.

AttentionLab is a polished, multi-page **Streamlit** application that simulates
and analyses audience-attention data across five platforms (YouTube, TikTok,
Instagram, X, LinkedIn). It features animated Plotly charts, a reusable
component library, attention forecasting and a filterable data explorer.

> ⚠️ **All data is synthetic and deterministic** (seeded). This is a
> demonstration of architecture and design, not real platform data.

---

## ✨ Features

- **Landing page** with an animated hero, network-pulse KPIs and a build-up chart.
- **Dashboard** — attention trends, audience-retention curves, weekday × hour
  heatmaps and a platform leaderboard, all filterable by platform and time window.
- **Predictions** — degree-2 OLS forecasts with a 95% confidence band, trend
  detection, a confidence gauge and an all-platform outlook table.
- **Data Explorer** — search/filter the raw content table and export to CSV.
- **About** — methodology, metric definitions and project structure.
- Custom dark "signal-lab" theme, Lottie animations and CSS micro-interactions.

---

## 🗂 Project structure

```
media-attention-analytics/
├── App.py                        # Main entry – orchestration & landing page
├── requirements.txt
├── README.md
├── .streamlit/
│   └── config.toml               # Theme & server settings
├── assets/
│   ├── css/style.css             # Custom theme, animations, typography
│   ├── js/animations.js          # Scroll-reveal / typewriter enhancements
│   ├── lottie/                   # hero_attention.json, pulse.json
│   └── images/                   # logo.png, favicon.png
├── src/
│   ├── data_generator.py         # Synthetic multi-platform data
│   ├── analytics_engine.py       # Scoring, trend detection, forecasting
│   ├── visualizations.py         # Animated Plotly charts
│   ├── components.py             # Reusable UI widgets
│   └── utils.py                  # Caching, formatting, config, navigation
└── pages/
    ├── 1_📊_Dashboard.py
    ├── 2_🔮_Predictions.py
    ├── 3_📁_Data_Explorer.py
    └── 4_ℹ️_About.py
```

The `src/` layer is **pure and Streamlit-free** where it matters
(`data_generator`, `analytics_engine`, `visualizations`), which keeps it easy
to test. Pages are linked through a single registry in `src/utils.py` and
rendered with `st.page_link`.

---

## 🚀 Getting started

```bash
# 1. (optional) create a virtual environment
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate

# 2. install dependencies
pip install -r requirements.txt

# 3. run the app
streamlit run App.py
```

Then open the URL Streamlit prints (default: <http://localhost:8501>).

---

## ☁️ Deploy

Push the repository to GitHub and deploy on
[Streamlit Community Cloud](https://streamlit.io/cloud):

- **Main file path:** `App.py`
- **Python version:** 3.10+

---

## 🛠 Tech stack

Streamlit · Plotly · pandas · NumPy · streamlit-lottie

## 📄 License

Provided as-is for demonstration and educational purposes.
