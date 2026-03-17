# DeltaShield: Bangladesh Disaster Risk Assessment & Visualization

![Python](https://img.shields.io/badge/python-3.8+-blue.svg)
![Folium](https://img.shields.io/badge/folium-0.20.0-green.svg)
![GeoPandas](https://img.shields.io/badge/geopandas-1.1.3-green.svg)
![License](https://img.shields.io/badge/license-MIT-blue.svg)

## Overview

**DeltaShield** is an advanced geospatial analytics platform designed to assess and visualize disaster risk across Bangladesh's administrative divisions. The system integrates multi-dimensional risk factors—flood hazards, population density, and critical infrastructure—to generate comprehensive risk scores and produce interactive web-based maps for disaster preparedness and response planning.

### Key Features

- **Interactive Risk Mapping**: Visualize district and thana-level disaster risk using choropleth and marker-based layers
- **Multi-Factor Risk Assessment**: Combines flood hazard, population exposure, and infrastructure vulnerability metrics
- **Infrastructure Awareness**: Identifies and maps critical facilities (hospitals, clinics, schools) to assess resource accessibility
- **Spatial Analytics**: Employs advanced geospatial operations (spatial joins, choropleth classification) for risk quantification
- **Customizable Visualization**: Tiered risk colorization with configurable thresholds and layer controls
- **Data-Driven Insights**: UI panels displaying aggregated statistics and risk breakdowns by category

---

## Project Structure

```
DeltaShield/
├── README.md                          # Project documentation (this file)
├── requirements.txt                   # Python dependency specifications
├── data/                              # Input datasets
│   ├── bangladesh_district.json       # District boundary GeoJSON
│   ├── osm_hospitals.csv              # Hospital locations (OpenStreetMap)
│   ├── osm_clinics.csv                # Clinic locations (OpenStreetMap)
│   ├── osm_schools.csv                # School locations (OpenStreetMap)
│   ├── flood/                         # Flood hazard vector data
│   │   └── bgd_nhr_floods_sparsso.*   # Shapefile: National Flood Hazard Risk
│   └── population/                    # Population statistics
│       └── bgd_admpop_adm2_2022.csv   # District-level population data (2022)
├── src/                               # Core application modules
│   ├── __init__.py                    # Package initialization
│   ├── main.py                        # Application entry point & orchestration
│   ├── config.py                      # Configuration, constants, weights, color maps
│   ├── data_loader.py                 # Data loading & preprocessing
│   ├── risk_scorer.py                 # Risk calculation & scoring logic
│   ├── map_builder.py                 # Folium map construction & layer management
│   ├── helpers.py                     # Utility functions (normalization, styling)
│   ├── ui_panels.py                   # UI legend and info panel generation
│   └── __pycache__/                   # Python cache (auto-generated)
├── scripts/                           # Standalone utility scripts
│   ├── openstreet_map_check.py        # Validate OSM data quality
│   ├── population.py                  # Population data analysis
│   ├── school.py                      # School infrastructure analysis
│   └── mismatches.py                  # Data validation & reconciliation
└── output/                            # Generated artifacts
    └── disaster_map.html              # Interactive web map (generated)
```

---

## Installation

### Prerequisites

- **Python 3.8+** (tested on Python 3.10+)
- **pip** package manager
- **Virtual Environment** (recommended)

### Setup Instructions

1. **Clone or download the project**:
   ```bash
   cd /path/to/DeltaShield
   ```

2. **Create and activate a virtual environment** (recommended):
   ```bash
   # Windows
   python -m venv venv
   venv\Scripts\activate

   # macOS/Linux
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

---

## Usage

### Running the Application

Execute the main application from the `src/` directory:

```bash
cd src
python main.py
```

**Expected Output**:
- Console logging of data loading, processing, and score computation stages
- Generation of `output/disaster_map.html` — an interactive web map
- Completion status message with file path

### Opening the Generated Map

1. Navigate to `output/disaster_map.html` in your project directory
2. Open the file in any web browser (Chrome, Firefox, Edge, Safari)
3. Interact with the map:
   - **Pan & Zoom**: Left-click and drag to move; scroll wheel to zoom
   - **Layer Toggle**: Use the control in the top-right to show/hide layers
   - **Search Districts**: Use the district search box to find specific administrative regions
   - **Inspect Data**: Click/hover on map features to view detailed information
   - **Explore UI Panels**: Review statistics and risk tier breakdowns in the legend/info sections

---

## Core Concepts & Methodology

### Risk Scoring Framework

DeltaShield employs a **weighted multi-factor** risk assessment model:

#### **1. Flood Risk Score**
- Derived from National Flood Hazard Risk (NFHR) shapefile data
- Captured at thana (sub-district) level
- Categories: Severe (≥7), High (≥5), Moderate (≥3), Low (<3)

#### **2. Population Exposure Score**
- Normalized district population from 2022 census data
- Measures demographic vulnerability within each district
- Higher density → higher exposure risk

#### **3. Infrastructure Vulnerability Score**
- Counts spatial distribution of critical facilities:
  - **Hospitals**: Emergency medical response capacity
  - **Clinics**: Primary health care availability
  - **Schools**: Community gathering & evacuation points
- Normalized to reflect resource allocation imbalances

#### **4. Combined Risk Score** (District Level)
```
combined_score = 0.70 × flood_score + 0.30 × population_score
```

#### **5. Final Risk Score** (With Infrastructure Adjustment)
```
final_score = 0.70 × flood_score + 0.20 × population_score + 0.10 × infrastructure_risk_score
```

### Risk Tiers

Districts are classified into four risk tiers based on percentile distribution:

| Tier | Classification | Color | Percentile Range |
|------|----------------|-------|------------------|
| 4 | **Critical** | Dark Red (#4a0000) | Top 25% |
| 3 | **High** | Red (#b71c1c) | 50–75% |
| 2 | **Moderate** | Orange (#e65100) | 25–50% |
| 1 | **Low** | Yellow (#ffc107) | Bottom 25% |

---

## Data Sources

| Dataset | Source | Format | Description |
|---------|--------|--------|-------------|
| **Boundaries** | bangladesh_district.json | GeoJSON | 64 district administrative boundaries |
| **Flood Hazard** | National Flood Hazard Risk (NFHR) | Shapefile (.shp) | Thana-level flood risk categories |
| **Population** | Bangladesh Bureau of Statistics (2022) | CSV | District population estimates |
| **Hospitals** | OpenStreetMap (curated) | CSV | Hospital facility locations & metadata |
| **Clinics** | OpenStreetMap (curated) | CSV | Clinic facility locations & metadata |
| **Schools** | OpenStreetMap (curated) | CSV | Educational institution locations |

---

## Module Documentation

### `main.py` — Application Orchestration
**Purpose**: Entry point that coordinates the complete pipeline.

**Flow**:
1. Load all geographic and demographic data
2. Merge population statistics into district boundaries
3. Calculate multi-dimensional risk scores
4. Build interactive Folium map
5. Render UI panels and legends
6. Save output as HTML file

**Run Command**: `python main.py`

---

### `config.py` — Configuration & Constants
**Purpose**: Centralized configuration management.

**Key Sections**:
- **Data Paths**: File references for all input/output datasets
- **Map Settings**: Folium map initialization (center, zoom, tiles)
- **Score Weights**: Weighting factors for risk calculation
- **Thresholds**: Flood category boundaries
- **Color Maps**: Tier colors, layer colors, marker colors

**Modification**: Adjust weights, colors, or thresholds by editing this file directly.

---

### `data_loader.py` — Data Loading & Preprocessing
**Purpose**: Load, clean, and validate all input data sources.

**Key Functions**:
- `load_boundaries()` → GeoDataFrame of district boundaries
- `load_population()` → DataFrame of population statistics
- `load_flood_data()` → GeoDataFrame of flood hazard polygons
- `load_infrastructure()` → Tuple of (hospitals, clinics, schools) GeoDataFrames
- `merge_population()` → Enriches boundaries with population data
- `slim_for_map()` → Optimizes data for web visualization

**Data Validation**: Checks for missing values, coordinate validity, and schema consistency.

---

### `risk_scorer.py` — Risk Computation
**Purpose**: Core scoring logic for multi-factor risk assessment.

**Key Functions**:
- `add_flood_scores()` → Computes flood risk per district
- `add_population_scores()` → Normalizes population exposure
- `add_infrastructure_scores()` → Counts facilities and calculates resource gaps
- `add_combined_scores()` → Merges flood + population scores
- `add_final_scores()` → Incorporates infrastructure factors
- `percentile_tier()` → Assigns risk tiers (1–4) based on percentile ranking

**Normalization**: All scores normalized to [0, 10] scale for comparability.

---

### `map_builder.py` — Geospatial Visualization
**Purpose**: Constructs interactive Folium map with multiple layers.

**Layer Types**:
1. **District Map**: Plain boundary layer with district search control
2. **Flood Layer**: Thana-level flood hazard choropleth (colored by category)
3. **Population Layer**: District population density choropleth
4. **Combined Risk Layer**: Multi-factor risk score choropleth (risk tiers)
5. **Infrastructure Markers**: Cluster-based markers for hospitals, clinics, schools

**Features**:
- Interactive layer toggle (radio controls)
- Feature group organization for performance
- Tooltips and popups with rich metadata
- Responsive styling functions
- Custom marker clustering for performance at zoom levels

---

### `ui_panels.py` — User Interface & Legends
**Purpose**: Generate interactive legend and statistics panels.

**Components**:
- **Legend**: Visual guide to color scales and tier definitions
- **Statistics Panel**: Aggregated counts by risk tier
- **Info Box**: Summary of data sources and methodology
- **Custom HTML/CSS**: Styled with responsive, accessible design

---

### `helpers.py` — Utility Functions
**Purpose**: Reusable functions for common operations.

**Key Utilities**:
- `normalize()` → Min-max normalization to [0, 10]
- `percentile_tier()` → Risk tier assignment
- `tier_color()` → Retrieve color code for a given tier
- `to_gdf()` → Convert DataFrame to GeoDataFrame
- Color mapping functions

---

### `scripts/` — Standalone Utilities

#### `openstreet_map_check.py`
Validates OpenStreetMap (OSM) infrastructure data for completeness and accuracy.

#### `population.py`
Analyzes population distribution patterns and generates demographic summaries.

#### `school.py`
Focuses on educational institution locations and coverage analysis.

#### `mismatches.py`
Identifies and reconciles data inconsistencies between datasets.

---

## Configuration Guide

### Adjusting Risk Weights

Edit `config.py` to modify the weighting scheme:

```python
SCORE_WEIGHTS = {
    "combined": {"flood": 0.70, "pop": 0.30},
    "final":    {"flood": 0.50, "pop": 0.30, "infra": 0.20},  # Example adjustment
}
```

**Impact**: Changes will be reflected in the next map generation.

---

### Customizing Colors

Modify `TIER_COLORS` or layer-specific color mappings in `config.py`:

```python
TIER_COLORS = {
    4: "#8b0000",  # Crimson red
    3: "#ff4500",  # Orange-red
    2: "#ffa500",  # Orange
    1: "#ffff00",  # Yellow
}
```

---

### Changing Map Center & Initial Zoom

```python
MAP_CENTER = [23.7, 90.4]      # [latitude, longitude]
MAP_ZOOM_START = 7              # Initial zoom level
MAP_MIN_ZOOM = 7                # Minimum allowed zoom
MAP_TILES = "cartodbpositron"   # Basemap provider
```

---

## Dependencies & Requirements

All project dependencies are pinned in `requirements.txt`:

```
folium==0.20.0           # Interactive mapping
geopandas==1.1.3         # Geospatial data operations
pandas==3.0.1            # Tabular data manipulation
shapely==2.1.2           # Geometric operations
pyproj==3.7.2            # Coordinate system transformations
```

**Install**: `pip install -r requirements.txt`

---

## Output & Deliverables

### Primary Output: `disaster_map.html`

An interactive web map with the following features:

- **Responsive Layout**: Works on desktop and tablet devices
- **Layer Controls**: Toggle between different risk visualization modes
- **Search Functionality**: Find districts by name
- **Hover/Click Information**: Display detailed metrics for each region
- **Statistics Sidebar**: Summary aggregations and risk breakdowns
- **Print-Ready**: Can be screenshot or saved as PDF via browser

### File Size
Typically 5–15 MB depending on data complexity.

### Browser Compatibility
- Chrome 90+
- Firefox 88+
- Edge 90+
- Safari 14+

---

## Troubleshooting

### Issue: Missing data files

**Error**: `FileNotFoundError: data/bangladesh_district.json not found`

**Solution**: Ensure all files in the `data/` directory exist. Check paths in `config.py`.

---

### Issue: Coordinate system mismatch

**Error**: Features not displaying correctly on the map

**Solution**: Verify that all shapefiles use EPSG:4326 (WGS84) projection. Use QGIS or `geopandas.GeoDataFrame.to_crs()` to reproject if needed.

---

### Issue: Out of memory with large datasets

**Error**: `MemoryError` during processing

**Solution**: 
1. Simplify geometries using `simplify()` in GeoPandas
2. Reduce marker clustering radius in `map_builder.py`
3. Increase system RAM or use a more powerful machine

---

### Issue: Map not rendering in browser

**Solution**:
1. Ensure JavaScript is enabled in your browser
2. Check browser console for errors (F12 → Console tab)
3. Try a different browser or clear cache (Ctrl+Shift+Delete)
4. Verify the HTML file path is correct

---
**Optimization Tips**:
- Simplify flood geometries if processing is slow
- Use marker clustering in `map_builder.py` for dense infrastructure datasets
- Consider spatial indexing (R-tree) for very large datasets (>100K features)

---


