from __future__ import annotations

import json
import logging
import math
import warnings
from pathlib import Path
from typing import Any

import joblib
import numpy as np

from app.config import get_settings
from app.schemas import PredictionResponse, StudentInput
from app.services.storage_service import download_model_artifacts_from_s3

logger = logging.getLogger(__name__)

DEFAULT_PROFILE_MAP = {
    0: "Líder Técnico",
    1: "Colaborador Analítico",
    2: "Comunicador Social",
    3: "Ejecutor Práctico",
    4: "Perfil en Desarrollo",
}

DEFAULT_MODEL_FEATURES = [
    "G1",
    "G2",
    "G3",
    "absences",
    "age",
    "studytime",
    "failures",
    "freetime",
    "goout",
    "Dalc",
    "Walc",
    "health",
    "traveltime",
    "famrel",
    "Medu",
    "Fedu",
    "indice_rendimiento",
    "tendencia_calificaciones",
    "indice_participacion",
    "perfil_social",
    "autonomia_estudio",
    "estilo_liderazgo",
    "riesgo_academico",
    "balance_social",
]

NUMERIC_DEFAULTS = {
    "G1": 12.0,
    "G2": 12.0,
    "G3": 12.0,
    "absences": 0.0,
    "age": 17.0,
    "studytime": 2.0,
    "failures": 0.0,
    "freetime": 3.0,
    "goout": 3.0,
    "Dalc": 1.0,
    "Walc": 1.0,
    "health": 3.0,
    "traveltime": 1.0,
    "famrel": 4.0,
    "Medu": 2.0,
    "Fedu": 2.0,
}


def as_binary(value: Any) -> float:
    if isinstance(value, bool):
        return 1.0 if value else 0.0

    if isinstance(value, (int, float)):
        return 1.0 if float(value) > 0 else 0.0

    text = str(value).strip().lower()

    return 1.0 if text in {"yes", "si", "sí", "true", "1", "y"} else 0.0


def safe_float(value: Any, default: float) -> float:
    try:
        if value is None or value == "":
            return default

        return float(value)

    except (TypeError, ValueError):
        return default


class ModelService:
    def __init__(self) -> None:
        self.settings = get_settings()
        self.model_dir = Path(self.settings.model_dir)

        self.rf_model: Any | None = None
        self.scaler: Any | None = None

        self.profile_map: dict[int, str] = DEFAULT_PROFILE_MAP.copy()
        self.model_features: list[str] = DEFAULT_MODEL_FEATURES.copy()
        self.model_version = "rf-kmedoids-v1"

    @property
    def loaded(self) -> bool:
        return self.rf_model is not None

    def load(self) -> None:
        download_model_artifacts_from_s3(
            self.settings.model_s3_bucket,
            str(self.model_dir)
        )

        rf_path = self.model_dir / "random_forest_model.joblib"
        scaler_path = self.model_dir / "scaler.joblib"
        profiles_path = self.model_dir / "profiles.json"
        features_path = self.model_dir / "selected_features.json"

        if not rf_path.exists():
            raise FileNotFoundError(f"No se encontró el modelo Random Forest en {rf_path}")

        self.rf_model = joblib.load(rf_path)
        logger.info("Random Forest cargado desde %s", rf_path)

        if scaler_path.exists():
            self.scaler = joblib.load(scaler_path)
            logger.info("Scaler cargado desde %s", scaler_path)

        if profiles_path.exists():
            with profiles_path.open("r", encoding="utf-8") as file:
                loaded_profiles = json.load(file)

            self.profile_map = {
                int(key): value
                for key, value in loaded_profiles.items()
            }

        if features_path.exists():
            with features_path.open("r", encoding="utf-8") as file:
                self.model_features = json.load(file)

        expected = getattr(self.rf_model, "n_features_in_", len(self.model_features))

        if expected != len(self.model_features):
            logger.warning(
                "El RF espera %s features, pero selected_features tiene %s. Se ajustará por padding/truncado.",
                expected,
                len(self.model_features),
            )

    def schema(self) -> dict[str, Any]:
        expected = (
            getattr(self.rf_model, "n_features_in_", len(self.model_features))
            if self.rf_model
            else len(self.model_features)
        )

        scaler_features = []

        if self.scaler is not None and hasattr(self.scaler, "feature_names_in_"):
            scaler_features = list(self.scaler.feature_names_in_)

        return {
            "model_version": self.model_version,
            "expected_model_features": expected,
            "feature_order": self.model_features,
            "scaler_features": scaler_features,
            "profiles": self.profile_map,
        }

    def _raw_values(self, student: StudentInput) -> dict[str, Any]:
        data = student.model_dump()
        extra = getattr(student, "model_extra", None) or {}
        data.update(extra)

        return data

    def _build_feature_dict(self, student: StudentInput) -> dict[str, float]:
        data = self._raw_values(student)

        raw = {
            name: safe_float(data.get(name), default)
            for name, default in NUMERIC_DEFAULTS.items()
        }

        activities = as_binary(data.get("activities", 0))
        internet = as_binary(data.get("internet", 1))
        schoolsup = as_binary(data.get("schoolsup", 0))
        famsup = as_binary(data.get("famsup", 1))
        romantic = as_binary(data.get("romantic", 0))

        indice_rendimiento = (raw["G1"] + raw["G2"] + 2 * raw["G3"]) / 4
        tendencia_calificaciones = raw["G3"] - raw["G1"]
        indice_participacion = (activities + internet + (1 - schoolsup)) / 3
        perfil_social = (raw["goout"] + raw["famrel"] + romantic) / 3
        autonomia_estudio = raw["studytime"] + internet - famsup
        estilo_liderazgo = (
            1.0
            if indice_rendimiento >= 14 and indice_participacion >= 0.66
            else 0.0
        )
        riesgo_academico = (
            raw["failures"]
            + math.log1p(raw["absences"])
            + (1.0 if raw["G1"] < 10 else 0.0)
        )
        balance_social = raw["freetime"] - raw["goout"]

        feature_dict = {
            **raw,
            "indice_rendimiento": indice_rendimiento,
            "tendencia_calificaciones": tendencia_calificaciones,
            "indice_participacion": indice_participacion,
            "perfil_social": perfil_social,
            "autonomia_estudio": autonomia_estudio,
            "estilo_liderazgo": estilo_liderazgo,
            "riesgo_academico": riesgo_academico,
            "balance_social": balance_social,
        }

        if self.scaler is not None and hasattr(self.scaler, "feature_names_in_"):
            scaler_features = list(self.scaler.feature_names_in_)

            scaler_input = np.array([
                [
                    safe_float(
                        feature_dict.get(name),
                        NUMERIC_DEFAULTS.get(name, 0.0)
                    )
                    for name in scaler_features
                ]
            ])

            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                scaled = self.scaler.transform(scaler_input)[0]

            for name, value in zip(scaler_features, scaled):
                feature_dict[name] = float(value)

        return feature_dict

    def vectorize(self, student: StudentInput) -> np.ndarray:
        feature_dict = self._build_feature_dict(student)

        vector = [
            float(feature_dict.get(name, 0.0))
            for name in self.model_features
        ]

        expected = (
            getattr(self.rf_model, "n_features_in_", len(vector))
            if self.rf_model
            else len(vector)
        )

        if len(vector) < expected:
            vector.extend([0.0] * (expected - len(vector)))

        elif len(vector) > expected:
            vector = vector[:expected]

        return np.array([vector], dtype=float)

    def predict_one(self, student: StudentInput) -> PredictionResponse:
        if self.rf_model is None:
            self.load()

        vector = self.vectorize(student)

        prediction = int(self.rf_model.predict(vector)[0])

        probabilities_raw = (
            self.rf_model.predict_proba(vector)[0]
            if hasattr(self.rf_model, "predict_proba")
            else []
        )

        classes = list(
            getattr(self.rf_model, "classes_", range(len(probabilities_raw)))
        )

        probabilities = {
            self.profile_map.get(int(cls), str(cls)): round(float(prob), 4)
            for cls, prob in zip(classes, probabilities_raw)
        }

        confidence = max(probabilities.values()) if probabilities else 1.0
        profile_name = self.profile_map.get(prediction, f"Perfil {prediction}")

        explanation = (
            f"El estudiante fue clasificado como '{profile_name}' porque sus variables académicas, "
            "conductuales y sociales son más similares a ese perfil aprendido por el modelo."
        )

        return PredictionResponse(
            student_id=student.student_id or "",
            student_name=student.student_name,
            profile_id=prediction,
            profile_name=profile_name,
            confidence=round(float(confidence), 4),
            probabilities=probabilities,
            model_version=self.model_version,
            explanation=explanation,
        )


model_service = ModelService()