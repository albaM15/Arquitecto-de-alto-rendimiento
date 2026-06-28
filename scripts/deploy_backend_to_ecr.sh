#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
INFRA_DIR="$ROOT_DIR/infra"
BACKEND_DIR="$ROOT_DIR/backend"

REGION="$(terraform -chdir="$INFRA_DIR" output -raw aws_region)"
ECR_REPO="$(terraform -chdir="$INFRA_DIR" output -raw ecr_repository_url)"
ACCOUNT_ID="$(aws sts get-caller-identity --query Account --output text)"
IMAGE_URI="$ECR_REPO:latest"

echo "==> Login en ECR: $ACCOUNT_ID / $REGION"
aws ecr get-login-password --region "$REGION" | docker login --username AWS --password-stdin "$ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com"

echo "==> Build imagen backend"
docker build -t "$IMAGE_URI" "$BACKEND_DIR"

echo "==> Push imagen backend"
docker push "$IMAGE_URI"

echo "==> Aplicando Terraform con imagen $IMAGE_URI"
terraform -chdir="$INFRA_DIR" apply -var="backend_image_uri=$IMAGE_URI"

echo "Backend desplegado: $(terraform -chdir="$INFRA_DIR" output -raw backend_url)"
