# config.py
# All constants, paths, weights, and color maps for the disaster map project.


# Data Paths

DATA_PATHS = {
    "boundaries":  "../data/bangladesh_district.json",
    "flood":       "../data/flood/bgd_nhr_floods_sparsso.shp",
    "population":  "../data/population/bgd_admpop_adm2_2022.csv",
    "hospitals":   "../data/osm_hospitals.csv",
    "clinics":     "../data/osm_clinics.csv",
    "schools":     "../data/osm_schools.csv",
    "output":      "../output/disaster_map.html",
}

# Map Settings

MAP_CENTER      = [23.7, 90.4]
MAP_ZOOM_START  = 7
MAP_MIN_ZOOM    = 7
MAP_TILES       = "cartodbpositron"

# -----------------------
# Score Weights
# -----------------------
# combined_score  = FLOOD_W * flood_score  + POP_W * pop_score
# final_score     = FLOOD_W * flood_score  + POP_W_FINAL * pop_score + INFRA_W * infra_risk_score
SCORE_WEIGHTS = {
    "combined": {"flood": 0.70, "pop": 0.30},
    "final":    {"flood": 0.70, "pop": 0.20, "infra": 0.10},
}

# -----------------------
# Flood Category Thresholds (used in style functions)
# -----------------------
FLOOD_THRESHOLDS = {
    "severe":   7,   # >= severe  → darkest red
    "high":     5,   # >= high    → red
    "moderate": 3,   # >= moderate → orange
    # below 3  → yellow
}

# -----------------------
# Tier Colors  (risk tier 1–4)
# -----------------------
TIER_COLORS = {
    4: "#4a0000",  # Critical
    3: "#b71c1c",  # High
    2: "#e65100",  # Moderate
    1: "#f9a825",  # Low
}

TIER_LABELS = {
    4: "Critical",
    3: "High",
    2: "Moderate",
    1: "Low",
}

# Flood-hazard layer colors keyed by FLOODCAT threshold
FLOOD_LAYER_COLORS = {
    "severe":   "#800000",
    "high":     "#e53935",
    "moderate": "#fb8c00",
    "low":      "#fdd835",
}

# Population choropleth colors (ratio thresholds 0–1)
POP_LAYER_COLORS = [
    (0.8, "#08306b"),
    (0.6, "#2171b5"),
    (0.4, "#4eb3d3"),
    (0.2, "#a8ddb5"),
    (0.0, "#edf8fb"),
]

# Infrastructure marker colors
INFRA_MARKER_COLORS = {
    "hospital": "#e53935",
    "clinic":   "#1a73e8",
    "school":   "#2e7d32",
}