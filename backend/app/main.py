from __future__ import annotations

import logging
from pathlib import Path

from fastapi import FastAPI, File, Form, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

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
from app.services.file_parser import EXPECTED_COLUMNS, read_students_from_upload
from app.services.grouping_service import generate_groups
from app.services.model_service import model_service

logging.basicConfig(level=logging.INFO)

settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="API para clasificar perfiles estudiantiles y generar grupos colaborativos balanceados desde Excel o JSON.",
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
        "health": "/api/v1/health",
        "template": "/api/v1/files/template",
    }


@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(
        status="ok" if model_service.loaded else "model_not_loaded",
        app=settings.app_name,
        version=settings.app_version,
        model_loaded=model_service.loaded,
    )


@app.get("/api/v1/health", response_model=HealthResponse)
def api_health() -> HealthResponse:
    return health()


@app.get("/api/v1/model/schema")
def model_schema() -> dict:
    schema = model_service.schema()
    schema["excel_expected_columns"] = EXPECTED_COLUMNS
    return schema


@app.get("/api/v1/files/template")
def download_excel_template() -> FileResponse:
    template_path = (
        Path(__file__).resolve().parents[1]
        / "templates"
        / "plantilla_estudiantes.xlsx"
    )

    return FileResponse(
        path=template_path,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        filename="plantilla_estudiantes_edutech.xlsx",
    )


@app.post("/api/v1/predict-profile", response_model=PredictionResponse)
def predict_profile(request: PredictionRequest) -> PredictionResponse:
    return model_service.predict_one(request.student)


@app.post("/api/v1/predict-profiles", response_model=list[PredictionResponse])
def predict_profiles(request: BatchPredictionRequest) -> list[PredictionResponse]:
    return [
        model_service.predict_one(student)
        for student in request.students
    ]


@app.post("/api/v1/generate-groups", response_model=GroupGenerationResponse)
def generate_student_groups(
    request: GroupGenerationRequest
) -> GroupGenerationResponse:
    return generate_groups(request)


@app.post("/api/v1/files/predict-profiles", response_model=list[PredictionResponse])
async def predict_profiles_from_file(
    file: UploadFile = File(...),
    sheet_name: str | None = Form(default=None),
) -> list[PredictionResponse]:
    students = await read_students_from_upload(file, sheet_name)

    return [
        model_service.predict_one(student)
        for student in students
    ]


@app.post("/api/v1/files/generate-groups", response_model=GroupGenerationResponse)
async def generate_groups_from_file(
    file: UploadFile = File(...),
    course_id: str = Form(default="CURSO_ML_2026"),
    group_size: int = Form(default=4),
    sheet_name: str | None = Form(default=None),
) -> GroupGenerationResponse:
    students = await read_students_from_upload(file, sheet_name)

    request = GroupGenerationRequest(
        course_id=course_id,
        group_size=group_size,
        students=students,
    )

    return generate_groups(request)


@app.post("/api/v1/feedback", response_model=FeedbackResponse)
def feedback(request: FeedbackRequest) -> FeedbackResponse:
    return save_feedback(request)