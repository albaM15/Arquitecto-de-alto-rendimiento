from __future__ import annotations

import logging
from pathlib import Path

import boto3
from botocore.exceptions import BotoCoreError, ClientError

logger = logging.getLogger(__name__)


def download_model_artifacts_from_s3(bucket: str | None, destination_dir: str) -> None:
    """Descarga artefactos del modelo desde S3 si se configuró MODEL_S3_BUCKET.

    La API funciona también sin S3 porque los archivos .joblib están copiados en
    backend/models. En AWS, S3 permite actualizar artefactos sin cambiar código.
    """
    if not bucket:
        return

    destination = Path(destination_dir)
    destination.mkdir(parents=True, exist_ok=True)

    required_file = destination / "random_forest_model.joblib"
    if required_file.exists():
        logger.info("Modelos locales encontrados; no se descarga desde S3.")
        return

    s3 = boto3.client("s3")
    try:
        objects = s3.list_objects_v2(Bucket=bucket).get("Contents", [])
        for obj in objects:
            key = obj["Key"]
            if not key.endswith((".joblib", ".json")):
                continue
            target = destination / Path(key).name
            logger.info("Descargando s3://%s/%s -> %s", bucket, key, target)
            s3.download_file(bucket, key, str(target))
    except (BotoCoreError, ClientError) as exc:
        logger.warning("No se pudieron descargar modelos desde S3: %s", exc)
