# main.py
# Entry point. Orchestrates loading → scoring → model → map building → UI → save.
# Run: python main.py

import os
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
from predictor import train_model, load_model, predict
from map_builder import (
    build_map,
    add_district_layer,
    add_flood_layer,
    add_population_layer,
    add_combined_layers,
    add_final_layers,
    add_infra_markers,
    add_prediction_layer,
)
from ui_panels import add_all_ui, add_prediction_ui
from config import DATA_PATHS

MODEL_PATH = "../output/flood_risk_model.pkl"


def main():
    # ------------------------------------------------------------------
    # 1. Load data
    # ------------------------------------------------------------------
    print("Loading data...")
    boundaries              = load_boundaries()
    pop_df                  = load_population()
    flood                   = load_flood_data()
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

    comb_percentiles = add_combined_scores.comb_percentiles
    fin_percentiles  = add_combined_scores.fin_percentiles

    # ------------------------------------------------------------------
    # 4. Prediction model
    # ------------------------------------------------------------------
    print("Running prediction model...")
    # load_model() returns None if no pkl exists OR if the pkl is stale
    # (trained on different features). In both cases we retrain.
    model = load_model()
    if model is None:
        model, bangladesh = train_model(bangladesh, save=True)
        bangladesh = predict(bangladesh, model)
    else:
        bangladesh = predict(bangladesh, model)

    # ------------------------------------------------------------------
    # 5. Slim columns to reduce GeoJSON payload size in the HTML output
    # ------------------------------------------------------------------
    bangladesh_map = slim_for_map(bangladesh, [
        "NAME_2", "NAME_2_clean", "T_TL", "M_TL", "F_TL",
        "avg_floodcat", "hosp_count", "clinic_count", "school_count",
        "combined_score", "risk_tier", "final_score", "final_risk_tier",
        "predicted_risk_tier", "risk_probability", "top_risk_factor",
    ])
    flood_map = slim_for_map(flood, [
        "DISTNAME", "THANANAME", "FLOODCAT", "FLOODCAT_L", "DISTNAME_clean",
        "combined_score", "risk_tier", "final_score", "final_risk_tier", "T_TL",
    ])

    # ------------------------------------------------------------------
    # 6. Build map + layers
    # ------------------------------------------------------------------
    print("Building map...")
    m = build_map(bangladesh_map)

    district_fg                   = add_district_layer(m, bangladesh_map)
    flood_fg                      = add_flood_layer(m, flood_map)
    pop_fg                        = add_population_layer(m, bangladesh_map)
    comb_dist_fg, comb_thana_fg   = add_combined_layers(m, bangladesh_map, flood_map)
    final_dist_fg, final_thana_fg = add_final_layers(m, bangladesh_map, flood_map)
    hosp_fg, clinic_fg, school_fg = add_infra_markers(m, hospitals, clinics, schools)
    pred_fg                       = add_prediction_layer(m, bangladesh_map)

    folium.LayerControl(collapsed=False).add_to(m)

    # ------------------------------------------------------------------
    # 7. Add UI panels, legends, radio toggle
    # ------------------------------------------------------------------
    print("Adding UI panels and legends...")
    add_all_ui(
        m             = m,
        bangladesh    = bangladesh,
        flood_fg      = flood_fg,
        pop_fg        = pop_fg,
        comb_dist_fg  = comb_dist_fg,
        comb_thana_fg = comb_thana_fg,
        final_dist_fg  = final_dist_fg,
        final_thana_fg = final_thana_fg,
        hosp_fg       = hosp_fg,
        clinic_fg     = clinic_fg,
        school_fg     = school_fg,
        comb_percentiles = comb_percentiles,
        fin_percentiles  = fin_percentiles,
    )
    add_prediction_ui(m, bangladesh, pred_fg, model)

    # ------------------------------------------------------------------
    # 8. Save
    # ------------------------------------------------------------------
    output_path = DATA_PATHS["output"]
    m.save(output_path)
    print(f"\nMap saved → {output_path}")


if __name__ == "__main__":
    main()