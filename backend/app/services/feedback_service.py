from __future__ import annotations

from datetime import datetime
from decimal import Decimal
import json
from uuid import uuid4

import boto3
from botocore.exceptions import BotoCoreError, ClientError

from app.config import get_settings
from app.schemas import FeedbackRequest, FeedbackResponse


def _to_dynamodb_item(payload: dict) -> dict:
    return json.loads(json.dumps(payload), parse_float=Decimal)


def save_feedback(feedback: FeedbackRequest) -> FeedbackResponse:
    settings = get_settings()
    feedback_id = str(uuid4())
    payload = {
        "pk": f"COURSE#{feedback.course_id}",
        "sk": f"FEEDBACK#{datetime.utcnow().isoformat()}#{feedback_id}",
        "feedback_id": feedback_id,
        "course_id": feedback.course_id,
        "group_id": feedback.group_id,
        "accepted": feedback.accepted,
        "teacher_comment": feedback.teacher_comment,
        "manual_changes": feedback.manual_changes,
        "created_at": datetime.utcnow().isoformat(),
    }

    if not settings.predictions_table:
        return FeedbackResponse(
            feedback_id=feedback_id,
            stored=False,
            message="Feedback recibido localmente. Configura PREDICTIONS_TABLE para guardarlo en DynamoDB.",
        )

    try:
        table = boto3.resource("dynamodb", region_name=settings.aws_region).Table(settings.predictions_table)
        table.put_item(Item=_to_dynamodb_item(payload))
        return FeedbackResponse(feedback_id=feedback_id, stored=True, message="Feedback guardado en DynamoDB.")
    except (BotoCoreError, ClientError) as exc:
        return FeedbackResponse(
            feedback_id=feedback_id,
            stored=False,
            message=f"No se pudo guardar en DynamoDB: {exc}",
        )
