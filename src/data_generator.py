"""
data_generator.py
=================
Synthetic, deterministic multi-platform "attention" data.

Everything here is pure (numpy / pandas only) so it can be imported and unit
tested without a running Streamlit server. All randomness is seeded so the
dashboard, predictions and explorer pages always agree on the same numbers.
"""
from __future__ import annotations

from datetime import datetime, timedelta

import numpy as np
import pandas as pd

# --------------------------------------------------------------------------- #
# Constants
# --------------------------------------------------------------------------- #
SEED = 42

PLATFORMS: list[str] = ["YouTube", "TikTok", "Instagram", "X (Twitter)", "LinkedIn"]

# Per-platform behavioural fingerprint used to shape the synthetic series.
PLATFORM_PROFILE: dict[str, dict[str, float]] = {
    "YouTube":     {"base": 82_000, "growth": 0.018, "volatility": 0.10, "retention": 0.62},
    "TikTok":      {"base": 145_000, "growth": 0.030, "volatility": 0.22, "retention": 0.41},
    "Instagram":   {"base": 96_000, "growth": 0.012, "volatility": 0.14, "retention": 0.48},
    "X (Twitter)": {"base": 54_000, "growth": -0.004, "volatility": 0.26, "retention": 0.33},
    "LinkedIn":    {"base": 28_000, "growth": 0.022, "volatility": 0.09, "retention": 0.55},
}

CONTENT_FORMATS: list[str] = ["Short-form", "Long-form", "Live", "Story", "Article"]

WEEKDAYS: list[str] = [
    "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday",
]


def _rng(offset: int = 0) -> np.random.Generator:
    """Return a deterministic numpy random generator."""
    return np.random.default_rng(SEED + offset)


# --------------------------------------------------------------------------- #
# 1. Daily time-series per platform
# --------------------------------------------------------------------------- #
def generate_timeseries(days: int = 180) -> pd.DataFrame:
    """
    Generate a tidy daily time-series of attention metrics for every platform.

    Columns: date, platform, views, watch_time_hours, engagements,
             avg_view_duration_sec, attention_score
    """
    end = datetime.now().date()
    dates = pd.date_range(end - timedelta(days=days - 1), end, freq="D")
    rows: list[dict] = []

    for p_idx, platform in enumerate(PLATFORMS):
        prof = PLATFORM_PROFILE[platform]
        rng = _rng(p_idx)

        # Smooth growth trend.
        trend = prof["base"] * (1 + prof["growth"]) ** np.arange(days)

        # Weekly seasonality (weekend dips on professional nets, peaks elsewhere).
        weekday = np.array([d.weekday() for d in dates])
        if platform == "LinkedIn":
            season = np.where(weekday >= 5, 0.78, 1.06)
        else:
            season = np.where(weekday >= 5, 1.12, 0.96)

        # Multiplicative noise + a couple of viral "spikes".
        noise = rng.normal(1.0, prof["volatility"], days)
        spikes = np.ones(days)
        for s in rng.choice(np.arange(10, days - 5), size=3, replace=False):
            spikes[s:s + 3] *= rng.uniform(1.4, 2.3)

        views = np.clip(trend * season * noise * spikes, 500, None).round().astype(int)

        retention = np.clip(
            prof["retention"] + rng.normal(0, 0.03, days), 0.05, 0.97
        )
        avg_duration = (retention * rng.uniform(180, 600)).round(1)
        watch_time = (views * avg_duration / 3600.0).round(1)        # hours
        engage_rate = np.clip(retention * rng.uniform(0.18, 0.32, days), 0.02, 0.6)
        engagements = (views * engage_rate).round().astype(int)

        # Composite attention score (0-100): retention + engagement weighted.
        attn = (retention * 60 + engage_rate * 120).clip(0, 100).round(1)

        for i, d in enumerate(dates):
            rows.append(
                {
                    "date": d.date(),
                    "platform": platform,
                    "views": int(views[i]),
                    "watch_time_hours": float(watch_time[i]),
                    "engagements": int(engagements[i]),
                    "avg_view_duration_sec": float(avg_duration[i]),
                    "retention": float(round(retention[i], 3)),
                    "attention_score": float(attn[i]),
                }
            )

    df = pd.DataFrame(rows)
    df["date"] = pd.to_datetime(df["date"])
    return df.sort_values(["platform", "date"]).reset_index(drop=True)


# --------------------------------------------------------------------------- #
# 2. Retention curves (avg % of audience still watching at second N)
# --------------------------------------------------------------------------- #
def generate_retention_curves(points: int = 60) -> pd.DataFrame:
    """
    Average audience-retention curve per platform.

    Columns: platform, second, pct_remaining
    """
    rows: list[dict] = []
    seconds = np.linspace(0, 100, points)            # % of content length

    for p_idx, platform in enumerate(PLATFORMS):
        prof = PLATFORM_PROFILE[platform]
        rng = _rng(100 + p_idx)
        # Exponential decay tuned by the platform retention fingerprint.
        decay = (1.1 - prof["retention"]) * 0.045
        curve = 100 * np.exp(-decay * seconds)
        # Small re-engagement bump near the end (call-to-action / loops).
        curve += rng.normal(0, 1.2, points) + 4 * np.exp(-((seconds - 92) ** 2) / 30)
        curve = np.clip(curve, 1, 100)
        curve[0] = 100.0

        for s, v in zip(seconds, curve):
            rows.append(
                {"platform": platform, "second": float(round(s, 1)),
                 "pct_remaining": float(round(v, 2))}
            )
    return pd.DataFrame(rows)


# --------------------------------------------------------------------------- #
# 3. Attention heatmap (weekday x hour)
# --------------------------------------------------------------------------- #
def generate_heatmap(platform: str | None = None) -> pd.DataFrame:
    """
    Weekday x hour attention-intensity grid (0-100).

    Returns a long DataFrame: weekday, hour, intensity
    """
    rng = _rng(500 + (PLATFORMS.index(platform) if platform in PLATFORMS else 0))
    hours = np.arange(24)
    rows: list[dict] = []

    # Two daily peaks: lunch (~12) and evening (~20).
    base_curve = (
        55
        + 30 * np.exp(-((hours - 12) ** 2) / 8)
        + 45 * np.exp(-((hours - 20) ** 2) / 6)
    )

    for d, wd in enumerate(WEEKDAYS):
        weekend_boost = 1.15 if d >= 5 else 1.0
        for h in hours:
            val = base_curve[h] * weekend_boost + rng.normal(0, 4)
            rows.append(
                {"weekday": wd, "hour": int(h),
                 "intensity": float(round(np.clip(val, 0, 100), 1))}
            )
    return pd.DataFrame(rows)


# --------------------------------------------------------------------------- #
# 4. Individual content / post table
# --------------------------------------------------------------------------- #
def generate_content(n: int = 120) -> pd.DataFrame:
    """
    A table of individual pieces of content with performance metrics.

    Columns: content_id, title, platform, format, published, views,
             attention_score, retention, engagements, viral_index
    """
    rng = _rng(900)
    topics = [
        "Behind the scenes", "Quick tutorial", "Hot take", "Product reveal",
        "Day in the life", "Q&A session", "Deep dive", "Reaction", "Challenge",
        "Announcement", "Case study", "Live recap", "Top 10", "Explainer",
        "Mini documentary",
    ]
    start = datetime.now().date() - timedelta(days=180)
    rows: list[dict] = []

    for i in range(n):
        platform = rng.choice(PLATFORMS)
        prof = PLATFORM_PROFILE[platform]
        fmt = rng.choice(CONTENT_FORMATS)
        topic = rng.choice(topics)
        pub = start + timedelta(days=int(rng.integers(0, 180)))
        views = int(np.clip(rng.lognormal(np.log(prof["base"]), 0.6), 800, None))
        retention = float(np.clip(prof["retention"] + rng.normal(0, 0.08), 0.05, 0.96))
        engage = int(views * np.clip(retention * rng.uniform(0.18, 0.34), 0.01, 0.6))
        attn = float(np.clip(retention * 60 + (engage / max(views, 1)) * 120, 0, 100))
        viral = float(round((views / prof["base"]) * (attn / 50), 2))

        rows.append(
            {
                "content_id": f"C-{1000 + i}",
                "title": f"{topic} #{i + 1}",
                "platform": platform,
                "format": fmt,
                "published": pub,
                "views": views,
                "attention_score": round(attn, 1),
                "retention": round(retention, 3),
                "engagements": engage,
                "viral_index": viral,
            }
        )

    df = pd.DataFrame(rows)
    df["published"] = pd.to_datetime(df["published"])
    return df.sort_values("published", ascending=False).reset_index(drop=True)


if __name__ == "__main__":  # pragma: no cover - manual smoke test
    print(generate_timeseries(30).head())
    print(generate_retention_curves(10).head())
    print(generate_heatmap("YouTube").head())
    print(generate_content(5))
