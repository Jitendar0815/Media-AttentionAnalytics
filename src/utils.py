"""
utils.py
========
Cross-cutting helpers: path resolution, app config, cached data access,
asset loaders (CSS / JS / Lottie) and number formatting.

This module *does* import Streamlit because it owns the caching layer and the
page-setup helpers, but the heavy data work is delegated to the pure modules
(`data_generator`, `analytics_engine`).
"""
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import streamlit as st

from src import data_generator as dg

# --------------------------------------------------------------------------- #
# Paths
# --------------------------------------------------------------------------- #
ROOT = Path(__file__).resolve().parent.parent          # project root
ASSETS = ROOT / "assets"
CSS_FILE = ASSETS / "css" / "style.css"
JS_FILE = ASSETS / "js" / "animations.js"
LOTTIE_DIR = ASSETS / "lottie"
IMAGES = ASSETS / "images"

# --------------------------------------------------------------------------- #
# App-wide config
# --------------------------------------------------------------------------- #
APP_CONFIG = {
    "title": "Media Attention Analytics",
    "tagline": "Measuring the half-life of attention across every platform.",
    "icon": "📡",
    "accent": "#c6f135",
    "default_days": 180,
}

# Page registry — single source of truth for cross-page navigation links.
PAGES = {
    "home":        {"path": "App.py",                      "label": "Home",          "icon": "🏠"},
    "dashboard":   {"path": "pages/1_📊_Dashboard.py",     "label": "Dashboard",     "icon": "📊"},
    "predictions": {"path": "pages/2_🔮_Predictions.py",   "label": "Predictions",   "icon": "🔮"},
    "explorer":    {"path": "pages/3_📁_Data_Explorer.py", "label": "Data Explorer", "icon": "📁"},
    "about":       {"path": "pages/4_ℹ️_About.py",         "label": "About",         "icon": "ℹ️"},
}


# --------------------------------------------------------------------------- #
# Page bootstrap
# --------------------------------------------------------------------------- #
def configure_page(page_title: str, icon: str = APP_CONFIG["icon"]) -> None:
    """Standard `st.set_page_config` + CSS injection for every page."""
    st.set_page_config(
        page_title=f"{page_title} · {APP_CONFIG['title']}",
        page_icon=icon,
        layout="wide",
        initial_sidebar_state="expanded",
    )
    inject_css()


def inject_css() -> None:
    """Load the custom stylesheet (and animation JS) into the page."""
    if CSS_FILE.exists():
        st.markdown(f"<style>{CSS_FILE.read_text(encoding='utf-8')}</style>",
                    unsafe_allow_html=True)
    if JS_FILE.exists():
        st.markdown(f"<script>{JS_FILE.read_text(encoding='utf-8')}</script>",
                    unsafe_allow_html=True)


def sidebar_nav(active: str) -> None:
    """Render consistent cross-page navigation in the sidebar."""
    with st.sidebar:
        st.markdown(
            f"<div class='side-brand'>{APP_CONFIG['icon']} "
            f"<span>Attention<b>Lab</b></span></div>",
            unsafe_allow_html=True,
        )
        st.markdown("<div class='side-sub'>navigate</div>", unsafe_allow_html=True)
        for key, meta in PAGES.items():
            st.page_link(
                meta["path"],
                label=meta["label"],
                icon=meta["icon"],
                disabled=(key == active),
            )
        st.markdown("<hr class='side-rule'/>", unsafe_allow_html=True)
        st.caption("Synthetic data · refreshed per session")


# --------------------------------------------------------------------------- #
# Cached data access (shared by every page → consistent numbers)
# --------------------------------------------------------------------------- #
@st.cache_data(show_spinner=False)
def load_timeseries(days: int = APP_CONFIG["default_days"]) -> pd.DataFrame:
    return dg.generate_timeseries(days)


@st.cache_data(show_spinner=False)
def load_retention() -> pd.DataFrame:
    return dg.generate_retention_curves()


@st.cache_data(show_spinner=False)
def load_heatmap(platform: str | None = None) -> pd.DataFrame:
    return dg.generate_heatmap(platform)


@st.cache_data(show_spinner=False)
def load_content(n: int = 120) -> pd.DataFrame:
    return dg.generate_content(n)


@st.cache_data(show_spinner=False)
def load_lottie(name: str) -> dict | None:
    """Load a Lottie JSON file from assets/lottie by stem name."""
    path = LOTTIE_DIR / f"{name}.json"
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None


# --------------------------------------------------------------------------- #
# Formatting
# --------------------------------------------------------------------------- #
def human(n: float) -> str:
    """Compact human-readable number: 12_300 -> '12.3K'."""
    n = float(n)
    sign = "-" if n < 0 else ""
    n = abs(n)
    for unit, div in (("B", 1e9), ("M", 1e6), ("K", 1e3)):
        if n >= div:
            return f"{sign}{n / div:.1f}{unit}"
    return f"{sign}{n:.0f}"


def pct(n: float, signed: bool = True) -> str:
    s = f"{n:+.1f}%" if signed else f"{n:.1f}%"
    return s


def delta_arrow(n: float) -> str:
    return "▲" if n > 0 else ("▼" if n < 0 else "■")
