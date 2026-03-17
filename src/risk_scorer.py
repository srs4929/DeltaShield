# risk_scorer.py
# Computes flood, population, infrastructure, combined, and final risk scores.
# All logic is pure transformation — takes GeoDataFrames in, returns enriched ones.

import geopandas as gpd
import pandas as pd
from helpers import normalize, percentile_tier, to_gdf
from config import SCORE_WEIGHTS


# -----------------------
# Infrastructure scoring
# -----------------------
def count_per_district(points_gdf: gpd.GeoDataFrame,
                        districts: gpd.GeoDataFrame,
                        label: str) -> pd.DataFrame:
    """
    Spatial join: count how many points fall within each district polygon.

    Args:
        points_gdf: Point GeoDataFrame (hospitals / clinics / schools).
        districts:  District GeoDataFrame with NAME_2_clean column.
        label:      Column name for the count result.

    Returns:
        DataFrame with columns [NAME_2_clean, label].
    """
    district_geom = districts[["NAME_2_clean", "geometry"]].copy()
    joined = gpd.sjoin(points_gdf, district_geom, how="left", predicate="within")
    counts = joined.groupby("NAME_2_clean").size().reset_index(name=label)
    return counts


def add_infrastructure_scores(bangladesh: gpd.GeoDataFrame,
                               hospitals: pd.DataFrame,
                               clinics: pd.DataFrame,
                               schools: pd.DataFrame) -> gpd.GeoDataFrame:
    """
    Count infrastructure points per district and compute a normalized
    infrastructure risk score (low infra = high risk).

    Adds columns:
        hosp_count, clinic_count, school_count,
        infra_per_100k, infra_score_raw, infra_risk_score

    Returns:
        Enriched GeoDataFrame.
    """
    hosp_gdf   = to_gdf(hospitals)
    clinic_gdf = to_gdf(clinics)
    school_gdf = to_gdf(schools)

    hosp_counts   = count_per_district(hosp_gdf,   bangladesh, "hosp_count")
    clinic_counts = count_per_district(clinic_gdf, bangladesh, "clinic_count")
    school_counts = count_per_district(school_gdf, bangladesh, "school_count")

    bangladesh = bangladesh.merge(hosp_counts,   on="NAME_2_clean", how="left")
    bangladesh = bangladesh.merge(clinic_counts, on="NAME_2_clean", how="left")
    bangladesh = bangladesh.merge(school_counts, on="NAME_2_clean", how="left")

    bangladesh["hosp_count"]   = bangladesh["hosp_count"].fillna(0)
    bangladesh["clinic_count"] = bangladesh["clinic_count"].fillna(0)
    bangladesh["school_count"] = bangladesh["school_count"].fillna(0)

    bangladesh["infra_per_100k"] = (
        (bangladesh["hosp_count"]
         + bangladesh["clinic_count"]
         + bangladesh["school_count"])
        / bangladesh["T_TL"]
        * 100_000
    )

    bangladesh["infra_score_raw"]   = normalize(bangladesh["infra_per_100k"])
    bangladesh["infra_risk_score"]  = 1 - bangladesh["infra_score_raw"]

    return bangladesh


# -----------------------
# Flood scoring
# -----------------------
def add_flood_scores(bangladesh: gpd.GeoDataFrame,
                     flood: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    """
    Compute average flood category per district and normalize it.

    Adds columns:
        avg_floodcat, flood_score

    Returns:
        Enriched GeoDataFrame.
    """
    district_flood = (
        flood.groupby("DISTNAME_clean")["FLOODCAT"]
        .mean()
        .reset_index()
        .rename(columns={"FLOODCAT": "avg_floodcat"})
    )

    bangladesh = bangladesh.merge(
        district_flood,
        left_on="NAME_2_clean",
        right_on="DISTNAME_clean",
        how="left",
    )
    bangladesh["avg_floodcat"] = bangladesh["avg_floodcat"].fillna(0)
    bangladesh["flood_score"]  = normalize(bangladesh["avg_floodcat"])

    return bangladesh


# -----------------------
# Combined + Final scores
# -----------------------
def add_combined_scores(bangladesh: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    """
    Compute combined (flood + pop) and final (flood + pop + infra) scores,
    then assign percentile-based risk tiers.

    Adds columns:
        pop_score, combined_score, risk_tier,
        final_score, final_risk_tier

    Returns:
        Enriched GeoDataFrame.
    """
    w_c = SCORE_WEIGHTS["combined"]
    w_f = SCORE_WEIGHTS["final"]

    bangladesh["pop_score"] = normalize(bangladesh["T_TL"])

    bangladesh["combined_score"] = (
        w_c["flood"] * bangladesh["flood_score"]
        + w_c["pop"]  * bangladesh["pop_score"]
    )
    bangladesh["final_score"] = (
        w_f["flood"] * bangladesh["flood_score"]
        + w_f["pop"]  * bangladesh["pop_score"]
        + w_f["infra"] * bangladesh["infra_risk_score"]
    )

    bangladesh["risk_tier"],       comb_p25, comb_p50, comb_p75 = percentile_tier(bangladesh["combined_score"])
    bangladesh["final_risk_tier"], fin_p25,  fin_p50,  fin_p75  = percentile_tier(bangladesh["final_score"])

    # Store percentile breakpoints as module-level attributes for legend use
    add_combined_scores.comb_percentiles = (comb_p25, comb_p50, comb_p75)
    add_combined_scores.fin_percentiles  = (fin_p25,  fin_p50,  fin_p75)

    return bangladesh


def merge_scores_into_flood(flood: gpd.GeoDataFrame,
                             bangladesh: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    """
    Join district-level scores back onto the thana-level flood layer.

    Returns:
        Flood GeoDataFrame with combined_score, risk_tier,
        final_score, final_risk_tier, T_TL attached.
    """
    flood = flood.merge(
        bangladesh[[
            "NAME_2_clean", "combined_score", "risk_tier",
            "final_score",  "final_risk_tier", "T_TL",
        ]],
        left_on="DISTNAME_clean",
        right_on="NAME_2_clean",
        how="left",
    )
    flood["risk_tier"]       = flood["risk_tier"].fillna(1)
    flood["final_risk_tier"] = flood["final_risk_tier"].fillna(1)
    return flood