from __future__ import annotations

from collections import Counter, defaultdict
from datetime import datetime
import math

from app.schemas import (
    GeneratedGroup,
    GroupGenerationRequest,
    GroupGenerationResponse,
    GroupMember,
    StudentInput,
)
from app.services.model_service import NUMERIC_DEFAULTS, model_service, safe_float


def _risk_score(student: StudentInput) -> float:
    data = student.model_dump()
    failures = safe_float(data.get("failures"), NUMERIC_DEFAULTS["failures"])
    absences = safe_float(data.get("absences"), NUMERIC_DEFAULTS["absences"])
    g1 = safe_float(data.get("G1"), NUMERIC_DEFAULTS["G1"])
    return round(failures + math.log1p(absences) + (1.0 if g1 < 10 else 0.0), 3)


def generate_groups(request: GroupGenerationRequest) -> GroupGenerationResponse:
    """Genera grupos balanceados por perfil, rendimiento y riesgo.

    La predicción del perfil la hace Random Forest. Esta función implementa la
    regla de negocio: mezclar perfiles complementarios y evitar que un grupo
    concentre demasiados estudiantes vulnerables o del mismo arquetipo.
    """
    if not request.students:
        return GroupGenerationResponse(
            course_id=request.course_id,
            group_size=request.group_size,
            generated_at=datetime.utcnow(),
            total_students=0,
            groups=[],
        )

    enriched: list[GroupMember] = []
    for student in request.students:
        pred = model_service.predict_one(student)
        g1 = safe_float(student.model_dump().get("G1"), NUMERIC_DEFAULTS["G1"])
        enriched.append(
            GroupMember(
                student_id=student.student_id,
                profile_id=pred.profile_id,
                profile_name=pred.profile_name,
                confidence=pred.confidence,
                G1=g1,
                risk_score=_risk_score(student),
            )
        )

    total_groups = max(1, math.ceil(len(enriched) / request.group_size))
    groups: list[list[GroupMember]] = [[] for _ in range(total_groups)]

    # 1) Separar por perfil para mezclar arquetipos.
    buckets: dict[int, list[GroupMember]] = defaultdict(list)
    for member in enriched:
        buckets[member.profile_id].append(member)

    # 2) Ordenar internamente por riesgo descendente para distribuir primero casos críticos.
    for bucket in buckets.values():
        bucket.sort(key=lambda item: (item.risk_score, -item.G1), reverse=True)

    # 3) Reparto round-robin por perfil, eligiendo el grupo con menor tamaño y menor promedio G1.
    for profile_id in sorted(buckets.keys(), key=lambda pid: len(buckets[pid]), reverse=True):
        for member in buckets[profile_id]:
            candidates = [index for index, group in enumerate(groups) if len(group) < request.group_size]
            if not candidates:
                candidates = list(range(total_groups))

            def score_group(index: int) -> tuple[int, float, int]:
                group = groups[index]
                avg_g1 = sum(item.G1 for item in group) / len(group) if group else 0.0
                same_profile_count = sum(1 for item in group if item.profile_id == member.profile_id)
                return (same_profile_count, avg_g1, len(group))

            target_index = min(candidates, key=score_group)
            groups[target_index].append(member)

    response_groups: list[GeneratedGroup] = []
    for index, group in enumerate(groups, start=1):
        if not group:
            continue
        avg_g1 = round(sum(member.G1 for member in group) / len(group), 2)
        distribution = Counter(member.profile_name for member in group)
        risk_count = sum(1 for member in group if member.risk_score >= 2.0)
        explanation = (
            f"Grupo con promedio académico G1={avg_g1}. "
            f"Incluye {len(distribution)} perfil(es) distinto(s) y {risk_count} estudiante(s) con riesgo académico alto. "
            "La asignación busca complementar rendimiento, participación y perfil social."
        )
        response_groups.append(
            GeneratedGroup(
                group_id=index,
                members=group,
                average_G1=avg_g1,
                profile_distribution=dict(distribution),
                explanation=explanation,
            )
        )

    return GroupGenerationResponse(
        course_id=request.course_id,
        group_size=request.group_size,
        generated_at=datetime.utcnow(),
        total_students=len(enriched),
        groups=response_groups,
    )
