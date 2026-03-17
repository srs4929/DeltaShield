# data_loader.py
# Responsible for loading and cleaning all raw data files.
# Returns plain DataFrames / GeoDataFrames — no scoring logic here.

import geopandas as gpd
import pandas as pd
from config import DATA_PATHS


def load_boundaries() -> gpd.GeoDataFrame:
    """
    Load Bangladesh district boundaries and add a cleaned name column.

    Returns:
        GeoDataFrame with columns including NAME_2, NAME_2_clean, geometry.
    """
    gdf = gpd.read_file(DATA_PATHS["boundaries"])
    gdf["NAME_2_clean"] = gdf["NAME_2"].str.strip().str.title()

    # Fix known name mismatches between boundary and population data
    gdf["NAME_2_clean"] = gdf["NAME_2_clean"].replace(
        {"Cox'Sbazar": "Cox'S Bazar"}
    )
    return gdf


def load_population() -> pd.DataFrame:
    """
    Load 2022 district-level population data.

    Returns:
        DataFrame with columns: NAME_2_clean, T_TL, M_TL, F_TL.
    """
    df = pd.read_csv(DATA_PATHS["population"])
    df["NAME_2_clean"] = df["ADM2_NAME"].str.strip().str.title()
    return df[["NAME_2_clean", "T_TL", "M_TL", "F_TL"]]


def load_flood_data() -> gpd.GeoDataFrame:
    """
    Load flood hazard shapefile and add a cleaned district name column.
    Geometry is simplified to reduce file size and speed up map rendering.

    Returns:
        GeoDataFrame with columns including DISTNAME, THANANAME, FLOODCAT,
        FLOODCAT_L, DISTNAME_clean, geometry.
    """
    gdf = gpd.read_file(DATA_PATHS["flood"])
    gdf = gdf.dropna(subset=["DISTNAME", "THANANAME"])
    gdf["DISTNAME_clean"] = gdf["DISTNAME"].str.strip().str.title()

    # Simplify geometry — tolerance in degrees (~50m at Bangladesh latitude).
    # preserve_topology=True prevents gaps/overlaps between polygons.
    gdf["geometry"] = gdf["geometry"].simplify(
        tolerance=0.0005, preserve_topology=True
    )
    return gdf


def load_infrastructure():
    """
    Load hospital, clinic, and school point CSVs.

    Returns:
        Tuple of (hospitals_df, clinics_df, schools_df).
    """
    hospitals = pd.read_csv(DATA_PATHS["hospitals"])
    clinics   = pd.read_csv(DATA_PATHS["clinics"])
    schools   = pd.read_csv(DATA_PATHS["schools"])
    return hospitals, clinics, schools


def merge_population(boundaries: gpd.GeoDataFrame,
                     pop_df: pd.DataFrame) -> gpd.GeoDataFrame:
    """
    Merge population figures into the boundaries GeoDataFrame.

    Args:
        boundaries: Output of load_boundaries().
        pop_df:     Output of load_population().

    Returns:
        GeoDataFrame with T_TL, M_TL, F_TL columns attached.
    """
    return boundaries.merge(pop_df, on="NAME_2_clean", how="left")


def slim_for_map(gdf: gpd.GeoDataFrame, keep_cols: list) -> gpd.GeoDataFrame:
    """
    Drop all columns except those needed for map rendering.
    Reduces the GeoJSON payload embedded in the HTML, speeding up load time.

    Args:
        gdf:       Any GeoDataFrame.
        keep_cols: List of column names to retain (geometry is always kept).

    Returns:
        Slimmed GeoDataFrame.
    """
    cols = [c for c in keep_cols if c in gdf.columns] + ["geometry"]
    return gdf[cols].copy()