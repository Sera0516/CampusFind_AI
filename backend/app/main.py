
import os
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer
from fastapi.staticfiles import StaticFiles
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app.api.assistant import router as assistant_router
from app.api.claims import router as claims_router
from app.api.notifications import router as notifications_router
from app.api.items import router as items_router
from app.api.auth import router as auth_router

from app.db.session import engine
from app.db.base import Base
from app import models


# Enable JWT Bearer authentication in Swagger UI
security = HTTPBearer()

# Image upload directory
UPLOAD_DIR = Path(__file__).resolve().parents[1] / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

app = FastAPI(
    title="CampusFind AI",
    description="Intelligent Campus Lost and Found Platform",
    version="1.0.0",
    swagger_ui_parameters={"persistAuthorization": True}
)

# CORS Configuration
cors_origins = os.getenv(
    "CORS_ORIGINS",
    "http://localhost:4200,http://127.0.0.1:4200"
)

allowed_origins = [
    origin.strip()
    for origin in cors_origins.split(",")
    if origin.strip()
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

# Serve uploaded images
app.mount(
    "/uploads",
    StaticFiles(directory=str(UPLOAD_DIR)),
    name="uploads"
)

# Register API routers
app.include_router(items_router)
app.include_router(auth_router)
app.include_router(claims_router)
app.include_router(notifications_router)
app.include_router(assistant_router)


# Create database tables
@app.on_event("startup")
def create_tables():
    Base.metadata.create_all(bind=engine)


# Root endpoint
@app.get("/")
def root():
    return {
        "message": "Welcome to CampusFind AI",
        "status": "running"
    }


# Application health check
@app.get("/health")
def health():
    return {
        "status": "healthy",
        "application": "CampusFind AI"
    }


# Database health check
@app.get("/health/database")
def database_health():
    try:
        with engine.connect() as connection:
            value = connection.execute(text("SELECT 1")).scalar()

        return {
            "status": "connected",
            "test_query_result": value
        }

    except SQLAlchemyError as exc:
        print("DATABASE HEALTH ERROR:", repr(exc))

        raise HTTPException(
            status_code=503,
            detail="Database connection failed"
        )
