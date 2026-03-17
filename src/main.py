# main.py
# Entry point. Orchestrates loading → scoring → map building → UI → save.
# Run: python main.py

import folium
from data_loader import (
    load_boundaries,
    load_population,
    load_flood_data,
    load_infrastructure,
    merge_population,
    slim_for_map,
)
from risk_scorer import (
    add_infrastructure_scores,
    add_flood_scores,
    add_combined_scores,
    merge_scores_into_flood,
)
from map_builder import (
    build_map,
    add_district_layer,
    add_flood_layer,
    add_population_layer,
    add_combined_layers,
    add_final_layers,
    add_infra_markers,
)
from ui_panels import add_all_ui
from config import DATA_PATHS


def main():
    # ------------------------------------------------------------------
    # 1. Load data
    # ------------------------------------------------------------------
    print("Loading data...")
    boundaries          = load_boundaries()
    pop_df              = load_population()
    flood               = load_flood_data()
    hospitals, clinics, schools = load_infrastructure()

    # ------------------------------------------------------------------
    # 2. Merge population into boundaries
    # ------------------------------------------------------------------
    bangladesh = merge_population(boundaries, pop_df)

    # ------------------------------------------------------------------
    # 3. Score
    # ------------------------------------------------------------------
    print("Computing scores...")
    bangladesh = add_infrastructure_scores(bangladesh, hospitals, clinics, schools)
    bangladesh = add_flood_scores(bangladesh, flood)
    bangladesh = add_combined_scores(bangladesh)
    flood      = merge_scores_into_flood(flood, bangladesh)

    # Retrieve stored percentile breakpoints for legend rendering
    comb_percentiles = add_combined_scores.comb_percentiles
    fin_percentiles  = add_combined_scores.fin_percentiles

    # ------------------------------------------------------------------
    # 4. Slim columns to reduce GeoJSON payload size in the HTML output
    # ------------------------------------------------------------------
    bangladesh_map = slim_for_map(bangladesh, [
        "NAME_2", "NAME_2_clean", "T_TL", "M_TL", "F_TL",
        "avg_floodcat", "hosp_count", "clinic_count", "school_count",
        "combined_score", "risk_tier", "final_score", "final_risk_tier",
    ])
    flood_map = slim_for_map(flood, [
        "DISTNAME", "THANANAME", "FLOODCAT", "FLOODCAT_L", "DISTNAME_clean",
        "combined_score", "risk_tier", "final_score", "final_risk_tier", "T_TL",
    ])

    # ------------------------------------------------------------------
    # 5. Build map + layers
    # ------------------------------------------------------------------
    print("Building map...")
    m = build_map(bangladesh_map)

    district_fg              = add_district_layer(m, bangladesh_map)
    flood_fg                 = add_flood_layer(m, flood_map)
    pop_fg                   = add_population_layer(m, bangladesh_map)
    comb_dist_fg, comb_thana_fg   = add_combined_layers(m, bangladesh_map, flood_map)
    final_dist_fg, final_thana_fg = add_final_layers(m, bangladesh_map, flood_map)
    hosp_fg, clinic_fg, school_fg = add_infra_markers(m, hospitals, clinics, schools)

    folium.LayerControl(collapsed=False).add_to(m)

    # ------------------------------------------------------------------
    # 6. Add UI panels, legends, radio toggle
    # ------------------------------------------------------------------
    print("Adding UI panels and legends...")
    add_all_ui(
        m            = m,
        bangladesh   = bangladesh,   # full df needed for panel computations
        flood_fg     = flood_fg,
        pop_fg       = pop_fg,
        comb_dist_fg  = comb_dist_fg,
        comb_thana_fg = comb_thana_fg,
        final_dist_fg  = final_dist_fg,
        final_thana_fg = final_thana_fg,
        hosp_fg      = hosp_fg,
        clinic_fg    = clinic_fg,
        school_fg    = school_fg,
        comb_percentiles = comb_percentiles,
        fin_percentiles  = fin_percentiles,
    )

    # ------------------------------------------------------------------
    # 7. Save
    # ------------------------------------------------------------------
    output_path = DATA_PATHS["output"]
    m.save(output_path)
    print(f"Map saved → {output_path}")


if __name__ == "__main__":
    main()