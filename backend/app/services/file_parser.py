from __future__ import annotations

from io import BytesIO, StringIO
from pathlib import Path
from typing import Any
import unicodedata

import pandas as pd
from fastapi import HTTPException, UploadFile

from app.schemas import StudentInput

MAX_UPLOAD_SIZE_MB = 10
MAX_UPLOAD_SIZE_BYTES = MAX_UPLOAD_SIZE_MB * 1024 * 1024

EXPECTED_COLUMNS = [
    "student_name",
    "age",
    "G1",
    "G2",
    "G3",
    "absences",
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
    "activities",
    "internet",
    "schoolsup",
    "famsup",
    "romantic",
]

REQUIRED_COLUMNS = ["student_name"]

COLUMN_ALIASES = {
    "student_name": "student_name",
    "student name": "student_name",
    "nombre": "student_name",
    "nombre completo": "student_name",
    "nombres completos": "student_name",
    "alumno": "student_name",
    "alumna": "student_name",
    "estudiante": "student_name",
    "estudiantes": "student_name",

    "nombres": "first_name",
    "primer nombre": "first_name",
    "apellidos": "last_name",
    "apellido": "last_name",

    "id": "student_id",
    "studentid": "student_id",
    "student_id": "student_id",
    "student id": "student_id",
    "codigo": "student_id",
    "cod estudiante": "student_id",
    "codigo estudiante": "student_id",
    "id estudiante": "student_id",

    "edad": "age",
    "age": "age",

    "g1": "G1",
    "nota 1": "G1",
    "nota1": "G1",
    "primer parcial": "G1",

    "g2": "G2",
    "nota 2": "G2",
    "nota2": "G2",
    "segundo parcial": "G2",

    "g3": "G3",
    "nota 3": "G3",
    "nota3": "G3",
    "nota final": "G3",
    "final": "G3",

    "absences": "absences",
    "ausencias": "absences",
    "faltas": "absences",
    "inasistencias": "absences",

    "studytime": "studytime",
    "tiempo estudio": "studytime",
    "tiempo de estudio": "studytime",
    "horas estudio": "studytime",

    "failures": "failures",
    "reprobadas": "failures",
    "cursos reprobados": "failures",
    "fallas": "failures",

    "freetime": "freetime",
    "tiempo libre": "freetime",

    "goout": "goout",
    "salidas": "goout",
    "salidas amigos": "goout",

    "dalc": "Dalc",
    "consumo diario": "Dalc",
    "consumo alcohol diario": "Dalc",

    "walc": "Walc",
    "consumo fin semana": "Walc",
    "consumo alcohol fin semana": "Walc",

    "health": "health",
    "salud": "health",

    "traveltime": "traveltime",
    "tiempo viaje": "traveltime",
    "viaje": "traveltime",

    "famrel": "famrel",
    "relacion familiar": "famrel",
    "relaciones familiares": "famrel",

    "medu": "Medu",
    "madre educacion": "Medu",
    "educacion madre": "Medu",

    "fedu": "Fedu",
    "padre educacion": "Fedu",
    "educacion padre": "Fedu",

    "activities": "activities",
    "actividades": "activities",
    "actividades extracurriculares": "activities",

    "internet": "internet",

    "schoolsup": "schoolsup",
    "apoyo escolar": "schoolsup",

    "famsup": "famsup",
    "apoyo familiar": "famsup",

    "romantic": "romantic",
    "romantico": "romantic",
    "relacion romantica": "romantic",
}


def strip_accents(text: str) -> str:
    normalized = unicodedata.normalize("NFKD", text)
    return "".join(char for char in normalized if not unicodedata.combining(char))


def normalize_key(value: Any) -> str:
    text = str(value).strip()
    text = strip_accents(text)
    text = text.lower()
    text = text.replace("_", " ").replace("-", " ")
    text = " ".join(text.split())
    return text


def normalize_column_name(column: Any) -> str:
    raw = str(column).strip()

    if raw in EXPECTED_COLUMNS:
        return raw

    compact = normalize_key(raw)

    if compact in COLUMN_ALIASES:
        return COLUMN_ALIASES[compact]

    underscored = compact.replace(" ", "_")
    if underscored in COLUMN_ALIASES:
        return COLUMN_ALIASES[underscored]

    for expected in EXPECTED_COLUMNS:
        if compact == expected.lower():
            return expected

    return raw


def clean_cell(value: Any) -> Any:
    if pd.isna(value):
        return None

    if isinstance(value, str):
        value = value.strip()
        if value == "":
            return None

    return value


def is_instruction_row(name: str) -> bool:
    import re
    name_clean = name.strip().lower()
    if name_clean == "instrucciones":
        return True
    # Si empieza con un número seguido de punto (ej: "1. ", "12. ", "3. ")
    if re.match(r'^\d+\s*\.\s*', name_clean):
        return True
    # Frases típicas de las celdas de instrucciones en la plantilla
    instruction_keywords = [
        "no necesitas colocar",
        "la primera columna",
        "son notas de",
        "permitidos:",
        "ejemplo:"
    ]
    for kw in instruction_keywords:
        if kw in name_clean:
            return True
    return False


def dataframe_to_students(df: pd.DataFrame) -> list[StudentInput]:
    if df.empty:
        raise HTTPException(
            status_code=400,
            detail="El archivo no contiene estudiantes."
        )

    df = df.rename(columns={column: normalize_column_name(column) for column in df.columns})

    if "student_name" not in df.columns:
        if "first_name" in df.columns and "last_name" in df.columns:
            df["student_name"] = (
                df["first_name"].fillna("").astype(str).str.strip()
                + " "
                + df["last_name"].fillna("").astype(str).str.strip()
            ).str.strip()
        elif "first_name" in df.columns:
            df["student_name"] = df["first_name"]
        else:
            raise HTTPException(
                status_code=422,
                detail={
                    "message": "El Excel debe tener una columna con el nombre del alumno.",
                    "accepted_names": [
                        "student_name",
                        "nombre",
                        "nombre completo",
                        "alumno",
                        "alumna",
                        "estudiante",
                        "nombres + apellidos",
                    ],
                    "expected_columns": EXPECTED_COLUMNS,
                },
            )

    if "student_id" not in df.columns:
        df["student_id"] = [f"STU{index + 1:03d}" for index in range(len(df))]

    students: list[StudentInput] = []
    errors: list[str] = []

    for row_index, row in df.iterrows():
        payload: dict[str, Any] = {}
        is_empty_row = True

        for column in df.columns:
            val = clean_cell(row[column])
            if val is not None:
                is_empty_row = False
                payload[column] = val

        if is_empty_row:
            continue

        if "student_name" not in payload or not payload["student_name"]:
            payload["student_name"] = f"Estudiante {row_index + 1}"

        # Filtrar si la fila es de instrucciones de la plantilla
        if is_instruction_row(str(payload["student_name"])):
            continue

        if "student_id" not in payload or not payload["student_id"]:
            payload["student_id"] = f"STU{row_index + 1:03d}"

        try:
            students.append(StudentInput(**payload))
        except Exception as exc:
            # Simplificar el mensaje de error de Pydantic para el usuario
            errors.append(f"Fila {row_index + 2}: {str(exc)}")

    if errors:
        raise HTTPException(
            status_code=422,
            detail={
                "message": "Algunas filas no cumplen el esquema esperado.",
                "errors": errors[:20],
                "expected_columns": EXPECTED_COLUMNS,
            },
        )

    return students


async def read_students_from_upload(
    file: UploadFile,
    sheet_name: str | None = None
) -> list[StudentInput]:
    filename = file.filename or ""
    suffix = Path(filename).suffix.lower()
    contents = await file.read()

    if not contents:
        raise HTTPException(
            status_code=400,
            detail="El archivo está vacío."
        )

    if len(contents) > MAX_UPLOAD_SIZE_BYTES:
        raise HTTPException(
            status_code=413,
            detail=f"El archivo supera {MAX_UPLOAD_SIZE_MB} MB."
        )

    try:
        if suffix in {".xlsx", ".xlsm"}:
            excel_kwargs: dict[str, Any] = {}

            if sheet_name:
                excel_kwargs["sheet_name"] = sheet_name

            df_or_dict = pd.read_excel(BytesIO(contents), **excel_kwargs)

            if isinstance(df_or_dict, dict):
                first_sheet = next(iter(df_or_dict.values()))
                df = first_sheet
            else:
                df = df_or_dict

        elif suffix == ".csv":
            text = contents.decode("utf-8-sig")
            df = pd.read_csv(StringIO(text))

        else:
            raise HTTPException(
                status_code=400,
                detail="Formato no soportado. Sube un archivo .xlsx, .xlsm o .csv."
            )

    except HTTPException:
        raise

    except Exception as exc:
        raise HTTPException(
            status_code=400,
            detail=f"No se pudo leer el archivo: {exc}"
        ) from exc

    return dataframe_to_students(df)