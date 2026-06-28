from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class StudentInput(BaseModel):
    """
    Perfil de entrada de un estudiante.

    El profesor sube nombres de alumnos, no IDs.
    El student_id es opcional porque el backend puede generarlo automáticamente.
    """

    model_config = ConfigDict(extra="allow")

    student_id: str | None = Field(default=None, examples=["STU001"])
    student_name: str = Field(..., examples=["Ana Torres"])

    age: float = Field(17, ge=10, le=80)
    G1: float = Field(12, ge=0, le=20)
    G2: float = Field(12, ge=0, le=20)
    G3: float = Field(12, ge=0, le=20)
    absences: float = Field(0, ge=0)
    studytime: float = Field(2, ge=1, le=4)
    failures: float = Field(0, ge=0)
    freetime: float = Field(3, ge=1, le=5)
    goout: float = Field(3, ge=1, le=5)
    Dalc: float = Field(1, ge=1, le=5)
    Walc: float = Field(1, ge=1, le=5)
    health: float = Field(3, ge=1, le=5)
    traveltime: float = Field(1, ge=1, le=4)
    famrel: float = Field(4, ge=1, le=5)
    Medu: float = Field(2, ge=0, le=4)
    Fedu: float = Field(2, ge=0, le=4)

    activities: Any = Field("no")
    internet: Any = Field("yes")
    schoolsup: Any = Field("no")
    famsup: Any = Field("yes")
    romantic: Any = Field("no")


class PredictionRequest(BaseModel):
    student: StudentInput


class PredictionResponse(BaseModel):
    student_id: str
    student_name: str
    profile_id: int
    profile_name: str
    confidence: float
    probabilities: dict[str, float]
    model_version: str
    explanation: str


class BatchPredictionRequest(BaseModel):
    students: list[StudentInput]


class GroupGenerationRequest(BaseModel):
    course_id: str = Field(..., examples=["CURSO_ML_2026"])
    group_size: int = Field(4, ge=2, le=8)
    students: list[StudentInput]


class GroupMember(BaseModel):
    student_id: str
    student_name: str
    profile_id: int
    profile_name: str
    confidence: float
    G1: float
    risk_score: float


class GeneratedGroup(BaseModel):
    group_id: int
    members: list[GroupMember]
    average_G1: float
    profile_distribution: dict[str, int]
    explanation: str


class GroupGenerationResponse(BaseModel):
    course_id: str
    group_size: int
    generated_at: datetime
    total_students: int
    groups: list[GeneratedGroup]


class FeedbackRequest(BaseModel):
    course_id: str
    group_id: int
    accepted: bool
    teacher_comment: str | None = None
    manual_changes: list[str] = Field(default_factory=list)


class FeedbackResponse(BaseModel):
    feedback_id: str
    stored: bool
    message: str


class HealthResponse(BaseModel):
    status: str
    app: str
    version: str
    model_loaded: bool