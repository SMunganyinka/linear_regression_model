"""
main.py
=======
Entry point for the FastAPI application. Configures the app, 
includes routers, and sets up secure CORS policies.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Import the routers from our other files
from .prediction import router as prediction_router
from .retrain import router as retrain_router

# ---------------------------------------------------------------------------
# 1. INITIALIZE FASTAPI APP
# ---------------------------------------------------------------------------
app = FastAPI(
    title="Student Exam Score Predictor",
    description="An API that predicts university students' final exam scores based on their daily habits using a Linear Regression model.",
    version="1.0.0",
    docs_url="/docs",       # Swagger UI endpoint
    redoc_url="/redoc"      # ReDoc endpoint
)

# ---------------------------------------------------------------------------
# 2. SECURE CORS CONFIGURATION
# ---------------------------------------------------------------------------
# CORS (Cross-Origin Resource Sharing) protects the API from being accessed 
# by unauthorized websites. We DO NOT use allow_origins=["*"] because that 
# allows any malicious site to make requests to our API via a user's browser.

app.add_middleware(
    CORSMiddleware,
    
    # allow_origins: A strict whitelist of domains permitted to call the API.
    # - "http://localhost:3000": Allows local frontend development (e.g., React/Flutter Web).
    # - "http://10.0.2.2:8000": Allows Android emulators to reach the host machine's localhost.
    # - "https://yourapp.onrender.com": Placeholder for your deployed frontend URL.
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:8000",
        "http://10.0.2.2:8000", 
        "https://student-predictor-apis.onrender.com"
    ],
    
    # allow_credentials: Set to True to support cookies and HTTP authentication 
    # headers. Kept True as best practice for secure, stateful applications.
    allow_credentials=True,
    
    # allow_methods: Restricts the HTTP verbs that can be used in cross-origin requests.
    # We only need POST (for /predict and /retrain), OPTIONS (for preflight checks), 
    # and GET (for the /docs page).
    allow_methods=["GET", "POST", "OPTIONS"],
    
    # allow_headers: Restricts which HTTP headers the browser is allowed to send.
    # "Content-Type" is strictly required so the browser can send JSON payloads.
    allow_headers=["Content-Type", "Authorization"],
)

# ---------------------------------------------------------------------------
# 3. INCLUDE ROUTERS
# ---------------------------------------------------------------------------
# This maps the endpoints defined in our other files to the main app.
# e.g., /api/v1/predict and /api/v1/retrain
app.include_router(prediction_router)
app.include_router(retrain_router)

# ---------------------------------------------------------------------------
# 4. ROOT ENDPOINT
# ---------------------------------------------------------------------------
@app.get("/", tags=["Health"])
async def root():
    """Basic health check to verify the API is running."""
    return {
        "message": "Student Performance Prediction API is running.",
        "docs": "/docs"
    }