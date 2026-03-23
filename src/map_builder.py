# map_builder.py
# Builds the Folium map and adds all geographic layers and infrastructure markers.
# Returns a folium.Map object. No scoring logic lives here.

import pandas as pd
import folium
from folium.plugins import Search, MarkerCluster
from folium import DivIcon

from helpers import tier_color
from config import (
    MAP_CENTER, MAP_ZOOM_START, MAP_MIN_ZOOM, MAP_TILES,
    FLOOD_THRESHOLDS, FLOOD_LAYER_COLORS, POP_LAYER_COLORS,
    INFRA_MARKER_COLORS, WATERLEVEL_ALERT_COLORS, WATERLEVEL_ALERT, WATERLEVEL_UI_COLORS,
)


# -----------------------
# Map initialisation
# -----------------------
def build_map(bangladesh) -> folium.Map:
    """
    Create the base Folium map, fit to Bangladesh bounds.

    Returns:
        folium.Map
    """
    minx, miny, maxx, maxy = bangladesh.total_bounds
    m = folium.Map(
        location=MAP_CENTER,
        zoom_start=MAP_ZOOM_START,
        max_bounds=True,
        min_zoom=MAP_MIN_ZOOM,
        tiles=MAP_TILES,
    )
    m.fit_bounds([[miny, minx], [maxy, maxx]])
    return m


# -----------------------
# District (normal) layer
# -----------------------
def add_district_layer(m: folium.Map, bangladesh) -> folium.FeatureGroup:
    """
    Add the plain district boundary layer with a search control.

    Returns:
        The FeatureGroup (needed by the radio toggle JS).
    """
    fg = folium.FeatureGroup(name="District Map", show=True)
    folium.GeoJson(
        bangladesh,
        style_function=lambda x: {
            "fillColor": "#e6f2ff",
            "color": "#1a1a1a",
            "weight": 1.5,
            "fillOpacity": 0.4,
        },
        tooltip=folium.GeoJsonTooltip(fields=["NAME_2"], aliases=["District:"]),
    ).add_to(fg)
    fg.add_to(m)

    Search(
        layer=fg,
        search_label="NAME_2",
        placeholder="Search district",
        collapsed=False,
    ).add_to(m)

    m.get_root().html.add_child(folium.Element("""
<style>
.leaflet-control-search input {
    width:300px !important; height:35px !important; font-size:16px !important;
}
</style>"""))

    return fg


# -----------------------
# Flood layer
# -----------------------
def add_flood_layer(m: folium.Map, flood) -> folium.FeatureGroup:
    """
    Add thana-level flood hazard choropleth layer.

    Returns:
        The FeatureGroup.
    """
    severe   = FLOOD_THRESHOLDS["severe"]
    high     = FLOOD_THRESHOLDS["high"]
    moderate = FLOOD_THRESHOLDS["moderate"]

    def flood_style(feature):
        risk = feature["properties"].get("FLOODCAT") or 0
        if risk >= severe:
            color = FLOOD_LAYER_COLORS["severe"]
        elif risk >= high:
            color = FLOOD_LAYER_COLORS["high"]
        elif risk >= moderate:
            color = FLOOD_LAYER_COLORS["moderate"]
        else:
            color = FLOOD_LAYER_COLORS["low"]
        return {"fillColor": color, "color": color, "weight": 0.5, "fillOpacity": 0.7}

    fg = folium.FeatureGroup(name="Flood Hazard", show=False)
    folium.GeoJson(
        flood,
        style_function=flood_style,
        tooltip=folium.GeoJsonTooltip(
            fields=["DISTNAME", "THANANAME", "FLOODCAT_L"],
            aliases=["District:", "Thana:", "Flood Risk:"],
        ),
    ).add_to(fg)
    fg.add_to(m)
    return fg


# -----------------------
# Population layer
# -----------------------
def add_population_layer(m: folium.Map, bangladesh) -> folium.FeatureGroup:
    """
    Add district-level population choropleth layer.

    Returns:
        The FeatureGroup.
    """
    pop_min = float(bangladesh["T_TL"].min())
    pop_max = float(bangladesh["T_TL"].max())

    def pop_color(val):
        if not val or pd.isna(val):
            return "#cccccc"
        ratio = (float(val) - pop_min) / (pop_max - pop_min)
        for threshold, color in POP_LAYER_COLORS:
            if ratio >= threshold:
                return color
        return POP_LAYER_COLORS[-1][1]

    fg = folium.FeatureGroup(name="Population", show=False)
    folium.GeoJson(
        bangladesh,
        style_function=lambda x: {
            "fillColor": pop_color(x["properties"].get("T_TL")),
            "color": "black",
            "weight": 0.8,
            "fillOpacity": 0.75,
        },
        tooltip=folium.GeoJsonTooltip(
            fields=["NAME_2", "T_TL", "M_TL", "F_TL"],
            aliases=["District:", "Total:", "Male:", "Female:"],
            localize=True,
        ),
    ).add_to(fg)
    fg.add_to(m)
    return fg


# -----------------------
# Combined risk layers
# -----------------------
def add_combined_layers(m: folium.Map,
                         bangladesh,
                         flood):
    """
    Add combined risk (flood + population) district and thana layers.

    Returns:
        (district_fg, thana_fg)
    """
    # District
    dist_fg = folium.FeatureGroup(name="Combined Risk District", show=False)
    folium.GeoJson(
        bangladesh,
        style_function=lambda x: {
            "fillColor": tier_color(x["properties"].get("risk_tier", 1)),
            "color": "black",
            "weight": 1.0,
            "fillOpacity": 0.75,
        },
        tooltip=folium.GeoJsonTooltip(
            fields=["NAME_2", "T_TL", "avg_floodcat", "combined_score", "risk_tier"],
            aliases=["District:", "Population:", "Avg Flood:", "Score:", "Tier:"],
            localize=True,
        ),
    ).add_to(dist_fg)
    dist_fg.add_to(m)

    # Thana
    def combined_thana_style(feature):
        tier     = int(feature["properties"].get("risk_tier") or 1)
        floodcat = float(feature["properties"].get("FLOODCAT") or 0)
        if tier >= 4 and floodcat >= 7:
            return {"fillColor": "#4a0000", "color": "#4a0000", "weight": 1.0, "fillOpacity": 0.85}
        elif tier >= 3 and floodcat >= 5:
            return {"fillColor": "#b71c1c", "color": "#b71c1c", "weight": 0.8, "fillOpacity": 0.75}
        elif tier >= 2 and floodcat >= 3:
            return {"fillColor": "#e65100", "color": "#e65100", "weight": 0.5, "fillOpacity": 0.50}
        else:
            return {"fillColor": "#f9a825", "color": "#f9a825", "weight": 0.3, "fillOpacity": 0.25}

    thana_fg = folium.FeatureGroup(name="Combined Risk Thana", show=False)
    folium.GeoJson(
        flood,
        style_function=combined_thana_style,
        tooltip=folium.GeoJsonTooltip(
            fields=["DISTNAME", "THANANAME", "FLOODCAT_L", "combined_score"],
            aliases=["District:", "Thana:", "Flood Risk:", "Score:"],
            localize=True,
        ),
    ).add_to(thana_fg)
    thana_fg.add_to(m)

    return dist_fg, thana_fg


# -----------------------
# Final risk layers
# -----------------------
def add_final_layers(m: folium.Map,
                      bangladesh,
                      flood):
    """
    Add final risk (flood + pop + infrastructure) district and thana layers.

    Returns:
        (district_fg, thana_fg)
    """
    # District
    dist_fg = folium.FeatureGroup(name="Final Risk District", show=False)
    folium.GeoJson(
        bangladesh,
        style_function=lambda x: {
            "fillColor": tier_color(x["properties"].get("final_risk_tier", 1)),
            "color": "black",
            "weight": 1.0,
            "fillOpacity": 0.75,
        },
        tooltip=folium.GeoJsonTooltip(
            fields=[
                "NAME_2", "T_TL", "avg_floodcat",
                "hosp_count", "clinic_count", "school_count",
                "final_score", "final_risk_tier",
            ],
            aliases=[
                "District:", "Population:", "Avg Flood:",
                "Hospitals:", "Clinics:", "Schools:",
                "Final Score:", "Risk Tier:",
            ],
            localize=True,
        ),
    ).add_to(dist_fg)
    dist_fg.add_to(m)

    # Thana
    def final_thana_style(feature):
        tier     = int(feature["properties"].get("final_risk_tier") or 1)
        floodcat = float(feature["properties"].get("FLOODCAT") or 0)
        if tier >= 4 and floodcat >= 7:
            return {"fillColor": "#4a0000", "color": "#4a0000", "weight": 1.0, "fillOpacity": 0.85}
        elif tier >= 3 and floodcat >= 5:
            return {"fillColor": "#b71c1c", "color": "#b71c1c", "weight": 0.8, "fillOpacity": 0.75}
        elif tier >= 2 and floodcat >= 3:
            return {"fillColor": "#e65100", "color": "#e65100", "weight": 0.5, "fillOpacity": 0.50}
        else:
            return {"fillColor": "#f9a825", "color": "#f9a825", "weight": 0.3, "fillOpacity": 0.25}

    thana_fg = folium.FeatureGroup(name="Final Risk Thana", show=False)
    folium.GeoJson(
        flood,
        style_function=final_thana_style,
        tooltip=folium.GeoJsonTooltip(
            fields=["DISTNAME", "THANANAME", "FLOODCAT_L", "final_score"],
            aliases=["District:", "Thana:", "Flood Risk:", "Final Score:"],
            localize=True,
        ),
    ).add_to(thana_fg)
    thana_fg.add_to(m)

    return dist_fg, thana_fg


# -----------------------
# Infrastructure markers
# -----------------------
def _make_marker_layer(m: folium.Map,
                        df: pd.DataFrame,
                        layer_name: str,
                        emoji: str,
                        color: str) -> folium.FeatureGroup:
    """Internal helper: create a clustered marker layer from a point DataFrame."""
    fg      = folium.FeatureGroup(name=layer_name, show=False)
    cluster = MarkerCluster(
        options={"maxClusterRadius": 40, "disableClusteringAtZoom": 12}
    ).add_to(fg)

    for _, row in df.iterrows():
        if pd.isna(row["lat"]) or pd.isna(row["lon"]):
            continue
        folium.Marker(
            location=[row["lat"], row["lon"]],
            tooltip=str(row["name"]),
            popup=folium.Popup(
                f"<b>{row['name']}</b><br>"
                f"Type: {row['amenity']}<br>"
                f"District: {row.get('district', 'N/A')}",
                max_width=220,
            ),
            icon=DivIcon(
                html=f"""<div style="
                    width:20px;height:20px;
                    background:{color};
                    border-radius:50%;
                    border:2px solid white;
                    box-shadow:0 1px 4px rgba(0,0,0,0.4);
                    display:flex;align-items:center;justify-content:center;
                    font-size:11px;line-height:20px;text-align:center;">
                    {emoji}</div>""",
                icon_size=(20, 20),
                icon_anchor=(10, 10),
                popup_anchor=(0, -10),
            ),
        ).add_to(cluster)

    fg.add_to(m)
    return fg


def add_infra_markers(m: folium.Map,
                       hospitals: pd.DataFrame,
                       clinics: pd.DataFrame,
                       schools: pd.DataFrame):
    """
    Add hospital, clinic, and school clustered marker layers.

    Returns:
        (hosp_fg, clinic_fg, school_fg)
    """
    hosp_fg   = _make_marker_layer(m, hospitals, "Hospitals",         "🏥", INFRA_MARKER_COLORS["hospital"])
    clinic_fg = _make_marker_layer(m, clinics,   "Clinics",           "💊", INFRA_MARKER_COLORS["clinic"])
    school_fg = _make_marker_layer(m, schools,   "Schools / Shelters","🏫", INFRA_MARKER_COLORS["school"])
    return hosp_fg, clinic_fg, school_fg


def _station_alert_level(row: pd.Series) -> int:
    """Compute station-level alert from observed water and danger level."""
    wl = row.get("waterlevel")
    dl = row.get("dangerlevel")
    warning_exceedance = float(WATERLEVEL_ALERT.get("warning_exceedance_m", 0.0))
    if pd.isna(wl) or pd.isna(dl):
        return int(WATERLEVEL_ALERT["none"])
    if float(wl) >= float(dl) + warning_exceedance:
        return int(WATERLEVEL_ALERT["warning"])
    if float(wl) >= float(dl) - float(WATERLEVEL_ALERT["watch_buffer_m"]):
        return int(WATERLEVEL_ALERT["watch"])
    return int(WATERLEVEL_ALERT["none"])


def add_water_alert_layers(m: folium.Map,
                           rivers,
                           stations: pd.DataFrame):
    """
    Add river polylines and gauge station markers for real-time water alerts.

    River styling is linked to station status by river name when available.

    Returns:
        (river_fg, station_fg)
    """
    river_fg = folium.FeatureGroup(name="Rivers (Water Alert)", show=False)
    station_fg = folium.FeatureGroup(name="Gauge Stations (Water Alert)", show=False)

    stations_map = stations.copy() if stations is not None else pd.DataFrame()
    if not stations_map.empty:
        stations_map["station_alert_level"] = stations_map.apply(_station_alert_level, axis=1)
        level_label = {
            int(WATERLEVEL_ALERT["none"]): "No Alert",
            int(WATERLEVEL_ALERT["watch"]): "Watch",
            int(WATERLEVEL_ALERT["warning"]): "Warning",
        }
        stations_map["station_alert_label"] = stations_map["station_alert_level"].map(level_label).fillna("No Alert")
        if "river" in stations_map.columns:
            stations_map["river_clean"] = stations_map["river"].astype(str).str.strip().str.title()

    if rivers is not None and len(rivers) > 0:
        rivers_map = rivers.copy()
        rivers_map["river_alert_level"] = int(WATERLEVEL_ALERT["none"])
        rivers_map["river_alert_label"] = "No Alert"

        if (
            not stations_map.empty
            and "river_name_clean" in rivers_map.columns
            and "river_clean" in stations_map.columns
        ):
            river_alert = (
                stations_map.groupby("river_clean")["station_alert_level"]
                .max()
                .reset_index()
            )
            river_alert.columns = ["river_name_clean", "river_alert_level"]
            rivers_map = rivers_map.merge(river_alert, on="river_name_clean", how="left", suffixes=("", "_obs"))
            rivers_map["river_alert_level"] = (
                rivers_map["river_alert_level_obs"]
                .fillna(rivers_map["river_alert_level"])
                .fillna(int(WATERLEVEL_ALERT["none"]))
                .astype(int)
            )
            rivers_map = rivers_map.drop(columns=[c for c in ["river_alert_level_obs"] if c in rivers_map.columns])

        label_map = {
            int(WATERLEVEL_ALERT["none"]): "No Alert",
            int(WATERLEVEL_ALERT["watch"]): "Watch",
            int(WATERLEVEL_ALERT["warning"]): "Warning",
        }
        rivers_map["river_alert_label"] = rivers_map["river_alert_level"].map(label_map).fillna("No Alert")

        def river_style(feature):
            level = int(feature["properties"].get("river_alert_level", WATERLEVEL_ALERT["none"]))
            color = WATERLEVEL_ALERT_COLORS.get(level, WATERLEVEL_UI_COLORS["river_default"])
            if level == int(WATERLEVEL_ALERT["none"]):
                color = WATERLEVEL_UI_COLORS["river_default"]
            return {
                "color": color,
                "weight": 2.5,
                "opacity": 0.75,
            }

        tooltip_fields = [c for c in ["river_name_clean", "river_alert_label"] if c in rivers_map.columns]
        tooltip_aliases = ["River:", "Status:"][:len(tooltip_fields)]

        folium.GeoJson(
            rivers_map,
            style_function=river_style,
            tooltip=folium.GeoJsonTooltip(fields=tooltip_fields, aliases=tooltip_aliases) if tooltip_fields else None,
            name="Rivers (Water Alert)",
        ).add_to(river_fg)

    if not stations_map.empty:
        cluster = MarkerCluster(
            options={"maxClusterRadius": 40, "disableClusteringAtZoom": 11}
        ).add_to(station_fg)
        print(f"✓ Rendering {len(stations_map)} gauge stations")
        southern_sample = stations_map[stations_map["district"].isin(["Chattogram", "Cox's Bazar", "Feni", "Chandpur"])][["name", "district", "lat", "lon"]].head(3)
        if not southern_sample.empty:
            print("  Sample southern stations:")
            for _, s in southern_sample.iterrows():
                print(f"    - {s['name']} ({s['district']}) @ ({s['lat']:.2f}, {s['lon']:.2f})")
        

        for _, row in stations_map.iterrows():
            if pd.isna(row.get("lat")) or pd.isna(row.get("lon")):
                continue

            level = int(row.get("station_alert_level", WATERLEVEL_ALERT["none"]))
            color = WATERLEVEL_ALERT_COLORS.get(level, WATERLEVEL_ALERT_COLORS[int(WATERLEVEL_ALERT["none"])])

            wl = row.get("waterlevel")
            dl = row.get("dangerlevel")
            wl_txt = f"{float(wl):.2f}" if pd.notna(wl) else "N/A"
            dl_txt = f"{float(dl):.2f}" if pd.notna(dl) else "N/A"
            date_txt = row.get("wl_date")
            if pd.notna(date_txt):
                date_txt = str(pd.to_datetime(date_txt, errors="coerce"))

            popup = (
                f"<b>{row.get('name', 'Unknown Station')}</b><br>"
                f"River: {row.get('river', 'N/A')}<br>"
                f"District: {row.get('district', 'N/A')}<br>"
                f"Water Level: {wl_txt} m<br>"
                f"Danger Level: {dl_txt} m<br>"
                f"Status: <b>{row.get('station_alert_label', 'No Alert')}</b><br>"
                f"Observed: {date_txt if pd.notna(date_txt) else 'N/A'}"
            )

            folium.CircleMarker(
                location=[float(row["lat"]), float(row["lon"])],
                radius=6,
                color="#222",
                weight=1,
                fill=True,
                fill_color=color,
                fill_opacity=0.9,
                tooltip=f"{row.get('name', 'Station')} — {row.get('station_alert_label', 'No Alert')}",
                popup=folium.Popup(popup, max_width=270),
            ).add_to(cluster)

    river_fg.add_to(m)
    station_fg.add_to(m)
    return river_fg, station_fg