"""
backend/main.py
---------------
FastAPI application entry point.
Registers all API routers, configures CORS, and initialises the database.
"""

import sys
import os

# Make project root importable
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from database.db import init_db
from backend.routers import auth, resume, jobs, interview, dashboard

# ── Initialise DB on startup ──────────────────────────────────────────────────
init_db()

app = FastAPI(
    title="Career Assistance System API",
    description=(
        "AI-powered Resume Analysis, Job Recommendation, Skill-Gap Analysis, "
        "and Interview Preparation platform."
    ),
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
)

# ── CORS (allow Streamlit frontend) ───────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],          # tighten in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Serve uploaded files as static ────────────────────────────────────────────
UPLOADS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "uploads")
os.makedirs(UPLOADS_DIR, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=UPLOADS_DIR), name="uploads")

# ── Register routers ──────────────────────────────────────────────────────────
app.include_router(auth.router,      prefix="/api/auth",      tags=["Authentication"])
app.include_router(resume.router,    prefix="/api/resume",    tags=["Resume Analysis"])
app.include_router(jobs.router,      prefix="/api/jobs",      tags=["Job Recommendations"])
app.include_router(interview.router, prefix="/api/interview", tags=["Interview"])
app.include_router(dashboard.router, prefix="/api/dashboard", tags=["Dashboard"])


@app.get("/", tags=["Health"])
def root():
    return {
        "service": "Career Assistance System",
        "status":  "running",
        "docs":    "/api/docs",
    }


@app.get("/api/health", tags=["Health"])
def health_check():
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)
