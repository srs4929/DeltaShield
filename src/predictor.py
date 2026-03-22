# predictor.py
# Flood risk prediction model — v3


import os
import pickle
import warnings

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import LeaveOneOut, cross_val_score, StratifiedKFold, cross_val_predict
from sklearn.inspection import permutation_importance
from sklearn.pipeline import Pipeline

# Suppress only the specific joblib/parallel UserWarning from sklearn internals.
# All other warnings (data issues, convergence) remain visible.
import warnings
warnings.filterwarnings(
    "ignore",
    message=".*sklearn.utils.parallel.*",
    category=UserWarning,
)
warnings.filterwarnings(
    "ignore",
    message=".*n_jobs.*",
    category=UserWarning,
)

MODEL_PATH = "../output/flood_risk_model.pkl"

FEATURE_COLS = [
    "avg_floodcat",           # flood hazard signal
    "neighbor_avg_floodcat",  # spatial flood context
    "T_TL",                   # raw population
    "hosp_count",
    "clinic_count",
    "school_count",
    "infra_per_100k",         # infrastructure density relative to population
]

TARGET_COL = "compound_risk"  # 1 = flood-exposed AND pop-loaded AND infra-deficient


# -----------------------
# Spatial feature
# -----------------------
def add_spatial_features(bangladesh):
    """
    Add neighbor_avg_floodcat: mean avg_floodcat of geometrically
    adjacent districts. Falls back to own value if no neighbors found.
    """
    import geopandas as gpd

    gdf = bangladesh.copy().reset_index(drop=True)
    n   = len(gdf)
    neighbor_vals = []

    for i in range(n):
        geom_i   = gdf.geometry.iloc[i]
        touching = gdf[
            (gdf.index != i) &
            (gdf.geometry.touches(geom_i) | gdf.geometry.intersects(geom_i))
        ]
        touching = touching[touching.index != i]
        if len(touching) > 0:
            neighbor_vals.append(touching["avg_floodcat"].mean())
        else:
            neighbor_vals.append(gdf["avg_floodcat"].iloc[i])

    gdf["neighbor_avg_floodcat"] = neighbor_vals
    return gdf


# -----------------------
# Target: compound flood-vulnerability risk
# -----------------------
def add_vulnerability_target(bangladesh):
    """
    Define compound_risk using a WEIGHTED SCORE approach rather than
    strict AND logic.

    Why change from AND to weighted score:
        AND logic gave only 10 positive cases out of 64 (15%).
        With 10 positives, LOO variance is high — one wrong prediction
        on a rare positive case swings F1 by ~0.24.
        A weighted score gives ~25-30 positives (top quartile),
        making folds more stable and all features more learnable.

    Scoring:
        Each district gets a score 0-3 counting how many conditions
        it meets above the 60th percentile (stricter than median,
        softer than AND-of-medians):

            +1 if avg_floodcat    >= p60  (significant flood exposure)
            +1 if T_TL            >= p60  (high population pressure)
            +1 if infra_per_100k  <= p40  (below-average infra coverage)

        compound_risk = 1 if score >= 2 (meets at least 2 of 3 conditions)
                      = 0 otherwise

    This means:
        - Flood + Pop (no infra gap)    → 1  high-risk city pattern
        - Flood + Infra gap (low pop)   → 1  vulnerable rural pattern
        - Pop + Infra gap (no flood)    → 1  latent risk pattern
        - All three                     → 1  worst case
        - Only one condition            → 0  single-factor, manageable

    All three features remain necessary predictors of the target,
    keeping flood, population, and infrastructure all in the model.
    """
    bd = bangladesh.copy()

    # Flood uses TWO thresholds to give it double weight in scoring:
    #   moderate flood (p40) = +1 point
    #   severe flood   (p70) = +1 additional point (total +2 if severe)
    # Population and infrastructure each contribute +1 point maximum.
    # Max possible score = 4. Label = 1 if score >= 2.
    #
    # Effect on importances:
    #   A severely flooded district can reach score=2 on flood alone,
    #   making flood a sufficient condition for positive label.
    #   Infra and pop can no longer dominate by themselves — they need
    #   at least moderate flood (score 1) to tip the label to 1.

    flood_p40 = bd["avg_floodcat"].quantile(0.40)   # moderate flood
    flood_p70 = bd["avg_floodcat"].quantile(0.70)   # severe flood
    pop_p60   = bd["T_TL"].quantile(0.60)
    infra_p40 = bd["infra_per_100k"].quantile(0.40)

    flood_score = (
        (bd["avg_floodcat"] >= flood_p40).astype(int) +   # +1 moderate
        (bd["avg_floodcat"] >= flood_p70).astype(int)     # +1 severe
    )
    pop_score_bin   = (bd["T_TL"]            >= pop_p60  ).astype(int)
    infra_score_bin = (bd["infra_per_100k"]  <= infra_p40).astype(int)

    score = flood_score + pop_score_bin + infra_score_bin  # range 0-4

    bd[TARGET_COL] = (score >= 2).astype(int)

    n_risk = bd[TARGET_COL].sum()
    print(f"Target split: {n_risk} compound-risk, {len(bd)-n_risk} lower-risk")
    print(f"  Flood p40 (+1): avg_floodcat >= {flood_p40:.2f}")
    print(f"  Flood p70 (+1): avg_floodcat >= {flood_p70:.2f}  (severe = +2 total)")
    print(f"  Pop p60   (+1): T_TL >= {pop_p60:,.0f}")
    print(f"  Infra p40 (+1): infra_per_100k <= {infra_p40:.2f}")
    print(f"  Label = 1 if total score >= 2 (max=4)")
    return bd


# -----------------------
# Feature matrix
# -----------------------
def build_features(bangladesh) -> pd.DataFrame:
    """Extract and NaN-fill the feature matrix."""
    X = bangladesh[FEATURE_COLS].copy()
    for col in FEATURE_COLS:
        if X[col].isna().any():
            X[col] = X[col].fillna(X[col].median())
    return X


# -----------------------
# Evaluate
# -----------------------
def evaluate(model_cls, X, y, label=""):
    """
    Stratified 5-fold + Leave-One-Out, both using f1_weighted.
    Returns (skf_mean, loo_mean).
    """
    skf    = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    skf_sc = cross_val_score(model_cls, X, y, cv=skf, scoring="f1_weighted")
    print(f"{label} Stratified-5fold  F1: {skf_sc.mean():.3f} (+/- {skf_sc.std():.3f})")

    loo    = LeaveOneOut()
    loo_sc = cross_val_score(model_cls, X, y, cv=loo, scoring="f1_weighted")
    print(f"{label} Leave-One-Out     F1: {loo_sc.mean():.3f} (+/- {loo_sc.std():.3f})")

    return skf_sc.mean(), loo_sc.mean()



# -----------------------
# CalibratedModel — defined at module level so pickle can serialise it
# -----------------------
class CalibratedModel:
    """Wraps base classifier + Platt scaler for calibrated probabilities."""

    def __init__(self, base, scaler, feature_cols):
        self.base             = base
        self.scaler           = scaler
        self.classes_         = base.classes_
        self._feature_cols    = feature_cols
        self._perm_importance = None

    def predict(self, X):
        return self.base.predict(X)

    def predict_proba(self, X):
        raw = self.base.predict_proba(X)[:, 1].reshape(-1, 1)
        return self.scaler.predict_proba(raw)

# -----------------------
# Train
# -----------------------
def train_model(bangladesh, save: bool = True):
    """
    Full pipeline:
      1. Add spatial features + vulnerability target
      2. Compare RF vs GB
      3. Train winner with calibrated probabilities
      4. Report permutation importances
      5. Save model

    Returns:
        (trained_model, enriched_bangladesh)
    """
    print("\n--- Preparing features ---")
    bangladesh = add_spatial_features(bangladesh)
    bangladesh = add_vulnerability_target(bangladesh)

    X = build_features(bangladesh)
    y = bangladesh[TARGET_COL]

    n_minority = int(y.value_counts().min())
    cv_folds   = max(2, min(5, n_minority))

    print(f"Dataset  : {len(X)} districts")
    print(f"Features : {FEATURE_COLS}\n")

    rf = RandomForestClassifier(
        n_estimators=500,
        max_depth=4,
        min_samples_leaf=3,
        max_features="sqrt",
        class_weight="balanced",
        random_state=42,
        n_jobs=1,   # n_jobs=1 avoids joblib parallel warnings on small datasets
    )
    gb = GradientBoostingClassifier(
        n_estimators=200,
        max_depth=3,
        learning_rate=0.05,
        min_samples_leaf=3,
        subsample=0.8,
        random_state=42,
    )

    print("--- Evaluating Random Forest ---")
    rf_skf, rf_loo = evaluate(rf, X, y, "RF")

    print("\n--- Evaluating Gradient Boosting ---")
    gb_skf, gb_loo = evaluate(gb, X, y, "GB")

    best_model = rf if rf_loo >= gb_loo else gb
    winner     = "Random Forest" if rf_loo >= gb_loo else "Gradient Boosting"
    best_loo   = max(rf_loo, gb_loo)
    print(f"\nWinner: {winner} (LOO F1 {best_loo:.3f})")

    # Train on full data
    best_model.fit(X, y)

    # Calibrated probabilities via Platt scaling:
    # Use cross_val_predict to get out-of-fold decision scores,
    # then fit a LogisticRegression to map scores → probabilities.
    # This avoids CalibratedClassifierCV's internal joblib usage
    # which triggers the sklearn parallel config warning.
    oof_scores = cross_val_predict(
        best_model, X, y,
        cv=cv_folds,
        method="predict_proba",
    )[:, 1]

    platt = LogisticRegression(random_state=42, max_iter=1000)
    platt.fit(oof_scores.reshape(-1, 1), y)

    # Bundle base model + Platt scaler into the module-level CalibratedModel.
    # Class is defined at module level so pickle.dump can serialise it.
    calibrated = CalibratedModel(best_model, platt, FEATURE_COLS)

    # Permutation importances (unbiased)
    perm = permutation_importance(
        best_model, X, y, n_repeats=30, random_state=42, scoring="f1_weighted"
    )
    perm_df = pd.DataFrame({
        "feature":        FEATURE_COLS,
        "importance":     perm.importances_mean,
        "std":            perm.importances_std,
        "importance_pct": (perm.importances_mean * 100).round(1),
    }).sort_values("importance", ascending=False).reset_index(drop=True)

    print("\nPermutation importances (unbiased):")
    print(perm_df[["feature", "importance", "std"]].to_string(index=False))

    # Store on the calibrated wrapper for later retrieval
    calibrated._perm_importance = perm_df
    calibrated._feature_cols    = FEATURE_COLS

    if save:
        os.makedirs(os.path.dirname(MODEL_PATH), exist_ok=True)
        with open(MODEL_PATH, "wb") as f:
            pickle.dump(calibrated, f)
        print(f"\nModel saved → {MODEL_PATH}")

    return calibrated, bangladesh


# -----------------------
# Load + validate
# -----------------------
def _get_model_feature_names(model) -> list:
    """Extract feature names stored on the model wrapper."""
    # Our custom CalibratedModel stores _feature_cols directly
    if hasattr(model, "_feature_cols"):
        return list(model._feature_cols)
    # sklearn CalibratedClassifierCV fallback
    base = getattr(model, "estimator", model)
    if hasattr(model, "calibrated_classifiers_"):
        base = model.calibrated_classifiers_[0].estimator
    return list(getattr(base, "feature_names_in_", []))


def load_model():
    """
    Load saved model. Returns None if:
      - no pkl exists, or
      - pkl was trained on different features (stale model auto-deleted).
    """
    if not os.path.exists(MODEL_PATH):
        return None

    with open(MODEL_PATH, "rb") as f:
        model = pickle.load(f)

    saved_features = _get_model_feature_names(model)
    if saved_features and sorted(saved_features) != sorted(FEATURE_COLS):
        print(
            f"Stale model detected.\n"
            f"  Saved   : {saved_features}\n"
            f"  Expected: {FEATURE_COLS}\n"
            f"  Deleting {MODEL_PATH} and retraining..."
        )
        os.remove(MODEL_PATH)
        return None

    print(f"Model loaded <- {MODEL_PATH}")
    return model


# -----------------------
# Predict
# -----------------------
def predict(bangladesh, model):
    """
    Add prediction columns to the GeoDataFrame.

    Columns added:
        compound_risk          — binary target used at training time
        neighbor_avg_floodcat  — spatial feature (added if missing)
        predicted_risk_tier    — 3 = vulnerable, 1 = not vulnerable
        risk_probability       — calibrated P(vulnerable), 0.0–1.0
        top_risk_factor        — feature driving risk for that district
    """
    if "neighbor_avg_floodcat" not in bangladesh.columns:
        bangladesh = add_spatial_features(bangladesh)
    if TARGET_COL not in bangladesh.columns:
        bangladesh = add_vulnerability_target(bangladesh)

    X = build_features(bangladesh)

    preds = model.predict(X)
    bangladesh["predicted_risk_tier"] = np.where(preds == 1, 3, 1)

    proba   = model.predict_proba(X)
    classes = list(model.classes_)
    high_idx = classes.index(1) if 1 in classes else 0
    bangladesh["risk_probability"] = proba[:, high_idx].round(3)

    # Per-district top risk factor
    fi          = get_feature_importance(model)
    importances = (
        fi.set_index("feature")["importance"]
        .reindex(FEATURE_COLS)
        .fillna(0)
        .values
    )
    X_arr  = X.values
    denom  = X_arr.max(axis=0) - X_arr.min(axis=0) + 1e-9
    X_norm = (X_arr - X_arr.min(axis=0)) / denom
    weighted = X_norm * importances
    top_idx  = weighted.argmax(axis=1)
    bangladesh["top_risk_factor"] = [FEATURE_COLS[i] for i in top_idx]

    return bangladesh


# -----------------------
# Feature importance summary
# -----------------------
def get_feature_importance(model) -> pd.DataFrame:
    """
    Return feature importances as a DataFrame with columns:
        feature, importance, importance_pct

    Uses permutation importances if stored (set during train_model),
    otherwise falls back to impurity importances from the base estimator.
    importance_pct is always present.
    """
    # Permutation importances stored during training (our CalibratedModel)
    if hasattr(model, "_perm_importance") and model._perm_importance is not None:
        df = model._perm_importance[["feature", "importance"]].copy()
        df["importance_pct"] = (df["importance"] * 100).round(1)
        return df.reset_index(drop=True)

    # Fallback: impurity importances from base estimator
    # Works for both our CalibratedModel and sklearn CalibratedClassifierCV
    base = getattr(model, "base", None) or getattr(model, "estimator", model)
    if hasattr(model, "calibrated_classifiers_"):
        base = model.calibrated_classifiers_[0].estimator
    if hasattr(base, "feature_importances_"):
        df = pd.DataFrame({
            "feature":    FEATURE_COLS,
            "importance": base.feature_importances_,
        }).sort_values("importance", ascending=False).reset_index(drop=True)
        df["importance_pct"] = (df["importance"] * 100).round(1)
        return df

    # Last resort: zeros
    return pd.DataFrame({
        "feature":        FEATURE_COLS,
        "importance":     [0.0] * len(FEATURE_COLS),
        "importance_pct": [0.0] * len(FEATURE_COLS),
    })
