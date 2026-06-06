"""
analytics_engine.py
===================
Attention scoring, trend detection and lightweight forecasting.

Pure numpy / pandas — deterministic and Streamlit-free so it is trivially
testable. Forecasting uses an ordinary-least-squares trend plus a residual
based confidence band (no heavy ML dependencies required).
"""
from __future__ import annotations

import numpy as np
import pandas as pd


# --------------------------------------------------------------------------- #
# Summary / KPI helpers
# --------------------------------------------------------------------------- #
def summarise(df: pd.DataFrame) -> dict[str, float]:
    """Return headline KPIs for a (possibly filtered) time-series frame."""
    if df.empty:
        return {
            "total_views": 0, "total_watch_hours": 0.0, "total_engagements": 0,
            "avg_attention": 0.0, "avg_retention": 0.0,
        }
    return {
        "total_views": int(df["views"].sum()),
        "total_watch_hours": float(df["watch_time_hours"].sum()),
        "total_engagements": int(df["engagements"].sum()),
        "avg_attention": float(df["attention_score"].mean()),
        "avg_retention": float(df["retention"].mean()),
    }


def period_delta(df: pd.DataFrame, metric: str = "views") -> float:
    """
    Percentage change between the most recent half and the previous half of
    the series (aggregated across whatever platforms are present).
    """
    if df.empty:
        return 0.0
    daily = df.groupby("date")[metric].sum().sort_index()
    if len(daily) < 4:
        return 0.0
    mid = len(daily) // 2
    prev = daily.iloc[:mid].mean()
    curr = daily.iloc[mid:].mean()
    if prev == 0:
        return 0.0
    return float(round((curr - prev) / prev * 100, 1))


# --------------------------------------------------------------------------- #
# Trend detection
# --------------------------------------------------------------------------- #
def detect_trend(series: pd.Series, window: int = 7) -> dict:
    """
    Classify the trend of a single numeric series.

    Returns dict with slope, direction ('rising'/'falling'/'stable'),
    strength (0-1) and a smoothed series for plotting.
    """
    s = series.dropna().astype(float)
    if len(s) < 3:
        return {"slope": 0.0, "direction": "stable", "strength": 0.0,
                "smoothed": s}

    x = np.arange(len(s))
    slope, _ = np.polyfit(x, s.values, 1)
    rng = s.max() - s.min()
    norm_slope = slope / (rng / len(s)) if rng else 0.0
    strength = float(np.clip(abs(norm_slope), 0, 1))

    if slope > 0 and strength > 0.08:
        direction = "rising"
    elif slope < 0 and strength > 0.08:
        direction = "falling"
    else:
        direction = "stable"

    smoothed = s.rolling(window, min_periods=1).mean()
    return {"slope": float(slope), "direction": direction,
            "strength": round(strength, 3), "smoothed": smoothed}


def detect_anomalies(series: pd.Series, z: float = 2.5) -> pd.Series:
    """Boolean mask of points that deviate more than `z` std-devs from a roll mean."""
    s = series.astype(float)
    roll_mean = s.rolling(7, min_periods=1).mean()
    roll_std = s.rolling(7, min_periods=1).std().fillna(s.std()).replace(0, 1e-9)
    return ((s - roll_mean).abs() / roll_std) > z


# --------------------------------------------------------------------------- #
# Forecasting
# --------------------------------------------------------------------------- #
def forecast(
    series: pd.Series,
    horizon: int = 30,
    degree: int = 2,
) -> pd.DataFrame:
    """
    Forecast `horizon` future steps with a polynomial OLS fit plus a residual
    derived confidence band.

    `series` should be indexed by date. Returns a DataFrame with columns:
    date, yhat, lower, upper, is_forecast
    """
    s = series.dropna().astype(float)
    if len(s) < 5:
        # Degenerate case: flat forecast at the last value.
        last = float(s.iloc[-1]) if len(s) else 0.0
        future_idx = pd.date_range(
            (s.index[-1] if len(s) else pd.Timestamp.today()) + pd.Timedelta(days=1),
            periods=horizon, freq="D",
        )
        return pd.DataFrame(
            {"date": future_idx, "yhat": last, "lower": last,
             "upper": last, "is_forecast": True}
        )

    x = np.arange(len(s))
    coeffs = np.polyfit(x, s.values, degree)
    model = np.poly1d(coeffs)

    resid_std = float(np.std(s.values - model(x)))
    fx = np.arange(len(s), len(s) + horizon)
    yhat = model(fx)

    # Widen the band the further out we predict.
    spread = resid_std * 1.96 * (1 + np.arange(horizon) / horizon)

    future_idx = pd.date_range(s.index[-1] + pd.Timedelta(days=1),
                               periods=horizon, freq="D")
    out = pd.DataFrame(
        {
            "date": future_idx,
            "yhat": np.clip(yhat, 0, None),
            "lower": np.clip(yhat - spread, 0, None),
            "upper": np.clip(yhat + spread, 0, None),
            "is_forecast": True,
        }
    )
    return out


def forecast_confidence(series: pd.Series, horizon: int = 30) -> float:
    """
    A 0-100 confidence proxy: high when the recent series is smooth and
    well explained by its trend, low when it is noisy.
    """
    s = series.dropna().astype(float)
    if len(s) < 5:
        return 50.0
    x = np.arange(len(s))
    coeffs = np.polyfit(x, s.values, 2)
    pred = np.poly1d(coeffs)(x)
    ss_res = float(np.sum((s.values - pred) ** 2))
    ss_tot = float(np.sum((s.values - s.values.mean()) ** 2)) or 1e-9
    r2 = 1 - ss_res / ss_tot
    # Decay confidence with horizon length.
    conf = np.clip(r2, 0, 1) * 100 * (1 - min(horizon, 90) / 240)
    return float(round(np.clip(conf, 5, 99), 1))


# --------------------------------------------------------------------------- #
# Ranking / insight helpers
# --------------------------------------------------------------------------- #
def platform_leaderboard(df: pd.DataFrame) -> pd.DataFrame:
    """Aggregate KPIs per platform, ranked by total attention-weighted views."""
    if df.empty:
        return pd.DataFrame()
    agg = (
        df.groupby("platform")
        .agg(
            views=("views", "sum"),
            watch_hours=("watch_time_hours", "sum"),
            engagements=("engagements", "sum"),
            attention=("attention_score", "mean"),
            retention=("retention", "mean"),
        )
        .reset_index()
    )
    agg["score"] = (agg["views"] * agg["attention"] / 100).round().astype(int)
    return agg.sort_values("score", ascending=False).reset_index(drop=True)


def best_posting_windows(heatmap: pd.DataFrame, top: int = 5) -> pd.DataFrame:
    """Return the `top` highest-intensity weekday/hour windows."""
    if heatmap.empty:
        return pd.DataFrame()
    return (
        heatmap.sort_values("intensity", ascending=False)
        .head(top)
        .reset_index(drop=True)
    )


if __name__ == "__main__":  # pragma: no cover
    from data_generator import generate_timeseries

    d = generate_timeseries(60)
    yt = d[d.platform == "YouTube"].set_index("date")["views"]
    print(summarise(d))
    print(detect_trend(yt))
    print(forecast(yt, 14).head())
    print("confidence", forecast_confidence(yt, 30))
