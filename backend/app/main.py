from __future__ import annotations

import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.schemas import (
    BatchPredictionRequest,
    FeedbackRequest,
    FeedbackResponse,
    GroupGenerationRequest,
    GroupGenerationResponse,
    HealthResponse,
    PredictionRequest,
    PredictionResponse,
)
from app.services.feedback_service import save_feedback
from app.services.grouping_service import generate_groups
from app.services.model_service import model_service

logging.basicConfig(level=logging.INFO)
settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="API para clasificar perfiles estudiantiles y generar grupos colaborativos balanceados.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup_event() -> None:
    model_service.load()


@app.get("/")
def root() -> dict[str, str]:
    return {
        "message": "API del Arquitecto de Grupos de Alto Rendimiento",
        "docs": "/docs",
        "health": "/health",
    }


@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(
        status="ok" if model_service.loaded else "model_not_loaded",
        app=settings.app_name,
        version=settings.app_version,
        model_loaded=model_service.loaded,
    )


@app.get("/api/v1/model/schema")
def model_schema() -> dict:
    return model_service.schema()


@app.post("/api/v1/predict-profile", response_model=PredictionResponse)
def predict_profile(request: PredictionRequest) -> PredictionResponse:
    return model_service.predict_one(request.student)


@app.post("/api/v1/predict-profiles", response_model=list[PredictionResponse])
def predict_profiles(request: BatchPredictionRequest) -> list[PredictionResponse]:
    return [model_service.predict_one(student) for student in request.students]


@app.post("/api/v1/generate-groups", response_model=GroupGenerationResponse)
def generate_student_groups(request: GroupGenerationRequest) -> GroupGenerationResponse:
    return generate_groups(request)


@app.post("/api/v1/feedback", response_model=FeedbackResponse)
def feedback(request: FeedbackRequest) -> FeedbackResponse:
    return save_feedback(request)
