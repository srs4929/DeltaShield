# DeltaShield: Bangladesh Disaster Risk Assessment & Visualization

## Overview

**DeltaShield** is a geospatial platform that helps visualize, assess, and predict disaster risk across Bangladesh. It combines flood hazards, population data, and critical infrastructure (hospitals, clinics, schools) to calculate risk scores for districts and thanas. Users can explore interactive maps, see which areas are most at risk, and make informed decisions to prepare for disasters. DeltaShield also uses machine learning to predict which districts may face problems in the future, helping authorities and planners take action before disasters happen.

### Key Features

- **Interactive Risk Mapping**: Visualize district and thana-level disaster risk using choropleth and marker-based layers
- **Multi-Factor Risk Assessment**: Combines flood hazard, population exposure, and infrastructure vulnerability metrics
- **Infrastructure Awareness**: Identifies and maps critical facilities (hospitals, clinics, schools) to assess resource accessibility
- **Spatial Analytics**: Employs advanced geospatial operations (spatial joins, choropleth classification) for risk quantification
- **Predictive Risk Analysis**: Uses machine learning to forecast district-level vulnerability, helping authorities anticipate future impacts.
- **Customizable Visualization**: Tiered risk colorization with configurable thresholds and layer controls
- **Data-Driven Insights**: UI panels displaying aggregated statistics and risk breakdowns by category

---

### Map Layers Preview

| Flood                                                                                                                               | Population                                                                                                                          |
| ----------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------- |
| <img width="1358" height="631" alt="Image" src="https://github.com/user-attachments/assets/d247e9ec-eb08-48b5-bf74-21213dfaa320" /> | <img width="1366" height="646" alt="Image" src="https://github.com/user-attachments/assets/9002b18b-2ec6-4a7a-98dd-03b4c984678e" /> |

| Flood + Population                                                                                                                  | Flood + Population + Infrastructure                                                                                                 |
| ----------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------- |
| <img width="1366" height="645" alt="Image" src="https://github.com/user-attachments/assets/f236f61b-57bd-415e-be3a-1cac0e407d0e" /> | <img width="1358" height="657" alt="Image" src="https://github.com/user-attachments/assets/59c212e1-3bbc-44f1-a37d-7896df0f7ab3" /> |

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
│   ├── predictor.py                   # Machine learning prediction pipeline
│   ├── helpers.py                     # Utility functions (normalization, styling)
│   ├── ui_panels.py                   # UI legend and info panel generation
│
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

| Tier | Classification | Color              | Percentile Range |
| ---- | -------------- | ------------------ | ---------------- |
| 4    | **Critical**   | Dark Red (#4a0000) | Top 25%          |
| 3    | **High**       | Red (#b71c1c)      | 50–75%           |
| 2    | **Moderate**   | Orange (#e65100)   | 25–50%           |
| 1    | **Low**        | Yellow (#ffc107)   | Bottom 25%       |

---

### Machine Learning-Based Prediction

In addition to rule-based risk scoring, DeltaShield uses ensemble machine learning models (Random Forest and Gradient Boosting) to identify district-level vulnerability. The system automatically selects the best-performing model based on cross-validation results.

The model uses the following key factors:

- Average flood category
- Neighboring districts' flood risk (spatial context)
- Total population
- Infrastructure counts (hospitals, clinics, schools)
- Infrastructure density per 100,000 population

A district is classified as **compound-risk** when multiple risk factors are high at the same time — especially flood exposure, population pressure, and limited infrastructure. This ensures that flood risk remains a key driver of vulnerability.

The model provides:

- **Predicted risk tier** (compound-risk or lower-risk)
- **Risk probability** — likelihood of being high-risk (0.0–1.0)
- **Top risk factor** — the most important factor behind the prediction

The model also highlights the most influential factor for each district, improving transparency and helping users understand why a district is considered at risk. Model performance is evaluated using cross-validation methods to ensure reliable results, especially for small datasets like Bangladesh’s 64 districts. Probability outputs are adjusted to better reflect real-world likelihood, making the predictions more reliable.

---

## Data Sources

| Dataset          | Source                                 | Format           | Description                            |
| ---------------- | -------------------------------------- | ---------------- | -------------------------------------- |
| **Boundaries**   | bangladesh_district.json               | GeoJSON          | 64 district administrative boundaries  |
| **Flood Hazard** | National Flood Hazard Risk (NFHR)      | Shapefile (.shp) | Thana-level flood risk categories      |
| **Population**   | Bangladesh Bureau of Statistics (2022) | CSV              | District population estimates          |
| **Hospitals**    | OpenStreetMap (curated)                | CSV              | Hospital facility locations & metadata |
| **Clinics**      | OpenStreetMap (curated)                | CSV              | Clinic facility locations & metadata   |
| **Schools**      | OpenStreetMap (curated)                | CSV              | Educational institution locations      |

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

### `predictor.py` — Machine Learning Risk Prediction

**Purpose**: Train and deploy a predictive classifier for district-level vulnerability assessment.

**Key Functions**:

- `add_spatial_features()` → Computes `neighbor_avg_floodcat` (mean flood category of adjacent districts)
- `add_vulnerability_target()` → Generates binary `compound_risk` label using weighted 3-factor rule (flood × 2 points + pop × 1 + infra × 1; label = 1 if score ≥ 2)
- `build_features()` → Extracts feature matrix from enriched dataset; NaN-fills with median
- `evaluate()` → Runs Stratified 5-fold and Leave-One-Out cross-validation; reports weighted F1
- `train_model()` → Trains Random Forest and Gradient Boosting candidates, selects winner by LOO score, calibrates probabilities via Platt scaling, saves `output/flood_risk_model.pkl`, reports permutation importances
- `load_model()` → Loads saved model with feature schema validation; auto-deletes stale models
- `predict()` → Applies trained model to annotate districts with `predicted_risk_tier`, `risk_probability` (calibrated P(vulnerable)), and `top_risk_factor` (most influential feature per district)
- `get_feature_importance()` → Returns feature importances as DataFrame with permutation or impurity scores

**Model Features** (7 total):

- `avg_floodcat`: Average flood category per district
- `neighbor_avg_floodcat`: Spatial adjacency context
- `T_TL`: Raw population count
- `hosp_count`, `clinic_count`, `school_count`: Infrastructure facility counts
- `infra_per_100k`: Infrastructure density per 100k population

**Calibration Method**: Logistic Regression (Platt scaling) on out-of-fold probability scores from cross-validation.

**Output Artifact**: `output/flood_risk_model.pkl` (serialized CalibratedModel wrapper with base estimator + Platt scaler).

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
