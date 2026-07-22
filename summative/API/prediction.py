"""
prediction.py
=============
Defines Pydantic models for strict input validation and the /predict endpoint.
"""

from typing import Literal
from pydantic import BaseModel, Field
from fastapi import APIRouter, HTTPException

# Import our custom preprocessing and prediction function

from . import model

# ---------------------------------------------------------------------------
# 1. PYDANTIC MODELS (Data Validation)
# ---------------------------------------------------------------------------

class StudentInput(BaseModel):
    """
    Validates incoming student data. 
    If a value falls outside these constraints, FastAPI returns a 422 Unprocessable Entity error.
    """
    age: int = Field(..., ge=16, le=30, description="Student age (realistic university range: 16-30)")
    
    # Literal ensures only exact strings are accepted (case-sensitive)
    gender: Literal["Male", "Female", "Other"] = Field(..., description="Student gender")
    
    study_hours_per_day: float = Field(..., ge=0.0, le=15.0, description="Hours spent studying per day")
    sleep_hours: float = Field(..., ge=0.0, le=12.0, description="Hours of sleep per night")
    social_media_hours: float = Field(..., ge=0.0, le=15.0, description="Hours on social media per day")
    netflix_hours: float = Field(..., ge=0.0, le=15.0, description="Hours watching Netflix per day")
    
    attendance_percentage: float = Field(..., ge=0.0, le=100.0, description="Class attendance percentage")
    
    exercise_frequency: int = Field(..., ge=0, le=7, description="Days of exercise per week")
    mental_health_rating: int = Field(..., ge=1, le=10, description="Self-rated mental health (1-10)")
    
    extracurricular_participation: Literal["Yes", "No"] = Field(..., description="Participates in extracurriculars")
    part_time_job: Literal["Yes", "No"] = Field(..., description="Has a part-time job")
    
    diet_quality: Literal["Poor", "Fair", "Good", "Excellent"] = Field(..., description="Quality of diet")
    parental_education_level: Literal["None", "High School", "Bachelor", "Master"] = Field(..., description="Highest parental education")
    internet_quality: Literal["Poor", "Average", "Good"] = Field(..., description="Quality of internet connection")


class PredictionOutput(BaseModel):
    """Standardized format for the API response."""
    predicted_exam_score: float


# ---------------------------------------------------------------------------
# 2. FASTAPI ROUTER & ENDPOINT
# ---------------------------------------------------------------------------

router = APIRouter(
    prefix="/api/v1",
    tags=["Prediction"]
)

@router.post(
    "/predict", 
    response_model=PredictionOutput,
    summary="Predict a student's final exam score",
    description="Accepts student habit data, validates it, runs it through the Linear Regression pipeline, and returns the predicted exam score (0-100)."
)
async def predict_score(student: StudentInput):
    try:
        # Convert Pydantic object to dictionary for our model pipeline
        student_dict = student.model_dump()
        
        # Call the preprocessing + prediction function from model.py
        score = model.predict(student_dict)
        
        # Clamp score between 0 and 100 just in case of slight linear extrapolation
        clamped_score = max(0.0, min(100.0, score))
        
        return PredictionOutput(predicted_exam_score=round(clamped_score, 2))
    
    except Exception as e:
        # Catch any unexpected errors (e.g., model file missing) and return a clean 500 error
        raise HTTPException(
            status_code=500, 
            detail=f"An error occurred during prediction: {str(e)}"
        )