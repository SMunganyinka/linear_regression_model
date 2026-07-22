"""
model.py
========
Handles loading the trained model artifacts and replicating the exact
preprocessing pipeline from the Jupyter notebook for single predictions.
"""

import joblib
import json
import pandas as pd
import os

# ---------------------------------------------------------------------------
# Paths: Navigate up one level from API/ to linear_regression/
# ---------------------------------------------------------------------------
ARTIFACT_DIR = os.path.join(os.path.dirname(__file__), "..", "linear_regression")
MODEL_PATH = os.path.join(ARTIFACT_DIR, "best_model.joblib")
SCALER_PATH = os.path.join(ARTIFACT_DIR, "scaler.joblib")
METADATA_PATH = os.path.join(ARTIFACT_DIR, "feature_metadata.json")

# ---------------------------------------------------------------------------
# Global cache (loads once per application lifecycle)
# ---------------------------------------------------------------------------
_model = None
_scaler = None
_metadata = None

# ---------------------------------------------------------------------------
# Mapping dictionaries (MUST match notebook exactly)
# ---------------------------------------------------------------------------
BINARY_MAP = {"Yes": 1, "No": 0}
DIET_ORDER = {"Poor": 0, "Fair": 1, "Good": 2, "Excellent": 3}
PARENTAL_ORDER = {"None": 0, "High School": 1, "Bachelor": 2, "Master": 3}
INTERNET_ORDER = {"Poor": 0, "Average": 1, "Good": 2}


def load_artifacts():
    """
    Lazily loads the model, scaler, and metadata from disk.
    Uses a global cache so we only load them once when the API starts.
    """
    global _model, _scaler, _metadata
    if _model is None:
        _model = joblib.load(MODEL_PATH)
        _scaler = joblib.load(SCALER_PATH)
        with open(METADATA_PATH, "r") as f:
            _metadata = json.load(f)
    return _model, _scaler, _metadata


def preprocess_single(student_data: dict) -> pd.DataFrame:
    """
    Transforms a raw dictionary (from the Flutter app or Swagger UI)
    into a scaled DataFrame that perfectly matches the training features.
    """
    _, scaler, metadata = load_artifacts()
    sdf = pd.DataFrame([student_data])

    # 1. Handle missing parental education (same logic as notebook)
    val = sdf["parental_education_level"].iloc[0]
    if pd.isnull(val) or str(val).strip() == "":
        sdf["parental_education_level"] = "None"

    # 2. Binary mappings
    sdf["extracurricular_participation"] = sdf["extracurricular_participation"].map(BINARY_MAP)
    sdf["part_time_job"] = sdf["part_time_job"].map(BINARY_MAP)

    # 3. Ordinal mappings
    sdf["diet_quality"] = sdf["diet_quality"].map(DIET_ORDER)
    sdf["parental_education_level"] = sdf["parental_education_level"].map(PARENTAL_ORDER)
    sdf["internet_quality"] = sdf["internet_quality"].map(INTERNET_ORDER)

    # 4. One-Hot gender (drop_first=True means we only keep gender_Male)
    sdf = pd.get_dummies(sdf, columns=["gender"], drop_first=True)
    if "gender_Male" not in sdf.columns:
        sdf["gender_Male"] = 0
    if "gender_Other" not in sdf.columns:
        sdf["gender_Other"] = 0
    sdf["gender_Male"] = sdf["gender_Male"].astype(int)
    sdf["gender_Other"] = sdf["gender_Other"].astype(int)

    # 5. Feature Engineering
    sdf["total_screen_time"] = sdf["social_media_hours"] + sdf["netflix_hours"]
    sdf["study_efficiency"] = sdf["study_hours_per_day"] / (1 + sdf["total_screen_time"])

        # 6. Wellness Score (Calculate bounds directly from CSV to avoid metadata mismatches)
    CSV_PATH = os.path.join(ARTIFACT_DIR, "student_habits_performance.csv")
    df_orig = pd.read_csv(CSV_PATH)
    
    # Encode the original data to get numeric values for min/max
    diet_ord = {"Poor": 0, "Fair": 1, "Good": 2, "Excellent": 3}
    df_orig["diet_quality"] = df_orig["diet_quality"].map(diet_ord).fillna(0)
    
    components = ["sleep_hours", "exercise_frequency", "diet_quality", "mental_health_rating"]
    score = 0.0
    for c in components:
        min_v = df_orig[c].min()
        max_v = df_orig[c].max()
        if max_v == min_v:
            score += 0.0
        else:
            score += (sdf[c].iloc[0] - min_v) / (max_v - min_v)
    sdf["wellness_score"] = score

    # 7. Reorder columns to match training & scale numerical features
    all_features = metadata["all_features"]
    numerical_cols = metadata["numerical_cols"]

    sdf = sdf[all_features]
    sdf[numerical_cols] = scaler.transform(sdf[numerical_cols])

    return sdf


def predict(student_data: dict) -> float:
    """
    End-to-end prediction: takes raw dict, preprocesses, returns float score.
    """
    model, _, _ = load_artifacts()
    sdf = preprocess_single(student_data)
    return float(model.predict(sdf)[0])