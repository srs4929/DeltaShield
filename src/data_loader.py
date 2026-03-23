# data_loader.py
# Responsible for loading and cleaning all raw data files.
# Returns plain DataFrames / GeoDataFrames — no scoring logic here.

import geopandas as gpd
import pandas as pd
import requests
from pathlib import Path
from config import DATA_PATHS, FFWC_CONFIG, RIVER_DATA_CONFIG


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


def load_rivers_data() -> gpd.GeoDataFrame:
    """
    Load river network shapefile for Bangladesh.

    Returns:
        GeoDataFrame of river line geometries.
        Adds `river_name_clean` if a likely river-name field is found.
    """
    river_path = Path(DATA_PATHS["rivers"])
    if not river_path.exists():
        river_dir = river_path.parent
        shp_candidates = sorted(river_dir.glob("*.shp")) if river_dir.exists() else []
        if shp_candidates:
            river_path = shp_candidates[0]
            print(f"Warning: configured river shapefile not found. Using: {river_path}")
        else:
            print("Warning: no river shapefile found in data/rivers")
            return gpd.GeoDataFrame()

    gdf = gpd.read_file(river_path)

    candidate_cols = [
        c for c in gdf.columns
        if any(k in c.lower() for k in ["river", "name", "nam"])
    ]
    name_col = candidate_cols[0] if candidate_cols else None
    if name_col:
        gdf["river_name_clean"] = (
            gdf[name_col]
            .astype(str)
            .str.strip()
            .str.title()
            .replace({"Nan": None})
        )

    if "geometry" in gdf.columns:
        gdf = gdf[gdf.geometry.notna()].copy()

        minx, miny, maxx, maxy = RIVER_DATA_CONFIG["bbox"]
        try:
            gdf = gdf.cx[minx:maxx, miny:maxy].copy()
        except Exception:
            pass

        max_features = int(RIVER_DATA_CONFIG["max_features"])
        if len(gdf) > max_features:
            metric = gdf.to_crs(3857)
            geom_type = metric.geom_type.astype(str).str.lower()
            size = metric.geometry.length.where(geom_type.str.contains("line"), metric.geometry.area)
            gdf = gdf.assign(_size_metric=size.fillna(0.0))
            gdf = gdf.sort_values("_size_metric", ascending=False).head(max_features).copy()
            gdf = gdf.drop(columns=["_size_metric"])

        simplify_tolerance = (
            float(RIVER_DATA_CONFIG["simplify_tolerance_large"])
            if len(gdf) > (max_features // 2)
            else float(RIVER_DATA_CONFIG["simplify_tolerance_small"])
        )
        gdf["geometry"] = gdf["geometry"].simplify(
            tolerance=simplify_tolerance,
            preserve_topology=True,
        )

        print(f"✓ Rivers prepared for map: {len(gdf)} features")

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


def load_waterlevel_data() -> pd.DataFrame:
    """
    Load near-real-time river gauge observations from FFWC API.

    Returns:
        DataFrame with parsed numeric columns and coordinates.
        Returns an empty DataFrame on API/network/parse failure.
    """
    url = FFWC_CONFIG["api_url"]
    timeout_sec = FFWC_CONFIG["timeout_sec"]

    try:
        response = requests.get(url, timeout=timeout_sec)
        response.raise_for_status()
        payload = response.json()
    except Exception as exc:
        print(f"Warning: Could not load FFWC water level data ({exc})")
        return pd.DataFrame()

    if not isinstance(payload, list) or len(payload) == 0:
        print("Warning: FFWC API returned empty/invalid payload")
        return pd.DataFrame()

    stations = pd.DataFrame(payload)

    # Keep only fields needed for map + risk logic (if available)
    keep_cols = [
        "st_id", "station_serial_no", "name", "lat", "long", "river",
        "division", "district", "upazilla", "union", "wl_date",
        "waterlevel", "dangerlevel", "riverhighestwaterlevel",
    ]
    stations = stations[[c for c in keep_cols if c in stations.columns]].copy()

    if "long" in stations.columns and "lon" not in stations.columns:
        stations = stations.rename(columns={"long": "lon"})

    for col in ["lat", "lon", "waterlevel", "dangerlevel", "riverhighestwaterlevel"]:
        if col in stations.columns:
            stations[col] = pd.to_numeric(stations[col], errors="coerce")

    if "wl_date" in stations.columns:
        stations["wl_date"] = pd.to_datetime(stations["wl_date"], errors="coerce", utc=True)

    stations = stations.dropna(subset=["lat", "lon", "waterlevel", "dangerlevel"])

    if stations.empty:
        print("Warning: FFWC data had no usable station records")
    else:
        print(f"✓ Loaded {len(stations)} water level stations from FFWC API")
        print(f"  Sample districts: {stations['district'].unique()[:3].tolist()}")

    return stations