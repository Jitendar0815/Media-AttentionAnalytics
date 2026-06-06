"""
visualizations.py
=================
Animated / styled Plotly figure builders.

Every function is pure: it takes data and returns a ``plotly.graph_objects.Figure``.
No Streamlit calls live here, which keeps the module importable and testable on
its own. Colours are kept in sync with ``assets/css/style.css``.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import plotly.graph_objects as go

# --------------------------------------------------------------------------- #
# Shared theme
# --------------------------------------------------------------------------- #
INK = "#0a0e1a"
PANEL = "rgba(255,255,255,0.02)"
GRID = "rgba(255,255,255,0.06)"
TEXT = "#e8ecf6"
MUTED = "#8b93a7"

ACCENT = "#c6f135"   # electric lime
CYAN = "#38e1d6"
MAGENTA = "#ff5c8a"
AMBER = "#ffb347"
VIOLET = "#9d7bff"

PLATFORM_COLORS: dict[str, str] = {
    "YouTube": "#ff5c8a",
    "TikTok": "#38e1d6",
    "Instagram": "#9d7bff",
    "X (Twitter)": "#c6f135",
    "LinkedIn": "#ffb347",
}

FONT = "IBM Plex Sans, Segoe UI, sans-serif"


def _base_layout(fig: go.Figure, height: int = 420, title: str | None = None) -> go.Figure:
    """Apply the shared dark, transparent layout to a figure."""
    fig.update_layout(
        template="plotly_dark",
        height=height,
        title=dict(text=title or "", x=0.01, xanchor="left",
                   font=dict(size=18, color=TEXT, family=FONT)),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family=FONT, color=TEXT, size=13),
        margin=dict(l=50, r=24, t=50 if title else 24, b=40),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0,
                    bgcolor="rgba(0,0,0,0)", font=dict(color=MUTED)),
        hoverlabel=dict(bgcolor="#11162a", font=dict(family=FONT, color=TEXT),
                        bordercolor=GRID),
    )
    fig.update_xaxes(gridcolor=GRID, zeroline=False, linecolor=GRID,
                     tickfont=dict(color=MUTED))
    fig.update_yaxes(gridcolor=GRID, zeroline=False, linecolor=GRID,
                     tickfont=dict(color=MUTED))
    return fig


# --------------------------------------------------------------------------- #
# 1. Attention time-series (multi-platform, optional draw-on animation)
# --------------------------------------------------------------------------- #
def attention_timeseries(
    df: pd.DataFrame,
    metric: str = "attention_score",
    animate: bool = False,
    title: str | None = None,
) -> go.Figure:
    """
    Multi-platform line chart of `metric` over time.

    When ``animate=True`` a play button progressively draws each line.
    """
    fig = go.Figure()
    platforms = list(df["platform"].unique())

    for platform in platforms:
        sub = df[df["platform"] == platform].sort_values("date")
        color = PLATFORM_COLORS.get(platform, ACCENT)
        fig.add_trace(
            go.Scatter(
                x=sub["date"], y=sub[metric], mode="lines",
                name=platform, line=dict(color=color, width=2.4, shape="spline"),
                fill="tozeroy",
                fillcolor=_rgba(color, 0.07),
                hovertemplate=f"<b>{platform}</b><br>%{{x|%b %d}}<br>"
                              f"{metric.replace('_', ' ').title()}: %{{y:.1f}}<extra></extra>",
            )
        )

    if animate and not df.empty:
        dates = sorted(df["date"].unique())
        frames = []
        # ~24 frames keeps the animation smooth but light.
        steps = np.linspace(2, len(dates), min(24, len(dates))).astype(int)
        for k in steps:
            cutoff = dates[k - 1]
            frame_data = []
            for platform in platforms:
                sub = df[(df["platform"] == platform) & (df["date"] <= cutoff)]
                frame_data.append(go.Scatter(x=sub["date"], y=sub[metric]))
            frames.append(go.Frame(data=frame_data, name=str(cutoff)))
        fig.frames = frames
        fig.update_layout(
            updatemenus=[dict(
                type="buttons", showactive=False, x=0.0, y=1.18, xanchor="left",
                bgcolor="rgba(255,255,255,0.05)", bordercolor=GRID,
                font=dict(color=TEXT),
                buttons=[dict(label="▶  Play", method="animate",
                              args=[None, dict(frame=dict(duration=60, redraw=True),
                                               fromcurrent=True,
                                               transition=dict(duration=0))])],
            )]
        )

    return _base_layout(fig, height=440, title=title)


# --------------------------------------------------------------------------- #
# 2. Retention curves
# --------------------------------------------------------------------------- #
def retention_curves(curves: pd.DataFrame, title: str | None = None) -> go.Figure:
    fig = go.Figure()
    for platform in curves["platform"].unique():
        sub = curves[curves["platform"] == platform]
        color = PLATFORM_COLORS.get(platform, CYAN)
        fig.add_trace(
            go.Scatter(
                x=sub["second"], y=sub["pct_remaining"], mode="lines",
                name=platform, line=dict(color=color, width=2.4, shape="spline"),
                hovertemplate=f"<b>{platform}</b><br>%{{x:.0f}}%% in<br>"
                              "%{y:.1f}%% remaining<extra></extra>",
            )
        )
    fig.update_xaxes(title="Content position (%)", ticksuffix="%")
    fig.update_yaxes(title="Audience remaining (%)", range=[0, 102], ticksuffix="%")
    return _base_layout(fig, height=400, title=title)


# --------------------------------------------------------------------------- #
# 3. Heatmap (weekday x hour)
# --------------------------------------------------------------------------- #
def attention_heatmap(heat: pd.DataFrame, title: str | None = None) -> go.Figure:
    weekday_order = ["Monday", "Tuesday", "Wednesday", "Thursday",
                     "Friday", "Saturday", "Sunday"]
    pivot = (
        heat.pivot(index="weekday", columns="hour", values="intensity")
        .reindex(weekday_order)
    )
    fig = go.Figure(
        go.Heatmap(
            z=pivot.values,
            x=[f"{h:02d}:00" for h in pivot.columns],
            y=pivot.index,
            colorscale=[[0, "#0a0e1a"], [0.4, "#1d3b5a"],
                        [0.7, "#38e1d6"], [1.0, "#c6f135"]],
            hovertemplate="%{y} %{x}<br>Attention: %{z:.0f}<extra></extra>",
            colorbar=dict(title="Intensity", tickfont=dict(color=MUTED),
                          outlinewidth=0),
        )
    )
    return _base_layout(fig, height=380, title=title)


# --------------------------------------------------------------------------- #
# 4. Forecast chart (history + prediction + confidence band)
# --------------------------------------------------------------------------- #
def forecast_chart(
    history: pd.Series,
    fc: pd.DataFrame,
    color: str = ACCENT,
    title: str | None = None,
) -> go.Figure:
    """
    `history` -> pd.Series indexed by date.
    `fc`      -> DataFrame from analytics_engine.forecast().
    """
    fig = go.Figure()

    # Confidence band.
    fig.add_trace(go.Scatter(
        x=list(fc["date"]) + list(fc["date"][::-1]),
        y=list(fc["upper"]) + list(fc["lower"][::-1]),
        fill="toself", fillcolor=_rgba(color, 0.12),
        line=dict(color="rgba(0,0,0,0)"), name="Confidence band",
        hoverinfo="skip",
    ))
    # History.
    fig.add_trace(go.Scatter(
        x=history.index, y=history.values, mode="lines", name="Observed",
        line=dict(color=CYAN, width=2.4, shape="spline"),
        hovertemplate="%{x|%b %d}<br>%{y:.0f}<extra></extra>",
    ))
    # Forecast.
    fig.add_trace(go.Scatter(
        x=fc["date"], y=fc["yhat"], mode="lines", name="Forecast",
        line=dict(color=color, width=2.6, dash="dot"),
        hovertemplate="%{x|%b %d}<br>%{y:.0f} (pred)<extra></extra>",
    ))
    # Connector marker at the boundary.
    if len(history):
        fig.add_trace(go.Scatter(
            x=[history.index[-1]], y=[history.values[-1]], mode="markers",
            marker=dict(color=color, size=9, line=dict(color=INK, width=2)),
            showlegend=False, hoverinfo="skip",
        ))
    return _base_layout(fig, height=440, title=title)


# --------------------------------------------------------------------------- #
# 5. Platform leaderboard bar
# --------------------------------------------------------------------------- #
def platform_bar(board: pd.DataFrame, title: str | None = None) -> go.Figure:
    colors = [PLATFORM_COLORS.get(p, ACCENT) for p in board["platform"]]
    fig = go.Figure(go.Bar(
        x=board["score"], y=board["platform"], orientation="h",
        marker=dict(color=colors, line=dict(width=0)),
        text=[_human(v) for v in board["score"]], textposition="outside",
        textfont=dict(color=TEXT),
        hovertemplate="<b>%{y}</b><br>Attention score: %{x:,}<extra></extra>",
    ))
    fig.update_yaxes(autorange="reversed")
    fig.update_layout(showlegend=False)
    return _base_layout(fig, height=360, title=title)


# --------------------------------------------------------------------------- #
# 6. Radial gauge
# --------------------------------------------------------------------------- #
def radial_gauge(value: float, title: str = "Attention",
                 color: str = ACCENT) -> go.Figure:
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=value,
        number=dict(suffix="", font=dict(color=TEXT, size=34)),
        title=dict(text=title, font=dict(color=MUTED, size=14)),
        gauge=dict(
            axis=dict(range=[0, 100], tickcolor=MUTED, tickfont=dict(color=MUTED)),
            bar=dict(color=color, thickness=0.28),
            bgcolor="rgba(255,255,255,0.03)",
            borderwidth=0,
            steps=[
                dict(range=[0, 40], color="rgba(255,92,138,0.12)"),
                dict(range=[40, 70], color="rgba(255,179,71,0.12)"),
                dict(range=[70, 100], color="rgba(198,241,53,0.12)"),
            ],
        ),
    ))
    return _base_layout(fig, height=260)


# --------------------------------------------------------------------------- #
# helpers
# --------------------------------------------------------------------------- #
def _rgba(hex_color: str, alpha: float) -> str:
    h = hex_color.lstrip("#")
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    return f"rgba({r},{g},{b},{alpha})"


def _human(n: float) -> str:
    n = float(n)
    for unit, div in (("B", 1e9), ("M", 1e6), ("K", 1e3)):
        if abs(n) >= div:
            return f"{n / div:.1f}{unit}"
    return f"{n:.0f}"
