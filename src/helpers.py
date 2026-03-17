# helpers.py
# Pure utility functions shared across multiple modules.
# No side effects — each function takes inputs and returns outputs only.

import geopandas as gpd
import pandas as pd
from config import TIER_COLORS, TIER_LABELS


# -----------------------
# GeoDataFrame helper
# -----------------------
def to_gdf(df: pd.DataFrame) -> gpd.GeoDataFrame:
    """Convert a DataFrame with 'lat' and 'lon' columns to a GeoDataFrame."""
    return gpd.GeoDataFrame(
        df,
        geometry=gpd.points_from_xy(df["lon"], df["lat"]),
        crs="EPSG:4326",
    )


# -----------------------
# Normalization
# -----------------------
def normalize(series: pd.Series) -> pd.Series:
    """Min-max normalize a pandas Series to [0, 1]. Returns zeros if all values are equal."""
    mn, mx = series.min(), series.max()
    if mx > mn:
        return (series - mn) / (mx - mn)
    return pd.Series([0.0] * len(series), index=series.index)


# -----------------------
# Tier helpers
# -----------------------
def tier_color(tier) -> str:
    """Return hex fill color for a given risk tier (1–4)."""
    tier = int(tier) if tier and not pd.isna(tier) else 1
    return TIER_COLORS.get(tier, "#cccccc")


def tier_label(tier) -> str:
    """Return human-readable label for a given risk tier (1–4)."""
    return TIER_LABELS.get(int(tier), "Unknown")


def tier_badge(tier):
    """
    Return (background_hex, text_hex, label_str) for badge rendering.

    Usage:
        bg, txt, label = tier_badge(row["risk_tier"])
    """
    tier = int(tier)
    bg  = TIER_COLORS.get(tier, "#cccccc")
    txt = "#fff" if tier >= 2 else "#333"
    return bg, txt, tier_label(tier)


# -----------------------
# Percentile-based tier assignment
# -----------------------
def percentile_tier(series: pd.Series):
    """
    Assign risk tiers 1–4 based on the series' own quartile distribution.

    Returns:
        (tier_series, p25, p50, p75)

    Tier mapping:
        4 = Critical  — top 25%     (>= p75)
        3 = High      — 50–75%      (>= p50)
        2 = Moderate  — 25–50%      (>= p25)
        1 = Low       — bottom 25%  (< p25)
    """
    p25 = series.quantile(0.25)
    p50 = series.quantile(0.50)
    p75 = series.quantile(0.75)

    def assign(score):
        if score >= p75:
            return 4
        elif score >= p50:
            return 3
        elif score >= p25:
            return 2
        else:
            return 1

    return series.apply(assign), p25, p50, p75