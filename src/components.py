"""
components.py
=============
Reusable Streamlit UI widgets — metric cards, animated section headers,
hero blocks, footers and a graceful Lottie renderer.

All functions call Streamlit, so they should only run inside a Streamlit
script (which is exactly where they are used).
"""
from __future__ import annotations

import streamlit as st

from src import utils

# Optional dependency — degrade gracefully if streamlit-lottie is missing.
try:
    from streamlit_lottie import st_lottie
    _HAS_LOTTIE = True
except Exception:  # pragma: no cover - import guard
    _HAS_LOTTIE = False


# --------------------------------------------------------------------------- #
# Headers / heroes
# --------------------------------------------------------------------------- #
def page_header(title: str, subtitle: str = "", kicker: str = "") -> None:
    """Animated page header with a small kicker label."""
    kicker_html = f"<div class='kicker'>{kicker}</div>" if kicker else ""
    sub_html = f"<p class='page-sub'>{subtitle}</p>" if subtitle else ""
    st.markdown(
        f"""
        <div class='page-header reveal'>
            {kicker_html}
            <h1 class='page-title'>{title}</h1>
            {sub_html}
        </div>
        """,
        unsafe_allow_html=True,
    )


def hero(title_lines: list[str], subtitle: str, lottie_name: str | None = None) -> None:
    """Landing-page hero. Optionally renders a Lottie animation on the right."""
    left, right = st.columns([1.35, 1], gap="large")
    with left:
        lines = "".join(
            f"<span class='hero-line' style='--d:{i * 0.12}s'>{ln}</span>"
            for i, ln in enumerate(title_lines)
        )
        st.markdown(
            f"""
            <div class='hero'>
                <div class='hero-badge'>● live signal</div>
                <h1 class='hero-title'>{lines}</h1>
                <p class='hero-sub'>{subtitle}</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with right:
        anim = utils.load_lottie(lottie_name) if lottie_name else None
        if anim and _HAS_LOTTIE:
            st_lottie(anim, height=300, key=f"hero_{lottie_name}",
                      loop=True, quality="high")
        else:
            # CSS fallback "radar" so the hero never looks empty.
            st.markdown("<div class='radar-fallback'></div>", unsafe_allow_html=True)


# --------------------------------------------------------------------------- #
# Metric cards
# --------------------------------------------------------------------------- #
def metric_card(label: str, value: str, delta: float | None = None,
                icon: str = "", accent: str = "var(--accent)") -> None:
    """A single animated metric card (renders standalone)."""
    st.markdown(_metric_html(label, value, delta, icon, accent),
                unsafe_allow_html=True)


def metric_row(cards: list[dict]) -> None:
    """
    Render a row of metric cards.

    `cards` -> list of dicts: {label, value, delta(optional), icon(optional),
                               accent(optional)}
    """
    cols = st.columns(len(cards), gap="medium")
    for col, card in zip(cols, cards):
        with col:
            metric_card(
                card["label"], card["value"],
                card.get("delta"), card.get("icon", ""),
                card.get("accent", "var(--accent)"),
            )


def _metric_html(label, value, delta, icon, accent) -> str:
    delta_html = ""
    if delta is not None:
        cls = "up" if delta > 0 else ("down" if delta < 0 else "flat")
        arrow = utils.delta_arrow(delta)
        delta_html = (
            f"<div class='metric-delta {cls}'>{arrow} {abs(delta):.1f}%</div>"
        )
    icon_html = f"<div class='metric-icon'>{icon}</div>" if icon else ""
    return f"""
    <div class='metric-card reveal' style='--card-accent:{accent}'>
        {icon_html}
        <div class='metric-label'>{label}</div>
        <div class='metric-value'>{value}</div>
        {delta_html}
    </div>
    """


# --------------------------------------------------------------------------- #
# Misc widgets
# --------------------------------------------------------------------------- #
def section_title(text: str, hint: str = "") -> None:
    hint_html = f"<span class='section-hint'>{hint}</span>" if hint else ""
    st.markdown(
        f"<div class='section-title'><h2>{text}</h2>{hint_html}</div>",
        unsafe_allow_html=True,
    )


def pill(text: str, tone: str = "accent") -> str:
    """Return a small inline pill (returns HTML string for embedding)."""
    return f"<span class='pill pill-{tone}'>{text}</span>"


def insight(text: str, tone: str = "accent") -> None:
    st.markdown(
        f"<div class='insight insight-{tone}'><span class='insight-dot'></span>"
        f"{text}</div>",
        unsafe_allow_html=True,
    )


def lottie(name: str, height: int = 200, key: str | None = None) -> None:
    """Render a Lottie animation by name, with a quiet fallback."""
    anim = utils.load_lottie(name)
    if anim and _HAS_LOTTIE:
        st_lottie(anim, height=height, key=key or f"lottie_{name}", loop=True)
    else:
        st.markdown("<div class='pulse-fallback'></div>", unsafe_allow_html=True)


def footer() -> None:
    st.markdown(
        f"""
        <div class='app-footer'>
            <div class='footer-brand'>{utils.APP_CONFIG['icon']} Attention<b>Lab</b></div>
            <div class='footer-meta'>
                {utils.APP_CONFIG['tagline']}<br/>
                Built with Streamlit · Plotly · synthetic data — for demonstration only.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
