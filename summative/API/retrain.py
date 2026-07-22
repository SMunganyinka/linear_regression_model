"""
retrain.py
==========
Defines the /retrain endpoint. It accepts new student data with actual exam scores,
appends it to the original dataset, runs the full preprocessing pipeline, retrains
the model, and overwrites the saved artifacts.
"""

from typing import List, Literal
from pydantic import BaseModel, Field
from fastapi import APIRouter, HTTPException
import pandas as pd
import numpy as np
import joblib
import json
import os
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split

# ---------------------------------------------------------------------------
# 1. PYDANTIC MODEL FOR RETRAINING
# ---------------------------------------------------------------------------

class RetrainRecord(BaseModel):
    """
    Same strict validation as prediction, but MUST include the actual exam_score
    so the model has ground truth to learn from.
    """
    age: int = Field(..., ge=16, le=30)
    gender: Literal["Male", "Female", "Other"]
    study_hours_per_day: float = Field(..., ge=0.0, le=15.0)
    sleep_hours: float = Field(..., ge=0.0, le=12.0)
    social_media_hours: float = Field(..., ge=0.0, le=15.0)
    netflix_hours: float = Field(..., ge=0.0, le=15.0)
    attendance_percentage: float = Field(..., ge=0.0, le=100.0)
    exercise_frequency: int = Field(..., ge=0, le=7)
    mental_health_rating: int = Field(..., ge=1, le=10)
    extracurricular_participation: Literal["Yes", "No"]
    part_time_job: Literal["Yes", "No"]
    diet_quality: Literal["Poor", "Fair", "Good", "Excellent"]
    parental_education_level: Literal["None", "High School", "Bachelor", "Master"]
    internet_quality: Literal["Poor", "Average", "Good"]
    
    # The target variable required for retraining
    exam_score: float = Field(..., ge=0.0, le=100.0)


class RetrainOutput(BaseModel):
    """Response confirming the retrain."""
    message: str
    new_dataset_size: int
    model_saved: bool


# ---------------------------------------------------------------------------
# 2. RETRAIN PIPELINE (Mirrors Notebook exactly)
# ---------------------------------------------------------------------------

def run_retrain_pipeline(new_records: List[RetrainRecord]):
    """Loads original data, appends new data, preprocesses, and retrains."""
    
    # Paths
    ARTIFACT_DIR = os.path.join(os.path.dirname(__file__), "..", "linear_regression")
    CSV_PATH = os.path.join(ARTIFACT_DIR, "student_habits_performance.csv")
    MODEL_PATH = os.path.join(ARTIFACT_DIR, "best_model.joblib")
    SCALER_PATH = os.path.join(ARTIFACT_DIR, "scaler.joblib")
    
    # 1. Load original dataset
    if not os.path.exists(CSV_PATH):
        raise HTTPException(status_code=500, detail="Original dataset CSV not found on server.")
    
    df = pd.read_csv(CSV_PATH)
    if "student_id" in df.columns:
        df.drop("student_id", axis=1, inplace=True)
        
    # 2. Append new data
    new_df = pd.DataFrame([r.model_dump() for r in new_records])
    df = pd.concat([df, new_df], ignore_index=True)
    
    # 3. PREPROCESSING (Exact copy of the bulletproof notebook cells)
    # Binary
    df["extracurricular_participation"] = df["extracurricular_participation"].map({"Yes": 1, "No": 0}).fillna(0).astype(int)
    df["part_time_job"] = df["part_time_job"].map({"Yes": 1, "No": 0}).fillna(0).astype(int)

    # Ordinal
    diet_order = {"Poor": 0, "Fair": 1, "Good": 2, "Excellent": 3}
    parental_order = {"None": 0, "High School": 1, "Bachelor": 2, "Master": 3}
    internet_order = {"Poor": 0, "Average": 1, "Good": 2}

    df["diet_quality"] = df["diet_quality"].map(diet_order).fillna(0).astype(int)
    df["parental_education_level"] = df["parental_education_level"].map(parental_order).fillna(0).astype(int)
    df["internet_quality"] = df["internet_quality"].map(internet_order).fillna(0).astype(int)

    # One-Hot gender
    df["gender"] = df["gender"].fillna("Male")
    df = pd.get_dummies(df, columns=["gender"], drop_first=True)
    bool_cols = df.select_dtypes(include="bool").columns
    df[bool_cols] = df[bool_cols].astype(int)

    # Feature Engineering
    df["total_screen_time"] = df["social_media_hours"] + df["netflix_hours"]
    df["study_efficiency"] = df["study_hours_per_day"] / (1 + df["total_screen_time"])

    def min_max_norm(series):
        min_val, max_val = series.min(), series.max()
        return pd.Series(0.0, index=series.index) if max_val == min_val else (series - min_val) / (max_val - min_val)

    wellness_components = ["sleep_hours", "exercise_frequency", "diet_quality", "mental_health_rating"]
    df["wellness_score"] = sum(min_max_norm(df[c]) for c in wellness_components)

    # Pandas 3.x nuclear option: force float64 and drop NAs
    for col in df.columns:
        if df[col].dtype in ['Int64', 'Float64', 'int32', 'int64', 'float32']:
            df[col] = df[col].astype(float)
    df.dropna(inplace=True)

    # 4. Split & Scale
    CATEGORICAL_COLS = ["extracurricular_participation", "part_time_job", "diet_quality", "parental_education_level", "internet_quality"]
    if "gender_Male" in df.columns: CATEGORICAL_COLS.append("gender_Male")
    if "gender_Other" in df.columns: CATEGORICAL_COLS.append("gender_Other")
    
    NUMERICAL_COLS = [c for c in df.drop(columns="exam_score").columns if c not in CATEGORICAL_COLS]
    
    X = df.drop(columns="exam_score").copy()
    y = df["exam_score"].copy()
    
    X_train, _, y_train, _ = train_test_split(X, y, test_size=0.2, random_state=42)
    
    new_scaler = StandardScaler()
    X_train[NUMERICAL_COLS] = new_scaler.fit_transform(X_train[NUMERICAL_COLS])
    
    # 5. Retrain Model
    new_model = LinearRegression()
    new_model.fit(X_train, y_train)
    
    # 6. Overwrite Artifacts
    joblib.dump(new_model, MODEL_PATH)
    joblib.dump(new_scaler, SCALER_PATH)
    
    # 7. Force API to reload new model on next prediction
    from . import model as model_module
    model_module._model = None
    model_module._scaler = None
    model_module._metadata = None
    
    return len(df)


# ---------------------------------------------------------------------------
# 3. FASTAPI ROUTER & ENDPOINT
# ---------------------------------------------------------------------------

router = APIRouter(
    prefix="/api/v1",
    tags=["Retraining"]
)

@router.post(
    "/retrain", 
    response_model=RetrainOutput,
    summary="Retrain the model with new student data",
    description="Accepts a list of student records INCLUDING their actual exam_score. Appends to the dataset, retrains the Linear Regression model, and saves the updated model automatically."
)
async def retrain_model(records: List[RetrainRecord]):
    if not records:
        raise HTTPException(status_code=400, detail="No records provided for retraining.")
    
    try:
        new_size = run_retrain_pipeline(records)
        return RetrainOutput(
            message="Model retrained and saved successfully.",
            new_dataset_size=new_size,
            model_saved=True
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Retraining failed: {str(e)}")