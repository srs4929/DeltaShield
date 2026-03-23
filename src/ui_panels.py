# ui_panels.py
# Generates all HTML panels, legends, and the radio-toggle JavaScript block.
# All functions return HTML strings or attach elements directly to the Folium map.

import pandas as pd
import folium
from helpers import tier_badge
from config import FLOOD_LAYER_COLORS, POP_LAYER_COLORS, WATERLEVEL_ALERT_COLORS, WATERLEVEL_ALERT


# -----------------------
# Low-level HTML builders
# -----------------------
def panel_row(name: str, sub: str, bg: str, txt: str, badge: str) -> str:
    """Render one row inside a top-5 panel."""
    sub_html = (
        f"<br><span style='color:#666;font-size:11px;'>{sub}</span>" if sub else ""
    )
    return f"""
    <div style="display:flex;justify-content:space-between;align-items:center;
                padding:6px 0;border-bottom:1px solid #eee;font-size:13px;">
        <div><b>{name}</b>{sub_html}</div>
        <span style="background:{bg};color:{txt};padding:2px 8px;
                     border-radius:10px;font-size:11px;font-weight:600;
                     white-space:nowrap;margin-left:8px;">{badge}</span>
    </div>"""


def make_panel(panel_id: str, title_color: str, title_icon: str,
               title_text: str, subtitle: str, rows_html: str) -> str:
    """Render a full floating panel (hidden by default)."""
    return f"""
    <div id="{panel_id}" style="display:none;position:fixed;top:70px;right:15px;
        width:285px;background:white;border:1.5px solid #ccc;border-radius:10px;
        z-index:9999;padding:12px 14px;font-family:Arial,sans-serif;
        box-shadow:0 3px 10px rgba(0,0,0,0.15);">
        <div style="font-size:14px;font-weight:700;margin-bottom:{"4px" if subtitle else "8px"};
                    color:{title_color};">{title_icon} {title_text}</div>
        {"<div style='font-size:11px;color:#888;margin-bottom:8px;'>" + subtitle + "</div>" if subtitle else ""}
        {rows_html}
    </div>"""


def make_legend(legend_id: str, title: str, subtitle: str,
                items: list) -> str:
    """
    Render a floating legend (hidden by default).

    Args:
        items: list of (color_hex, label_str) tuples.
    """
    rows = ""
    for color, label in items:
        border = "border:1px solid #ccc;" if color == "#edf8fb" else ""
        rows += (
            f"""<span style="background:{color};width:16px;height:11px;"""
            f"""display:inline-block;border-radius:3px;vertical-align:middle;"""
            f"""margin-right:6px;{border}"></span>{label}<br><br>"""
        )
    sub_html = (
        f"<span style='font-size:11px;color:#888;'>{subtitle}</span><br><br>"
        if subtitle else "<br>"
    )
    return f"""
    <div id="{legend_id}" style="display:none;position:fixed;bottom:40px;left:15px;
        width:235px;background:white;border:1.5px solid #ccc;border-radius:10px;
        z-index:9999;padding:12px 14px;font-family:Arial,sans-serif;font-size:13px;
        box-shadow:0 3px 10px rgba(0,0,0,0.15);">
        <b style="font-size:14px;">{title}</b><br>{sub_html}{rows}
    </div>"""


# -----------------------
# Panel content builders
# -----------------------
def _flood_panel(bangladesh) -> str:
    top5 = bangladesh.sort_values("avg_floodcat", ascending=False)[
        ["NAME_2", "avg_floodcat"]
    ].head(5)
    rows = ""
    for _, row in top5.iterrows():
        risk = row["avg_floodcat"]
        bg  = (FLOOD_LAYER_COLORS["severe"]   if risk >= 7
               else FLOOD_LAYER_COLORS["high"]     if risk >= 5
               else FLOOD_LAYER_COLORS["moderate"] if risk >= 3
               else FLOOD_LAYER_COLORS["low"])
        txt = "#fff" if risk >= 3 else "#333"
        rows += panel_row(row["NAME_2"], f"Avg Flood Score: {risk:.2f}", bg, txt, f"{risk:.2f}")
    return make_panel("top5-flood-panel", "#c62828", "⚠️",
                      "Top 5 Flood Risk Districts", "", rows)


def _pop_panel(bangladesh) -> str:
    pop_min = float(bangladesh["T_TL"].min())
    pop_max = float(bangladesh["T_TL"].max())

    top5 = bangladesh.sort_values("T_TL", ascending=False)[
        ["NAME_2", "T_TL", "M_TL", "F_TL"]
    ].head(5)
    rows = ""
    for _, row in top5.iterrows():
        val   = int(row["T_TL"])
        ratio = (val - pop_min) / (pop_max - pop_min)
        bg    = ("#08306b" if ratio >= 0.8
                 else "#2171b5" if ratio >= 0.6
                 else "#4eb3d3" if ratio >= 0.4
                 else "#a8ddb5")
        txt = "#fff" if ratio >= 0.4 else "#333"
        rows += panel_row(
            row["NAME_2"],
            f"M: {int(row['M_TL']):,} | F: {int(row['F_TL']):,}",
            bg, txt, f"{val:,}",
        )
    return make_panel("top5-pop-panel", "#08306b", "👥",
                      "Top 5 Most Populated", "", rows)


def _combined_panel(bangladesh) -> str:
    top5 = bangladesh.sort_values("combined_score", ascending=False)[
        ["NAME_2", "combined_score", "avg_floodcat", "T_TL", "risk_tier"]
    ].head(5)
    rows = ""
    for _, row in top5.iterrows():
        bg, txt, label = tier_badge(row["risk_tier"])
        rows += panel_row(
            row["NAME_2"],
            f"Flood avg: {row['avg_floodcat']:.1f} | Pop: {int(row['T_TL']):,}",
            bg, txt, f"{label} ({row['combined_score']:.2f})",
        )
    return make_panel("top5-combined-panel", "#4a0000", "🚨",
                      "Top 5 Combined Risk", "70% Flood + 30% Population", rows)


def _final_panel(bangladesh) -> str:
    top5 = bangladesh.sort_values("final_score", ascending=False)[
        ["NAME_2", "final_score", "avg_floodcat", "T_TL",
         "hosp_count", "clinic_count", "school_count", "final_risk_tier"]
    ].head(5)
    rows = ""
    for _, row in top5.iterrows():
        bg, txt, label = tier_badge(row["final_risk_tier"])
        infra = int(row["hosp_count"] + row["clinic_count"] + row["school_count"])
        rows += panel_row(
            row["NAME_2"],
            f"Flood:{row['avg_floodcat']:.1f} | Pop:{int(row['T_TL']):,} | Infra:{infra}",
            bg, txt, f"{label} ({row['final_score']:.2f})",
        )
    return make_panel("top5-final-panel", "#1b5e20", "📍",
                      "Top 5 Final Risk Districts",
                      "70% Flood + 20% Pop + 10% Infrastructure", rows)


def _water_panel(bangladesh) -> str:
    needed = {"NAME_2", "water_alert_level", "max_exceedance_m", "station_count"}
    if not needed.issubset(set(bangladesh.columns)):
        rows = panel_row("No live alert data", "FFWC feed unavailable", "#9e9e9e", "#fff", "N/A")
        return make_panel(
            "top5-water-panel",
            "#1565c0",
            "🌊",
            "Water Alerts (Rivers)",
            "FFWC live gauge feed",
            rows,
        )

    # Filter to only districts with at least one station, then sort by alert level + exceedance
    with_stations = bangladesh[bangladesh["station_count"] > 0].copy()
    
    if with_stations.empty:
        rows = panel_row("No stations detected", "All systems normal across Bangladesh", "#43a047", "#fff", "OK")
        return make_panel(
            "top5-water-panel",
            "#1565c0",
            "🌊",
            "Water Alerts (Rivers)",
            "FFWC observed gauge levels",
            rows,
        )

    top5 = with_stations.sort_values(
        ["water_alert_level", "max_exceedance_m", "station_count"],
        ascending=[False, False, False],
    )[["NAME_2", "water_alert_level", "max_exceedance_m", "station_count"]].head(5)

    label_map = {2: "Warning", 1: "Watch", 0: "No Alert"}
    rows = ""
    for _, row in top5.iterrows():
        level = int(row["water_alert_level"])
        bg = WATERLEVEL_ALERT_COLORS.get(level, "#43a047")
        txt = "#fff" if level >= 1 else "#111"
        exceedance = float(row["max_exceedance_m"]) if pd.notna(row["max_exceedance_m"]) else 0.0
        rows += panel_row(
            row["NAME_2"],
            f"Stations: {int(row['station_count'])} | Exceedance: {exceedance:+.2f} m",
            bg,
            txt,
            label_map.get(level, "No Alert"),
        )

    return make_panel(
        "top5-water-panel",
        "#1565c0",
        "🌊",
        "Top 5 Water Alert Districts",
        "API: FFWC observed gauge levels",
        rows,
    )


# -----------------------
# Legend builders
# -----------------------
def _flood_legend() -> str:
    return make_legend(
        "flood-legend", "Flood Risk", "",
        [
            (FLOOD_LAYER_COLORS["severe"],   "Severe (≥7)"),
            (FLOOD_LAYER_COLORS["high"],     "High (5–6)"),
            (FLOOD_LAYER_COLORS["moderate"], "Moderate (3–4)"),
            (FLOOD_LAYER_COLORS["low"],      "Low (<3)"),
        ],
    )


def _pop_legend(bangladesh) -> str:
    pop_min = float(bangladesh["T_TL"].min())
    pop_max = float(bangladesh["T_TL"].max())
    t1 = int(pop_min + 0.2 * (pop_max - pop_min))
    t2 = int(pop_min + 0.4 * (pop_max - pop_min))
    t3 = int(pop_min + 0.6 * (pop_max - pop_min))
    t4 = int(pop_min + 0.8 * (pop_max - pop_min))
    return make_legend(
        "pop-legend", "Population (2022)", "",
        [
            ("#08306b", f"> {t4:,}"),
            ("#2171b5", f"{t3:,} – {t4:,}"),
            ("#4eb3d3", f"{t2:,} – {t3:,}"),
            ("#a8ddb5", f"{t1:,} – {t2:,}"),
            ("#edf8fb", f"< {t1:,}"),
        ],
    )


def _combined_legend(comb_p25, comb_p50, comb_p75) -> str:
    return make_legend(
        "combined-legend", "Combined Risk", "70% Flood + 30% Population",
        [
            ("#4a0000", f"Critical (≥{comb_p75:.2f})"),
            ("#b71c1c", f"High ({comb_p50:.2f}–{comb_p75:.2f})"),
            ("#e65100", f"Moderate ({comb_p25:.2f}–{comb_p50:.2f})"),
            ("#f9a825", f"Low (<{comb_p25:.2f})"),
        ],
    )


def _final_legend(fin_p25, fin_p50, fin_p75) -> str:
    return make_legend(
        "final-legend", "Final Risk Score",
        "70% Flood + 20% Pop + 10% Infrastructure",
        [
            ("#4a0000", f"Critical (≥{fin_p75:.2f})"),
            ("#b71c1c", f"High ({fin_p50:.2f}–{fin_p75:.2f})"),
            ("#e65100", f"Moderate ({fin_p25:.2f}–{fin_p50:.2f})"),
            ("#f9a825", f"Low (<{fin_p25:.2f})"),
        ],
    )


def _water_legend() -> str:
    watch_buffer = float(WATERLEVEL_ALERT.get("watch_buffer_m", 0.5))
    return make_legend(
        "water-legend",
        "Water Alerts",
        "Based on gauge water level vs danger level",
        [
            (WATERLEVEL_ALERT_COLORS[2], "Warning (WL ≥ Danger Level)"),
            (WATERLEVEL_ALERT_COLORS[1], f"Watch (within {watch_buffer:.1f}m below danger)"),
            (WATERLEVEL_ALERT_COLORS[0], "No Alert"),
        ],
    )


# -----------------------
# Radio toggle JS block
# -----------------------
def radio_toggle_js(flood_var, pop_var, comb_dist_var, comb_thana_var,
                     final_dist_var, final_thana_var,
                     hosp_var, clinic_var, school_var,
                     river_var, station_var) -> str:
    """
    Generate the 6-way radio toggle bar and its JavaScript controller.

    Args:
        *_var: Folium layer variable names returned by fg.get_name().
    """
    return f"""
<div style="position:fixed;top:15px;left:50%;transform:translateX(-50%);
    z-index:9999;background:white;border:1.5px solid #ccc;border-radius:10px;
    padding:8px 16px;display:flex;align-items:center;gap:12px;
    box-shadow:0 2px 8px rgba(0,0,0,0.15);font-family:Arial,sans-serif;font-size:13px;">
    <label style="display:flex;align-items:center;gap:5px;cursor:pointer;">
        <input type="radio" name="mapMode" id="normalMode" checked
               style="accent-color:#1a73e8;width:14px;height:14px;">
        <span id="lbl-normal" style="font-weight:600;color:#1a73e8;">Normal</span>
    </label>
    <span style="color:#ddd;">|</span>
    <label style="display:flex;align-items:center;gap:5px;cursor:pointer;">
        <input type="radio" name="mapMode" id="floodMode"
               style="accent-color:#e53935;width:14px;height:14px;">
        <span id="lbl-flood" style="color:#999;">Flood</span>
    </label>
    <span style="color:#ddd;">|</span>
    <label style="display:flex;align-items:center;gap:5px;cursor:pointer;">
        <input type="radio" name="mapMode" id="popMode"
               style="accent-color:#08306b;width:14px;height:14px;">
        <span id="lbl-pop" style="color:#999;">Population</span>
    </label>
    <span style="color:#ddd;">|</span>
    <label style="display:flex;align-items:center;gap:5px;cursor:pointer;">
        <input type="radio" name="mapMode" id="combinedMode"
               style="accent-color:#4a0000;width:14px;height:14px;">
        <span id="lbl-combined" style="color:#999;">Flood+Pop</span>
    </label>
    <span style="color:#ddd;">|</span>
    <label style="display:flex;align-items:center;gap:5px;cursor:pointer;">
        <input type="radio" name="mapMode" id="finalMode"
               style="accent-color:#1b5e20;width:14px;height:14px;">
        <span id="lbl-final" style="color:#999;">Final Risk</span>
    </label>
    <span style="color:#ddd;">|</span>
    <label style="display:flex;align-items:center;gap:5px;cursor:pointer;">
        <input type="radio" name="mapMode" id="waterMode"
               style="accent-color:#1565c0;width:14px;height:14px;">
        <span id="lbl-water" style="color:#999;">Water Alerts</span>
    </label>
</div>

<script>
var FLOOD_VAR          = "{flood_var}";
var POP_VAR            = "{pop_var}";
var COMB_DIST_VAR      = "{comb_dist_var}";
var COMB_THANA_VAR     = "{comb_thana_var}";
var FINAL_DIST_VAR     = "{final_dist_var}";
var FINAL_THANA_VAR    = "{final_thana_var}";
var HOSP_VAR           = "{hosp_var}";
var CLINIC_VAR         = "{clinic_var}";
var SCHOOL_VAR         = "{school_var}";
var RIVER_VAR          = "{river_var}";
var STATION_VAR        = "{station_var}";

function getMap() {{
    for (var k in window) {{
        try {{
            if (window[k] && window[k]._leaflet_id !== undefined &&
                typeof window[k].addLayer === 'function') return window[k];
        }} catch(e) {{}}
    }}
    return null;
}}

function setLayer(mapObj, varName, show) {{
    var layer = window[varName];
    if (!layer || !mapObj) return;
    if (show  && !mapObj.hasLayer(layer)) mapObj.addLayer(layer);
    if (!show &&  mapObj.hasLayer(layer)) mapObj.removeLayer(layer);
}}

function applyMode(mode) {{
    var mapObj = getMap();
    if (!mapObj) return;

    setLayer(mapObj, FLOOD_VAR,       mode==='flood');
    setLayer(mapObj, POP_VAR,         mode==='pop');
    setLayer(mapObj, COMB_DIST_VAR,   mode==='combined');
    setLayer(mapObj, COMB_THANA_VAR,  mode==='combined');
    setLayer(mapObj, FINAL_DIST_VAR,  mode==='final');
    setLayer(mapObj, FINAL_THANA_VAR, mode==='final');
    setLayer(mapObj, HOSP_VAR,        mode==='final');
    setLayer(mapObj, CLINIC_VAR,      mode==='final');
    setLayer(mapObj, SCHOOL_VAR,      mode==='final');
    setLayer(mapObj, RIVER_VAR,       mode==='water');
    setLayer(mapObj, STATION_VAR,     mode==='water');

    var allIds = ['top5-flood-panel','flood-legend',
                  'top5-pop-panel','pop-legend',
                  'top5-combined-panel','combined-legend',
                  'top5-final-panel','final-legend',
                  'top5-water-panel','water-legend'];
    allIds.forEach(function(id) {{
        var el = document.getElementById(id);
        if (el) el.style.display = 'none';
    }});

    var showIds = {{
        flood:    ['top5-flood-panel',    'flood-legend'],
        pop:      ['top5-pop-panel',      'pop-legend'],
        combined: ['top5-combined-panel', 'combined-legend'],
        final:    ['top5-final-panel',    'final-legend'],
        water:    ['top5-water-panel',    'water-legend']
    }};
    if (showIds[mode]) {{
        showIds[mode].forEach(function(id) {{
            var el = document.getElementById(id);
            if (el) el.style.display = 'block';
        }});
    }}

    var cfg = {{
        normal:   {{id:'lbl-normal',   color:'#1a73e8'}},
        flood:    {{id:'lbl-flood',    color:'#e53935'}},
        pop:      {{id:'lbl-pop',      color:'#08306b'}},
        combined: {{id:'lbl-combined', color:'#4a0000'}},
        final:    {{id:'lbl-final',    color:'#1b5e20'}},
        water:    {{id:'lbl-water',    color:'#1565c0'}}
    }};
    Object.keys(cfg).forEach(function(k) {{
        var el = document.getElementById(cfg[k].id);
        if (!el) return;
        el.style.color      = (k===mode) ? cfg[k].color : '#999';
        el.style.fontWeight = (k===mode) ? '600' : '400';
    }});
}}

document.getElementById('normalMode').addEventListener('change',
    function() {{ if(this.checked) applyMode('normal'); }});
document.getElementById('floodMode').addEventListener('change',
    function() {{ if(this.checked) applyMode('flood'); }});
document.getElementById('popMode').addEventListener('change',
    function() {{ if(this.checked) applyMode('pop'); }});
document.getElementById('combinedMode').addEventListener('change',
    function() {{ if(this.checked) applyMode('combined'); }});
document.getElementById('finalMode').addEventListener('change',
    function() {{ if(this.checked) applyMode('final'); }});
document.getElementById('waterMode').addEventListener('change',
    function() {{ if(this.checked) applyMode('water'); }});
</script>"""


# -----------------------
# Master function: attach everything to the map
# -----------------------
def add_all_ui(m: folium.Map,
               bangladesh,
               flood_fg, pop_fg,
               comb_dist_fg, comb_thana_fg,
               final_dist_fg, final_thana_fg,
               hosp_fg, clinic_fg, school_fg,
               river_fg, station_fg,
               comb_percentiles: tuple,
               fin_percentiles: tuple):
    """
    Attach all panels, legends, and the radio toggle to the Folium map.

    Args:
        comb_percentiles: (p25, p50, p75) for combined score.
        fin_percentiles:  (p25, p50, p75) for final score.
    """
    comb_p25, comb_p50, comb_p75 = comb_percentiles
    fin_p25,  fin_p50,  fin_p75  = fin_percentiles

    for html in [
        _flood_panel(bangladesh),
        _pop_panel(bangladesh),
        _combined_panel(bangladesh),
        _final_panel(bangladesh),
        _water_panel(bangladesh),
        _flood_legend(),
        _pop_legend(bangladesh),
        _combined_legend(comb_p25, comb_p50, comb_p75),
        _final_legend(fin_p25, fin_p50, fin_p75),
        _water_legend(),
        radio_toggle_js(
            flood_var       = flood_fg.get_name(),
            pop_var         = pop_fg.get_name(),
            comb_dist_var   = comb_dist_fg.get_name(),
            comb_thana_var  = comb_thana_fg.get_name(),
            final_dist_var  = final_dist_fg.get_name(),
            final_thana_var = final_thana_fg.get_name(),
            hosp_var        = hosp_fg.get_name(),
            clinic_var      = clinic_fg.get_name(),
            school_var      = school_fg.get_name(),
            river_var       = river_fg.get_name(),
            station_var     = station_fg.get_name(),
        ),
    ]:
        m.get_root().html.add_child(folium.Element(html))


# -----------------------
# Prediction panel + legend
# -----------------------
def _prediction_panel(bangladesh, model) -> str:
    """Top-5 predicted risk districts panel."""
    from predictor import get_feature_importance

    top5 = bangladesh.sort_values("risk_probability", ascending=False)[
        ["NAME_2", "predicted_risk_tier", "risk_probability", "top_risk_factor"]
    ].head(5)

    rows = ""
    for _, row in top5.iterrows():
        bg, txt, label = tier_badge(row["predicted_risk_tier"])
        prob_pct = f"{row['risk_probability']*100:.0f}%"
        rows += panel_row(
            row["NAME_2"],
            f"Confidence: {prob_pct} | Driver: {row['top_risk_factor']}",
            bg, txt,
            f"{label} ({prob_pct})",
        )

    # Feature importance bar (text only, compact)
    fi = get_feature_importance(model).head(4)
    fi_html = "<div style='margin-top:8px;font-size:11px;color:#555;'><b>Top drivers (global):</b><br>"
    for _, r in fi.iterrows():
        bar_w = int(r["importance_pct"] * 1.4)  # scale to ~140px max
        fi_html += (
            f"<div style='display:flex;align-items:center;gap:6px;margin:3px 0;'>"
            f"<span style='width:110px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;'>{r['feature']}</span>"
            f"<div style='width:{bar_w}px;height:6px;background:#b71c1c;border-radius:3px;'></div>"
            f"<span>{r['importance_pct']}%</span></div>"
        )
    fi_html += "</div>"

    return make_panel(
        "top5-prediction-panel", "#1b5e20", "🔮",
        "Top 5 Predicted Risk",
        "Next season forecast",
        rows + fi_html,
    )


def _prediction_legend() -> str:
    return make_legend(
        "prediction-legend", "Predicted risk", "Dashed border = forecast",
        [
            ("#4a0000", "Critical — tier 4"),
            ("#b71c1c", "High — tier 3"),
            ("#e65100", "Moderate — tier 2"),
            ("#f9a825", "Low — tier 1"),
        ],
    )


def add_prediction_ui(m: folium.Map, bangladesh, pred_fg, model,
                       existing_toggle_html: str = None):
    """
    Attach prediction panel and legend to the map.
    Also patches the radio toggle to include a 6th 'Prediction' button.

    Call this AFTER add_all_ui() so the toggle patch appends cleanly.

    Args:
        m:           Folium map.
        bangladesh:  GeoDataFrame with prediction columns.
        pred_fg:     FeatureGroup returned by add_prediction_layer().
        model:       Trained RandomForestClassifier (for feature importances).
    """
    import folium as _folium

    for html in [
        _prediction_panel(bangladesh, model),
        _prediction_legend(),
    ]:
        m.get_root().html.add_child(_folium.Element(html))

    # Inject JS to wire the prediction layer into the existing toggle system
    pred_var = pred_fg.get_name()
    patch_js = f"""
<script>
(function() {{
    var PRED_VAR = "{pred_var}";

    // Add Prediction radio button to the toggle bar
    var bar = document.querySelector('div[style*="transform:translateX(-50%)"]');
    if (bar) {{
        var sep  = document.createElement('span');
        sep.style.color = '#ddd';
        sep.textContent = '|';

        var lbl  = document.createElement('label');
        lbl.style.cssText = 'display:flex;align-items:center;gap:5px;cursor:pointer;';
        lbl.innerHTML = '<input type="radio" name="mapMode" id="predMode" '
            + 'style="accent-color:#1b5e20;width:14px;height:14px;">'
            + '<span id="lbl-pred" style="color:#999;">Prediction</span>';

        bar.appendChild(sep);
        bar.appendChild(lbl);
    }}

    function getMap() {{
        for (var k in window) {{
            try {{
                if (window[k] && window[k]._leaflet_id !== undefined &&
                    typeof window[k].addLayer === 'function') return window[k];
            }} catch(e) {{}}
        }}
        return null;
    }}

    function setLayer(mapObj, varName, show) {{
        var layer = window[varName];
        if (!layer || !mapObj) return;
        if (show  && !mapObj.hasLayer(layer)) mapObj.addLayer(layer);
        if (!show &&  mapObj.hasLayer(layer)) mapObj.removeLayer(layer);
    }}

    var predInput = document.getElementById('predMode');
    if (predInput) {{
        predInput.addEventListener('change', function() {{
            if (!this.checked) return;
            var mapObj = getMap();

            // Hide all other layers
            ['flood_var','pop_var','comb_dist_var','comb_thana_var',
             'final_dist_var','final_thana_var',
             'hosp_var','clinic_var','school_var'].forEach(function(v) {{
                if (window[v]) setLayer(mapObj, v, false);
             }});

            // Show prediction layer
            setLayer(mapObj, PRED_VAR, true);

            // Hide all panels/legends then show prediction ones
            var allIds = ['top5-flood-panel','flood-legend',
                          'top5-pop-panel','pop-legend',
                          'top5-combined-panel','combined-legend',
                          'top5-final-panel','final-legend'];
            allIds.forEach(function(id) {{
                var el = document.getElementById(id);
                if (el) el.style.display = 'none';
            }});
            ['top5-prediction-panel','prediction-legend'].forEach(function(id) {{
                var el = document.getElementById(id);
                if (el) el.style.display = 'block';
            }});

            // Update label styles
            var cfg = {{
                normal:'lbl-normal', flood:'lbl-flood', pop:'lbl-pop',
                combined:'lbl-combined', final:'lbl-final', pred:'lbl-pred'
            }};
            var colors = {{
                normal:'#1a73e8', flood:'#e53935', pop:'#08306b',
                combined:'#4a0000', final:'#1b5e20', pred:'#1b5e20'
            }};
            Object.keys(cfg).forEach(function(k) {{
                var el = document.getElementById(cfg[k]);
                if (!el) return;
                el.style.color      = (k==='pred') ? colors[k] : '#999';
                el.style.fontWeight = (k==='pred') ? '600' : '400';
            }});
        }});
    }}

    // Also hide prediction layer when other modes are selected
    var origApply = window.applyMode;
    if (origApply) {{
        window.applyMode = function(mode) {{
            origApply(mode);
            setLayer(getMap(), PRED_VAR, false);
            ['top5-prediction-panel','prediction-legend'].forEach(function(id) {{
                var el = document.getElementById(id);
                if (el) el.style.display = 'none';
            }});
            var lbl = document.getElementById('lbl-pred');
            if (lbl) {{ lbl.style.color = '#999'; lbl.style.fontWeight = '400'; }}
        }};
    }}
}})();
</script>"""

    m.get_root().html.add_child(_folium.Element(patch_js))